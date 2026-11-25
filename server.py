from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/advice', methods=['POST'])
def get_advice():
    data = request.json
    print("=== ПОЛУЧЕНЫ ДАННЫЕ ===")
    print(data)
    
    my_cards = data.get('myCards', [])
    to_call = data.get('toCall', 0)
    
    # Если карты не введены
    if not my_cards or '?' in my_cards or len(my_cards) < 2:
        return jsonify({"action": "ОШИБКА", "reason": "Введите свои карты (нажмите на слоты ?)"})

    # Парсим карты
    try:
        card1, card2 = my_cards[0], my_cards[1]
        rank1, suit1 = card1[0], card1[1]
        rank2, suit2 = card2[0], card2[1]
        
        ranks = "23456789TJQKA"
        r1_idx = ranks.index(rank1)
        r2_idx = ranks.index(rank2)
        
        is_pair = rank1 == rank2
        is_suited = suit1 == suit2
        
        # Сортируем для красивого отображения (например, 93o вместо 39o)
        high_rank = rank1 if r1_idx > r2_idx else rank2
        low_rank = rank2 if r1_idx > r2_idx else rank1
        
        hand_str = f"{high_rank}{low_rank}"
        if is_pair:
            hand_str += "p" # Пара
        elif is_suited:
            hand_str += "s" # Одномастные
        else:
            hand_str += "o" # Разномастные
            
    except Exception as e:
        return jsonify({"action": "ОШИБКА", "reason": "Не удалось распознать карты. Убедитесь, что они введены как 'Ah', 'Kd'."})

    # Определяем премиум-руки
    premium = ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
    strong = ["TT", "99", "AQs", "AJs", "KQs"]
    
    # Если перед нами была ставка (toCall > 0)
    if to_call > 0:
        if hand_str in premium:
            action = "RAISE"
            reason = f"У вас премиум-рука {hand_str}. Смело делайте 3-бет или 4-бет!"
        elif hand_str in strong:
            action = "CALL"
            reason = f"У вас сильная рука {hand_str}. Можно уравнять ставку оппонента."
        else:
            action = "FOLD"
            reason = f"У вас рука {hand_str}. Это слишком слабая рука, чтобы платить {to_call} BB против агрессии оппонента."
            
    # Если ставок нет (мы можем чекнуть или открыть)
    else:
        if hand_str in premium or hand_str in strong or hand_str in ["QJs", "JTs", "T9s"]:
            action = "RAISE"
            reason = f"У вас хорошая рука {hand_str}. Открывайте ставку (Raise)."
        else:
            action = "CHECK"
            reason = f"У вас рука {hand_str}. Лучше просто прочекать (Check) и посмотреть флоп бесплатно."

    return jsonify({
        "action": action,
        "reason": reason
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8091)
