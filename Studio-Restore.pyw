import requests
import time
import re
import threading
from http.cookies import SimpleCookie
from datetime import datetime, timedelta, UTC
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QListWidget, QLabel, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)

    def run(self):
        for i in range(101):
            time.sleep(0.05)  # Имитация работы
            self.progress_updated.emit(i)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
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
        self.copyright = QLabel()
        self.copyright.setText("© 2025 Teskum Researches")

        self.restore_btn = QPushButton('Восстановить')
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        layout = QVBoxLayout()

        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.destroyer)
        layout.addWidget(self.studio_line)
        layout.addWidget(self.restore_btn)
        layout.addWidget(self.logs)
        layout.addWidget(self.copyright)
        layout.addWidget(self.progress_bar)


        self.setLayout(layout)

        self.restore_btn.clicked.connect(self.restore)

        
    def log(self, message):
        window.logs.addItem(message)
        window.logs.scrollToBottom()

    def restore(self):
        self.progress_bar.setValue(0)  # Сбрасываем прогресс
        self.restore_btn.setEnabled(False)  # Делаем кнопку неактивной на время процесса
        self.worker = WorkerThread()
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.task_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def task_finished(self):
        self.restore_btn.setEnabled(True)  # Возвращаем кнопку в активное состояние
        self.progress_bar.setValue(100)
        
        # Опционально: можно показать сообщение, что задача завершена
        self.log("Ура, восстонавили!")


        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show() # Показываем окно
    sys.exit(app.exec())