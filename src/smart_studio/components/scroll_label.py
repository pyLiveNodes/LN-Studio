from qtpy.QtWidgets import QInputDialog, QMessageBox, QToolButton, QComboBox, QComboBox, QPushButton, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout, QScrollArea, QLabel

# class for scrollable label
# from: https://www.geeksforgeeks.org/pyqt5-scrollable-label/
class ScrollLabel(QScrollArea):
    # constructor
    def __init__(self, keep_bottom=False, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)
 
        # making widget resizable
        self.setWidgetResizable(True)
 
        # making qwidget object
        content = QWidget(self)
        self.setWidget(content)
 
        # vertical box layout
        lay = QVBoxLayout(content)
 
        # creating label
        self.label = QLabel(content)
 
        # setting alignment to the text
        # self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
 
        # making label multi-line
        self.label.setWordWrap(True)
 
        # adding label to the layout
        lay.addWidget(self.label)
 
        if keep_bottom:
            self.verticalScrollBar().rangeChanged.connect(
                self.scrollToBottom,
            )

    # new function in same class
    def scrollToBottom (self, minVal=None, maxVal=None):
        # Additional params 'minVal' and 'maxVal' are declared because
        # rangeChanged signal sends them, but we set it to optional
        # because we may need to call it separately (if you need).
        
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        )

    # the setText method
    def setText(self, text):
        # setting text to the label
        self.label.setText(text)


