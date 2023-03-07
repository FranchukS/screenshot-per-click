import datetime
import pickle
import sys

import jwt
import requests
from PyQt5.QtWidgets import QApplication, QDialog, QWidget
from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication, pyqtSignal
from pynput.mouse import Listener


API_LOGIN = "http://localhost:8000/api/v1/signin/"
API_TOKEN_REFRESH = "http://localhost:8000/api/v1/authentication/token/refresh/"
API_GET_ORGANIZATIONS = "http://localhost:8000/api/v1/organizations/"


class LoginForm(QWidget):
    login_successful = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 250, 150)

        # Username label and field
        self.username_label = QtWidgets.QLabel("Email:", self)
        self.username_label.setGeometry(30, 30, 80, 30)
        self.username_field = QtWidgets.QLineEdit(self)
        self.username_field.setGeometry(110, 30, 100, 30)

        # Password label and field
        self.password_label = QtWidgets.QLabel("Password:", self)
        self.password_label.setGeometry(30, 70, 80, 30)
        self.password_field = QtWidgets.QLineEdit(self)
        self.password_field.setGeometry(110, 70, 100, 30)
        self.password_field.setEchoMode(QtWidgets.QLineEdit.Password)

        # Login button
        self.login_button = QtWidgets.QPushButton("Login", self)
        self.login_button.setGeometry(80, 110, 80, 30)
        self.login_button.clicked.connect(self.login)

        self.parent = parent

    def login(self):
        auth_data = {
            "email": self.username_field.text(),
            "password": self.password_field.text()
        }
        try:
            response_data = self.get_token(auth_data)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid email or password.")
        else:
            print(type(response_data))
            print(response_data)
            access_token = response_data.get("access_token")
            refresh_token = response_data.get("refresh_token")
            self.login_successful.emit(access_token, refresh_token)
            self.close()

    def get_token(self, data):
        response = requests.post(API_LOGIN, data=data)

        if response.status_code != 200:
            raise ValueError("Could not authenticate user")

        response_data = response.json()
        return response_data


class MainWindow(QDialog):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.setWindowTitle("Monitoring App")
        self.setGeometry(100, 100, 450, 300)

        # Start button
        self.start_button = QtWidgets.QPushButton("Start", self)
        self.start_button.setGeometry(330, 30, 80, 30)
        self.start_button.clicked.connect(self.start_monitoring)

        # Stop button
        self.stop_button = QtWidgets.QPushButton("Stop", self)
        self.stop_button.setGeometry(330, 80, 80, 30)
        self.stop_button.clicked.connect(self.stop_monitoring)

        # organizations dropdown
        self.org_combobox = QtWidgets.QComboBox(self)
        self.org_combobox.addItem("organizations")
        self.org_combobox.setCurrentText("organizations")
        self.org_combobox.setGeometry(30, 30, 200, 30)


        # Initial state of the variable to follow button clicks
        self.monitoring = False

        # Login and tokens
        self.login = LoginForm()
        self.access_token = None
        self.refresh_token = self.load_token()
        self.login.login_successful.connect(self.set_tokens)

        self.start_app()

    def start_monitoring(self):
        self.monitoring = True
        with Listener(on_click=self.take_screenshot) as listener:
            while self.monitoring:
                QCoreApplication.processEvents()

    def stop_monitoring(self):
        self.monitoring = False

    def take_screenshot(self, x, y, button, pressed):
        if pressed:
            print(f"Mouse clicked at ({x}, {y}) with {button}")
            screen = self.app.primaryScreen()
            screenshot = screen.grabWindow(0)
            filename = f"screenshots/screen{datetime.datetime.now()}.png"
            screenshot.save(filename, "png")

    def start_app(self):
        if not self.refresh_token:
            self.login.show()
            return None

        if not self.is_token_valid() and not self.use_refresh_token():
            self.login.show()
            return None

        self.main_page()

    def set_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.save_token()
        self.start_app()

    def save_token(self):
        with open("token.pickle", "wb") as f:
            pickle.dump(self.refresh_token, f)

    @staticmethod
    def load_token():
        try:
            with open("token.pickle", "rb") as f:
                token = pickle.load(f)
                return token
        except FileNotFoundError:
            return None

    def is_token_valid(self):
        try:
            payload = jwt.decode(self.access_token, options={"verify_signature": False})
            exp = payload.get("exp")
            if exp is None:
                return False
            return datetime.datetime.utcfromtimestamp(exp) > datetime.datetime.utcnow()
        except (jwt.DecodeError, jwt.ExpiredSignatureError):
            return False

    def use_refresh_token(self):
        data = {"refresh": self.refresh_token}
        response = requests.post(API_TOKEN_REFRESH, data=data)

        if response.status_code != 200:
            self.login.show()
            return False
        print(response.json())
        self.access_token = response.json().get("access")
        return True

    def main_page(self):
        self.show()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(API_GET_ORGANIZATIONS, headers=headers)

        organizations = sorted([organization["name"] for organization in response.json()["results"]])
        self.org_combobox.addItems(organizations)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = MainWindow(app)
    sys.exit(app.exec_())
