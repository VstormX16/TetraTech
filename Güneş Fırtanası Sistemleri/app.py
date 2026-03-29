from flask import Flask, render_template, jsonify, request
import sys
import os
import threading
import time
import requests
import datetime
import copy

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.risk_assessor import load_or_train_model, SolarRiskAssessor
from data.nasa_api import fetch_all_solar_data

app = Flask(__name__)

model = None
assessor = None
cached_solar_data = None
last_fetch_time = 0

def init_ai():
    global model, assessor
    if model is None:
         model = load_or_train_model(retrain=False, verbose=False)
         assessor = SolarRiskAssessor(model)

def get_solar_data():
    global cached_solar_data, last_fetch_time
    if cached_solar_data is None or time.time() - last_fetch_time > 300:
        cached_solar_data = fetch_all_solar_data(verbose=False)
        last_fetch_time = time.time()
    return cached_solar_data

def find_next_window(assessor, solar_data, lat, lon):
    current_hour = datetime.datetime.utcnow().hour
    best_offset = None
    
    # 72 saat ileriye (her saat dilimi için) simüle edelim
    # Güneş fırtınalarının etkisini simüle ederek lineer olarak azaldığını varsayalım
    sim_data = copy.deepcopy(solar_data)
    
    for offset in range(1, 73):
        h = (current_hour + offset) % 24
        
        # Etkileri yumuşatalım (zamanla uzay havası durulur)
        if sim_data.get('bz_component', 0) < 0:
            sim_data['bz_component'] *= 0.9  # 0'a yaklaşır
        if sim_data.get('solar_wind_speed', 0) > 400:
            sim_data['solar_wind_speed'] = max(400, sim_data['solar_wind_speed'] * 0.95)
        if sim_data.get('kp_index', 0) > 2:
            sim_data['kp_index'] = max(2, sim_data['kp_index'] * 0.9)
            
        # Simüle edilmiş değerlendirme
        res = assessor.assess(sim_data, lat, lon, utc_hour=h)
        if res['risk_level'] <= 1:
            best_offset = offset
            break
            
    if best_offset:
        target_time = datetime.datetime.now() + datetime.timedelta(hours=best_offset)
        return {"hours": best_offset, "time_str": target_time.strftime("%d %b %H:00")}
    return None

def generate_ai_comment(assessment, next_window, city_name):
    # Temel durum yorumu
    risk = assessment['risk_level']
    if risk == 0:
        return f"Hedef: {city_name}. Yörünge telemetrileri ve güneş rüzgârı tertemiz. Bütün sistemler YEŞİL. Fırlatmaya izin verildi."
    elif risk == 1:
        return f"Hedef: {city_name}. Atmosferin üst tabakalarında hafif dalgalanmalar var ama engel değil. Dikkatli şekilde fırlatma yapılabilir (SARI DURUM)."
    elif risk == 2:
        return f"Hedef: {city_name}. DİKKAT! Güneş aktivitesi fırlatma sahasının o anki konumuna göre çok tehlikeli seviyede (KIRMIZI DURUM). Kalkanlarda yırtılma ve iletişim kaybı riski yüksek. Fırlatma ERTELENMELİDİR.\nÖnerilen ilk fırlatma penceresi: {next_window['time_str'] if next_window else 'Bilinmiyor'} ({next_window['hours']} st sonra)."
    else:
        return f"Hedef: {city_name}. ŞİDDETLİ UZAY HAVA KOŞULLARI TESPİT EDİLDİ (KRİTİK DURUM). Patlamadan yayılan yüklü parçacıklar şu an tam bu bölgeye vuruyor. Elektronikler anında yanar. KESİNLİKLE FIRLATMAYIN.\nÖnerilen ilk güvenli fırlatma penceresi: {next_window['time_str'] if next_window else 'Bekleniyor'} ({next_window['hours']} st sonra)."


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/evaluate_city', methods=['POST'])
def eval_city():
    init_ai()
    solar = get_solar_data()
    req = request.get_json()
    city_name = req.get('city', 'Istanbul')
    
    # Geocoding via static map or nominatim
    headers = {'User-Agent': 'NasaSolarWeatherApp/2.0'}
    try:
        geo_resp = requests.get(f'https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1', headers=headers).json()
        if not geo_resp:
            return jsonify({'error': f"'{city_name}' koordinatları bulunamadı."}), 404
        lat = float(geo_resp[0]['lat'])
        lon = float(geo_resp[0]['lon'])
        display_name = geo_resp[0]['display_name'].split(',')[0]
    except Exception as e:
        return jsonify({'error': "Harita servisi çalışmıyor, tekrar deneyin."}), 500

    assessment = assessor.assess(solar, lat, lon)
    
    next_window = None
    if assessment['risk_level'] > 1:
        next_window = find_next_window(assessor, solar, lat, lon)
        
    ai_comment = generate_ai_comment(assessment, next_window, display_name)

    return jsonify({
        'id': 'custom',
        'name': display_name.upper() + ' BASE',
        'lat': round(lat, 2),
        'lon': round(lon, 2),
        'assessment': assessment,
        'ai_comment': ai_comment,
        'next_window': next_window
    })

@app.route('/api/status')
def status():
    init_ai()
    solar = get_solar_data()
    
    locations = [
        {'id': 'istanbul', 'name': 'İstanbul Mission Control', 'lat': 41.0, 'lon': 28.9},
        {'id': 'kennedy', 'name': 'Kennedy Space Center', 'lat': 28.5, 'lon': -80.6},
        {'id': 'vandenberg', 'name': 'Vandenberg SFB', 'lat': 34.7, 'lon': -120.5}
    ]
    
    results = {}
    for loc in locations:
        res = assessor.assess(solar, loc['lat'], loc['lon'])
        
        n_win = None
        if res['risk_level'] > 1:
             n_win = find_next_window(assessor, solar, loc['lat'], loc['lon'])
        comment = generate_ai_comment(res, n_win, loc['name'].split()[0])
        
        results[loc['id']] = {
            'name': loc['name'],
            'lat': loc['lat'],
            'lon': loc['lon'],
            'assessment': res,
            'ai_comment': comment,
            'next_window': n_win
        }
    
    return jsonify({
        'solar_data': solar,
        'predictions': results
    })

if __name__ == '__main__':
    threading.Thread(target=init_ai).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
