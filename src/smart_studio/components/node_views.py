# import json
import yaml
import numpy as np
import multiprocessing as mp
from livenodes import viewer

from qtpy import QtCore
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import QTimer

from qtpy.QtWidgets import QSplitter, QVBoxLayout, QWidget, QHBoxLayout, QLabel

from .scroll_label import ScrollLabel
from .views.pyqt import QT_View
from .utils import is_installed

import logging
logger = logging.getLogger('smart-studio')

# TODO: make each subplot their own animation and use user customizable panels
# TODO: allow nodes to use qt directly -> also consider how to make this understandable to user (ie some nodes will not run everywhere then)

def node_view_mapper(parent, node):
    if isinstance(node, viewer.View_MPL):
        if is_installed('matplotlib'):
            from .views.matplotlib import MPL_View
            return MPL_View(node)
        else:
            raise ValueError('Matplotlib not installed, cannot load MPL_View')
    elif isinstance(node, viewer.View_QT):
        return QT_View(node, parent=parent)
    else:
        raise ValueError(f'Unkown Node type {str(node)}')

class Debug_Metrics(QWidget):
    def __init__(self, view=None, parent=None):
        super().__init__(parent=parent)

        layout_metrics = QVBoxLayout(self)
        if view is not None:
            self.fps = QLabel('FPS: xxx')
            layout_metrics.addWidget(self.fps)
        self.latency = QLabel('')
        layout_metrics.addWidget(self.latency)

class Debug_View(QWidget):
    def __init__(self, node, view=None, parent=None):
        super().__init__(parent=parent)

        self.view = view 
        self.node = node

        self.metrics = Debug_Metrics(view)

        self.log = ScrollLabel(keep_bottom=True)
        self.log_list = ['--- Log --------–-------']
        self.log.setText('\n'.join(self.log_list))

        self.state = ScrollLabel()

        self.layout = QSplitter(QtCore.Qt.Vertical)
        i = 0
        self.layout.addWidget(self.metrics)
        self.layout.setStretchFactor(i, 0)
        if view is not None:
            i = 1
            self.layout.addWidget(view)
            self.layout.setStretchFactor(i, 1)
        self.layout.addWidget(self.log)
        self.layout.setStretchFactor(i + 1, 1)
        self.layout.addWidget(self.state)
        self.layout.setStretchFactor(i + 2, 1)
        
        l = QHBoxLayout(self)
        l.addWidget(self.layout)

        self.val_queue = mp.Queue()
        self.forward_report = mp.Event()
        self.node.register_reporter(self.reporter)

        self.timer = QTimer(self)
        self.timer.setInterval(16) # max 60fps
        self.timer.timeout.connect(self.update)
        self.timer.start()
    
    @staticmethod
    def _rm_numpy(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, dict):
                    obj[k] = Debug_View._rm_numpy(v)
                elif isinstance(v, list):
                    obj[k] = [Debug_View._rm_numpy(i) for i in v]
                elif isinstance(v, np.ndarray):
                    obj[k] = v.tolist()
        return obj

    def update(self):
        # i = 0
        # print('-------------------')
        fps_str = None
        latency_str = None
        cur_state = None
        while not self.val_queue.empty():
            try:
                infos = self.val_queue.get_nowait()
                # i += 1
                # print(i)
                if 'fps' in infos:
                    fps = infos['fps']
                    fps_str = f"FPS: {fps['fps']:.2f} \nTotal frames: {fps['total_frames']}"
                if 'latency' in infos:
                    latency = infos['latency']
                    latency_str = f'Processing Duration: {latency["process"] * 1000:.5f}ms\nInvocation Interval: {latency["invocation"] * 1000:.5f}ms'
                if 'log' in infos:
                    self.log_list.append(infos['log'])
                    self.log_list = self.log_list[-100:]
                if 'current_state' in infos:
                    cur_state = infos['current_state']
            except Exception as err:
                logger.exception('Exception updating debug info')
        
        # TODO: my gut feeling is, that before the pipeline is started something in the node system alredy runs as fast as it can (should_draw or similar?) and thus blocks all cpu from the gui thread without producing anything
        # -> find and fix
        if fps_str is not None:
            # print(fps_str)
            self.metrics.fps.setText(fps_str)
        if latency_str is not None:
            # print(latency_str)
            self.metrics.latency.setText(latency_str)
        if cur_state is not None:
            # cur_state_str = json.dumps(cur_state, cls=NumpyEncoder, indent=2)
            cur_state_str = yaml.dump(self._rm_numpy(cur_state), default_flow_style=False, indent=2)
            # print(cur_state_str)
            self.state.setText(cur_state_str)
        self.log.setText('\n'.join(self.log_list))
        # print(len('\n'.join(self.log_list)))
        # print('-------------------')

    def reporter(self, **kwargs):
        # Try to acquire the lock without blocking
        if not self.forward_report.is_set():
            return 
        
        # TODO: clean this up and move it into the Time_per_call etc reporters
        if 'node' in kwargs and 'latency' not in kwargs:
            processing_duration = self.node._perf_user_fn.average()
            invocation_duration = self.node._perf_framework.average()
            kwargs['latency'] = {
                "process": processing_duration,
                "invocation": invocation_duration,
                "time_between_calls": (invocation_duration - processing_duration) * 1000
            }
            del kwargs['node']
        if self.val_queue is not None: 
            self.val_queue.put(kwargs)


    def sleep(self, sleep):
        # print('Setting to sleep', str(self.node), sleep)
        # change visibility hoping that makes qts rendering faster
        # TODO: check if that's actually the case
        self.setVisible(not sleep)

        # if there is no timer, ie the pipeline is not running -> do nothing
        if self.timer is None:
            return
        
        # if the pipeline is running and we want to sleep, stop the timer
        # otherwise (re-)start it 
        if sleep:
            self.timer.stop()
            self.forward_report.clear()
            if self.view is not None:
                self.view.pause()
        elif not self.timer.isActive():
            if self.view is not None:
                self.view.resume()
            self.forward_report.set()
            self.timer.start()

    def stop(self):
        if self.view is not None:
            self.view.stop()
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        if self.val_queue is not None:
            self.val_queue.close()
            self.val_queue = None

