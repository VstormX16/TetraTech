import requests
import datetime
import time

# PRD Endpoints
KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
FLARE_URL = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json"
ALERTS_URL = "https://services.swpc.noaa.gov/products/alerts.json"

_cached_data = None
_last_fetch = 0
CACHE_DURATION = 60 # 1 dakika cache (PRD: 1-5 dk guncelleme)
_prev_kp = 0.0
_history = []
MAX_HISTORY = 50

def parse_flare_class(flare_str):
    if not flare_str: return "A", 1.0
    if isinstance(flare_str, dict): flare_str = flare_str.get("max_class", "A1.0")
    flare_class = flare_str[0].upper()
    try:
        intensity = float(flare_str[1:])
    except:
        intensity = 1.0
    return flare_class, intensity

def fetch_noaa_data():
    data = {}
    try:
        kp_res = requests.get(KP_URL, timeout=5)
        if kp_res.status_code == 200:
            kp_data = kp_res.json()
            if kp_data:
                data['kp_index'] = float(kp_data[-1].get('kp_index', 0.0))
            else:
                data['kp_index'] = 0.0
    except:
        data['kp_index'] = 0.0

    try:
        flare_res = requests.get(FLARE_URL, timeout=5)
        if flare_res.status_code == 200:
            flare_data = flare_res.json()
            if flare_data:
                last_flare = flare_data[-1] if isinstance(flare_data, list) else flare_data
                data['flare'] = last_flare.get('max_class', last_flare.get('current_class', 'A1.0'))
            else:
                data['flare'] = "A1.0"
    except:
        data['flare'] = "A1.0"
        
    try:
        alerts_res = requests.get(ALERTS_URL, timeout=5)
        if alerts_res.status_code == 200:
            alerts_data = alerts_res.json()
            alerts_list = []
            for a in alerts_data[:5]:
                try:
                    msg = a.get('message', 'Uyarı')
                    if "WARNING" in msg or "ALERT" in msg:
                        alerts_list.append(msg)
                except:
                    pass
            data['alerts'] = alerts_list
    except:
        data['alerts'] = []
        
    return data

def get_space_weather_data(lat=40.18, lon=29.07):
    global _last_fetch, _cached_data, _prev_kp, _history
    
    now = time.time()
    if _cached_data and (now - _last_fetch) < CACHE_DURATION:
        raw_data = _cached_data
    else:
        raw_data = fetch_noaa_data()
        _cached_data = raw_data
        _last_fetch = now
        
    current_kp = float(raw_data.get('kp_index', 0.0))
    flare_str = raw_data.get('flare', 'A1.0')
    flare_class, flare_intensity = parse_flare_class(flare_str)
    
    # Risk Analizi (PRD)
    if current_kp >= 7 or flare_class == "X":
        risk_level = "HIGH"
    elif current_kp >= 5 or flare_class == "M":
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
        
    # Event Detection (PRD)
    event = "NOMINAL"
    if _prev_kp < 5.0 and current_kp >= 5.0:
        event = "STORM_START"
    elif _prev_kp >= 5.0 and current_kp < 5.0:
        event = "STORM_END"
    elif current_kp >= 7.0:
        event = "SEVERE_STORM"
    _prev_kp = current_kp
    
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    result = {
        "kp_index": current_kp,
        "solar_flare": flare_class,
        "flare_intensity": flare_intensity,
        "risk_level": risk_level,
        "event": event,
        "timestamp": timestamp,
        "active_alerts": raw_data.get('alerts', []),
        
        # Geriye dönük uyumluluk (Dashboard kırılmasın diye varsayılan veriler)
        "time_tag": timestamp,
        "mag_bz": "-2.1", 
        "g_scale": f"G{int(current_kp-4)}" if current_kp >= 5 else "Normal",
        "radio_scale": "Radyo Kesintisi Bekleniyor" if flare_class in ["M", "X"] else "İletişim Net",
        "alert": "KIRMIZI" if risk_level == "HIGH" else ("SARI" if risk_level == "MEDIUM" else "YEŞİL"),
        "ai_consensus": f"NOAA Doğrudan Veri Bağlantısı Aktif. Güncel Kp: {current_kp}",
        "cme_risk": "Yüksek" if risk_level == "HIGH" else "Düşük",
        "sw_speed": "450 km/s",
        "next_window": "GEREKLİ DEĞİL" if risk_level != "HIGH" else "48 Saat Sonra"
    }
    
    _history.append({
        "kp_index": current_kp,
        "solar_flare": flare_class + str(flare_intensity),
        "risk_level": risk_level,
        "timestamp": timestamp
    })
    
    if len(_history) > MAX_HISTORY:
        _history.pop(0)

    result["history"] = _history
    return result

if __name__ == "__main__":
    print(get_space_weather_data())
