import os
import telebot
from telebot.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Вставь сюда токен ТВОЕГО НОВОГО тестового бота (который ты создавал в BotFather)
BOT_TOKEN = "9058528898:AAGEWivjXOBfFA_Uvx3-Kf4EtvwlxtiGwwU"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    # Создаем кнопку, которая открывает нашу страницу по IP и порту
    markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url="http://79.236.147.116:8091")
    markup.add(InlineKeyboardButton("🎴 Открыть покер", web_app=web_app))
    
    bot.send_message(message.chat.id, "Привет! Нажми на кнопку ниже, чтобы запустить тестовое приложение:", reply_markup=markup)

print("Бот запущен...")
bot.polling(none_stop=True)
