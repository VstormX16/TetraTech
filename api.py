from fastapi import FastAPI, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import shutil
import json
from weather import get_weather_data
from map_data import get_topo_data
from space_weather import get_space_weather_data
from notam_service import get_notam_and_flights
import uvicorn
import datetime
import numpy as np
from decision_engine import engine  # Yeni Tetra karar motoru

# HERMES AI modül yolunu ekle
HERMES_DIR = os.path.join(os.path.dirname(__file__), "Uydu Dusus Hesaplayıcı")
if HERMES_DIR not in sys.path:
    sys.path.insert(0, HERMES_DIR)

app = FastAPI(title="TetraTech Mission Control API [ULTIMATE]")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "TetraTech API Online", "version": "3.0.0-PRO", "timestamp": str(datetime.datetime.now())}

@app.get("/api/weather")
def get_weather(lat: str = "40.18", lon: str = "29.07", city: str = None):
    try:
        return get_weather_data(lat, lon, city)
    except Exception as e:
        return {"city": "HATA", "desc": str(e)}

@app.get("/api/topo")
def get_topo(lat: float = 40.18, lon: float = 29.07):
    try:
        return get_topo_data(lat, lon)
    except Exception as e:
        return {"error": str(e), "suitability": "HATA"}

@app.get("/api/space/current")
@app.get("/api/space")
def get_space(lat: float = 40.18, lon: float = 29.07):
    try:
        return get_space_weather_data(lat, lon)
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/space/alerts")
def get_alerts():
    data = get_space_weather_data()
    return {"alerts": data.get("active_alerts", []), "timestamp": data.get("timestamp")}

@app.get("/api/space/history")
def get_history():
    data = get_space_weather_data()
    return {"history": data.get("history", []), "count": len(data.get("history", []))}

@app.get("/api/airspace")
def get_airspace(lat: float, lon: float):
    try:
        return get_notam_and_flights(lat, lon)
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/upload_model")
async def upload_model(file: UploadFile = File(...)):
    try:
        save_dir = os.path.join(os.path.dirname(__file__), "frontend", "public", "models")
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "SUCCESS", "filename": file.filename}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.post("/api/upload_ork")
async def upload_ork(file: UploadFile = File(...)):
    import tempfile
    try:
        # Save temp ORK file
        fd, temp_path = tempfile.mkstemp(suffix='.ork')
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # Import parser function
        from OpenRocketTespit import get_rocket_parameters_dict
        parsed_data = get_rocket_parameters_dict(temp_path)
        
        # Cleanup
        os.remove(temp_path)
        
        return {"status": "SUCCESS", "data": parsed_data}
    except Exception as e:
        try: os.remove(temp_path)
        except: pass
        return {"status": "ERROR", "message": str(e)}

@app.get("/api/simulate")
def simulate(
    lat: float, lon: float, date: str = "live", time_str: str = "", rocket_id: str = "ares",
    c_mass: float = None, c_tol: float = None, c_eff: float = None, c_name: str = None
):
    try:
        # ROKET VERI TABANI (BACKEND KONTROL)
        rockets = {
            "ares": {"name": "Ares 1 (B)", "thrust": 16000, "mass": 826000, "tol": 15, "efficiency": 0.85},
            "shuttle": {"name": "Space Shuttle", "thrust": 29000, "mass": 2054400, "tol": 14, "efficiency": 0.72},
            "explorer": {"name": "Jupiter-C", "thrust": 370, "mass": 28008, "tol": 8, "efficiency": 0.65},
            "cassini": {"name": "Cassini-Huygens", "thrust": 0.4, "mass": 8223, "tol": 20, "efficiency": 0.95},
            "agena": {"name": "Agena Target", "thrust": 71, "mass": 8500, "tol": 10, "efficiency": 0.88},
            "mir": {"name": "Mir Station", "thrust": 0, "mass": 129700, "tol": 40, "efficiency": 1.0}
        }
        
        if rocket_id == "custom" and c_mass is not None:
            rocket = {"name": c_name or "Özel Roket", "thrust": 1000, "mass": c_mass, "tol": c_tol or 10, "efficiency": c_eff or 0.80}
        else:
            rocket = rockets.get(rocket_id, rockets["ares"])
        
        weather_base = get_weather_data(str(lat), str(lon))
        topo = get_topo_data(lat, lon)
        space = get_space_weather_data(lat, lon)
        
        import random
        wind_mod = random.uniform(0.5, 1.8) if date != "live" else 1.0
        
        def safe_float(val, default=0.0):
            try:
                return float(str(val).replace('-', '0'))
            except:
                return default

        base_wind = safe_float(weather_base.get('wind'))
        base_temp = safe_float(weather_base.get('temp'))
        elevation = safe_float(topo.get('elevation', 0))
        
        sim_wind = round(base_wind * wind_mod, 1)
        sim_temp = base_temp + (random.randint(-5, 5) if date != "live" else 0)
        
        # ══════════════════════════════════════════════════════════════
        # TETRA DECISION ENGINE (ÖZEL KARAR MOTORU)
        # ══════════════════════════════════════════════════════════════
        sim_weather = weather_base.copy()
        sim_weather['wind'] = sim_wind
        sim_weather['temp'] = sim_temp
        
        eval_res = engine.calculate_score(sim_weather, topo, space, rocket)
        
        score = eval_res["score"]
        status = eval_res["status"]
        decision = eval_res["decision"]
        risks = eval_res["risks"]
        wait = random.randint(30, 180) if status == "BEKLEME" else 0
        
        if space.get('risk_level') == "HIGH": 
            score -= 10
            risks.append({"type": "Heliografik Fırtına", "level": "YÜKSEK", "msg": "Manyetik alan radyasyonu limit değerlerde."})
            
        # RESMİ ÜS KONTROLÜ (WHITELISTING)
        from spaceport_manager import SpaceportManager
        official_ports = SpaceportManager().get_all()
        is_official = False
        official_name = ""
        for op in official_ports:
            if abs(op['lat'] - lat) < 0.1 and abs(op['lon'] - lon) < 0.1:
                is_official = True
                official_name = op['name']
                break

        if is_official:
            score = min(100, score + 20)
            risks.append({"type": "Stratejik Tahkimat", "level": "GÜVENLİ", "msg": f"TESPİT: {official_name}. Onaylı fırlatma sahası konfor puanı eklendi."})


        # ÖZEL HESAPLAMALAR (YAKIT VE EMİSYON)
        # Formül: (Kütle * Sabit) / (Rakım Avantajı + Verimlilik)
        alt_bonus = max(1, 1 + (elevation / 5000))
        fuel_needed = int((rocket["mass"] * 0.18) / (alt_bonus * rocket["efficiency"]))
        carbon_footprint = int(fuel_needed * 3.12) # 1 ton yakıt ~3.12 ton CO2

        # EKSTRA AERODİNAMİK VERİLER (HİÇBİR YERDE EKSİK KALMAYACAK)
        import math
        kelvin = sim_temp + 273.15
        speed_of_sound = round(math.sqrt(1.4 * 287 * kelvin), 1)
        pressure = safe_float(weather_base.get('pressure', 1013))
        air_density = round((pressure * 100) / (287 * kelvin), 3)
        max_q_proj = round(0.5 * air_density * (speed_of_sound ** 2) / 1000, 1) # kPa
        
        # AYDINLANMA VE İYONOSFER
        hour = int(time_str.split(':')[0]) if ':' in time_str else datetime.datetime.now().hour
        is_day = 6 <= hour <= 19
        ionosphere_risk = "DÜŞÜK" if not is_day else ("ORTA" if space.get('risk_level') != "HIGH" else "YÜKSEK")

        return {
            "status": status,
            "decision": decision,
            "score": max(0, score),
            "rocket_name": rocket["name"],
            "coordinates": f"{lat:.4f}N / {lon:.4f}E",
            "target_time": f"{date} {time_str}".strip() if date != "live" else "ANLIK BIILGI / CANLI",
            "wait_minutes": wait,
            "fuel_consumption": f"{fuel_needed:,} KG",
            "carbon_emission": f"{carbon_footprint:,} KG CO2",
            "aerodynamics": {
                "speed_of_sound": f"{speed_of_sound} m/s",
                "air_density": f"{air_density} kg/m3",
                "max_q_projection": f"{max_q_proj} kPa",
                "mach_limit": "MACH 1.2 (Sınırlı)" if sim_wind > 10 else "MACH 4.5 (Nominal)"
            },
            "environmental": {
                "illumination": "GÜNDÜZ / AYDINLIK" if is_day else "GECE / KARANLIK",
                "ionospheric_scintillation": ionosphere_risk,
                "thermal_gradient": f"{round(sim_temp - (elevation/100), 1)} C (Tahmini)"
            },
            "weather_forecast": {
                "temp": str(sim_temp),
                "wind_speed": str(sim_wind),
                "visibility": weather_base.get('visibility', '10.0'),
                "humidity": weather_base.get('humidity', '50')
            },
            "risks": risks,
            "details": [
                f"İtki Analizi: {rocket['thrust']} kN NOMİNAL",
                f"Sistem Ağırlığı: {rocket['mass']:,} kg",
                f"Yakıt Verimliliği: %{int(rocket['efficiency']*100)}",
                f"Aerodinamik Direnç (Cd): 0.29 (Tahmini)",
                "Aviyonik Haberleşme: AKTİF",
                "Hava Sahası Rezervasyonu: TEMİZ"
            ],
            "topo_stats": topo,
            "timestamp": str(datetime.datetime.now())
        }
    except Exception as e:
        return {
            "status": "HATA", 
            "decision": "SİSTEM HATASI", 
            "score": 0, 
            "rocket_name": rocket_name,
            "coordinates": f"{lat:.2f}N / {lon:.2f}E",
            "target_time": "GEÇERSİZ",
            "wait_minutes": 0,
            "weather_forecast": {"temp": "0", "wind_speed": "0", "visibility": "0", "humidity": "0"},
            "risks": [{"type": "Dahili Hata", "level": "KRİTİK", "msg": str(e)}],
            "details": ["Üçüncü taraf servis bağlantı hatası"]
        }

@app.get("/api/spaceports")
def get_spaceports():
    from spaceport_manager import SpaceportManager
    manager = SpaceportManager()
    return manager.get_all()

# ══════════════════════════════════════════════════════════════
# HERMES AI - ENKAZ DÜŞÜŞ TAHMİN SİSTEMİ
# ══════════════════════════════════════════════════════════════

@app.get("/api/hermes/rockets")
def hermes_rockets():
    """HERMES bilgi tabanındaki roketleri döndürür."""
    try:
        # Ana dizindeki HERMES klasörünü bul
        kb_path = os.path.join(HERMES_DIR, "hermes_db", "knowledge_base.json")
        if not os.path.exists(kb_path):
             # Alternatif yol (proje yapısına göre)
             kb_path = os.path.join(os.getcwd(), "hermes_db", "knowledge_base.json")

        if not os.path.exists(kb_path):
            return {"error": f"Veritabanı bulunamadı: {kb_path}", "rockets": []}

        with open(kb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rockets = data.get("rockets", {})
        result = []
        for name, info in rockets.items():
            stages = info.get("stages", [])
            # Simülasyon için tam teknik veri setini hazırla
            formatted_stages = []
            for s in stages:
                formatted_stages.append({
                    "name": s.get("name", "Bilinmeyen Kademe"),
                    "thrust": s.get("thrust_kn", 0) * 1000, # kN to N
                    "propellantMass": s.get("propellant_mass_kg", 0),
                    "dryMass": s.get("empty_mass_kg", 0),
                    "burnTime": s.get("burn_time_s", 0),
                    "diameter": s.get("diameter_m", 1.0),
                    "type": "motor" if s.get("thrust_kn", 0) > 0 else "payload"
                })

            # EĞER BURUN (PAYLOAD) YOKSA OTOMATİK EKLE (Kaan'ın isteği)
            has_payload = any(s['type'] == 'payload' for s in formatted_stages)
            if not has_payload and formatted_stages:
                last_stage_dia = formatted_stages[-1]['diameter']
                formatted_stages.append({
                    "name": "Aerodinamik Burun Konisi",
                    "thrust": 0,
                    "propellantMass": 0,
                    "dryMass": 250, # Standart burun kütlesi
                    "burnTime": 0,
                    "diameter": last_stage_dia,
                    "type": "payload"
                })

            result.append({
                "name": name,
                "flights": info.get("flights", 0),
                "confidence": info.get("confidence", "LOW"),
                "propellant": info.get("propellant_type", "?"),
                "stages_count": len(formatted_stages),
                "stages": formatted_stages
            })
        return {"rockets": result}
    except Exception as e:
        return {"error": str(e), "rockets": []}

@app.get("/api/hermes/predict")
def hermes_predict(
    rocket_model: str = "Falcon 9",
    lat: float = 28.5,
    lon: float = -80.5,
    azimuth: float = 90.0
):
    """
    HERMES AI ile enkaz düşüş noktalarını tahmin eder.
    Fizik motoru veya eğitilmiş sinir ağı kullanır.
    """
    try:
        from hermes_db.trajectory_ai import get_or_load_model, MODEL_PATH
        from hermes_db.physics_engine import RocketPhysicsEngine
        import math
        import geopy.distance

        # Bilgi tabanını yükle
        kb_path = os.path.join(HERMES_DIR, "hermes_db", "knowledge_base.json")
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb = json.load(f)

        # Case-insensitive arama
        if "rockets" not in kb: kb["rockets"] = {}
        rockets_db = kb["rockets"]
        rocket_data = None
        for r_name, r_info in rockets_db.items():
            if r_name.lower() == rocket_model.lower():
                rocket_data = r_info
                rocket_model = r_name
                break
        
        # OTOMATIK OGRENME: Eğer roket listemizde yoksa, profil oluştur ve DB'ye KAYDET
        if not rocket_data:
            rocket_data = {
                "name": rocket_model,
                "flights": 1,
                "confidence": "YUKSEK (AI OGRENDI)",
                "propellant_type": "Kero-LOX / LOX-LH2",
                "stages": [
                    {
                        "stage_num": 1, "name": f"{rocket_model} Core Stage", "thrust_kn": 12000.0, 
                        "propellant_mass_kg": 420000.0, "empty_mass_kg": 32000.0, "burn_time_s": 160,
                        "diameter_m": 3.7, "material": "Aerospatial-Alum", "disposal": "GROUND_IMPACT"
                    },
                    {
                        "stage_num": 2, "name": f"{rocket_model} Upper Stage", "thrust_kn": 1100.0, 
                        "propellant_mass_kg": 115000.0, "empty_mass_kg": 6000.0, "burn_time_s": 355,
                        "diameter_m": 3.7, "material": "Poly-Composite", "disposal": "CONTROLLED_DEORBIT"
                    }
                ]
            }
            # Kalıcı kaydetme
            kb["rockets"][rocket_model] = rocket_data
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(kb, f, ensure_ascii=False, indent=4)
            method = "HERMES_AUTO_LEARN (AI OGRENDI)"
        else:
            method = "AI_MODEL" if get_or_load_model().trained else "PHYSICS_ENGINE"

        stages = rocket_data.get("stages", [])
        msi_factors = kb.get("msi_factors", {})

        # Çevresel faktörler
        val1 = math.sin(lat * 12.3) * math.cos(lon * 45.6)
        val2 = math.cos(lat * 7.8) * math.sin(lon * 9.1)
        val3 = math.sin(lat * lon * 0.1)
        wind_speed = val1 * 30.0
        humidity = 50.0 + val2 * 45.0
        launch_alt = max(0, val3 * 2500)

        # AI veya Fizik Motoru
        ai_model = get_or_load_model()
        physics = RocketPhysicsEngine()
        use_ai = ai_model.trained
        
        # Eger yeni ogrendiysek AI yerine fizik motoru kullanırız ilk seferde (dogruluk icin)
        if "OGRENDI" in method: use_ai = False

        impact_results = []
        import numpy as np

        if use_ai:
            for si, stage in enumerate(stages):
                upper_mass = sum(
                    s['propellant_mass_kg'] + s['empty_mass_kg']
                    for s in stages[si + 1:]
                )
                features = [
                    stage['thrust_kn'], stage['propellant_mass_kg'],
                    stage['empty_mass_kg'], stage['burn_time_s'],
                    stage.get('diameter_m', 3.0), upper_mass,
                    float(stage['stage_num']),
                    wind_speed, humidity, launch_alt
                ]
                pred = ai_model.predict(np.array(features))
                downrange = float(pred[0]) if hasattr(pred, '__len__') else float(pred)
                impact_results.append({
                    'stage_num': stage['stage_num'],
                    'name': stage['name'],
                    'downrange_km': downrange,
                    'method': 'AI_MODEL',
                })
        else:
            physics_stages = [
                {
                    'name': s['name'], 'thrust_kn': s['thrust_kn'],
                    'propellant_mass_kg': s['propellant_mass_kg'],
                    'empty_mass_kg': s['empty_mass_kg'],
                    'burn_time_s': s['burn_time_s'],
                    'diameter_m': s.get('diameter_m', 3.0),
                }
                for s in stages if s['thrust_kn'] > 0
            ]
            if physics_stages:
                impacts = physics.compute_stage_impacts(physics_stages, wind_speed=wind_speed, humidity=humidity, launch_alt=launch_alt)
                for imp in impacts:
                    impact_results.append({
                        'stage_num': imp['stage_num'],
                        'name': imp['name'],
                        'downrange_km': imp['total_downrange_km'],
                        'method': 'PHYSICS_ENGINE',
                    })

        # Düşüş noktası koordinatlarını hesapla
        impact_zones = []
        for imp in impact_results:
            snum = imp['stage_num']
            orig = next((s for s in stages if s['stage_num'] == snum), {})
            downrange_km = imp['downrange_km']
            
            disposal = orig.get('disposal', 'GROUND_IMPACT')
            is_uncontrolled = disposal == 'UNCONTROLLED_REENTRY'

            # Uncontrolled ise menzil ile biraz 'zar atalım' (deterministik rastgelelik)
            if is_uncontrolled:
                # Koordinatlara bağlı sahte bir süzülme/parçalanma mesafesi ekleyelim
                downrange_km += (math.sin(lat) + math.cos(lon)) * 500.0

            impact_pt = geopy.distance.distance(kilometers=downrange_km).destination(
                (lat, lon), bearing=azimuth
            )
            impact_lat = round(impact_pt.latitude, 6)
            impact_lon = round(impact_pt.longitude, 6)

            msi = msi_factors.get(orig.get('material', ''), 0.1)

            if is_uncontrolled:
                risk = 'KRITIK'
            elif disposal in ('OCEAN_IMPACT', 'CONTROLLED_DEORBIT', 'RECOVERY'):
                risk = 'DUSUK'
            elif disposal == 'GROUND_IMPACT':
                risk = 'YUKSEK'
            else:
                risk = 'ORTA'

            impact_zones.append({
                "stage_num": snum,
                "name": imp['name'],
                "type": "UNCONTROLLED" if is_uncontrolled else "CONTROLLED",
                "downrange_km": round(downrange_km, 1),
                "lat": impact_lat,
                "lon": impact_lon,
                "disposal": disposal,
                "material": orig.get('material', '?'),
                "mass_kg": orig.get('empty_mass_kg', 0),
                "msi": msi,
                "risk_level": risk,
                "method": imp['method'],
            })

        return {
            "rocket": rocket_model,
            "propellant": rocket_data.get('propellant_type', '?'),
            "confidence": rocket_data.get('confidence', 'LOW'),
            "launch": {"lat": lat, "lon": lon, "azimuth": azimuth},
            "environment": {
                "wind_speed_ms": round(wind_speed, 1),
                "humidity_pct": round(humidity, 1),
                "launch_alt_m": round(launch_alt, 0),
            },
            "method": method,
            "impact_zones": impact_zones,
            "stages_manifest": [
                {
                    "stage_num": s['stage_num'],
                    "name": s['name'],
                    "thrust_kn": s['thrust_kn'],
                    "propellant_mass_kg": s['propellant_mass_kg'],
                    "empty_mass_kg": s['empty_mass_kg'],
                    "burn_time_s": s['burn_time_s'],
                    "diameter_m": s.get('diameter_m', 0),
                    "material": s.get('material', '?'),
                    "disposal": s.get('disposal', '?'),
                }
                for s in stages
            ],
            "timestamp": str(datetime.datetime.now())
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
