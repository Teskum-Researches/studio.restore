import requests
import time
import re
import threading
from http.cookies import SimpleCookie
from datetime import datetime, timedelta, UTC
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QListWidget
from PyQt6 import uic


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.setWindowTitle('Studio.Restore()')
        self.setGeometry(100, 100, 600, 480) # (x, y, ширина, высота)
        self.setFixedSize(600, 480)
        self.username = QLineEdit()
        self.username.setPlaceholderText('Ник')

        self.password = QLineEdit()
        self.password.setPlaceholderText('Пароль')
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.destroyer = QLineEdit()
        self.destroyer.setPlaceholderText('Ник уничтожителя')

        self.studio_line = QLineEdit()
        self.studio_line.setPlaceholderText('ID или ссылка уничтоженной студии')


        self.logs = QListWidget()

        self.restore_btn = QPushButton('Восстановить')

        layout = QVBoxLayout()

        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.destroyer)
        layout.addWidget(self.studio_line)
        layout.addWidget(self.restore_btn)
        layout.addWidget(self.logs)

        self.setLayout(layout)

        self.restore_btn.clicked.connect(self.restore)

        
    def log(self, message):
        window.logs.addItem(message)
        window.logs.scrollToBottom()

    def restore(self):
        self.log("unreleased")


        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show() # Показываем окно
    sys.exit(app.exec())