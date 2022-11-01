import json
import queue
import time
import traceback
import multiprocessing as mp
from livenodes import viewer
from livenodes.components.utils.utils import NumpyEncoder
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from matplotlib.figure import Figure
from matplotlib import animation
import matplotlib.pyplot as plt
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer

from vispy import app as vp_app
import vispy.plot as vp
from vispy import scene
vp_app.use_app('pyqt5')

from PyQt5.QtWidgets import QSplitter, QInputDialog, QMessageBox, QToolButton, QComboBox, QComboBox, QPushButton, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout, QScrollArea, QLabel

from .scroll_label import ScrollLabel

import seaborn as sns

sns.set_style("darkgrid")
sns.set_context("paper")

# TODO: make each subplot their own animation and use user customizable panels
# TODO: allow nodes to use qt directly -> also consider how to make this understandable to user (ie some nodes will not run everywhere then)

def node_view_mapper(parent, node):
    if isinstance(node, viewer.View_MPL):
        return MPL_View(node)
    elif isinstance(node, viewer.View_Vispy):
        return Vispy_View(node, parent=parent)
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
                    print(err)
                    # print(traceback.format_exc())

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



class QT_View(QWidget):
    def __init__(self, node, parent=None):
        super().__init__(parent=parent)

        if not isinstance(node, viewer.View_QT):
            raise ValueError('Node must be of Type (MPL) View')

        # self.setStyleSheet("QWidget { background-color: 'white' }") 
        self.setProperty("cssClass", "bg-white")
        artist_update_fn = node.init_draw(self)

        if artist_update_fn is not None:
            self.timer = QTimer(self)
            self.timer.setInterval(10) # max 100fps
            self.timer.timeout.connect(artist_update_fn)
            self.timer.start()

        # self.setBackgroundRole(True)
        # p = self.palette()
        # p.setColor(self.backgroundRole(), Qt.white)
        # self.setPalette(p)
    
    def stop(self):
        # self.timer.stop()
        pass

class Vispy_View(QWidget):
    def __init__(self, node, interval=0, parent=None):
        super().__init__(parent=parent)

        if not isinstance(node, viewer.View_Vispy):
            raise ValueError('Node must be of Type (Vispy) View')

        # self.fig = vp.Fig(size=(400, 300), app="pyqt5", show=False, parent=parent)
        # self.fig = vp.Fig(size=(400, 300), show=False, parent=parent)
        self.fig = scene.SceneCanvas(show=False, parent=self, bgcolor='white')
        node_update_fn = node.init_draw(self.fig)

        def update(*args, **kwargs):
            nonlocal self, node_update_fn
            if node_update_fn():
                self.update()

        self._timer = vp_app.Timer(interval=interval, connect=update, start=True)
    
    def get_qt_widget(self):
        return self.fig.native
    
    def stop(self):
        self._timer.stop()


class MPL_View(FigureCanvasQTAgg):

    def __init__(self, node, figsize=(4, 4), font = {'size': 10}, interval=10):
        super().__init__(Figure(figsize=figsize))

        if not isinstance(node, viewer.View_MPL):
            raise ValueError('Node must be of Type (MPL) View')

        plt.rc('font', **font)

        # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/subfigures.html
        # subfigs = self.figure.subfigures(rows, cols)  #, wspace=1, hspace=0.07)
        # we might create subfigs, but if each node has it's own qwidget, we do not need to and can instead just pass the entire figure
        artist_update_fn = node.init_draw(self.figure)

        def draw_update(i, **kwargs):
            try:
                return artist_update_fn(i, **kwargs)
            except Exception as err:
                print(err)
                print(traceback.format_exc())
            return []

        self.animation = animation.FuncAnimation(fig=self.figure,
                                                 func=draw_update,
                                                 interval=interval,
                                                 blit=True)

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()
        
        self.show()

    def stop(self):
        self.animation.pause()

