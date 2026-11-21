from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app) # Разрешаем запросы с нашего же домена

# Отдаем главную страницу
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Отдаем остальные файлы (css, js, картинки)
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# Прием данных для ИИ
@app.route('/api/advice', methods=['POST'])
def get_advice():
    data = request.json
    print("=== ПОЛУЧЕНЫ ДАННЫЕ С КЛИЕНТА ===")
    print(data)
    print("=================================")

    # Здесь в будущем будет логика PokerKit и OpenAI.
    # А пока возвращаем тестовую заглушку, чтобы проверить связь.
    
    to_call = data.get('toCall', 0)
    
    if to_call > 0:
        action = "CALL"
        reason = f"Нужно доставить {to_call} BB. Это тестовый ответ от сервера. Связь работает!"
    else:
        action = "CHECK"
        reason = "Ставок нет. Это тестовый ответ от сервера. Связь работает!"

    return jsonify({
        "action": action,
        "reason": reason
    })

if __name__ == '__main__':
    # Запускаем на порту 8091
    app.run(host='127.0.0.1', port=8091)
