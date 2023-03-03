from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton
import datetime
import sys
from pynput.mouse import Listener


class ScreenshotThread(QThread):
    screenshot_taken = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False

    def run(self):
        self.running = True
        with Listener(on_click=self.on_click) as listener:
            while self.running:
                listener.join()

    def stop(self):
        self.running = False

    def on_click(self, x, y, button, pressed):
        if pressed:
            print(f"Mouse clicked at ({x}, {y}) with {button}")
            screen = QCoreApplication.instance().primaryScreen()
            screenshot = screen.grabWindow(0)
            filename = f"screenshots/screen{datetime.datetime.now()}.png"
            screenshot.save(filename, 'png')
            self.screenshot_taken.emit(filename)


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
        self.screenshot_thread = None

    def start_monitoring(self):
        self.monitoring = True
        self.screenshot_thread = ScreenshotThread()
        self.screenshot_thread.screenshot_taken.connect(self.handle_screenshot)
        self.screenshot_thread.start()

    def stop_monitoring(self):
        if self.screenshot_thread is not None:
            self.screenshot_thread.stop()
        self.close()

    def handle_screenshot(self, filename):
        print(f'Screenshot taken: {filename}')

    def closeEvent(self, event):
        self.stop_monitoring()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = MainWindow(app)
    dialog.show()
    sys.exit(app.exec_())
