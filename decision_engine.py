import numpy as np

class TetraDecisionEngine:
    def __init__(self):
        # Ağırlık merkezleri (Taktiksel Öncelikler)
        self.weights = {
            "wind": -2.5,          # Rüzgar hızı (m/s) her bir birim için -2.5 puan
            "visibility": 1.5,      # Görüş mesafesi (km) her bir birim için +1.5 puan
            "humidity": -0.5,      # Nem (%) her bir birim için -0.5 puan
            "temp_range": (10, 35), # İdeal sıcaklık aralığı (C)
            "kp_index": -12.0,     # Manyetik fırtına etkisi
            "topo_base": 0.6       # Topografik uygunluğun %60 etkisi
        }

    def calculate_score(self, weather, topo, space, rocket):
        """
        Gemini/Ollama kullanmadan, tamamen matematiksel/taktiksel 
        TetraTech özel karar motoru.
        """
        score = 100.0
        risks = []

        # 1. HAVA DURUMU ANALİZİ (WEATHER)
        wind_speed = float(weather.get('wind', 0))
        visibility = float(weather.get('visibility', 10))
        humidity = float(weather.get('humidity', 50))
        temp = float(weather.get('temp', 20))
        desc = weather.get('desc', '').upper()

        # Rüzgar Toleransı (Rokete göre dinamik)
        rocket_tol = rocket.get('tol', 15)
        if wind_speed > rocket_tol:
            penalty = (wind_speed - rocket_tol) * 8.0 # Tolerans sonrası sert düşüş
            score -= penalty
            risks.append({"type": "Meteorolojik İhlal", "level": "KRİTİK" if penalty > 40 else "YÜKSEK", "msg": f"Rüzgar hızı ({wind_speed} m/s) araç limitini ({rocket_tol} m/s) aşıyor."})
        elif wind_speed > rocket_tol * 0.7:
            score -= 10
            risks.append({"type": "Hava Muhalefeti", "level": "DİKKAT", "msg": "Yüksek irtifa rüzgar makaslaması riski mevcut."})

        # Görüş ve Nem
        if visibility < 2.0:
            score -= 25
            risks.append({"type": "Görüş Kısıtı", "level": "YÜKSEK", "msg": "Düşük görüş mesafesi (VFR limit dışı)."})
        
        if humidity > 85:
            score -= 15
            risks.append({"type": "Atmosferik Nem", "level": "ORTA", "msg": "Korozyon ve sensör buğulanma riski."})

        # Ekstrem Hava (Fırtına, Kar, Yağmur)
        dangerous_conds = ["FIRTINA", "KAR", "SAĞANAK", "YARK", "DOĞU"]
        for cond in dangerous_conds:
            if cond in desc:
                score -= 40
                risks.append({"type": "Ekstrem Hava", "level": "KRİTİK", "msg": f"Tehlikeli hava olayı tespit edildi: {desc}"})

        # 2. TOPOGRAFİK ANALİZ (TOPO)
        topo_score = float(topo.get('score', 100))
        # Topo skoru 100 üzerinden gelir, bunu total skora yedirelim
        score = (score * 0.4) + (topo_score * 0.6) # Ağırlığı araziye veriyoruz (Kullanıcı isteği)

        # 3. UZAY HAVASI (SPACE)
        kp = float(space.get('kp_index', 0))
        if kp >= 5:
            penalty = (kp - 4) * 15.0
            score -= penalty
            risks.append({"type": "Jeomanyetik Risk", "level": "KRİTİK" if kp >= 7 else "YÜKSEK", "msg": f"Manyetik fırtına (Kp {kp}) aviyonik sistemleri tehdit ediyor."})

        # Final Karar Mekanizması
        score = max(0, min(100, score))
        
        status = "UYGUN"
        decision = "GÖREV ONAYLANDI"
        if score < 45:
            status = "İPTAL"
            decision = "GÖREV İPTAL (RED)"
        elif score < 75:
            status = "BEKLEME"
            decision = "GÖREV ERTELENDİ (İZLEME)"

        return {
            "score": int(score),
            "status": status,
            "decision": decision,
            "risks": risks
        }

engine = TetraDecisionEngine()
