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
from .run import Run

class Debug(Run, Page):

    def __init__(self, pipeline_path, pipeline, node_registry, parent=None):
        super(Page, self).__init__(parent=parent)

        if hasattr(pipeline, 'get_non_macro_node'):
            pipeline = pipeline.get_non_macro_node()

        self.pipeline = pipeline
        self.graph = Graph(start_node=pipeline)
        self.pipeline_path = pipeline_path
        self.pipeline_gui_path = pipeline_path.replace('.yml', '_gui_dock_debug.xml')

        self.worker = None
        self.logger = logging.getLogger("smart-studio")

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
        self.edit_graph = QT_Graph_edit(pipeline_path=pipeline_path, node_registry=node_registry, parent=self, read_only=True, resolve_macros=True)
        self.edit_graph.setMinimumWidth(300)
        self.edit_graph.node_selected.connect(self.focus_node_view)

        # === Setup draw canvases and add items to views =================================================
        self.dock_manager = DockManager(self)
        self.nodes = Node.discover_graph(pipeline)
        self.draw_widgets = [Debug_View(n, view=node_view_mapper(self, n) if isinstance(n, viewer.View) else None, parent=self) for n in self.nodes]

        for widget, node in zip(self.draw_widgets, self.nodes):
            name = node.get_name_resolve_macro() if hasattr(node, "get_name_resolve_macro") else node.name
            dock_widget = DockWidget(name)
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
        print('focusing node', node)
        name = node.get_name_resolve_macro() if hasattr(node, "get_name_resolve_macro") else node.name
        dock_widget = self.dock_manager.find_dock_widget(name)
        dock_area = dock_widget.dock_area_widget()
        dock_area.set_current_index(dock_area.index(dock_widget))


    # def _stop_pipeline(self):
    #     if self.worker is not None:
    #         super(Run, self)._stop_pipeline()
    #         # self.worker_term_lock.release()
    #         # print('Termination time in view!')
    #         # self.worker_term_lock.acquire()
    #         # self.worker_term_lock.release()
    #         # print('View terminated')
    #         # self.worker = None
            
            # self.worker_log_handler_termi_sig.set()
        
    # i would have assumed __del__ would be the better fit, but that doesn't seem to be called when using del... for some reason
    # will be called in parent view, but also called on exiting the canvas
    # def stop(self, *args, **kwargs):
    #     self._stop_pipeline()

    #     print('Terminating draw widgets')
    #     for widget in self.draw_widgets:
    #         widget.stop()

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
