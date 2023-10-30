import json
from qtpy.QtWidgets import QHBoxLayout
from qtpy.QtWidgets import QDialogButtonBox, QDialog, QVBoxLayout, QWidget, QHBoxLayout, QScrollArea, QLabel
from qtpy.QtCore import Qt
from qtpy.QtCore import Signal

from .edit import EditDict


class NodeParameterSetter(QWidget):
    changed = Signal(bool)

    def __init__(self, node=None, parent=None):
        super().__init__(parent)

        self.node = node

        # let's assume we only have class instances here and no classes
        # for classes we would need a combination of info() and something else...
        if self.node is not None:
            self.edit = EditDict(in_items=self.node._node_settings(), extendable=False)
            # let's assume the edit interfaces do not overwrite any of the references
            # otherwise we would need to do a recursive set_attr here....

            # TODO: remove _set_attr in node, this is no good design
            self.edit.changed.connect(self.edit_changed_handler)
        else:
            self.edit = EditDict(in_items={})

        self.layout = QVBoxLayout(self)
        # Add edit inputs
        self.layout.addWidget(self.edit, stretch=1)
        # Add info about ports
        if self.node is not None: # in case no node is selected
            self.layout.addWidget(QLabel("-- Ports --"), stretch=0)
            self.layout.addWidget(QLabel(self._format_ports(self.node.ports_in)), stretch=0)
            self.layout.addWidget(QLabel(self._format_ports(self.node.ports_out)), stretch=0)
        # Add Nodes' description
        if self.node.__doc__ is not None:
            self.layout.addWidget(QLabel("-- Description --"), stretch=0)
            label = QLabel(self.node.__doc__)
            label.setWordWrap(True)
            self.layout.addWidget(label, stretch=0)
    
    def _format_ports(self, ports):
        return "\n".join([f"{name}: {value.__class__.__name__}" for name, value in ports._asdict().items()])

    def edit_changed_handler(self, attrs):
        # TODO: remove _set_attr in node, this is no good design
        attrs_new = self.node._set_attr(**attrs)
        if json.dumps(attrs) != json.dumps(attrs_new):
            # print('set_attr diff from received attrs, will re-build ui')
            self.changed.emit(True)

class NodeConfigureContainer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scroll_panel = QWidget()
        self.scroll_panel_layout = QHBoxLayout(self.scroll_panel)
        self.scroll_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # self.scroll_area.setHorizontalScrollBarPolicy(
        #     Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.scroll_panel)

        self._title = QLabel("")
        self._category = QLabel("")

        self.l1 = QVBoxLayout(self)
        self.l1.setContentsMargins(0, 0, 0, 0)
        self.l1.addWidget(self._title)
        self.l1.addWidget(self._category)
        self.l1.addWidget(self.scroll_area, stretch=1)

        self.params = None
        self.set_pl_node()

    def set_pl_node(self, node=None, **kwargs):
        if node is None:
            self._title.setText("Click node to configure.")
            self._category.setText("")
            new_params = NodeParameterSetter()
        else:
            self._title.setText(str(node))
            self._category.setText(node.category)
            new_params = NodeParameterSetter(node)

        if self.params is None:
            self.scroll_panel_layout.addWidget(new_params)
        else:
            self.scroll_panel_layout.replaceWidget(self.params, new_params)
            self.params.deleteLater()

        self.params = new_params
        self.params.changed.connect(lambda _: self.set_pl_node(node))


class CreateNodeDialog(QDialog):

    def __init__(self, node):
        super().__init__()

        self.node = node

        self.setWindowTitle(f"Create Node: {node.model.name}")

        # TODO: replace with ok with save
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.edit_dict = node.model.constructor.example_init
        edit_form = EditDict(self.edit_dict)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(edit_form)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
