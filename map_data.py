import requests

def get_topo_data(lat=40.2, lon=29.0):
    import requests
    # ELEVASYON (RAKIM) / DAGLIK ALAN KONTROLU
    elevation_m = 0
    terrain_desc = "Arazi Ölçümü Hesaplanıyor..."
    try:
        elev_url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        elev_resp = requests.get(elev_url, timeout=5)
        if elev_resp.status_code == 200:
            elev_data = elev_resp.json()
            if "elevation" in elev_data and elev_data["elevation"]:
                elevation_m = int(elev_data["elevation"][0])
    except:
        elevation_m = 0

    # HASSAS TARAMA MANTIĞI (Nokta atışı için daraltıldı: ~3-5km)
    offset_lat = 0.025   
    offset_lon = 0.035   
    min_lat, max_lat = lat - offset_lat, lat + offset_lat
    min_lon, max_lon = lon - offset_lon, lon + offset_lon

    # Yedek sunucu listesi (Hızlı Mirror Sistemi)
    overpass_mirrors = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter"
    ]
    
    # ESKİ SORGUNUN GÜCÜ (Place temelli)
    overpass_query = f"""
    [out:json][timeout:15];
    (
      node["natural"="peak"]({min_lat}, {min_lon}, {max_lat}, {max_lon});
      node["man_made"="communications_tower"]({min_lat}, {min_lon}, {max_lat}, {max_lon});
      node["place"~"city|town|village|suburb|quarter|borough"]({min_lat}, {min_lon}, {max_lat}, {max_lon});
      way["landuse"~"industrial|commercial"]({min_lat}, {min_lon}, {max_lat}, {max_lon});
      way["aeroway"="aerodrome"]({min_lat}, {min_lon}, {max_lat}, {max_lon});
      way["highway"~"motorway|trunk"]({min_lat}, {min_lon}, {max_lat}, {max_lon});
    );
    out center;
    """

    success = False
    data = {"elements": []}
    for mirror in overpass_mirrors:
        try:
            headers = {'User-Agent': 'TetraTechNode/3.0'}
            response = requests.get(mirror, params={'data': overpass_query}, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                success = True
                break
        except:
            continue
            
    if not success:
        return {
            "peaks": "-", "towers": "-", "residential": "X",
            "score": "0", "acoustic_risk": "UYDU SUNUCUSU ZAMAN ASIMI",
            "civ_risk": "OVERPASS API DEVRE DISI - FAILSAFE",
            "airspace_risk": "BILINMEYEN", "logistics": "BILINMEYEN", "water_safety": "BILINMEYEN",
            "terrain_info": "HATALI VERI ZINCIRI",
            "names": ["Ag Baglantisi Yok - Analiz İptal Edildi (Red)"], "hazards": [],
            "suitability": "HATA: HARITA YUKLENEMEDI",
            "target_lat": str(lat), "target_lon": str(lon)
        }
        
    # SU ÜZERİ KORUMA KATMANI (Deniz ortamında sivil veri taramasını kesin olarak engelle)
    elements = data.get("elements", [])
    if elevation_m <= 0:
        elements = [] # Denizdeyken her şeyi temizle
    
    peaks, towers, airports, roads, water_bodies = 0, 0, 0, 0, 0
    metropolis_count = 0
    village_count = 0
    industrial_count = 0
    names = []
    hazards = []
    res_markers = 0 
    ind_markers = 0
    
    for el in elements:
        tags = el.get("tags", {})
        has_name = "name" in tags
        name = tags.get("name", "Bilinmeyen")
        
        item_lat = el.get("lat")
        item_lon = el.get("lon")
        if not item_lat and "center" in el:
            item_lat = el["center"].get("lat")
            item_lon = el["center"].get("lon")
            
        def add_hazard(htype, label_suffix):
            if item_lat and item_lon:
                hazards.append({
                    "name": f"{name} ({label_suffix})",
                    "type": htype,
                    "lat": item_lat,
                    "lon": item_lon
                })
            else:
                 names.append(f"{name} ({label_suffix})")
        
        if tags.get("natural") == "peak":
            peaks += 1
            if has_name and peaks <= 5: add_hazard("peak", "Zirve")
        elif tags.get("man_made") == "communications_tower":
            towers += 1
            if has_name and towers <= 3: add_hazard("tower", "Kule")
        elif tags.get("place") in ["city", "town", "village", "suburb", "quarter", "borough"]:
            p = tags.get("place")
            if p in ["city", "town", "borough"]:
                metropolis_count += 1 
            else:
                village_count += 1
                
            if has_name and res_markers < 2:
                add_hazard("residential", "Sivil Yerlesim Odagi")
                res_markers += 1
                
        elif tags.get("aeroway") == "aerodrome":
            airports += 1
            if has_name: add_hazard("airport", "Havalimani Rota")
        elif tags.get("landuse") in ["industrial", "commercial"]:
            industrial_count += 1
            if ind_markers < 3:
                add_hazard("industrial", "Sanayi/Lojistik Bölgesi")
                ind_markers += 1
        elif tags.get("highway") in ["motorway", "trunk"]:
            roads += 1
    
    score = 100
    ses_soku_riski = "MİNİMAL: Yerleşim Alanı Saptanmadı"
    sivil_guvenlik = "HEDEF SEKTÖR SİVİL YAŞAMDAN ARINDIRILMIŞ"
    lojistik_kapasite = "BİLİNMİYOR: Veri Yetersiz"
    hava_sahasi_riski = "KORİDOR TEMİZ: OPERASYONEL HAVA SAHASI"
    
    # Yerleşim Özeti Formatlama
    residential_total_formatted = f"[Şehirleşme: {metropolis_count} | Kırsal: {village_count}]" if elevation_m > 0 else "[SU KÜTLESİ]"
    
    if metropolis_count >= 1:
        score -= 85 
        ses_soku_riski = "KRİTİK: Metropol Yapıların Tahribat Riski"
        sivil_guvenlik = "YÜKSEK İHLAL: Şehir Merkezi / Yerleşim Odağı"
    elif village_count >= 10:
        score -= 40
        ses_soku_riski = "YÜKSEK: Yoğun Kırsal Yerleşim Ağı"
        sivil_guvenlik = "ORTA RİSK: Çok Sayıda Köy Yerleşimi"
    elif village_count >= 1:
        # Birkaç ev operasyona engel değil, sadece uyarı verilir
        score -= 5
        ses_soku_riski = "MİNİMAL: Seyrek Köy Evleri"
        sivil_guvenlik = "DÜŞÜK RİSK: Münferit Yerleşim Tespiti (Operasyonel Engel Değil)"
    
    if industrial_count > 0:
        # Sanayi bölgeleri lojistik artıdır
        score -= 5
        sivil_guvenlik = f"TAKTİK AVANTAJ: {industrial_count} Sanayi/İş Odak Noktası"
        if metropolis_count == 0 and village_count < 5:
            score += 15
            lojistik_kapasite = "YÜKSEK: Mevcut Sanayi Altyapısı"
            lojistik_kapasite = "YÜKSEK: Sanayi Altyapısı Mevcut"
        
    if airports > 0:
        score -= 50
        hava_sahasi_riski = f"KORİDOR KESİŞİMİ ({airports} Sivil Rota Tespiti)"
    else:
        hava_sahasi_riski = "KORİDOR TEMİZ: OPERASYONEL HAVA SAHASI"
        
    # ELEVATION SCORING & LOGISTICS (YENI: PLATO VS ZIRVE AYRIMI)
    is_mountainous = peaks > 0
    
    if elevation_m >= 1500:
        if is_mountainous:
            terrain_desc = f"{elevation_m} Metre Rakım (Aşırı Dağlık Zirve)"
            score -= 60
            lojistik_kapasite = "ERİŞİLEMEZ: Sarp Dağ Zirvesi / Ağır Arazi"
            uygunluk = "TEKNİK RED: OPERASYONA ELVERİŞSİZ ARAZİ"
        else:
            terrain_desc = f"{elevation_m} Metre (Yüksek Rakımlı Plato / Ova)"
            score += 20 # YUKSEK RAKIM + DUZ ARAZI = YAKIT TASARRUFU (AVANTAJ)
            lojistik_kapasite = "STRATEJİK: Yüksek İrtifa / Düz Plato"
            
    elif elevation_m >= 600:
        if is_mountainous:
            terrain_desc = f"{elevation_m} Metre (Engebeli / Dağlık Yüzey)"
            score -= 25
            lojistik_kapasite = "ZORLU: Engebeli Arazi / Sınırlı Erişim"
        else:
            terrain_desc = f"{elevation_m} Metre (Orta İrtifa Taktik Plato)"
            score += 15
            lojistik_kapasite = "UYGUN: Operasyonel Rakım Avantajı"
            
    elif elevation_m > 0:
        terrain_desc = f"{elevation_m} Metre (Düz Ova / Standart Rakım)"
        score += 5
        lojistik_kapasite = "STANDART: Düz Arazi / Optimal Lojistik"
    else:
        # SU ÜZERİ VEYA OKYANUS TESPİTİ (KRİTİK ENGEL)
        terrain_desc = f"{elevation_m} Metre (SU KÜTLESİ / OKYANUS)"
        score = 0  # Su üzerinde fırlatma veya inşaat yapılamaz
        lojistik_kapasite = "İMKANSIZ: Su Yüzeyi Analiz Edildi"
        uygunluk = "TEKNİK RED: SU ÜSTÜ OPERASYONU İMKANSIZ"
        sivil_guvenlik = "İHLAL: TAŞIYICI PLATFORM EKSİKLİĞİ (SU)"
        ses_soku_riski = "GEÇERSİZ: AKUSTİK ANALİZ İPTAL"
        
    if peaks > 0: score -= min(20, peaks * 5)
    if towers > 0: score -= min(15, towers * 5)
        
    water_safety = "Veri Yuklenemedi (Sabitlendi)"

    score = max(0, min(100, score))
    
    if score >= 85:
        uygunluk = "STRATEJİK: YÜKSEK GÜVENLİKLİ OPERASYON SAHASI"
    elif score >= 60:
        uygunluk = "TAKTİK: İKİNCİL DESTEK BÖLGESİ (DÜŞÜK RİSK)"
    elif score >= 35:
        uygunluk = "KISITLI EVEKÜASYON: SİVİL ENGEL YOĞUNLUĞU"
    elif metropolis_count >= 1:
        uygunluk = "KRİTİK İHLAL: METROPOL YERLEŞİM MERKEZİ"
    elif elevation_m >= 1500:
        uygunluk = "TEKNİK RED: OPERASYONA ELVERİŞSİZ ARAZİ"
    else:
         uygunluk = "GÜVENLİ DEĞİL: YÜKSEK RİSKLİ SEKTÖR"

    for h in hazards:
        names.append(h["name"])

    return {
        "peaks": str(peaks),
        "towers": str(towers),
        "residential": residential_total_formatted,
        "score": str(score),
        "terrain_info": terrain_desc,
        "acoustic_risk": ses_soku_riski,
        "civ_risk": sivil_guvenlik,
        "industrial": str(industrial_count),
        "airspace_risk": hava_sahasi_riski,
        "logistics": lojistik_kapasite,
        "water_safety": "Taranmadı",
        "names": names[:12], 
        "hazards": hazards, 
        "suitability": uygunluk,
        "target_lat": str(lat),
        "target_lon": str(lon)
    }

if __name__ == "__main__":
    print(get_topo_data())
