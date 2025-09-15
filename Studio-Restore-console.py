import requests
import time
import re

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

        cookie_string = f'scratchsessionsid="{session_cookie.value}"; scratchcsrftoken={csrf_token}'
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
    
def getactivity(studio, offset):
    req = requests.get(f"https://api.scratch.mit.edu/studios/{str(studio)}/activity?limit=40&offset={str(offset)}")
    if req.status_code == 200:
        return {"success": True, "data": req.json()}
    else:
        return {"success": False, "status": req.status_code}
    
def openprojects(cookie, studio):
    resp = requests.put(f"https://scratch.mit.edu/site-api/galleries/{str(studio)}/mark/open/", headers=cookie)
    return resp.status_code == 200

def removeproject(token, studio, project):
    r = requests.delete(f"https://api.scratch.mit.edu/studios/{str(studio)}/project/{str(project)}/", headers={"X-Token": token})
    return r.status_code

def removeuser(studio, user, cookie):
    resp = requests.put(f"https://scratch.mit.edu/site-api/users/curators-in/{str(studio)}/remove/?usernames={user}", headers=cookie)
    return resp.status_code

def main():
    username = input("Ник: ")
    password = input("Пароль: ")
    destroyer = input("Уничтожитель: ")
    studio = re.search(r'\d+', input("Студия: "))

    print("Собираем информацию о действиях уничтожителя...")

    off = 0
    loop = True
    all_acts = []
    c = 0
    while loop:
        a = getactivity(studio, off)
        if a["success"]:
            hasd = False
            for act in a["data"]:
                if act["actor_username"].lower() == destroyer.lower():
                    hasd = True
            if hasd:
                all_acts += a["data"]
                c = 0
            else:
                c += 1
                if c >= 3:
                    loop = False
            off += 40
        elif a.get("status") == 404:
            print("Студия удалена! Восстановление невозможно!")
            return
        elif a.get("status", 0) >= 500:
            print(f"Произошла ошибка сервера: {a.get('status')}. Повторная попытка через 30 секунд...")
            time.sleep(30)
        else:
            print(f"Произошла неожиданная ошибка: {a.get('status')}")
            return
    total_acts = len(all_acts)
    percent_per_act = 100 / total_acts
    current_progress = 0

    def log(msg):
        print(f"({current_progress}) {msg}")

    if total_acts == 0:
        log("Не найдено действий уничтожителя. Восстановление не требуется.")
        return
    print("Входим в аккаунт...")
    account = login(username, password)

    if account["success"]:
        if account["isbanned"]:
            print("Аккаунт забанен!")
            return
    else:
        print(f"Ошибка входа: {account['msg']}")
    
    print("Начинаем восстановление!")
    for i, act in enumerate(all_acts):
        current_progress += percent_per_act
        if act["actor_username"].lower() == destroyer.lower():
            if act["type"] == "updatestudio":
                if openprojects(account["cookie"], studio):
                    log('Включено "Любой может добавлять проекты"')
                else:
                    log('Не удалось включить "любой может добавлять проекты"')
            elif act["type"] == "removeprojectstudio":
                l = True
                while l:
                    l = False
                    p = addproject(account["token"], studio, act["project_id"])
                    if p == 200:
                        log(f'Добавлен проект "{act["project_title"]}"')
                    elif p == 429:
                        log("Аккаунт получил временное ограничение на добавление проектов. Повторная попытка через 1 минуту...")
                        l = True
                        time.sleep(60)
                    elif p == 403:
                        log(f'Проект "{act["project_title"]}" не в общем доступе')
                    else:
                        log(f'Произошла ошибка {p} при добавлении проекта "{act["project_title"]}"')
            elif act["type"] == "addprojecttostudio":
                l = True
                while l:
                    l = False
                    p = removeproject(account["token"], studio, act["project_id"])
                    if p == 200 or p == 204:
                        log(f'Удалён проект "{act["project_title"]}"')
                    elif p == 429:
                        log("Слишком много запросов. Следующая попытка будет через 1 минуту...")
                        l = True
                        time.sleep(60)
                    elif p == 403:
                        log(f'Проект "{act["project_title"]}" не в общем доступе')
                    else:
                        log(f'Произошла ошибка {p} при удалении проекта "{act["project_title"]}"')
            elif act["type"] == "removecuratorstudio":
                if act["username"].lower() == destroyer.lower():
                    log(f"{destroyer} не приглашаем, он уничтожил студию")
                else:
                    iii = invite(studio, act["username"], account["cookie"])
                    if iii["success"]:
                        log(iii["data"])
                    else:
                        log(f"Ошибка {iii.get('status')} при приглашении {act['username']}")
            elif act["type"] == "becomeownerstudio":
                rem = removeuser(studio, act["recipient_username"], account["cookie"])
                if rem == 200:
                    log(f'Успешно удалён возможный твинк "{act["recipient_username"]}"')
                else:
                    log(f"Произошла ошибка {rem} при удалении возможного твинка с именем {act['recipient_username']}")
    log("Восстановление завершено!")
        


if __name__ == '__main__':
    main()