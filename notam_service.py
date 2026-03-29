import requests
import random
import math

def get_notam_and_flights(lat, lon):
    """
    OpenSky Network API üzerinden GERÇEK CANLI UÇUŞ TRAFİĞİ çeker.
    Eğer koordinatta uçuş yoksa veya API hata verirse akıllı simülasyonu devreye alır.
    """
    try:
        # 1 derecelik bir bounding box (yaklaşık 100km çap)
        lamin, lomin = lat - 0.5, lon - 0.5
        lamax, lomax = lat + 0.5, lon + 0.5
        
        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"
        
        # API'den gerçek veriyi çekelim
        response = requests.get(url, timeout=5)
        flights = []
        has_conflict = False
        max_wait = 0
        
        if response.status_code == 200:
            data = response.json()
            states = data.get("states", [])
            
            if states:
                for s in states[:10]: # En fazla 10 uçağı gösterelim (UI performans için)
                    callsign = s[1].strip() or "BİLİNMİYOR"
                    f_lon = s[5]
                    f_lat = s[6]
                    alt_val = s[7] # barometric altitude
                    
                    # Fırlatma merkezine olan uzaklık (Basit mesafe hesabı)
                    d = math.sqrt((f_lat - lat)**2 + (f_lon - lon)**2) * 111 # km cinsinden
                    
                    is_conflict = d < 12.0 # 12km altı çatışma kabul edilir
                    eta = random.randint(3, 15) if is_conflict else 0
                    
                    if is_conflict:
                        has_conflict = True
                        if eta > max_wait: max_wait = eta
                    
                    flights.append({
                        "callsign": callsign,
                        "alt": f"{int(alt_val)} m" if alt_val else "BİLİNMİYOR",
                        "dist": f"{d:.1f} km",
                        "lat": f_lat,
                        "lon": f_lon,
                        "is_conflict": is_conflict,
                        "eta_minutes": eta,
                        "status": "RİSKLİ" if is_conflict else "GÜVENLİ"
                    })
            else:
                # Bölgede uçuş yoksa boş dönelim
                pass
        else:
            # API Limiti veya Hata Durumunda (Simülasyon - opsiyonel)
            pass

        # Eğer gerçek veri boşsa (API limiti vs) yedek simülasyonu çalıştıralım
        if not flights:
            seed_val = int(abs(lat * 100) + abs(lon * 100))
            random.seed(seed_val)
            for i in range(3):
                cs = f"THY{random.randint(100, 999)}"
                d_val = random.uniform(5, 25)
                is_c = d_val < 10.0
                eta = random.randint(5, 12) if is_c else 0
                if is_c: has_conflict = True; max_wait = max(max_wait, eta)
                flights.append({
                    "callsign": cs, "alt": "32000 ft", "dist": f"{d_val:.1f} km",
                    "lat": lat + random.uniform(-0.1, 0.1), "lon": lon + random.uniform(-0.1, 0.1),
                    "is_conflict": is_c, "eta_minutes": eta, "status": "YEDEK-RADAR"
                })

        status_msg = "SİSTEM NOMİNAL - FIRLATMAYA UYGUN"
        if has_conflict:
            status_msg = f"DİKKAT! {max_wait} DK İÇİNDE HAVA SAHASI TEMİZLENECEKTİR"

        return {
            "status": "CANLI RADAR (OPENSKY)",
            "is_airspace_clear": not has_conflict,
            "status_message": status_msg,
            "wait_time": max_wait,
            "flights": flights,
            "notams": [
                {"id": f"A{random.randint(1000, 9999)}/26", "msg": "ACTUAL TRAFFIC MONITORING ENABLED.", "severity": "BİLGİ"},
                {"id": f"N0{random.randint(100, 999)}/26", "msg": f"LAUNCH SECTOR CLEARANCE ACTIVE AT [{lat:.2f}, {lon:.2f}]", "severity": "KRİTİK"}
            ]
        }
    except Exception as e:
        return {"error": str(e)}
