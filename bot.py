import os
import telebot
import requests  # Библиотека для HTTP-запросов
from telebot.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import socket

# ПРИНУДИТЕЛЬНОЕ ИСПОЛЬЗОВАНИЕ IPv4 ДЛЯ БОТА
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4
# Вставь сюда токен ТВОЕГО бота
BOT_TOKEN = "9058528898:AAGEWivjXOBfFA_Uvx3-Kf4EtvwlxtiGwwU"
bot = telebot.TeleBot(BOT_TOKEN)

# Адрес нашего локального сервера GTOpen
SERVER_URL = "http://127.0.0.1:3737/api/advice" 

def get_advice_from_server(data):
    try:
        # Отправляем JSON на сервер
        response = requests.post(SERVER_URL, json=data, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка сервера: {response.text}")
            return {"action": "ERROR", "reason": "Сервер GTOpen вернул ошибку"}
    except Exception as e:
        print(f"Сервер GTOpen не отвечает: {e}")
        return {"action": "ERROR", "reason": "Сервер GTOpen недоступен"}

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url="https://pokerbot.cyou/?v=31")
    markup.add(InlineKeyboardButton("🎴 Открыть покер", web_app=web_app))
    bot.send_message(message.chat.id, "Привет! Нажми на кнопку для веб-версии или введи данные вручную:", reply_markup=markup)

@bot.message_handler(commands=['advice'])
def handle_advice_request(message):
    msg = bot.send_message(message.chat.id, "Введите данные в формате: `As Kh Qs Js 2h 100 100`\n(Ваши карты, доска, ваш стек, стек оппонента)")
    bot.register_next_step_handler(msg, process_poker_data)

def process_poker_data(message):
    try:
        parts = message.text.split()
        if len(parts) < 6:
            bot.reply_to(message, "Ошибка: мало данных. Пример: As Kh Qs Js 2h 100 100")
            return

        data = {
            "myCards": [parts[0], parts[1]],
            "board": parts[2:5],
            "stacks": {
                "me": int(parts[5]),
                "p1": int(parts[6])
            },
            "toCall": 0,
            "pot": 0
        }

        bot.reply_to(message, "🧠 Идет расчет через GTOpen...")
        result = get_advice_from_server(data)

        bot.send_message(
            message.chat.id, 
            f"**Действие:** {result['action']}\n**Причина:** {result['reason']}",
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

print("Бот запущен...")
bot.polling(none_stop=True)
