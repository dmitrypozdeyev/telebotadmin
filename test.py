from config import *
from telebotadmin import Telebotadmin
from telebot import TeleBot, types


bot = TeleBot(TOKEN)
admin = Telebotadmin(bot, sqlite=True)

@bot.message_handler(commands=['start'])
def register(message):
    if not admin.isregesteredm(message):
        admin.adduserm(message)
    bot.send_message(message.chat.id, f"Привет {message.from_user.username}! Вы зарегистрированы!")

@bot.message_handler(commands=['foradmin'])
@admin.setaccess(0)
def foradmin(message : types.Message):
    bot.send_message(message.chat.id, "сообщение для администратора")

@bot.message_handler(commands=['formoder'])
@admin.setaccess(1)
def formoder(message : types.Message):
    bot.send_message(message.chat.id, "сообщение для модератора")

@bot.message_handler(commands=['incperm'])
def incperm(message : types.Message):
    admin.requestperminc(message)


@bot.message_handler(commands=['showuserdict'])
def showuserdict(message : types.Message):
    bot.send_message(message.chat.id, str(admin.getusers()[str(message.chat.id)]))

if __name__ == '__main__':
    bot.infinity_polling()
