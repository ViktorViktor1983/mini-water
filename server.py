import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

CHARTS_DIR = os.path.join(os.path.dirname(__file__), 'charts', 'scraper', 'gtowizard-mtt', 'out')

# Кэш для загруженных чартов
charts_cache = {}

def load_chart(stack, position, scenario):
    """Загружает JSON-чарт для конкретного стека, позиции и сценария."""
    # Пример пути: charts/scraper/gtowizard-mtt/out/100bb/rfi/BTN.json
    path = os.path.join(CHARTS_DIR, f"{stack}bb", scenario, f"{position}.json")
    if path in charts_cache:
        return charts_cache[path]
    
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
            charts_cache[path] = data
            return data
    return None

def get_my_position(data):
    """Определяет позицию 'me' относительно BB."""
    SEAT_ORDER = ['p1', 'p2', 'p3', 'p4', 'p5', 'me', 'p6', 'p7', 'p8']
    bb_seat = data.get('bbSeat')
    sb_seat = data.get('sbSeat')
    active_seats = data.get('stacks', {})
    
    active_in_order = [s for s in SEAT_ORDER if s in active_seats]
    
    if 'me' not in active_in_order or bb_seat not in active_in_order:
        return "UNKNOWN"
    
    me_idx = active_in_order.index('me')
    bb_idx = active_in_order.index(bb_seat)
    sb_idx = active_in_order.index(sb_seat) if sb_seat in active_in_order else (bb_idx - 1) % len(active_in_order)
    btn_idx = (sb_idx - 1) % len(active_in_order)
    
    if me_idx == bb_idx: return "BB"
    elif me_idx == sb_idx: return "SB"
    elif me_idx == btn_idx: return "BTN"
    else:
        distance = (btn_idx - me_idx) % len(active_in_order)
        if distance == 1: return "CO"
        elif distance == 2: return "MP"
        else: return "UTG"

def get_my_stack(data):
    """Возвращает стек 'me' в виде числа (например, '100bb' -> 100)."""
    stacks = data.get('stacks', {})
    me_stack = stacks.get('me', '100')
    if isinstance(me_stack, str) and 'bb' in me_stack:
        try:
            return int(me_stack.replace('bb', ''))
        except:
            return 100
    return 100

def get_scenario(data):
    """Определяет сценарий: rfi (открытие), vs_rfi (против рейза), vs_3b и т.д."""
    to_call = data.get('toCall', 0)
    if to_call > 0:
        # Если перед нами была ставка, это защита (vs_rfi или vs_3b и т.д.)
        # Упрощенно считаем, что это vs_rfi
        return "vs_rfi"
    else:
        # Если ставок нет, это открытие (rfi)
        return "rfi"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/advice', methods=['POST'])
def get_advice():
    data = request.json
    my_cards = data.get('myCards', [])
    
    if not my_cards or '?' in my_cards or len(my_cards) < 2:
        return jsonify({"action": "ОШИБКА", "reason": "Введите свои карты."})

    # Парсим карты в строку вида "AKs" или "T9o"
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
        
        if is_pair:
            hand_str = high_rank + low_rank
        elif is_suited:
            hand_str = high_rank + low_rank + "s"
        else:
            hand_str = high_rank + low_rank + "o"
    except Exception as e:
        return jsonify({"action": "ОШИБКА", "reason": f"Не удалось распознать карты: {my_cards}"})

    # Определяем контекст
    position = get_my_position(data)
    stack = get_my_stack(data)
    scenario = get_scenario(data)
    
    # Пытаемся найти стек, кратный 10 (100, 90, 80...). Если нет, берем ближайший.
    # В репозитории есть стеки: 10bb, 11bb, 12bb, ..., 100bb, 130bb, 160bb и т.д.
    # Для простоты округлим до ближайшего доступного.
    available_stacks = [10, 11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 130, 160]
    closest_stack = min(available_stacks, key=lambda x: abs(x - stack))
    
    # Загружаем чарт
    chart_data = load_chart(closest_stack, position, scenario)
    
    if chart_data is None:
        # Если чарт не найден, используем упрощенную логику
        if hand_str in ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]:
            return jsonify({"action": "RAISE", "reason": f"У вас {hand_str} — премиум-рука. Делайте рейз."})
        elif scenario == "vs_rfi":
            return jsonify({"action": "FOLD", "reason": f"У вас {hand_str}. Чарт для {position} (стек {closest_stack}bb) не найден, но против рейза эта рука слабая."})
        else:
            return jsonify({"action": "CHECK", "reason": f"У вас {hand_str}. Чарт не найден, играем осторожно."})

    # Ищем нашу руку в чарте
    # Формат чарта: {"AA": {"raise": 1.0, "call": 0.0}, "AKs": {"raise": 0.5, "call": 0.5}, ...}
    hand_data = chart_data.get(hand_str)
    
    if hand_data:
        # Выбираем действие с наибольшей частотой
        action = max(hand_data, key=hand_data.get)
        frequency = hand_data[action]
        if action == "raise":
            return jsonify({"action": "RAISE", "reason": f"Позиция: {position}. Стек: {closest_stack}bb. У вас {hand_str}. Чарт рекомендует рейз (частота {frequency*100:.0f}%)."})
        elif action == "call":
            return jsonify({"action": "CALL", "reason": f"Позиция: {position}. Стек: {closest_stack}bb. У вас {hand_str}. Чарт рекомендует колл (частота {frequency*100:.0f}%)."})
        else:
            return jsonify({"action": "FOLD", "reason": f"Позиция: {position}. Стек: {closest_stack}bb. У вас {hand_str}. Чарт рекомендует фолд."})
    else:
        return jsonify({"action": "FOLD", "reason": f"Позиция: {position}. Стек: {closest_stack}bb. Руки {hand_str} нет в диапазоне. Фолд."})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8091)
