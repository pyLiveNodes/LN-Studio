from livenodes import viewer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from qtpy import QtCore

import logging
logger = logging.getLogger('LN-Studio')

import seaborn as sns
import darkdetect

class MPL_View(FigureCanvasQTAgg):
    
    # max 30 fps and 50 dpi (high could be 100 and 100)
    def __init__(self, node, figsize=(4, 4), font = {'size': 10}, interval=33, dpi=100):
        super().__init__(Figure(figsize=figsize, dpi=dpi))

        if not isinstance(node, viewer.View_MPL):
            raise ValueError('Node must be of Type (MPL) View')

        self.node = node

        self.figure.patch.set_facecolor("None")
        self.figure.set_facecolor("None")
        plt.rc('font', **font)

        if darkdetect.isDark():
            plt.style.use("dark_background")
        else:
            sns.set_style("darkgrid")
        sns.set_context("paper")
        
        # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/subfigures.html
        # subfigs = self.figure.subfigures(rows, cols)  #, wspace=1, hspace=0.07)
        # we might create subfigs, but if each node has it's own qwidget, we do not need to and can instead just pass the entire figure
        # https://www.pythonguis.com/tutorials/plotting-matplotlib/
        # https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html
        self.artist_update_fn = node.init_draw(self.figure)
        self.renderer = self.figure.canvas.get_renderer()
        
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()
        
        self.show()
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.draw_update)
        self.timer.start()


    def draw_update(self):
        try:
            self.artist_update_fn(0)
            self.draw()
        except Exception as err:
            logger.exception('Exception in drawing on canvas')

    def pause(self):
        self.timer.stop()

    def resume(self):
        self.timer.start()
    
    def stop(self):
        self.timer.stop()

