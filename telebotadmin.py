import json
from telebot import types, TeleBot
import sqlite3


class Telebotadmin:
    """Класс для разграничения доступа к выполнению комманд бота.
    !!!ыВНИМАНИЕ!!! Не используйте callback hendlerы с текстом incperm """

    def __init__(self, bot: TeleBot, filename="users", roles: dict = None, sqlite = False):
        if sqlite:
            self.getusers = self.getuserssqlite
            self.saveusers = self.saveuserssqlite
        else:
            self.getusers = self.getusersjson
            self.saveusers = self.saveusersjson
        self.dbname = f"{filename}.db"
        db = sqlite3.connect(self.dbname)
        db.execute("CREATE TABLE IF NOT EXISTS users (chatid TEXT UNIQUE, username TEXT, permission INTEGER)")
        db.commit()
        if roles is None:
            self.roles = ["Администратор", "Модератор", "Пользователь"]
            self.rolemessages = ["Для выполнения этого действия надо быть администратором",
                                 "Для выполнения этого действия надо быть модератором",
                                 "Для выполнения этого действия надо зарегистрироваться"]
        else:
            self.roles = roles.keys()
            self.rolemessages = [roles[perm] for perm in roles.keys()]
        self.bot = bot
        self.filename = f"{filename}.json"

        def setperm(callback: types.CallbackQuery):
            users = self.getusers()
            userid, perm = callback.data.split("incperm")
            self.setperm(int(userid), int(perm))
            self.bot.send_message(callback.message.chat.id, f"Успешно установлены права уровня "
                                                            f"{self.roles[int(perm)]} пользователю "
                                                            f"{users[userid]["username"]}")
            self.bot.send_message(int(userid), f"Ваша увеличенная привилегия: {self.roles[int(perm)]}")

        self.bot.callback_query_handler(func=lambda call: "incperm" in call.data)(setperm)

    def saveuserssqlite(self, users: dict):
        """Сохраняет словарь с пользователями вида {chatid: {"username": "username", "permission": 0}}"""
        with sqlite3.connect(self.dbname) as db:
            for chatid, user in users.items():
                db.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (chatid, user["username"], user["permission"]))

    def getuserssqlite(self) -> dict:
        """Возвращает словарь с пользователями вида {chatid: {"username": "username", "permission": 0}}"""
        with sqlite3.connect(self.dbname) as db:
            return {row[0]: {"username": row[1], "permission": row[2]} for row in db.execute("SELECT * FROM users")}

    def getusersjson(self):
        """Возвращает словарь с пользователями вида {chatid: {"username": "username", "permission": 0}}"""
        try:
            with open(self.filename, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def saveusersjson(self, users: dict):
        """Сохраняет словарь с пользователями вида {chatid: {"username": "username", "permission": 0}}"""
        with open(self.filename, "w") as file:
            json.dump(users, file, indent=4)

    def adduser(self, chatid: int, username: str, perm=-2):
        """Добавление пользователя по чат айди и имени пользователя"""
        perm = len(self.roles) - 1 if perm == -2 else perm
        users = self.getusers()
        user = {
            "username": username,
            "permission": perm
        }
        users[str(chatid)] = user
        self.saveusers(users)

    def adduserm(self, message, perm=-2):
        """Добавление пользователя по чат айди и имени пользователя"""
        perm = len(self.roles) - 1 if perm == -2 else perm
        self.adduser(message.from_user.id, message.from_user.username, perm)

    def deluser(self, chatid: int):
        """Удаление пользователя по чат айди"""
        users = self.getusers()
        ids = str(chatid)
        if ids in users:
            del users[ids]
            with open(self.filename, "w") as file:
                json.dump(users, file, indent=4)

    def deluserm(self, message):
        """Удаление пользователя по сообщению"""
        self.deluser(message.from_user.id)

    def haspermission(self, chatid: int, perm: int):
        """Возвращает True, если пользователь имеет данную привилегию"""
        users = self.getusers()
        ids = str(chatid)
        if ids in users:
            return users[ids]["permission"] <= perm
        return False

    def setaccess(self, permission: int):
        """Возвращает декоратор для проверки привилегий"""

        def decorator(func):
            def wrapper(message: types.Message, *args, **kwargs):
                if self.haspermission(message.from_user.id, permission):
                    func(message, *args, **kwargs)
                else:
                    self.bot.send_message(message.chat.id, self.rolemessages[permission])

            return wrapper

        return decorator

    def getperm(self, chatid):
        """Возвращает название привилегии по чат айди"""
        if str(chatid) not in self.getusers():
            return "Не зарегистрирован"
        user = self.getusers()[str(chatid)]
        if user:
            return self.roles[user["permission"]]
        return "Не зарегистрирован"

    def istegistered(self, chatid):
        """Возвращает True, если пользователь зарегистрирован"""
        return str(chatid) in self.getusers()

    def isregesteredm(self, message):
        """Возвращает True, если пользователь зарегистрирован"""
        return self.istegistered(message.from_user.id)

    def getpermm(self, message: types.Message):
        """Возвращает название привилегии по сообщению"""
        return self.getperm(message.chat.id)

    def setperm(self, chatid, permission):
        """Устанавливает привилегию по чат айди"""
        users = self.getusers()
        users[str(chatid)]["permission"] = permission
        self.saveusers(users)

    def requestperminc(self, message: types.Message):
        """Запрос на увеличение привилегий"""
        users = self.getusers()
        if users[str(message.chat.id)]["permission"] == 0:
            self.bot.send_message(message.chat.id, "Вы  и так имеете максимальные права!")
        else:
            acceptmenu = types.InlineKeyboardMarkup()
            acceptmenu.add(types.InlineKeyboardButton(text="Да",
                                                      callback_data=f"{message.chat.id}incperm"
                                                                    f"{users[str(message.chat.id)]['permission'] - 1}"))
            acceptmenu.add(types.InlineKeyboardButton(text="Нет",
                                                      callback_data=f"{message.chat.id}incperm"
                                                                    f"{users[str(message.chat.id)]['permission']}"))
            for userid in users.keys():
                if users[userid]["permission"] < users[str(message.chat.id)]["permission"] - 1:
                    self.bot.send_message(userid,
                                          f"Пользователь {users[str(message.chat.id)]['username']} "
                                          f"запросил увеличение прав на "
                                          f"{self.roles[int(users[str(message.chat.id)]['permission']) - 1]}"
                                          f", повысить ему права?",
                                          reply_markup=acceptmenu)
            self.bot.send_message(message.chat.id, f"Отправлен запрос на получение прав уровня "
                                                   f"{self.roles[users[str(message.chat.id)]['permission'] - 1]}")

    def decreaseperm(self, message: types.Message):
        """Уменьшение привилегий"""
        users = self.getusers()
        availibleusers = {}
        for userid in users.keys():
            if users[userid]["permission"] > users[str(message.chat.id)]["permission"] and users[userid]["permission"] != len(self.roles) - 1:
                availibleusers[userid] = users[userid]
        if len(availibleusers) == 0:
            self.bot.send_message(message.chat.id, "Нет доступных пользователей")
        else:
            usersmenu = types.InlineKeyboardMarkup()
            for userid in availibleusers.keys():
                usersmenu.add(types.InlineKeyboardButton(availibleusers[userid]["username"],
                                                         callback_data=f"{userid}incperm"
                                                                       f"{availibleusers[userid]['permission'] + 1}"))
            self.bot.send_message(message.chat.id, f"Выберите пользователя для уменьшения привилегий до уровня "
                                                   f"{self.roles[users[str(message.chat.id)]['permission'] + 1]}",
                                  reply_markup=usersmenu)
