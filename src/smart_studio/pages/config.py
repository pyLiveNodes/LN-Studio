import json

from PyQt5.QtWidgets import QSplitter, QHBoxLayout

from smart_studio.components.edit_node import NodeConfigureContainer
from smart_studio.components.edit_graph import QT_Graph_edit
from smart_studio.components.page import ActionKind, Page, Action

class Config(Page):

    def __init__(self, pipeline_path, pipeline=None, node_registry=None, parent=None):
        super().__init__(parent)

        self.edit_graph = QT_Graph_edit(pipeline_path=pipeline_path, pipeline=pipeline, node_registry=node_registry, parent=self)
        self.edit_node = NodeConfigureContainer(parent=self)
        self.edit_node.setMinimumWidth(300)

        self.edit_graph.node_selected.connect(self.edit_node.set_pl_node)

        grid = QSplitter()
        grid.addWidget(self.edit_graph)
        grid.addWidget(self.edit_node)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(grid)

    def get_actions(self):
        return [ \
            Action(label="Back", fn=self.save, kind=ActionKind.BACK),
            Action(label="Cancel", kind=ActionKind.BACK),
            Action(label="Auto-layout", fn=self.edit_graph.auto_layout, kind=ActionKind.OTHER),
        ]

    def save(self):
        self.edit_graph.save()