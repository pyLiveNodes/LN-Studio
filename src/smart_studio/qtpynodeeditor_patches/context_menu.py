#### Monkey Patch context menu adjustments
# Patches new node context menu to remove empty groups and not be case-sensetive

import logging

from qtpy.QtCore import QLineF, QPoint, QRectF, Qt
from qtpy.QtGui import (QContextMenuEvent, QKeyEvent, QMouseEvent, QPainter,
                        QPen, QShowEvent, QWheelEvent, QKeySequence)
from qtpy.QtWidgets import (QAction, QGraphicsView, QLineEdit, QMenu,
                            QTreeWidget, QTreeWidgetItem, QWidgetAction)

# from .connection_graphics_object import ConnectionGraphicsObject
# from .flow_scene import FlowScene
# from .node_graphics_object import NodeGraphicsObject

import qtpynodeeditor.flow_view

logger = logging.getLogger(__name__)

def generate_context_menu(self, pos: QPoint):
    """
    Generate a context menu for contextMenuEvent

    Parameters
    ----------
    pos : QPoint
        The point where the context menu was requested
    """
    model_menu = QMenu()
    skip_text = "skip me"

    # Add filterbox to the context menu
    txt_box = QLineEdit(model_menu)
    txt_box.setPlaceholderText("Filter")
    txt_box.setClearButtonEnabled(True)
    txt_box_action = QWidgetAction(model_menu)
    txt_box_action.setDefaultWidget(txt_box)
    model_menu.addAction(txt_box_action)

    # Add result treeview to the context menu
    tree_view = QTreeWidget(model_menu)
    tree_view.header().close()
    tree_view_action = QWidgetAction(model_menu)
    tree_view_action.setDefaultWidget(tree_view)
    model_menu.addAction(tree_view_action)

    top_level_items = {}
    for cat in self._scene.registry.categories():
        item = QTreeWidgetItem(tree_view)
        item.setText(0, cat)
        item.setData(0, Qt.UserRole, skip_text)
        top_level_items[cat] = item

    registry = self._scene.registry
    for model, category in registry.registered_models_category_association().items():
        self.parent = top_level_items[category]
        item = QTreeWidgetItem(self.parent)
        item.setText(0, model)
        item.setData(0, Qt.UserRole, model)

    tree_view.expandAll()

    def click_handler(item):
        model_name = item.data(0, Qt.UserRole)
        if model_name == skip_text:
            return

        try:
            model, _ = self._scene.registry.get_model_by_name(model_name)
        except ValueError:
            logger.error("Model not found: %s", model_name)
        else:
            node = self._scene.create_node(model)
            if node is not None:
                pos_view = self.mapToScene(pos)
                node.graphics_object.setPos(pos_view)
                self._scene.node_placed.emit(node)

        model_menu.close()

    tree_view.itemClicked.connect(click_handler)

    # Setup filtering
    def filter_handler(text):
        for name, top_lvl_item in top_level_items.items():
            any_visible = False
            for i in range(top_lvl_item.childCount()):
                child = top_lvl_item.child(i)
                model_name = child.data(0, Qt.UserRole)
                hidden = text.lower() not in model_name.lower()
                child.setHidden(hidden)
                any_visible = any_visible or not hidden
            top_lvl_item.setHidden(not any_visible)

    txt_box.textChanged.connect(filter_handler)

    # make sure the text box gets focus so the user doesn't have to click on it
    txt_box.setFocus()
    return model_menu


qtpynodeeditor.flow_view.FlowView.generate_context_menu = generate_context_menu
print('Patched Fix for context menu')
### End patch