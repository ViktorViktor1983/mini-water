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

# Порядок мест по часовой стрелке
SEAT_ORDER = ['p1', 'p2', 'p3', 'p4', 'p5', 'me', 'p6', 'p7', 'p8']

# Диапазоны рук
PREMIUM = ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
STRONG = ["TT", "99", "AQs", "AJs", "KQs"]
PLAYABLE = ["88", "77", "66", "55", "44", "33", "22", "ATs", "KJs", "KTs", "QJs", "JTs", "T9s", "98s", "87s", "76s", "65s"]

def get_my_position(data):
    """Определяет позицию 'me' относительно BB"""
    bb_seat = data.get('bbSeat')
    sb_seat = data.get('sbSeat')
    active_seats = data.get('stacks', {})
    
    # Активные места в порядке
    active_in_order = [s for s in SEAT_ORDER if s in active_seats]
    
    if 'me' not in active_in_order or bb_seat not in active_in_order:
        return "UNKNOWN", 0
    
    me_idx = active_in_order.index('me')
    bb_idx = active_in_order.index(bb_seat)
    sb_idx = active_in_order.index(sb_seat) if sb_seat in active_in_order else (bb_idx - 1) % len(active_in_order)
    btn_idx = (sb_idx - 1) % len(active_in_order)
    
    if me_idx == bb_idx:
        return "BB", 0
    elif me_idx == sb_idx:
        return "SB", 1
    elif me_idx == btn_idx:
        return "BTN", 5
    else:
        # Считаем сколько мест от BTN до нас (назад)
        distance = (btn_idx - me_idx) % len(active_in_order)
        if distance == 1:
            return "CO", 4
        elif distance == 2:
            return "MP", 3
        else:
            return "UTG", 2

def get_my_zone(data):
    """Возвращает зону стека 'me'"""
    stacks = data.get('stacks', {})
    me_stack = stacks.get('me', '100')
    
    if '-' in str(me_stack):
        zone = str(me_stack)
    elif '+' in str(me_stack):
        zone = str(me_stack)
    else:
        try:
            val = float(me_stack)
            if val < 15: zone = "0-15"
            elif val < 25: zone = "15-25"
            elif val < 40: zone = "25-40"
            elif val < 100: zone = "40-100"
            else: zone = "100+"
        except:
            zone = "100+"
    return zone

@app.route('/api/advice', methods=['POST'])
def get_advice():
    data = request.json
    my_cards = data.get('myCards', [])
    to_call = data.get('toCall', 0)
    
    if not my_cards or '?' in my_cards or len(my_cards) < 2:
        return jsonify({"action": "ОШИБКА", "reason": "Введите свои карты (нажмите на слоты ?)"})

    try:
        card1, card2 = my_cards[0], my_cards[1]
        rank1, suit1 = card1[0], card1[1]
        rank2, suit2 = card2[0], card2[1]
        
        ranks = "23456789TJQKA"
        r1_idx = ranks.index(rank1)
        r2_idx = ranks.index(rank2)
        
        is_pair = rank1 == rank2
        is_suited = suit1 == suit2
        
        high_rank = rank1 if r1_idx > r2_idx else rank2
        low_rank = rank2 if r1_idx > r2_idx else rank1
        
        hand_str = f"{high_rank}{low_rank}"
        if is_pair:
            hand_str += "p"
        elif is_suited:
            hand_str += "s"
        else:
            hand_str += "o"
    except Exception as e:
        return jsonify({"action": "ОШИБКА", "reason": f"Не удалось распознать карты: {my_cards}"})

    position, pos_rank = get_my_position(data)
    zone = get_my_zone(data)
    
    # Определяем категорию руки
    hand_base = hand_str.replace("p", "")
    is_premium = hand_str.replace("p", "") in ["AA", "KK", "QQ", "JJ", "AK"] or hand_str in ["AKs", "AKo"]
    is_strong = hand_base in ["TT", "99", "AQ", "AJ", "KQ"]
    is_playable = hand_base in ["88","77","66","55","44","33","22","AT","KJ","KT","QJ","JT","T9","98","87","76","65"]
    
    # ===== ЛОГИКА ПРЕФЛОПА =====
    
    # Короткий стек (0-15) - режим Push/Fold
    if zone == "0-15":
        if is_premium or (is_strong and position in ["BTN", "CO"]):
            return jsonify({
                "action": "ALL-IN",
                "reason": f"Позиция: {position}. Зона стека: {zone}bb (Push/Fold). У вас {hand_str} — это сильная рука для пуша. Идите олл-ин."
            })
        else:
            return jsonify({
                "action": "FOLD",
                "reason": f"Позиция: {position}. Зона стека: {zone}bb (Push/Fold). С {hand_str} в этой зоне лучше сбросить."
            })
    
    # Если перед нами была ставка
    if to_call > 0:
        if is_premium:
            return jsonify({
                "action": "RAISE",
                "reason": f"Позиция: {position}. У вас премиум-рука {hand_str}. Делайте 3-бет или 4-бет."
            })
        elif is_strong and position in ["BTN", "CO", "BB"]:
            return jsonify({
                "action": "CALL",
                "reason": f"Позиция: {position}. У вас {hand_str} — сильная рука. Колл против агрессии оправдан."
            })
        else:
            return jsonify({
                "action": "FOLD",
                "reason": f"Позиция: {position}. С {hand_str} против {to_call}bb колл не оправдан. Сброс."
            })
    
    # Ставок нет — мы можем открыться
    else:
        if is_premium or is_strong:
            return jsonify({
                "action": "RAISE",
                "reason": f"Позиция: {position}. У вас {hand_str} — отличная рука. Открывайте рейзом."
            })
        elif is_playable and position in ["BTN", "CO"]:
            return jsonify({
                "action": "RAISE",
                "reason": f"Позиция: {position}. С {hand_str} в поздней позиции можно открыть рейз."
            })
        elif position in ["BB", "SB"]:
            return jsonify({
                "action": "CHECK",
                "reason": f"Позиция: {position}. С {hand_str} лучше прочекать и посмотреть флоп бесплатно."
            })
        else:
            return jsonify({
                "action": "FOLD",
                "reason": f"Позиция: {position}. С {hand_str} из ранней позиции лучше сбросить."
            })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8091)
