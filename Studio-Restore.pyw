import requests
import time
import re
import sys

from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                            QLineEdit, QListWidget, QLabel, QProgressBar, 
                            QHBoxLayout)
from PyQt6.QtCore import QThread, pyqtSignal, QObject

# Функции для взаимодействия с Scratch API
def login(username, password):
    session = requests.Session()
    session.get("https://scratch.mit.edu/csrf_token/")
    csrf_token = session.cookies.get('scratchcsrftoken')
    headers = {
        "referer": "https://scratch.mit.edu",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json",
        "Accept-Language": "ru-RU,ru;q=0.9"
    }
    body = {
        "username": username,
        "password": password,
        "useMessages": "true"
    }
    respo = session.post(
        "https://scratch.mit.edu/accounts/login/",
        headers=headers,
        json=body
    )
    if respo.status_code == 200:
        cookies = respo.cookies
        session_cookie = cookies.get('scratchsessionsid')
        if not session_cookie:
            return {"success": False, "msg": "Не удалось получить cookie сессии."}

        cookie_string = f'scratchsessionsid="{session_cookie}"; scratchcsrftoken={csrf_token}'
        head = {
            "Cookie": cookie_string,
            "referer": "https://scratch.mit.edu/",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrf_token,
            "Content-Type": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Origin": "https://scratch.mit.edu",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept": "*/*",
        }
        
        resp = requests.get("https://scratch.mit.edu/session/", headers=head)
        if resp.status_code == 200:
            lol = resp.json()
            return {"success": True, "cookie": head, "token": lol["user"]["token"], "username": lol["user"]["username"], "isbanned": lol["user"]["banned"]}
        else:
            return {"success": False, "msg": "Не удалось получить информацию о сессии."}
    else:
        try:
            data = respo.json()
            return {"success": False, "msg": data[0].get("msg")}
        except (requests.exceptions.JSONDecodeError, IndexError):
            return {"success": False, "msg": "Ошибка входа, проверьте имя пользователя и пароль."}

def addproject(token, studio, project):
    r = requests.post(f"https://api.scratch.mit.edu/studios/{str(studio)}/project/{str(project)}/", headers={"X-Token": token})
    return r.status_code

def invite(studio, user, cookie):
    resp = requests.put(f"https://scratch.mit.edu/site-api/users/curators-in/{str(studio)}/invite_curator/?usernames={user}", headers=cookie)
    if resp.status_code == 200:
        try:
            j = resp.json()
            if j["status"] == "success":
                return {"success": True, "data": f"Пригласили {user}"}
            elif j["status"] == "error":
                return {"success": True, "data": f"{user} уже есть в приглашённых/кураторах/менеджерах"}
            else:
                return {"success": True, "data": f"Произошла неизвестная ошибка при приглашении {user}"}
        except requests.exceptions.JSONDecodeError:
            return {"success": False, "status": resp.status_code, "msg": "Неверный ответ от API."}
    else:
        return {"success": False, "status": resp.status_code}
    
def openprojects(cookie, studio):
    resp = requests.put(f"https://scratch.mit.edu/site-api/galleries/{str(studio)}/mark/open/", headers=cookie)
    return resp.status_code == 200

def removeproject(token, studio, project):
    r = requests.delete(f"https://api.scratch.mit.edu/studios/{str(studio)}/project/{str(project)}/", headers={"X-Token": token})
    return r.status_code

def removeuser(studio, user, cookie):
    resp = requests.put(f"https://scratch.mit.edu/site-api/users/curators-in/{str(studio)}/remove/?usernames={user}", headers=cookie)
    return resp.status_code

def getactivity(studio: int, log):
    datelimit = datetime.now().isoformat()
    first = True

    while True:
        res = requests.get(f'https://api.scratch.mit.edu/studios/{studio}/activity?limit=20&dateLimit={datelimit}')
        if res.status_code == 200:
            pass
        elif res.status_code == 404:
            log.emit("Студия удалена! Восстановление невозможно!")
            return
        elif res.status_code >= 500:
            log.emit(f"Произошла ошибка сервера: {res.status_code}. Повторная попытка через 30 секунд...")
            time.sleep(30)
        else:
            log.emit(f"Произошла неожиданная ошибка: {res.status_code}")
            return

        data = res.json()
        if not first:
            data = data[1:]
        if len(data) == 0: 
            return
        for item in data:
            yield item
    
        first = False
        datelimit = data[-1]['datetime_created']

class Worker(QObject):
    log_message = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    task_finished = pyqtSignal()

    def __init__(self, username: str, password: str, studio_id: int, destroyer_name: str):
        super().__init__()
        self.username = username
        self.password = password
        self.studio_id = studio_id
        self.destroyer_name = destroyer_name
        self.is_running = True

    def run(self):
        self.log_message.emit("Собираем информацию о действиях уничтожителя...")
        all_acts = []
        c = 0
        acts = getactivity(self.studio_id, self.log_message)

        while True:
            if not self.is_running: 
                break

            try:
                act = next(acts)
            except StopIteration:
                break

            if act["actor_username"].lower() == self.destroyer_name.lower():
                all_acts.append(act)
            else:
                c += 1
                if c >= 3 * 40:
                    break

        if not self.is_running:
            self.task_finished.emit()
            return

        if len(all_acts) == 0:
            self.log_message.emit("Не найдено действий уничтожителя. Восстановление не требуется.")
            self.task_finished.emit()
            return

        percent_per_act = 100 / len(all_acts)
        current_progress = 0
        self.log_message.emit("Входим в аккаунт...")
        account = login(self.username, self.password)
        if not self.is_running:
            self.task_finished.emit()
            return
            
        if not account["success"]:
            self.log_message.emit(f"Ошибка входа: {account['msg']}")
            self.task_finished.emit()
            return

        if account["isbanned"]:
            self.log_message.emit("Аккаунт забанен!")
            self.task_finished.emit()
            return
        
        self.log_message.emit("Начинаем восстановление!")
        
        for act in all_acts:
            if not self.is_running: 
                break

            if act["type"] == "updatestudio":
                if openprojects(account["cookie"], self.studio_id):
                    self.log_message.emit('Включено "Любой может добавлять проекты"')
                else:
                    self.log_message.emit('Не удалось включить "любой может добавлять проекты"')
            elif act["type"] == "removeprojectstudio":
                l = True
                while l:
                    l = False
                    p = addproject(account["token"], self.studio_id, act["project_id"])
                    if p == 200:
                        self.log_message.emit(f'Добавлен проект "{act["project_title"]}"')
                    elif p == 429:
                        self.log_message.emit("Аккаунт получил временное ограничение на добавление проектов. Повторная попытка через 1 минуту...")
                        l = True
                        time.sleep(60)
                    elif p == 403:
                        self.log_message.emit(f'Проект "{act["project_title"]}" не в общем доступе')
                    else:
                        self.log_message.emit(f'Произошла ошибка {p} при добавлении проекта "{act["project_title"]}"')
            elif act["type"] == "addprojecttostudio":
                l = True
                while l:
                    l = False
                    p = removeproject(account["token"], self.studio_id, act["project_id"])
                    if p == 200 or p == 204:
                        self.log_message.emit(f'Удалён проект "{act["project_title"]}"')
                    elif p == 429:
                        self.log_message.emit("Слишком много запросов. Следующая попытка будет через 1 минуту...")
                        l = True
                        time.sleep(60)
                    elif p == 403:
                        self.log_message.emit(f'Проект "{act["project_title"]}" не в общем доступе')
                    else:
                        self.log_message.emit(f'Произошла ошибка {p} при удалении проекта "{act["project_title"]}"')
            elif act["type"] == "removecuratorstudio":
                if act["username"].lower() == self.destroyer_name.lower():
                    self.log_message.emit(f"{self.destroyer_name} не приглашаем, он уничтожил студию")
                else:
                    iii = invite(self.studio_id, act["username"], account["cookie"])
                    if iii["success"]:
                        self.log_message.emit(iii["data"])
                    else:
                        self.log_message.emit(f"Ошибка {iii.get('status')} при приглашении {act['username']}")
            elif act["type"] == "becomeownerstudio":
                rem = removeuser(self.studio_id, act["recipient_username"], account["cookie"])
                if rem == 200:
                    self.log_message.emit(f'Успешно удалён возможный твинк "{act["recipient_username"]}"')
                else:
                    self.log_message.emit(f"Произошла ошибка {rem} при удалении возможного твинка с именем {act['recipient_username']}")
            
            current_progress += percent_per_act
            self.progress_updated.emit(int(current_progress))

        if self.is_running:
            self.log_message.emit("Восстановление завершено!")
        else:
            self.log_message.emit("Восстановление отменено.")
        self.task_finished.emit()

    def stop(self):
        self.is_running = False

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Studio.Restore()')
        self.setGeometry(100, 100, 600, 480)
        self.setFixedSize(600, 480)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Ник')

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.destroyer_input = QLineEdit()
        self.destroyer_input.setPlaceholderText('Ник уничтожителя')

        self.studio_input = QLineEdit()
        self.studio_input.setPlaceholderText('ID или ссылка уничтоженной студии')

        self.logs = QListWidget()
        self.copyright_label = QLabel("© 2025 Teskum Researches")

        self.restore_btn = QPushButton('Восстановить')
        self.cancel_btn = QPushButton('Отмена')
        self.cancel_btn.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        self.worker_thread = None
        self.worker = None

        # Layout для кнопок
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.restore_btn)
        button_layout.addWidget(self.cancel_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.destroyer_input)
        layout.addWidget(self.studio_input)
        layout.addLayout(button_layout)
        layout.addWidget(self.logs)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.copyright_label)
        

        self.setLayout(layout)
        self.restore_btn.clicked.connect(self.start_restore)
        self.cancel_btn.clicked.connect(self.cancel_restore)

    def start_restore(self):
        self.progress_bar.setValue(0)
        self.logs.clear()
        
        username = self.username_input.text().strip()
        password = self.password_input.text()
        destroyer_name = self.destroyer_input.text().strip()
        studio_text = self.studio_input.text().strip()

        if not all([username, password, destroyer_name, studio_text]):
            self.log("Пожалуйста, заполните все поля.")
            return

        try:
            studio_id_match = re.search(r'\d+', studio_text)
            if not studio_id_match:
                self.log("Неверный формат ID студии. Укажите число.")
                return
            studio_id = int(studio_id_match.group(0))
        except (ValueError, IndexError):
            self.log("Неверный формат ID студии. Укажите число.")
            return
            
        self.restore_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        self.worker_thread = QThread()
        self.worker = Worker(username, password, studio_id, destroyer_name)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.log_message.connect(self.log)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.task_finished.connect(self.task_finished)
        self.worker.task_finished.connect(self.worker_thread.quit)
        self.worker.task_finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        self.worker_thread.start()

    def cancel_restore(self):
        if self.worker:
            self.worker.stop()
        self.restore_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def task_finished(self):
        self.restore_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)

    def log(self, message):
        self.logs.addItem(message)
        self.logs.scrollToBottom()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
