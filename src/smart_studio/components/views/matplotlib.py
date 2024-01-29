from livenodes import viewer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from matplotlib.figure import Figure
from matplotlib import animation
import matplotlib.pyplot as plt
from qtpy import QtCore

import logging
logger = logging.getLogger('smart-studio')

import seaborn as sns
import darkdetect

class MPL_View(FigureCanvasQTAgg):

    def __init__(self, node, figsize=(4, 4), font = {'size': 10}, interval=10):
        super().__init__(Figure(figsize=figsize))

        if not isinstance(node, viewer.View_MPL):
            raise ValueError('Node must be of Type (MPL) View')

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
        artist_update_fn = node.init_draw(self.figure)

        def draw_update(i, **kwargs):
            try:
                return artist_update_fn(i, **kwargs)
            except Exception as err:
                logger.exception('Exception in drawing on canvas')
            return []

        self.animation = animation.FuncAnimation(fig=self.figure,
                                                 func=draw_update,
                                                 interval=interval,
                                                 blit=True)

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()
        
        self.show()

    def stop(self):
        self.animation.pause()

