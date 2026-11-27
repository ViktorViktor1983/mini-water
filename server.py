import os
import json
import glob
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'charts', 'scraper', 'gtowizard-mtt', 'out')
charts_cache = {}

def get_my_position(data):
    SEAT_ORDER = ['p1', 'p2', 'p3', 'p4', 'p5', 'me', 'p6', 'p7', 'p8']
    bb_seat = data.get('bbSeat')
    sb_seat = data.get('sbSeat')
    active_seats = data.get('stacks', {})
    active_in_order = [s for s in SEAT_ORDER if s in active_seats]
    
    if 'me' not in active_in_order or bb_seat not in active_in_order:
        return "btn" 
    
    me_idx = active_in_order.index('me')
    bb_idx = active_in_order.index(bb_seat)
    sb_idx = active_in_order.index(sb_seat) if sb_seat in active_in_order else (bb_idx - 1) % len(active_in_order)
    btn_idx = (sb_idx - 1) % len(active_in_order)
    
    if me_idx == bb_idx: return "bb"
    elif me_idx == sb_idx: return "sb"
    elif me_idx == btn_idx: return "btn"
    else:
        distance = (btn_idx - me_idx) % len(active_in_order)
        if distance == 1: return "co"
        elif distance == 2: return "hj"
        elif distance == 3: return "lj"
        elif distance == 4: return "utg1"
        else: return "utg"

def get_stack_bb(data):
    stacks = data.get('stacks', {})
    me_stack = stacks.get('me', '100')
    
    if '-' in str(me_stack):
        parts = str(me_stack).split('-')
        try: return int((int(parts[0]) + int(parts[1])) / 2)
        except: return 20
    elif '+' in str(me_stack):
        return 100
    else:
        try: return int(float(me_stack))
        except: return 100

def find_chart_file(stack_bb, scenario, position):
    available_dirs = glob.glob(os.path.join(CHARTS_DIR, '*bb'))
    available_stacks = []
    for d in available_dirs:
        try: available_stacks.append(int(os.path.basename(d).replace('bb', '')))
        except: pass
    
    if not available_stacks: return None
        
    closest_stack = min(available_stacks, key=lambda x: abs(x - stack_bb))
    stack_dir = os.path.join(CHARTS_DIR, f"{closest_stack}bb")
    scenario_dir = os.path.join(stack_dir, scenario)
    
    if not os.path.exists(scenario_dir): return None
        
    file_path = None
    if scenario == 'rfi':
        file_path = os.path.join(scenario_dir, f"rfi_{position}.json")
    else:
        # Ищем файл, который начинается с нашей позиции во всех папках (например btn_vs_co.json)
        search_pattern = os.path.join(scenario_dir, '*', f"{position}_vs_*.json")
        files = glob.glob(search_pattern)
        if files: file_path = files[0]

    if not file_path or not os.path.exists(file_path):
        return None
        
    if file_path in charts_cache:
        return charts_cache[file_path]
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        charts_cache[file_path] = data
        return data

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
    to_call = data.get('toCall', 0)
    
    if not my_cards or '?' in my_cards or len(my_cards) < 2:
        return jsonify({"action": "ОШИБКА", "reason": "Введите свои карты."})

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
        
        if is_pair: hand_str = high_rank + low_rank
        elif is_suited: hand_str = high_rank + low_rank + "s"
        else: hand_str = high_rank + low_rank + "o"
    except Exception as e:
        return jsonify({"action": "ОШИБКА", "reason": "Ошибка распознавания карт."})

    position = get_my_position(data)
    stack_bb = get_stack_bb(data)
    
    if to_call > 0:
        scenario = "vs_rfi" 
    else:
        scenario = "rfi"
        
    chart_data = find_chart_file(stack_bb, scenario, position)
    
    if not chart_data:
        return jsonify({
            "action": "ОШИБКА", 
            "reason": f"Файл чарта не найден по пути: {scenario}/{position} для стека {stack_bb}bb."
        })

    processed = chart_data.get('processed', {})
    raise_data = processed.get('raise', {})
    call_data = processed.get('call', {})
    
    def get_freq(data_dict, hand):
        if hand in data_dict and isinstance(data_dict[hand], (int, float)):
            return data_dict[hand]
        for k, v in data_dict.items():
            if isinstance(v, dict) and hand in v:
                return v[hand]
        return 0.0

    raise_freq = get_freq(raise_data, hand_str)
    call_freq = get_freq(call_data, hand_str)

    if raise_freq > 0.5:
        return jsonify({"action": "RAISE", "reason": f"Позиция: {position.upper()}. Стек: {stack_bb}bb. У вас {hand_str}. GTO-чарт рекомендует рейз ({raise_freq*100:.0f}%)."})
    elif call_freq > 0.5:
        return jsonify({"action": "CALL", "reason": f"Позиция: {position.upper()}. Стек: {stack_bb}bb. У вас {hand_str}. GTO-чарт рекомендует колл ({call_freq*100:.0f}%)."})
    elif raise_freq > 0.1 or call_freq > 0.1:
        if raise_freq > call_freq:
             return jsonify({"action": "RAISE", "reason": f"Позиция: {position.upper()}. Стек: {stack_bb}bb. Рука {hand_str} играется смешанно, рейз чаще ({raise_freq*100:.0f}%)."})
        else:
             return jsonify({"action": "CALL", "reason": f"Позиция: {position.upper()}. Стек: {stack_bb}bb. Рука {hand_str} играется смешанно, колл чаще ({call_freq*100:.0f}%)."})
    else:
        return jsonify({"action": "FOLD", "reason": f"Позиция: {position.upper()}. Стек: {stack_bb}bb. Руки {hand_str} нет в диапазоне. GTO-чарт рекомендует фолд."})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8091)
