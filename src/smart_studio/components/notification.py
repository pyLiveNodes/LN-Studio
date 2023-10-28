# TODO: figure out again from where this was installed...
# from notificator import notificator
# from notificator.alingments import TopCenter

from QNotifications import QNotificationArea

from logging.handlers import QueueHandler
from PySide6 import QtCore
import queue
import multiprocessing as mp
import threading as th
from PySide6.QtCore import Qt

from PySide6 import QtWidgets

import logging

class QToast_Logger(QtWidgets.QWidget):
    """
    Slightly complicated.
    Basically:
    - qna needs to run in main thread of qt to display toasts via the qna.display method
    - some logs are from sub-threads of sub-processes tho -> we collect those in a mp.queue
        -> the queue must be drained without blocking the main thread
        -> we create a subthread that forwards all items from the queue to the pyqt signal which in turn connects to the main threads qna.display method

    Note: if you have a better way of doing this, please create a PR! This feels rather hacky
    """
    notify = QtCore.Signal(str,str,int, bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        # self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # self.setMinimumWidth(400)
        # self.setMinimumHeight(250)

        qna_queue = mp.Queue()
        logger_toast_handler_mp_queue = QueueHandler(qna_queue)
        logger_toast_handler_mp_queue.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(name)s | %(message)s')
        logger_toast_handler_mp_queue.setFormatter(formatter)
        logger_toast = logging.getLogger('smart-studio')
        logger_toast.addHandler(logger_toast_handler_mp_queue)
        logger_toast = logging.getLogger('livenodes')
        logger_toast.addHandler(logger_toast_handler_mp_queue)


        # TODO: fix me to the upper right corner and make me relative to the window size!
        # Alternaively: figure out, why repeated errors do not show
        # reprocude: create a graph with incompatible connection; edit -> error shows; cancel (!); edit again -> error doesn't show
        # something very fishy is going on here: the error is shown when the log is double, but not on the second time, where it is single...
        # self.setGeometry(50, 50, 400, 250)

        # doesn't work, as the processing happens in the sub-thread...
        # queue_listener = QueueListener(qna_queue, logger_toast_handler)
        # queue_listener.start()

        self.worker_log_handler_termi_sig = th.Event()
        self.worker_log_handler = th.Thread(target=self.qna_drain_log_queue, args=(qna_queue, self.worker_log_handler_termi_sig))
        self.worker_log_handler.deamon = True
        self.worker_log_handler.name = f"QTToastLogDrain-{self.worker_log_handler.name.split('-')[-1]}"
        self.worker_log_handler.start()

        # qna = QNotificationArea(parent)
        # self.notify.connect(qna.display)

        self.noft = notificator()
        self.notify.connect(self.display)

        # noft.critical("Test","blka",parent,TopCenter)

    def display(self, msg, level, some_bool=False):
        lvl_short, timeout = level
        if lvl_short == 'danger':
            self.noft.cricital('Error', msg, TopCenter, timeout=timeout)
        elif lvl_short == 'warning':
            self.noft.warning('Warning', msg, TopCenter, timeout=timeout)
        elif lvl_short == 'info':
            self.noft.info('Info', msg, TopCenter, timeout=timeout)


    def level_map(self, level):
        if level >= 40:
            return 'danger', None
        elif level >=30:
            return 'warning', 10000
        else:
            return 'info', 3000

    def qna_drain_log_queue(self, parent_log_queue, stop_log_event):
        while not stop_log_event.is_set():
            try:
                record = parent_log_queue.get(timeout=0.1)
                self.notify.emit(record.msg, *self.level_map(record.levelno), False)
            except queue.Empty:
                pass
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break

    def close(self):
        self.worker_log_handler_termi_sig.set()
