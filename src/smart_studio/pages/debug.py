from functools import partial
from livenodes import viewer
import os
import json

from PyQt5.QtWidgets import QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QToolButton, QComboBox, QComboBox, QPushButton, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout, QScrollArea, QLabel

from PyQtAds import QtAds

import multiprocessing as mp

from livenodes.node import Node
from smart_studio.components.node_views import node_view_mapper, Debug_View
from smart_studio.components.page import Page, Action, ActionKind

class Debug(Page):

    def __init__(self, pipeline_path, pipeline, parent=None):
        super().__init__(parent=parent)

        self.pipeline = pipeline
        self._create_paths(pipeline_path)

        # === Setup buttons =================================================
        def toggle():
            nonlocal self
            if self.worker is None:
                self._start_pipeline()
                self.toggle.setText("Stop")
            else:
                self._stop_pipeline()
                self.toggle.setText("Start")

        self.toggle = QPushButton("Start")
        self.toggle.clicked.connect(toggle)

        buttons = QHBoxLayout()
        buttons.addWidget(self.toggle)


        # === Setup draw canvases =================================================
        self.nodes = Node.discover_graph(pipeline)
        self.draw_widgets = [Debug_View(n, view=node_view_mapper(self, n) if isinstance(n, viewer.View) else None) for n in self.nodes]
        
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.XmlCompressionEnabled, False)
        
        self.layout = QVBoxLayout(self)
        self.dock_manager = QtAds.CDockManager(self)
        self.layout.addWidget(self.dock_manager)
        self.layout.addLayout(buttons)
        self.widgets = []

        for widget, node in zip(self.draw_widgets, self.nodes):
            dock_widget = QtAds.CDockWidget(node.name)
            self.widgets.append(dock_widget)
            dock_widget.viewToggled.connect(partial(print, '=======', str(node), "qt emitted signal"))
            dock_widget.setWidget(widget)
            dock_widget.setFeature(QtAds.CDockWidget.DockWidgetClosable, False)

            self.dock_manager.addDockWidget(QtAds.BottomDockWidgetArea, dock_widget)

        if os.path.exists(self.pipeline_gui_path):
            with open(self.pipeline_gui_path, 'r') as f:
                self.dock_manager.restoreState(QtCore.QByteArray(f.read().encode()))

        # restore might remove some of the newly added widgets -> add it back in here
        for widget, node in zip(self.widgets, self.nodes):
            if widget.isClosed():
                # print('----', str(node))
                widget.setClosedState(False)
                self.dock_manager.addDockWidget(QtAds.RightDockWidgetArea, widget)


        # === Start pipeline =================================================
        self.worker_term_lock = mp.Lock()
        self.worker = None

    def _start_pipeline(self):
        self.worker_term_lock.acquire()
        self.worker = mp.Process(target=self.worker_start)
        # self.worker.daemon = True
        self.worker.start()

    def _stop_pipeline(self):
        self.worker_term_lock.release()
        self.worker.join(2)

        # yes, sometimes the program will then not return, but only if we also really need to kill the subprocesses!
        self.worker_term_lock.acquire()
        # self.pipeline.stop()
        
        print('Termination time in view!')
        self.worker.terminate()
        self.worker = None
        
    def worker_start(self):
        self.pipeline.start()
        self.worker_term_lock.acquire()

        print('Termination time in pipeline!')
        self.pipeline.stop()
        self.worker_term_lock.release()

    # i would have assumed __del__ would be the better fit, but that doesn't seem to be called when using del... for some reason
    # will be called in parent view, but also called on exiting the canvas
    def stop(self, *args, **kwargs):
        self._stop_pipeline()

        print('Terminating draw widgets')
        for widget in self.draw_widgets:
            widget.stop()

    def get_actions(self):
        return [ \
            Action(label="Back", fn=self.save, kind=ActionKind.BACK),
            # Action(label="Cancel", kind=ActionKind.BACK),
        ]

    def save(self):
        with open(self.pipeline_gui_path, 'w') as f:
            f.write(self.dock_manager.saveState().data().decode())

    def _create_paths(self, pipeline_path):
        self.pipeline_path = pipeline_path
        self.pipeline_gui_path = pipeline_path.replace('/pipelines/', '/gui/', 1).replace('.json', '_dock_debug.xml')

        gui_folder = '/'.join(self.pipeline_gui_path.split('/')[:-1])
        if not os.path.exists(gui_folder):
            os.mkdir(gui_folder)