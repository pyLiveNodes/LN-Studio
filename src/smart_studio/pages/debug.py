import logging
from logging.handlers import QueueHandler
import os

from qtpy.QtWidgets import QHBoxLayout
from qtpy import QtCore, QtWidgets
from qtpy.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout

# from PyQtAds import QtAds
from smart_studio.qtpydocking import DockManager, DockWidget, DockWidgetArea
from smart_studio.qtpydocking.enums import DockWidgetFeature

import multiprocessing as mp
import threading as th

from livenodes import Node, Graph, viewer
from livenodes.components.utils.log import drain_log_queue
from smart_studio.components.node_views import node_view_mapper, Debug_View
from smart_studio.components.page import Page, Action, ActionKind

from qtpy.QtWidgets import QSplitter, QHBoxLayout

from smart_studio.components.edit_graph import QT_Graph_edit
from smart_studio.components.page import ActionKind, Page, Action


class Debug(Page):

    def __init__(self, pipeline_path, pipeline, node_registry, parent=None):
        super().__init__(parent=parent)

        if hasattr(pipeline, 'get_non_macro_node'):
            pipeline = pipeline.get_non_macro_node()

        self.pipeline = pipeline
        self.graph = Graph(start_node=pipeline)
        self.pipeline_path = pipeline_path
        self.pipeline_gui_path = pipeline_path.replace('.yml', '_gui_dock_debug.xml')


        # === Setup Start/Stop =================================================
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

        # === Setup Edit Side =================================================
        self.edit_graph = QT_Graph_edit(pipeline_path=pipeline_path, node_registry=node_registry, parent=self, read_only=True)
        self.edit_graph.setMinimumWidth(300)
        self.edit_graph.node_selected.connect(self.focus_node_view)

        # === Setup draw canvases and add items to views =================================================
        self.dock_manager = DockManager(self)
        self.nodes = Node.discover_graph(pipeline)
        self.draw_widgets = [Debug_View(n, view=node_view_mapper(self, n) if isinstance(n, viewer.View) else None, parent=self) for n in self.nodes]

        for widget, node in zip(self.draw_widgets, self.nodes):
            dock_widget = DockWidget(node.name)
            dock_widget.set_widget(widget)
            dock_widget.set_feature(DockWidgetFeature.closable, False)
            self.dock_manager.add_dock_widget_tab(DockWidgetArea.center, dock_widget)

        if os.path.exists(self.pipeline_gui_path):
            try:
                with open(self.pipeline_gui_path, 'r') as f:
                    self.dock_manager.restore_state(QtCore.QByteArray(f.read().encode()))
            except Exception as e:
                self.logger.error(f"Failed to load gui layout: {e}")

        # === Create overall layout =================================================
        grid = QSplitter()
        grid.addWidget(self.edit_graph)
        grid.addWidget(self.dock_manager)
        width = QtWidgets.qApp.desktop().availableGeometry(self).width()
        grid.setSizes([width // 2, width // 2])

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(grid)

        # === Start pipeline =================================================
        self.worker_term_lock = mp.Lock()
        self.worker = None

    def focus_node_view(self, node):
        dock_widget = self.dock_manager.find_dock_widget(node.name)
        dock_area = dock_widget.dock_area_widget()
        dock_area.set_current_index(dock_area.index(dock_widget))

    # TODO: check if we really need to re-implement _start stop etc from run page... -yh

    def _start_pipeline(self):
        self.worker_term_lock.acquire()

        parent_log_queue = mp.Queue()
        logger_name = 'smart-studio'
        
        self.worker_log_handler_termi_sig = th.Event()

        self.worker_log_handler = th.Thread(target=drain_log_queue, args=(parent_log_queue, logger_name, self.worker_log_handler_termi_sig))
        self.worker_log_handler.deamon = True
        self.worker_log_handler.name = f"LogDrain-{self.worker_log_handler.name.split('-')[-1]}"
        self.worker_log_handler.start()

        self.worker = mp.Process(target=self.worker_start, args=(parent_log_queue, logger_name,), name="LN-Executor")
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
            
            self.worker_log_handler_termi_sig.set()
        
    def worker_start(self, subprocess_log_queue, logger_name):
        logger = logging.getLogger(logger_name)
        logger.addHandler(QueueHandler(subprocess_log_queue))

        logger.info(f"Starting Worker")
        self.graph.start_all()
        self.worker_term_lock.acquire()

        logger.info(f"Stopping Worker")
        # timeout to make sure potential non-returning nodes do not block until eternity
        self.graph.stop_all(stop_timeout=2.0, close_timeout=2.0)
        self.worker_term_lock.release()
        logger.info(f"Worker Stopped")

    # i would have assumed __del__ would be the better fit, but that doesn't seem to be called when using del... for some reason
    # will be called in parent view, but also called on exiting the canvas
    def stop(self, *args, **kwargs):
        self._stop_pipeline()

        print('Terminating draw widgets')
        for widget in self.draw_widgets:
            widget.stop()

        # self.nodes = None
        # self.graph = None
        # print('Ref count debug during stoppage', sys.getrefcount(self))
        

    def get_actions(self):
        return [ \
            Action(label="Back", fn=self.save, kind=ActionKind.BACK),
        ]

    def save(self):
        with open(self.pipeline_gui_path, 'w') as f:
            f.write(self.dock_manager.save_state().data().decode())
        self.edit_graph.save()
