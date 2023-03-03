import datetime
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton
from PyQt5.QtCore import QCoreApplication
from pynput.mouse import Listener


class MainWindow(QDialog):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.setWindowTitle('Monitoring App')
        self.setGeometry(100, 100, 250, 100)

        # Start button
        self.start_button = QPushButton('Start', self)
        self.start_button.setGeometry(30, 30, 80, 30)
        self.start_button.clicked.connect(self.start_monitoring)

        # Stop button
        self.stop_button = QPushButton('Stop', self)
        self.stop_button.setGeometry(130, 30, 80, 30)
        self.stop_button.clicked.connect(self.stop_monitoring)

        # Initial state of the variable to follow button clicks
        self.monitoring = False

    def start_monitoring(self):
        self.monitoring = True
        with Listener(on_click=self.take_screenshot) as listener:
            while self.monitoring:
                QCoreApplication.processEvents()

    def stop_monitoring(self):
        self.monitoring = False
        # self.close() - close application when press stop button

    def take_screenshot(self, x, y, button, pressed):
        if pressed:
            print(f"Mouse clicked at ({x}, {y}) with {button}")
            screen = self.app.primaryScreen()
            screenshot = screen.grabWindow(0)
            filename = f"screenshots/screen{datetime.datetime.now()}.png"
            screenshot.save(filename, 'png')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = MainWindow(app)
    dialog.show()
    sys.exit(app.exec_())
