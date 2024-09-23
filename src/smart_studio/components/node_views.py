import json
import multiprocessing as mp
from livenodes import viewer
from livenodes.components.utils.utils import NumpyEncoder

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
        self.layout.setStretchFactor(i + 2, 0)
        
        l = QHBoxLayout(self)
        l.addWidget(self.layout)

        self.val_queue = mp.Queue()

        def reporter(**kwargs):
            nonlocal self, node
            # TODO: clean this up and move it into the Time_per_call etc reporters
            if 'node' in kwargs and 'latency' not in kwargs:
                processing_duration = node._perf_user_fn.average()
                invocation_duration = node._perf_framework.average()
                kwargs['latency'] = {
                    "process": processing_duration,
                    "invocation": invocation_duration,
                    "time_between_calls": (invocation_duration - processing_duration) * 1000
                }
                del kwargs['node']
            if self.val_queue is not None: 
                self.val_queue.put(kwargs)

        node.register_reporter(reporter)

        def update():
            nonlocal self
            while not self.val_queue.empty():
                try:
                    infos = self.val_queue.get_nowait()
                    if 'fps' in infos:
                        fps = infos['fps']
                        self.metrics.fps.setText(f"FPS: {fps['fps']:.2f} \nTotal frames: {fps['total_frames']}")
                    if 'latency' in infos:
                        latency = infos['latency']
                        self.metrics.latency.setText(f'Processing Duration: {latency["process"] * 1000:.5f}ms\nInvocation Interval: {latency["invocation"] * 1000:.5f}ms')
                    if 'log' in infos:
                        self.log_list.append(infos['log'])
                        self.log_list = self.log_list[-100:]
                        self.log.setText('\n'.join(self.log_list))
                    if 'current_state' in infos:
                        self.state.setText(json.dumps(infos['current_state'], cls=NumpyEncoder, indent=2))
                except Exception as err:
                    logger.exception('Exception updating debug info')

        self.timer = QTimer(self)
        self.timer.setInterval(10) # max 100fps
        self.timer.timeout.connect(update)
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

