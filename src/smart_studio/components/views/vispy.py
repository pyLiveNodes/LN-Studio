from livenodes import viewer

from vispy import app as vp_app
from vispy import scene
vp_app.use_app('pyqt5')

from qtpy.QtWidgets import QWidget

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
