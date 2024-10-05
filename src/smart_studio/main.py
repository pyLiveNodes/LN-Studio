import sys
import multiprocessing as mp
import platform
from qtpy import QtWidgets
import darkdetect
import qdarktheme
from qdarktheme._main import _sync_theme_with_system, _apply_style
from functools import partial

import matplotlib.pyplot as plt
import seaborn as sns

from smart_studio.pages.home import Home
from smart_studio.pages.config import Config
from smart_studio.pages.run import Run
from smart_studio.pages.debug import Debug
from smart_studio.components.page_parent import Parent
from livenodes.node import Node
from livenodes import get_registry


import os

import logging

from smart_studio.utils.state import STATE, write_state
# from smart_studio.components.notification import QToast_Logger

def noop(*args, **kwargs):
    pass



class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, state_handler, parent=None, home_dir=os.getcwd(), _on_close_cb=noop):
        super(MainWindow, self).__init__(parent)

        self.logger = logging.getLogger('smart-studio')
        # frm = QFrame()
        # self.setCentralWidget(frm)
        # self.layout = QHBoxLayout(self)
        # self.setLayout(QHBoxLayout())

        # self.toast_logger = QToast_Logger(self)

        self.central_widget = QtWidgets.QStackedWidget(self)

        # if darkdetect.isDark():
        #     self.central_widget.setProperty("cssClass", [ "dark_bg" ])
        # else:
        #     self.central_widget.setProperty("cssClass", [ "light_bg" ])

        self.setCentralWidget(self.central_widget)
        # self.layout.addWidget(self.central_widget)
        # self.layout.addWidget(QLabel('Test'))

        self.widget_home = Home(onconfig=self.onconfig,
                                onstart=self.onstart,
                                ondebug=self.ondebug,
                                projects=state_handler['View.Home']['folders'])
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
        logger.info('Stopping Current Widget and Pipeline')
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
        if hasattr(view, 'set_state') and section_name in self.state_handler:
            view.set_state(self.state_handler[section_name])

    def _save_state(self, view):
        section_name = f"View.{view.__class__.__name__}"
        if hasattr(view, 'save_state'):
            if not section_name in self.state_handler:
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

        try:
            # TODO: open dialog on connection errors
            pipeline = Node.load(pipeline_path, ignore_connection_errors=False)
            # TODO: make these logs project dependent as well
            widget_run = Parent(child=Run(pipeline=pipeline, pipeline_path=pipeline_path),
                                name=f"Running: {pipeline_path}",
                                back_fn=self.return_home)
            self.central_widget.addWidget(widget_run)
            self.central_widget.setCurrentWidget(widget_run)

            self._set_state(widget_run)
        except Exception as err:
            self.logger.exception('Could not load pipeline. Staying home')
            self.stop()
            os.chdir(self.home_dir)
            self.logger.info(f'CWD: {os.getcwd()}')

    def ondebug(self, project_path, pipeline_path):
        self._save_state(self.widget_home)
        os.chdir(project_path)
        self.logger.info(f'Debugging: {project_path}/{pipeline_path}')
        self.logger.info(f'CWD: {os.getcwd()}')

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
            self.logger.exception('Could not load pipeline. Staying home')
            self.stop()
            os.chdir(self.home_dir)
            self.logger.info(f'CWD: {os.getcwd()}')


    def onconfig(self, project_path, pipeline_path):
        self._save_state(self.widget_home)
        os.chdir(project_path)
        self.logger.info(f'Configuring: {project_path}/{pipeline_path}')
        self.logger.info(f'CWD: {os.getcwd()}')

        try:
            widget_run = Parent(child=Config(node_registry=get_registry(),
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

def create_stylesheet(theme):
    image_dir = os.path.join(os.path.dirname(__file__), 'static')
    return f"""
            MainWindow {{
                background-image: url('{image_dir}/connected_human_{theme}.jpg');
                background-repeat: no-repeat; 
                background-position: center top;
            }}

            QStackedWidget {{
                background-color: transparent;
            }}

            """
            # MPL_View {{
            #     background-color: transparent;
            # }}

def dark_mode_callback(app):
    theme = darkdetect.theme().lower()
    additional_qss = create_stylesheet(theme)
    _apply_style(
        app,
        additional_qss=additional_qss,
        theme=theme,
        corner_shape="rounded",
        custom_colors=None,
        default_theme=theme
    )

def main():
    # === Load environment variables ========================================================================
    import os

    logger_root = logging.getLogger()
    logger_root.setLevel(logging.DEBUG)

    logger_stdout_handler = logging.StreamHandler(sys.stdout)
    logger_stdout_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s | %(levelname)s | %(message)s')
    logger_stdout_handler.setFormatter(formatter)
    logger_root.addHandler(logger_stdout_handler)

    logger = logging.getLogger('smart-studio')
    home_dir = os.getcwd()

    logger.info(f"Projects folders: {STATE['View.Home']['folders']}")

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
    qdarktheme.enable_hi_dpi() # must be set before the application is created
    app = QtWidgets.QApplication([])
    app.setApplicationName("Smart Studio")

    # app.setStyleSheet(create_stylesheet(darkdetect.theme().lower()))
    # qdarktheme.setup_theme("auto", additional_qss=create_stylesheet(darkdetect.theme().lower())) #, custom_colors={"background": "#0f0f0f00"})
    dark_mode_callback(app)
    _sync_theme_with_system(app, partial(dark_mode_callback, app))

    # print(smart_state)
    # print(smart_state.space_get('views'))
    window_state = STATE['Window']

    def onclose():
        nonlocal window, window_state
        logger.info('Writing Application State')
        try:
            window_state['size'] = [window.size().width(), window.size().height()]
            write_state()
        except:
            logger.error('Could not gracfully write application state')

    # Global error handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            logger.error("KeyboardInterrupt, exiting")
        else:
            logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            QtWidgets.QMessageBox.critical(None, "Uncaught Exception", str(exc_value), QtWidgets.QMessageBox.Ok)
        try:
            onclose()
            window.stop()
        except:
            logger.error('Could not gracfully close application')
        sys.exit(1)

    sys.excepthook = handle_exception
    
    window = MainWindow(state_handler=STATE, home_dir=home_dir, _on_close_cb=onclose)
    window.resize(*window_state.get('size', (1400, 820)))
    window.setWindowTitle("Smart Studio")

    # uncomment to have a debugger for qss on the side
    # from qss_debugger.debugger import VisualTreeDebugger
    # debugger = VisualTreeDebugger(window)

    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
