import requests
import time
import re
import threading
from http.cookies import SimpleCookie
from datetime import datetime, timedelta, UTC
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QListWidget, QPushButton, QVBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Studio.Restore()')
        self.setGeometry(100, 100, 400, 100) # (x, y, ширина, высота)
        self.username = QLineEdit()
        self.username.setPlaceholderText('Имя пользователя')
        self.password = QLineEdit()
        self.password.echoMode("Password")
        self.password.setPlaceholderText('Пароль')
        self.restore_btn = QPushButton('Восстановить')
        self.logs = QListWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.restore_btn)
        layout.addWidget(self.logs)
        self.setLayout(layout)
    def log(message):
        window.logs.addItem(message)
        window.logs.scrollToBottom()
if __name__ == "__main__":
    global window
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())