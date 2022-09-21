from functools import partial
import os

from PyQt5.QtWidgets import QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtWidgets import QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout

from PyQtAds import QtAds

import multiprocessing as mp

from livenodes import Node, Graph, viewer
from livenodes.components.utils.logger import logger
from smart_studio.components.node_views import node_view_mapper, Debug_View
from smart_studio.components.page import Page, Action, ActionKind

class Debug(Page):

    def __init__(self, pipeline_path, pipeline, parent=None):
        super().__init__(parent=parent)

        self.pipeline = pipeline
        self.graph = Graph(start_node=pipeline)
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

        # === Setup item list =================================================
        sidebar_items = QVBoxLayout()
        sidebar_items.addLayout(buttons)
        sidebar_items.spacerItem()


        # === Create overall layout =================================================
        self.dock_manager = QtAds.CDockManager(self)

        self.layout = QHBoxLayout(self)
        self.layout.addLayout(sidebar_items, stretch=0)
        self.layout.addWidget(self.dock_manager, stretch=1)


        # === Setup draw canvases and add items to views =================================================
        self.nodes = Node.discover_graph(pipeline)
        self.draw_widgets = [Debug_View(n, view=node_view_mapper(self, n) if isinstance(n, viewer.View) else None) for n in self.nodes]
        
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.XmlCompressionEnabled, False)
        self.widgets = []

        def toggle(dock_widget, state):
            dock_widget.toggleView(state == QtCore.Qt.Checked)

        for widget, node in zip(self.draw_widgets, self.nodes):
            dock_widget = QtAds.CDockWidget(node.name)
            self.widgets.append(dock_widget)
            dock_widget.viewToggled.connect(partial(print, '=======', str(node), "qt emitted signal"))
            dock_widget.setWidget(widget)
            # dock_widget.setFeature(QtAds.CDockWidget.DockWidgetClosable, False)

            self.dock_manager.addDockWidget(QtAds.RightDockWidgetArea, dock_widget)

        if os.path.exists(self.pipeline_gui_path):
            with open(self.pipeline_gui_path, 'r') as f:
                self.dock_manager.restoreState(QtCore.QByteArray(f.read().encode()))

        # # restore might remove some of the newly added widgets -> add it back in here
        for dock_widget, node in zip(self.widgets, self.nodes):
            # sidebar_items.addWidget(dock_widget.toggleViewAction())
            box = QCheckBox(str(node))
            box.setChecked(not dock_widget.isClosed())
            sidebar_items.addWidget(box, stretch=0)
            # dock_widget.closed.connect()
            box.stateChanged.connect(partial(toggle, dock_widget))

            # if widget.isClosed():
            #     # print('----', str(node))
            #     widget.setClosedState(False)
            #     self.dock_manager.addDockWidget(QtAds.RightDockWidgetArea, widget)


        # === Start pipeline =================================================
        self.worker_term_lock = mp.Lock()
        self.worker = None

    def _start_pipeline(self):
        self.worker_term_lock.acquire()
        self.worker = mp.Process(target=self.worker_start)
        # self.worker.daemon = True
        self.worker.start()

    def _stop_pipeline(self):
        if self.worker is not None:
            self.worker_term_lock.release()
            print('Termination time in view!')
            self.worker_term_lock.acquire()
            self.worker_term_lock.release()
            print('View terminated')
            self.worker = None
        
    def worker_start(self):
        logger.info(f"Smart-Studio | Starting Worker")
        self.graph.start_all()
        self.worker_term_lock.acquire()

        logger.info(f"Smart-Studio | Stopping Worker")
        # timeout to make sure potential non-returning nodes do not block until eternity
        self.graph.stop_all(stop_timeout=2.0, close_timeout=2.0)
        self.worker_term_lock.release()
        logger.info(f"Smart-Studio | Worker Stopped")

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