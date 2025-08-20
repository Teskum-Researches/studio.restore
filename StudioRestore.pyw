import requests
import time
import re
import threading
from http.cookies import SimpleCookie
from datetime import datetime, timedelta, UTC
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6 import uic


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('gui.ui', self)


        
    def log(message):
        window.logs.addItem(message)
        window.logs.scrollToBottom()


        
if __name__ == "__main__":
    global window
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())