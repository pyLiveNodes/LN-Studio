from qtpy import QtWidgets, QtCore

class LoadingWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading")
        self.setFixedSize(400, 100)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        layout = QtWidgets.QVBoxLayout()

        # Add image
        # self.image_label = QtWidgets.QLabel(self)
        # pixmap = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), 'static') + "/connected_human_light.jpg")  # Replace with your image path
        # scaled_pixmap = pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        # self.image_label.setPixmap(scaled_pixmap)
        # self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        # layout.addWidget(self.image_label)

        # Add loading bar
        self.loading_bar = QtWidgets.QProgressBar(self)
        self.loading_bar.setRange(0, 0)  # Determinate mode
        layout.addWidget(self.loading_bar)

        # Add status text
        self.status_label = QtWidgets.QLabel(self)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Center the window on the screen
        self.center_on_screen()

    def center_on_screen(self):
        screen_geometry = QtWidgets.QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
 
    def update_status(self, status):
        self.status_label.setText(status)

        