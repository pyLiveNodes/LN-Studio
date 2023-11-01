import sys
import multiprocessing as mp
import platform
from qtpy import QtWidgets

from smart_studio.pages.home import Home
from smart_studio.pages.config import Config
from smart_studio.pages.run import Run
from smart_studio.pages.debug import Debug
from smart_studio.components.page_parent import Parent
from livenodes.node import Node
from livenodes import get_registry


import datetime
import time
import os

import logging

from smart_studio.utils.state import State, STATE, write_state, state_parse
# from smart_studio.components.notification import QToast_Logger

def noop(*args, **kwargs):
    pass


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, state_handler, parent=None, projects='./projects/*', home_dir=os.getcwd(), _on_close_cb=noop):
        super(MainWindow, self).__init__(parent)

        self.logger = logging.getLogger('smart-studio')
        # frm = QFrame()
        # self.setCentralWidget(frm)
        # self.layout = QHBoxLayout(self)
        # self.setLayout(QHBoxLayout())

        # self.toast_logger = QToast_Logger(self)

        self.central_widget = QtWidgets.QStackedWidget(self)
        self.setCentralWidget(self.central_widget)
        # self.layout.addWidget(self.central_widget)
        # self.layout.addWidget(QLabel('Test'))

        self.widget_home = Home(onconfig=self.onconfig,
                                onstart=self.onstart,
                                ondebug=self.ondebug,
                                projects=projects)
        self.central_widget.addWidget(self.widget_home)
        # self.resized.connect(self.widget_home.refresh_selection)

        self.logging_handler = None

        self.home_dir = home_dir
        self.logger.info(f'Home Dir: {home_dir}')
        self.logger.info(f'CWD: {os.getcwd()}')

        self._on_close_cb = _on_close_cb
        self.state_handler = state_handler

        # for some fucking reason i cannot figure out how to set the css class only on the home class... so hacking this by adding and removign the class on view change...
        # self.central_widget.setProperty("cssClass", "home")
        # self.widget_home.setProperty("cssClass", "home")
        self._set_state(self.widget_home)

    def stop(self):
        cur = self.central_widget.currentWidget()
        if hasattr(cur, 'stop'):
            cur.stop()

        # self.toast_logger.close()

        if self.logging_handler is not None:
            logger = logging.getLogger('livenodes')
            logger.removeHandler(self.logging_handler)
            self.logging_handler.close()
            self.logging_handler = None

    def closeEvent(self, event):
        self.stop()

        os.chdir(self.home_dir)
        self.logger.info(f'CWD: {os.getcwd()}')

        self._save_state(self.widget_home)
        self._on_close_cb()

        return super().closeEvent(event)

    def _set_state(self, view):
        section_name = f"View.{view.__class__.__name__}"
        if hasattr(view, 'set_state') and self.state_handler.has_section(section_name):
            view.set_state(self.state_handler[section_name])

    def _save_state(self, view):
        section_name = f"View.{view.__class__.__name__}"
        if hasattr(view, 'save_state'):
            if not self.state_handler.has_section(section_name):
                self.state_handler[section_name] = {}
            view.save_state(self.state_handler[section_name])

    def return_home(self):
        cur = self.central_widget.currentWidget()
        self._save_state(cur)
        self.stop()
        os.chdir(self.home_dir)
        self.logger.info(f'Back to Home Screen')
        self.logger.info(f'CWD: {os.getcwd()}')
        self.central_widget.setCurrentWidget(self.widget_home)
        self.central_widget.removeWidget(cur)
        self.widget_home.refresh_selection()
        self._set_state(self.widget_home)
        self.logger.info(f'Ref count old view (Home) {sys.getrefcount(cur)}')
        self.logger.info(f'Nr of views: {self.central_widget.count()}')

    def onstart(self, project_path, pipeline_path):
        self._save_state(self.widget_home)
        os.chdir(project_path)
        self.logger.info(f'Running: {project_path}/{pipeline_path}')
        self.logger.info(f'CWD: {os.getcwd()}')

        log_folder = './logs'
        log_file = f"{log_folder}/{datetime.datetime.fromtimestamp(time.time())}"

        if not os.path.exists(log_folder):
            os.mkdir(log_folder)

        logger_ln = logging.getLogger('livenodes')
        self.logging_handler = logging.FileHandler(log_file)
        # The time here is actually correct, as record creation time is used (not time of formatting)
        # see: https://docs.python.org/3/library/logging.html#logging.Formatter.formatTime
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        self.logging_handler.setFormatter(formatter)
        self.logging_handler.setLevel(logging.INFO)
        logger_ln.addHandler(self.logging_handler)

        try:
            pipeline = Node.load(pipeline_path, ignore_connection_errors=False)
            # TODO: make these logs project dependent as well
            widget_run = Parent(child=Run(pipeline=pipeline, pipeline_path=pipeline_path),
                                name=f"Running: {pipeline_path}",
                                back_fn=self.return_home)
            self.central_widget.addWidget(widget_run)
            self.central_widget.setCurrentWidget(widget_run)

            self._set_state(widget_run)
        except Exception as err:
            logger_ln.exception('Could not load pipeline. Staying home')
            self.stop()
            os.chdir(self.home_dir)
            logger_ln.info(f'CWD: {os.getcwd()}')

    def ondebug(self, project_path, pipeline_path):
        self._save_state(self.widget_home)
        os.chdir(project_path)
        self.logger.info(f'Debugging: {project_path}/{pipeline_path}')
        self.logger.info(f'CWD: {os.getcwd()}')

        log_folder = './logs'
        log_file = f"{log_folder}/{datetime.datetime.fromtimestamp(time.time())}"

        if not os.path.exists(log_folder):
            os.mkdir(log_folder)

        logger_ln = logging.getLogger('livenodes')
        self.logging_handler = logging.FileHandler(log_file)
        logger_ln.addHandler(self.logging_handler)

        try:
            pipeline = Node.load(pipeline_path, ignore_connection_errors=False, should_time=True)
            # TODO: make these logs project dependent as well
            widget_run = Parent(child=Debug(pipeline=pipeline, pipeline_path=pipeline_path),
                                name=f"Debuging: {pipeline_path}",
                                back_fn=self.return_home)
            self.central_widget.addWidget(widget_run)
            self.central_widget.setCurrentWidget(widget_run)

            self._set_state(widget_run)
        except Exception as err:
            logger_ln.exception('Could not load pipeline. Staying home')
            self.stop()
            os.chdir(self.home_dir)
            logger_ln.info(f'CWD: {os.getcwd()}')


    def onconfig(self, project_path, pipeline_path):
        self._save_state(self.widget_home)
        os.chdir(project_path)
        self.logger.info(f'Configuring: {project_path}/{pipeline_path}')
        self.logger.info(f'CWD: {os.getcwd()}')

        try:
            if os.stat(pipeline_path).st_size == 0:
                # the pipeline was just created and no nodes were added yet
                pipeline = None
            else:
                # this is an existing pipeline we should try to load
                pipeline = Node.load(pipeline_path, ignore_connection_errors=True)
            widget_run = Parent(child=Config(pipeline=pipeline,
                                            node_registry=get_registry(),
                                            pipeline_path=pipeline_path),
                                name=f"Configuring: {pipeline_path}",
                                back_fn=self.return_home)
            self.central_widget.addWidget(widget_run)
            self.central_widget.setCurrentWidget(widget_run)

            self._set_state(widget_run)
        except Exception as err:
            self.logger.exception('Could not load pipeline. Staying home')
            self.stop()
            os.chdir(self.home_dir)
            self.logger.info(f'CWD: {os.getcwd()}')



def main():
    # === Load environment variables ========================================================================
    import os
    import shutil

    logger_root = logging.getLogger()
    logger_root.setLevel(logging.DEBUG)

    logger_stdout_handler = logging.StreamHandler(sys.stdout)
    logger_stdout_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s | %(levelname)s | %(message)s')
    logger_stdout_handler.setFormatter(formatter)
    logger_root.addHandler(logger_stdout_handler)

    logger_file_handler = logging.FileHandler('smart_studio.full.log', mode='w')
    logger_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s | %(asctime)s | %(levelname)s | %(message)s')
    logger_file_handler.setFormatter(formatter)
    logger_root.addHandler(logger_file_handler)

    logger_smart = logging.getLogger("smart-studio")
    logger_smart_file_handler = logging.FileHandler('smart_studio.log', mode='w')
    logger_smart_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(processName)s | %(threadName)s | %(message)s')
    logger_smart_file_handler.setFormatter(formatter)
    logger_smart.addHandler(logger_smart_file_handler)

    logger = logging.getLogger('smart-studio')
    home_dir = os.getcwd()

    env_projects = smart_state.val_get('projects', './projects/*')
    TODO
    logger.info(f'Projects folder: {env_projects}')

    # === Fix MacOS specifics ========================================================================
    # this fix is for macos (https://docs.python.org/3.8/library/multiprocessing.html#contexts-and-start-methods)
    if platform.system() == 'Darwin':
        mp.set_start_method(
            'fork',
            force=True)  # force=True doesn't seem like a too good idea, but hey
    # IMPORTANT TODO: 'spawn' fails due to objects not being picklable (which makes sense)
    # -> however, fork is not present on windows and more generally the python community seems to shift towards making spawn the default/expected behaviour
    # -> resulting in the TODO: check and then separate qt views from the actuall running pipeline such that we can safely switch to spawn for all subprocesses.

    # === Load modules ========================================================================
    # i'd rather spent time in booting up, than on switching views, so we'll prefetch everything here
    get_registry()

    # === Setup application ========================================================================
    app = QtWidgets.QApplication([])
    # print(smart_state)
    # print(smart_state.space_get('views'))
    window_state = STATE['Window']

    def onclose():
        window_state['window_size'] = [window.size().width(), window.size().height()]
        write_state()

    window = MainWindow(state_handler=STATE, projects=env_projects, home_dir=home_dir, _on_close_cb=onclose)
    window.resize(*state_parse(window_state.get('window_size', '[1400, 820]')))
    window.show()

    # chdir because of relative imports in style.qss ....
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    os.chdir(script_dir)
    with open("./static/style.qss", 'r') as f:
        app.setStyleSheet(f.read())
    os.chdir(home_dir)

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
