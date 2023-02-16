from functools import partial
from livenodes import viewer
import os
import json
import logging
import threading as th
from logging.handlers import QueueHandler

from PyQt5.QtWidgets import QHBoxLayout
from PyQt5 import QtCore

from PyQtAds import QtAds

import multiprocessing as mp

from livenodes import Node, Graph
from livenodes.components.utils.log import drain_log_queue

from smart_studio.components.node_views import node_view_mapper
from smart_studio.components.page import Page, Action, ActionKind

# adapted from: https://stackoverflow.com/questions/39835300/python-qt-and-matplotlib-scatter-plots-with-blitting
class Run(Page):

    def __init__(self, pipeline_path, pipeline, parent=None):
        super().__init__(parent=parent)

        self.pipeline = pipeline
        self.graph = Graph(start_node=pipeline)
        self._create_paths(pipeline_path)

        # === Setup draw canvases =================================================
        self.nodes = [n for n in Node.discover_graph(pipeline) if isinstance(n, viewer.View)]
        self.draw_widgets = list(map(partial(node_view_mapper, self), self.nodes))
        
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.XmlCompressionEnabled, False)
        
        self.layout = QHBoxLayout(self)
        self.dock_manager = QtAds.CDockManager(self)
        self.layout.addWidget(self.dock_manager)
        self.widgets = []

        def debug_partial(logger, *text):
            logger.debug(' '.join(map(str, text)))

        for widget, node in zip(self.draw_widgets, self.nodes):
            dock_widget = QtAds.CDockWidget(node.name)
            self.widgets.append(dock_widget)
            dock_widget.viewToggled.connect(partial(debug_partial, self.logger, '=======', str(node), "qt emitted signal"))
            dock_widget.setWidget(widget)
            dock_widget.setFeature(QtAds.CDockWidget.DockWidgetClosable, False)

            self.dock_manager.addDockWidget(QtAds.RightDockWidgetArea, dock_widget)

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
        self.logger = logging.getLogger("smart-studio")
        self.worker_term_lock = mp.Lock()
        self._start_pipeline()

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

    def stop(self, *args, **kwargs):
        self._stop_pipeline()

    # i would have assumed __del__ would be the better fit, but that doesn't seem to be called when using del... for some reason
    # will be called in parent view, but also called on exiting the canvas
    def _stop_pipeline(self):
        # Tell the process to terminate, then wait until it returns
        self.worker_term_lock.release()
        
        self.logger.info(f"Stopping Worker")
        # Block until graph finished all it's nodes
        self.worker_term_lock.acquire()
        self.worker_term_lock.release()
        self.logger.info('View terminated')

        self.logger.info('Terminating draw widgets')
        self.logger.info(f"Stopping Widgets")
        for widget in self.draw_widgets:
            widget.stop()

        self.logger.info(f"Killing Worker")
        self.worker.terminate()

        self.worker_log_handler_termi_sig.set()

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
        self.pipeline_gui_path = pipeline_path.replace('/pipelines/', '/gui/', 1).replace('.json', '.xml')

        # Deprecation and renaming notice here
        old_path = pipeline_path.replace('/pipelines/', '/gui/', 1).replace('.json', '_dock.xml')
        if os.path.exists(old_path):
            self.logger.warn('_dock.xml is old format. renaming to just .xml')
            os.rename(old_path, self.pipeline_gui_path)


        gui_folder = '/'.join(self.pipeline_gui_path.split('/')[:-1])
        if not os.path.exists(gui_folder):
            os.mkdir(gui_folder)