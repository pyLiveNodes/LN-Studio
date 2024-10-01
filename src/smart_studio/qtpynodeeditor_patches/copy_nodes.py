#### Monkey Patch context menu adjustments
# Patches new node context menu to remove empty groups and not be case-sensetive

import logging

from qtpy.QtCore import QLineF, QPointF, QRectF, Qt, QCoreApplication
from qtpy.QtGui import (QContextMenuEvent, QKeyEvent, QMouseEvent, QPainter,
                        QPen, QShowEvent, QWheelEvent, QKeySequence)
from qtpy.QtWidgets import (QAction, QGraphicsView, QLineEdit, QMenu,
                            QTreeWidget, QTreeWidgetItem, QWidgetAction)

from qtpynodeeditor.connection_graphics_object import ConnectionGraphicsObject
from qtpynodeeditor.flow_scene import FlowScene
from qtpynodeeditor.node_graphics_object import NodeGraphicsObject
from qtpynodeeditor import PortType

import qtpynodeeditor.flow_view

def __init__(self, scene, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self._clear_selection_action = None
        self._delete_selection_action = None
        self._copy_selection_action = None
        self._scene = None
        self._click_pos = None

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)

        # setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.setCacheMode(QGraphicsView.CacheBackground)
        # setViewport(new QGLWidget(QGLFormat(QGL.SampleBuffers)))
        if scene is not None:
            self.setScene(scene)

        self._style = self._scene.style_collection
        self.setBackgroundBrush(self._style.flow_view.background_color)

def setScene(self, scene: FlowScene):
    """
    setScene

    Parameters
    ----------
    scene : FlowScene
    """
    self._scene = scene
    super(self.__class__, self).setScene(self._scene)

    # setup actions
    del self._clear_selection_action
    self._clear_selection_action = QAction("Clear Selection", self)
    self._clear_selection_action.setShortcut(QKeySequence.Cancel)
    self._clear_selection_action.triggered.connect(self._scene.clearSelection)
    self.addAction(self._clear_selection_action)

    del self._delete_selection_action
    self._delete_selection_action = QAction("Delete Selection", self)
    self._delete_selection_action.setShortcut(QKeySequence.Backspace)
    self._delete_selection_action.setShortcut(QKeySequence.Delete)
    self._delete_selection_action.triggered.connect(self.delete_selected)
    self.addAction(self._delete_selection_action)

    del self._copy_selection_action
    self._copy_selection_action = QAction("Copy Selection", self)
    self._copy_selection_action.setShortcut(QCoreApplication.translate('context', 'Ctrl+D'))
    # self._copy_selection_action.setShortcut(QKeySequence.Copy)
    self._copy_selection_action.triggered.connect(self.copy_selected)
    self.addAction(self._copy_selection_action)

def copy_selected(self):
    # TODO: once created the new nodes should be selected not the old ones...

    id_map = {}
    # create nodes first
    for item in self._scene.selectedItems():
        if isinstance(item, NodeGraphicsObject):
            pl_node = item._node._model.association_to_node.copy()
            pos = item.scenePos()
            # since we have overwritten the scene.create_node function in edit_graph, we do not need to set any associations etc here
            s_node = self._scene.create_node(item._node._model, pl_node) 
            s_node.graphics_object.setPos(QPointF(pos.x() + 10, pos.y() + 10))
            id_map[id(item._node)] = s_node

    # then create connections where possible (ie the connection might be between a newly created and an existing node which might lead to duplicate inputs in the existing which would not be allowed atm)
    for item in self._scene.selectedItems():
        if isinstance(item, ConnectionGraphicsObject):
            in_node = id_map[id(item.connection.input_node)]
            in_port = in_node[PortType.input][item.connection.ports[0].index]

            out_node = id_map[id(item.connection.output_node)]
            out_port = out_node[PortType.output][item.connection.ports[1].index]
            self._scene.create_connection(out_port, in_port)


def copy_selection_action(self) -> QAction:
        """
        Copy selection action

        Returns
        -------
        value : QAction
        """
        return self._copy_selection_action

qtpynodeeditor.flow_view.FlowView.__init__ = __init__
qtpynodeeditor.flow_view.FlowView.setScene = setScene
qtpynodeeditor.flow_view.FlowView.copy_selected = copy_selected
qtpynodeeditor.flow_view.FlowView.copy_selection_action = copy_selection_action
print('Patched Copy/Duplicate Selection')
### End patch