from livenodes import viewer

from qtpy.QtWidgets import QWidget
from qtpy.QtCore import QTimer

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