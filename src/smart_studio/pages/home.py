from functools import partial
import sys
from qtpy import QtWidgets
from glob import glob
import os
import shutil

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QInputDialog, QMessageBox, QToolButton, QComboBox, QComboBox, QPushButton, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout, QScrollArea, QLabel
from qtpy.QtCore import Qt, QSize, Signal


class Home(QWidget):

    def __init__(self,
                 onstart,
                 onconfig,
                 ondebug,
                 projects,
                 parent=None):
        super().__init__(parent)

        self.projects = projects

        self.onstart = onstart
        self.onconfig = onconfig
        self.ondebug = ondebug

        self.qt_selection = None

        self.qt_projects = Project_Selection(self.projects)
        self.qt_projects.selection.connect(self.select_project_by_id)

        self.qt_grid = QVBoxLayout(self)
        self.qt_grid.addWidget(self.qt_projects)
        self.qt_grid.addStretch(1)
        # l1.setFixedWidth(80)

        self.select_project_by_id(0)

    def save_state(self, config):
        config["selected_folder"] = self.selected_folder
        config["selected_file"] = self.qt_selection.get_selected()

    def set_state(self, config):
        selected_folder = config["selected_folder"] # has to be always present
        selected_file = config.get("selected_file", None)
        
        # Set UI State
        id = 0
        if selected_folder in self.projects:
            id = self.projects.index(selected_folder)

        self.qt_projects._set_selected(id)
        self.select_project_by_id(id)
        
        if selected_file is not None:
            self.qt_selection.set_selected(selected_file)
        

    def _on_start(self, pipeline_path):
        self.onstart(self.selected_folder,
                     pipeline_path.replace(self.selected_folder, '.'))

    def _on_config(self, pipeline_path):
        self.onconfig(self.selected_folder,
                      pipeline_path.replace(self.selected_folder, '.'))

    def _on_debug(self, pipeline_path):
        self.ondebug(self.selected_folder,
                      pipeline_path.replace(self.selected_folder, '.'))

    def refresh_selection(self):
        self.select_project(self.selected_folder)

    def select_project(self, project):
        self.selected_folder = project
        pipelines = f"{self.selected_folder}/*.yml"

        qt_selection = Selection(folder_path=self.selected_folder, pipelines=pipelines)
        qt_selection.items_changed.connect(self.refresh_selection)
        qt_selection.item_on_start.connect(self._on_start)
        qt_selection.item_on_config.connect(self._on_config)
        qt_selection.item_on_debug.connect(self._on_debug)

        if self.qt_selection is not None:
            self.qt_grid.removeWidget(self.qt_selection)
            self.qt_selection.deleteLater()
        self.qt_grid.addWidget(qt_selection)
        self.qt_selection = qt_selection

    def select_project_by_id(self, project_id):
        self.select_project(self.projects[project_id])


class Project_Selection(QWidget):
    selection = Signal(int)

    def __init__(self, projects=[], parent=None):
        super().__init__(parent)

        self.combo = QComboBox()
        self.combo.addItems(projects)
        self.combo.currentIndexChanged.connect(self._selected)

        l2 = QHBoxLayout(self)
        # l2.addWidget(QLabel('S-MART'))
        l2.addWidget(self.combo)
        l2.addStretch(2)
        # for project in projects:
        #     l2.addWidget(QLabel(project))

        # l1 = QVBoxLayout(self)
        # l1.addChildLayout(l2)
        # l1.addStretch(2)

    def _set_selected(self, id):
        self.combo.setCurrentIndex(id)

    def _selected(self, id):
        self.selection.emit(id)


class Pipline_Selection(QWidget):
    clicked = Signal(str)

    # Adapted from: https://gist.github.com/JokerMartini/538f8262c69c2904fa8f
    def __init__(self, pipelines, parent=None):
        super().__init__(parent)

        self.scroll_panel = QWidget()
        self.scroll_panel_layout = QHBoxLayout(self.scroll_panel)
        self.scroll_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidget(self.scroll_panel)

        # layout
        self.mainLayout = QGridLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.scroll_area)

        for itm in pipelines:
            icon = QIcon(itm.replace('.yml', '.png'))
            button = QToolButton()
            button.setText(itm.split('/')[-1].replace('.yml', ''))
            button.setIcon(icon)
            button.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.clicked.connect(partial(self.__select, itm))
            button.setIconSize(QSize(200, 200))
            self.scroll_panel_layout.addWidget(button)

    def __select(self, pipline_path):
        self.clicked.emit(pipline_path)


class Selection(QWidget):
    items_changed = Signal()
    item_on_config = Signal(str)
    item_on_debug = Signal(str)
    item_on_start = Signal(str)

    def __init__(self, folder_path, pipelines="*.yml"):
        super().__init__()

        pipelines = sorted(glob(pipelines))

        self.folder_path = folder_path

        # combobox1 = QComboBox()
        # print(pipelines)
        # for itm in pipelines:
        #     combobox1.addItem(itm)

        # combobox1.currentTextChanged.connect(self.text_changed)

        selection = Pipline_Selection(pipelines)
        selection.clicked.connect(self.text_changed)

        new = QPushButton("New")
        new.clicked.connect(self.onnew)

        copy = QPushButton("Copy")
        copy.clicked.connect(self.oncopy)

        delete = QPushButton("Delete")
        delete.clicked.connect(self.ondelete)

        start = QPushButton("Start")
        start.clicked.connect(self.onstart)

        config = QPushButton("Config")
        config.clicked.connect(self.onconfig)

        debug = QPushButton("Debug")
        debug.clicked.connect(self.ondebug)

        self.selected = QLabel("")

        buttons = QHBoxLayout()
        buttons.addWidget(delete)
        buttons.addStretch(1)
        buttons.addWidget(self.selected)
        buttons.addWidget(new)
        buttons.addWidget(copy)
        buttons.addWidget(debug)
        buttons.addWidget(config)
        buttons.addWidget(start)

        self.set_selected(pipelines[0])

        self.setProperty("cssClass", "home")

        # self.pixmap = QLabel(self)
        # w, h = self.pixmap.width(), self.pixmap.height()
        # p = QPixmap('./src/gui/static/connected_human.jpg')
        # self.pixmap.setPixmap(p.scaled(w, h))

        l1 = QVBoxLayout(self)
        # l1.addWidget(self.pixmap, stretch=1)
        # l1.addStretch(
        #     1
        # )  # idea from: https://zetcode.com/gui/pysidetutorial/layoutmanagement/
        l1.addWidget(selection, stretch=0)
        l1.addLayout(buttons)

    def onstart(self):
        self.item_on_start.emit(self.text)

    def onconfig(self):
        self.item_on_config.emit(self.text)

    def ondebug(self):
        self.item_on_debug.emit(self.text)


    def _associated_files(self, path):
        return list(glob.glob(f"{path.replace('.yml', '')}*"))


    def onnew(self):
        text, ok = QInputDialog.getText(self, 'Create new', f'Name:')
        if ok:
            new_name = f"{self.folder_path}/{text}.yml"
            if os.path.exists(new_name):
                raise Exception('Pipeline already exists')
            if len(text) == 0:
                raise Exception('Name cannot be empty')
            open(new_name, 'w').close()
            self.items_changed.emit()

    def oncopy(self):
        name = self.text.split('/')[-1].replace('.yml', '')
        text, ok = QInputDialog.getText(self, f'Copy {name}', 'New name:')
        if ok:
            if os.path.exists(self.text.replace(name, text)):
                raise Exception('Pipeline already exists')
            if len(text) == 0:
                raise Exception('Name cannot be empty')
            for f in self._associated_files(self.text):
                shutil.copyfile(f, f.replace(name, text))
            self.items_changed.emit()

    def ondelete(self):
        reply = QMessageBox.question(self, 'Delete', f'Are you sure you want to delete {self.text}', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for f in self._associated_files(self.text):
                if os.path.exists(f):
                    os.remove(f)
            self.items_changed.emit()

    def text_changed(self, text):
        self.selected.setText(text)
        self.text = text

    def get_selected(self):
        return self.text

    def set_selected(self, text):
        self.selected.setText(text)
        self.text = text



def noop(*args, **kwargs):
    # print(args, kwargs)
    pass


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = Home(noop, noop)
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
