"""
HERMES-DB Impact Engine v3.0
Fizik motoru / AI + Detaylı Coğrafi Analiz ile enkaz düşüş tahmini.
"""
import json
import os
from datetime import datetime
import numpy as np
import geopy.distance
import time

from hermes_db.trajectory_ai import get_or_load_model, MODEL_PATH
from hermes_db.physics_engine import RocketPhysicsEngine


class GeoAnalyzer:
    """Her düşüş noktası için detaylı coğrafi analiz üretir."""

    def __init__(self):
        from geopy.geocoders import Nominatim
        self.geo = Nominatim(user_agent="hermes_geo_analyzer_v3", timeout=10)

    def analyze_point(self, lat, lon, launch_lat, launch_lon):
        """
        Bir koordinat için tam coğrafi profil oluşturur.
        Dönüş: dict (country, region, city, is_ocean, density, terrain, full_address, ...)
        """
        result = {
            "lat": lat, "lon": lon,
            "is_ocean": True,
            "country": None, "country_code": None,
            "region": None, "city": None,
            "full_address": "Okyanus / Bilinmeyen Sular",
            "short_name": "Okyanus/Bilinmeyen",
            "density_class": "UNINHABITED",
            "density_detail": "Açık deniz — insansız bölge",
            "terrain": "OCEAN",
            "distance_from_launch_km": 0.0,
            "bearing_from_launch": "",
            "environmental_notes": [],
            "risk_factors": [],
        }

        # Fırlatma noktasından mesafe
        try:
            dist = geopy.distance.distance((launch_lat, launch_lon), (lat, lon)).km
            result["distance_from_launch_km"] = round(dist, 1)
        except Exception:
            pass

        # Yön (bearing) hesapla
        result["bearing_from_launch"] = self._compass_bearing(launch_lat, launch_lon, lat, lon)

        # Tersine jeokodlama
        time.sleep(1.1)  # Nominatim rate limit
        try:
            loc = self.geo.reverse(f"{lat}, {lon}", language="en", exactly_one=True, timeout=10)
            if loc and loc.raw:
                raw = loc.raw
                addr = raw.get("address", {})
                result["full_address"] = loc.address
                result["country"] = addr.get("country")
                result["country_code"] = addr.get("country_code", "").upper()
                result["region"] = addr.get("state") or addr.get("region") or addr.get("province")
                result["city"] = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")

                # Kara mı deniz mi?
                loc_type = raw.get("type", "")
                loc_class = raw.get("class", "")
                address_str = loc.address.lower()

                ocean_keywords = ["ocean", "sea", "strait", "gulf", "bay", "pacific", "atlantic",
                                  "indian", "mediterranean", "black sea", "caspian", "karadeniz",
                                  "akdeniz", "ege", "marmara"]
                is_water = any(kw in address_str for kw in ocean_keywords)
                is_water = is_water or (loc_class in ["natural", "waterway"] and loc_type in ["water", "sea", "ocean", "bay", "strait"])

                if result["country"] and not is_water:
                    result["is_ocean"] = False
                    # Kısa isim
                    if result["city"]:
                        result["short_name"] = f"{result['city']}, {result['country']}"
                    elif result["region"]:
                        result["short_name"] = f"{result['region']}, {result['country']}"
                    else:
                        result["short_name"] = result["country"]
                else:
                    result["is_ocean"] = True
                    result["short_name"] = self._identify_ocean(lat, lon, address_str)
                    result["terrain"] = "OCEAN"
        except Exception:
            pass

        # Nüfus yoğunluğu tahmini
        if not result["is_ocean"]:
            result["terrain"] = "LAND"
            result["density_class"], result["density_detail"] = self._estimate_density(
                lat, lon, result["country_code"], result["city"], result["region"]
            )
        else:
            result["density_class"] = "UNINHABITED"
            result["density_detail"] = "Açık deniz — insansız bölge"

        # Çevresel notlar
        result["environmental_notes"] = self._environmental_notes(lat, lon, result)
        # Risk faktörleri
        result["risk_factors"] = self._risk_factors(result)

        return result

    def _compass_bearing(self, lat1, lon1, lat2, lon2):
        """İki nokta arasındaki pusula yönünü hesaplar."""
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dl = lon2 - lon1
        x = np.sin(dl) * np.cos(lat2)
        y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dl)
        bearing = (np.degrees(np.arctan2(x, y)) + 360) % 360

        dirs = ["Kuzey", "Kuzeydoğu", "Doğu", "Güneydoğu",
                "Güney", "Güneybatı", "Batı", "Kuzeybatı"]
        ix = int((bearing + 22.5) / 45) % 8
        return f"{dirs[ix]} ({bearing:.0f}°)"

    def _identify_ocean(self, lat, lon, address_lower=""):
        """Koordinata göre okyanus/deniz ismi belirle."""
        if "black sea" in address_lower or "karadeniz" in address_lower:
            return "Karadeniz"
        if "mediterranean" in address_lower or "akdeniz" in address_lower:
            return "Akdeniz"
        if "caspian" in address_lower or "hazar" in address_lower:
            return "Hazar Denizi"
        if "marmara" in address_lower:
            return "Marmara Denizi"
        if "ege" in address_lower or "aegean" in address_lower:
            return "Ege Denizi"
        if "atlantic" in address_lower:
            return "Atlantik Okyanusu"
        if "pacific" in address_lower:
            return "Pasifik Okyanusu"
        if "indian" in address_lower:
            return "Hint Okyanusu"
        if "arctic" in address_lower:
            return "Kuzey Buz Denizi"

        # Koordinat tabanlı tahmin
        if -80 < lon < 0 and 0 < lat < 60:
            return "Atlantik Okyanusu"
        if lon < -100 or lon > 140:
            return "Pasifik Okyanusu"
        if 40 < lon < 100 and -40 < lat < 30:
            return "Hint Okyanusu"
        if 25 < lon < 42 and 30 < lat < 47:
            return "Akdeniz / Doğu Havzası"
        return "Açık Deniz"

    def _estimate_density(self, lat, lon, country_code, city, region):
        """Ülke + şehir bilgisine dayanarak nüfus yoğunluğu tahmini."""
        high_density_countries = {"TR", "DE", "GB", "NL", "BE", "JP", "KR", "IN", "BD", "IL", "LB", "IT", "FR"}
        mega_cities = {
            "istanbul", "tokyo", "delhi", "shanghai", "beijing", "mumbai", "são paulo",
            "cairo", "dhaka", "mexico city", "osaka", "karachi", "new york", "london",
            "paris", "moscow", "los angeles", "chicago", "berlin", "rome"
        }

        city_lower = (city or "").lower()
        region_lower = (region or "").lower()
        cc = (country_code or "").upper()

        if city_lower in mega_cities:
            return "MEGA_CITY", f"Mega kent ({city}) — nüfus >10 milyon, çok yüksek yoğunluk"
        if cc in high_density_countries and city:
            return "URBAN", f"Yerleşik kent ({city}, {region or cc}) — yüksek nüfus yoğunluğu"
        if city:
            return "SUBURBAN", f"Orta yoğunluklu yerleşim ({city}) — karma bölge"
        if region:
            return "RURAL", f"Kırsal alan ({region}, {cc}) — düşük yoğunluk"
        if cc:
            return "RURAL", f"Ülke toprakları ({cc}) — belirlenemeyen kırsal bölge"
        return "UNINHABITED", "Nüfus yoğunluğu belirlenemiyor"

    def _environmental_notes(self, lat, lon, profile):
        """Çevresel risk notları."""
        notes = []
        if profile["is_ocean"]:
            notes.append("🌊 Deniz ekosistemi etkilenebilir (balıkçılık, mercan, deniz canlıları)")
            if -60 < lat < -40 or 50 < lat < 70:
                notes.append("🐋 Balina göç yolu/ balıkçılık sahası olabilir")
            if 25 < lon < 45 and 30 < lat < 45:
                notes.append("🚢 Yoğun deniz ticareti güzergahı (Doğu Akdeniz)")
        else:
            cc = profile.get("country_code", "")
            if cc in ("TR", "GR", "IT", "ES"):
                notes.append("🏛️ UNESCO Dünya Mirası ve arkeolojik alan riski yüksek bölge")
            if cc in ("BR", "CO", "ID", "CG"):
                notes.append("🌳 Yağmur ormanı ve biyoçeşitlilik merkezi")
            if profile["density_class"] in ("URBAN", "MEGA_CITY"):
                notes.append("🏥 Hastane ve kritik altyapı hasar riski yüksek")
                notes.append("🏫 Yoğun nüfus: okul, üniversite ve kamu binaları mevcut")
            if cc in ("RU", "KZ"):
                notes.append("🏜️ Geniş bozkır/step alanları — tarımsal etki riski")
        return notes

    def _risk_factors(self, profile):
        """Genel risk faktörleri."""
        factors = []
        dc = profile["density_class"]
        if dc == "MEGA_CITY":
            factors.append("⛔ KRİTİK: Mega kent bölgesi — fırlatma onaylanmamalı")
            factors.append("⛔ Tahmini etkilenen nüfus: >100,000 (yarıçap 5km)")
        elif dc == "URBAN":
            factors.append("🔴 YÜKSEK RİSK: Kentsel alan — ciddi can kaybı potansiyeli")
            factors.append("🔴 Tahmini etkilenen nüfus: 10,000-100,000 (yarıçap 5km)")
        elif dc == "SUBURBAN":
            factors.append("🟡 ORTA RİSK: Yarı kentsel alan — can kaybı olasılığı mevcut")
            factors.append("🟡 Tahmini etkilenen nüfus: 1,000-10,000 (yarıçap 5km)")
        elif dc == "RURAL":
            factors.append("🟢 DÜŞÜK RİSK: Kırsal alan — düşük nüfus yoğunluğu")
        else:
            factors.append("🟢 MİNİMAL RİSK: İnsansız bölge — deniz veya çöl")

        if not profile["is_ocean"]:
            factors.append(f"📍 Ülke: {profile.get('country', '?')} — diplomatik/hukuki sorumluluk")
        return factors


class HermesDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.msi_factors = data.get("msi_factors", {})
            self.rockets = data.get("rockets", {})

        self.ai_model = get_or_load_model()
        self.physics = RocketPhysicsEngine()
        self.geo = GeoAnalyzer()

    def _use_ai(self):
        return self.ai_model.trained

    def _generate_env_factors(self, lat, lon):
        import math
        # Her koordinat için benzersiz (ama sabit) çevresel koşullar türetir
        val1 = math.sin(lat * 12.3) * math.cos(lon * 45.6)
        val2 = math.cos(lat * 7.8) * math.sin(lon * 9.1)
        val3 = math.sin(lat * lon * 0.1)
        
        wind_speed = val1 * 30.0  # -30 to +30 m/s rüzgar
        humidity = 50.0 + val2 * 45.0 # 5% to 95% nem
        launch_alt = max(0, val3 * 2500) # 0 to 2500 m rakım
        return wind_speed, humidity, launch_alt

    def _compute_downrange(self, stages, env_factors):
        wind, humid, l_alt = env_factors
        results = []
        if self._use_ai():
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
                    wind, humid, l_alt
                ]
                pred = self.ai_model.predict(np.array(features))
                results.append({
                    'stage_num': stage['stage_num'],
                    'name': stage['name'],
                    'downrange_km': float(pred[0]) if hasattr(pred, '__len__') else float(pred),
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
                impacts = self.physics.compute_stage_impacts(physics_stages, wind_speed=wind, humidity=humid, launch_alt=l_alt)
                for imp in impacts:
                    results.append({
                        'stage_num': imp['stage_num'],
                        'name': imp['name'],
                        'downrange_km': imp['total_downrange_km'],
                        'method': 'PHYSICS_ENGINE',
                    })
            for s in stages:
                if s['thrust_kn'] <= 0:
                    last_dr = results[-1]['downrange_km'] if results else 500
                    results.append({
                        'stage_num': s['stage_num'],
                        'name': s['name'],
                        'downrange_km': last_dr * 1.1,
                        'method': 'PHYSICS_ENGINE',
                    })
        return results

    def _ec_flag(self, disposal, density_class, msi, mass):
        if disposal in ("OCEAN_IMPACT", "CONTROLLED_DEORBIT", "RECOVERY"):
            return "GREEN", "Ec < 1:100,000"
        if disposal == "UNCONTROLLED_REENTRY":
            return "RED", "Ec 1:1,000 - 1:10,000 (Uncontrolled)"
        if density_class == "MEGA_CITY":
            return "BLACK", "Ec > 1:100 — KRİTİK"
        if density_class == "URBAN":
            return "BLACK", "Ec > 1:1,000"
        if density_class == "SUBURBAN":
            return "RED", "Ec 1:1,000 - 1:10,000"
        if density_class == "RURAL" and mass * msi > 500:
            return "YELLOW", "Ec 1:10,000 - 1:100,000"
        return "GREEN", "Ec < 1:100,000"

    # ══════════════════════════════════════════════════════════
    # ANA RAPOR ÜRETİCİ
    # ══════════════════════════════════════════════════════════
    def generate_impact_report(self, query):
        rocket_model = query.get("rocket_model")
        launch_site = query.get("launch_site", {})
        azimuth = query.get("mission_profile", {}).get("azimuth_deg", 90)

        rocket = self.rockets.get(rocket_model)
        if not rocket:
            available = ", ".join(self.rockets.keys())
            return f"[red]Error: '{rocket_model}' bulunamadı. Mevcut roketler: {available}[/red]"

        stages = rocket.get("stages", [])
        is_toxic = "UDMH" in rocket.get("propellant_type", "")
        
        launch_lat = launch_site.get("latitude", 0)
        launch_lon = launch_site.get("longitude", 0)
        env_factors = self._generate_env_factors(launch_lat, launch_lon)
        wind, humid, l_alt = env_factors
        
        impact_results = self._compute_downrange(stages, env_factors)
        method_used = impact_results[0]['method'] if impact_results else "N/A"

        # ── Rapor ──
        r = []
        r.append("══════════════════════════════════════════════════════════════════════════════")
        r.append("[bold white]DEBRIS IMPACT PROBABILITY REPORT[/bold white]")
        r.append(f"Generator: HERMES-DB v3.0 | Engine: [bold cyan]{method_used}[/bold cyan]")
        r.append(f"Rocket: {rocket_model} | Propellant: {rocket.get('propellant_type', '?')}")
        r.append(f"Launch Site: {launch_site.get('name', '?')} ({launch_lat:.4f}, {launch_lon:.4f})")
        r.append(f"Environment: Rakım [bold]{l_alt:.0f}m[/bold] | Nem [bold]%{(humid):.0f}[/bold] | Rüzgar [bold]{wind:.1f} m/s[/bold]")
        r.append(f"Azimuth: {azimuth}° | Date: {datetime.utcnow().isoformat()}")
        r.append("══════════════════════════════════════════════════════════════════════════════")

        # ── Parça Listesi ──
        r.append("\n[bold]SEPARATION EVENT MANIFEST:[/bold]")
        for s in stages:
            msi = self.msi_factors.get(s["material"], 0.1)
            r.append(f"  • {s['stage_num']}. Aşama / {s['name']}")
            r.append(f"    Kütle: {s['empty_mass_kg']:,} kg | İtki: {s['thrust_kn']:,} kN | Yanma: {s['burn_time_s']}s | Çap: {s.get('diameter_m', '?')}m")
            r.append(f"    Malzeme: {s['material']} (MSI: {msi}) | Bertaraf: {s['disposal']}")

        # ── Her aşama için detaylı analiz ──
        r.append("\n[bold]═══ AŞAMA BAZLI DETAYLI ANALİZ ═══[/bold]")

        compliance_flags = []
        ai_commentary = []

        for imp in impact_results:
            snum = imp['stage_num']
            orig = next((s for s in stages if s['stage_num'] == snum), {})
            downrange_km = imp['downrange_km']

            r.append(f"\n┌{'─' * 70}")
            r.append(f"│ [bold white]{snum}. AŞAMA: {imp['name']}[/bold white]")
            r.append(f"├{'─' * 70}")

            # Kontrolsüz yeniden giriş
            if orig.get('disposal') == 'UNCONTROLLED_REENTRY':
                r.append("│  ⚠️  [bold red]KONTROLSÜZ YENİDEN GİRİŞ[/bold red]")
                r.append("│  Düşüş noktası T-3h'e kadar kesin olarak tahmin edilemez.")
                r.append(f"│  Tahmini yörüngesel menzil: ~{downrange_km:.0f} km")
                r.append(f"│  Enlem bandı: ±{41.5}° — dünya çevresinde herhangi bir nokta")
                r.append("│  ────────────────────────────────────────")
                r.append("│  [bold red]RİSK DEĞERLENDİRMESİ:[/bold red]")
                r.append("│    ⛔ Düşüş noktası önceden belirlenemediği için tüm lat<±41.5° nüfus riski altında")
                r.append("│    ⛔ CZ-5B tipi kontrolsüz giriş geçmişte yerleşim alanlarına yakın düşmüştür")
                r.append("│    📋 Uluslararası Uzay Hukuku (OST Md. VII) — fırlatan devlet sorumludur")
                r.append(f"└{'─' * 70}")
                compliance_flags.append(f"[RED] {imp['name']}: Kontrolsüz Reentry — Ec 1:1,000-1:10,000")
                ai_commentary.append(
                    f"🔹 {snum}. Aşama ({imp['name']}): Bu kademe yörüngede kalarak kontrolsüz "
                    f"atmosfere geri dönecektir. Düşüş noktası ancak yörüngeden çıkmasına saatler "
                    f"kala belirlenebilir. ±41.5° enlem bandında herhangi bir kara parçası "
                    f"risk altındadır. Long March 5B'nin geçmiş uçuşlarında Fildişi Sahili, "
                    f"Malezya ve Filipinler yakınlarına kontrolsüz düşüş gerçekleşmiştir."
                )
                continue

            # Düşüş koordinatını hesapla
            impact_pt = geopy.distance.distance(kilometers=downrange_km).destination(
                (launch_lat, launch_lon), bearing=azimuth
            )
            lat, lon = impact_pt.latitude, impact_pt.longitude

            # DETAYLI COĞRAFİ ANALİZ
            r.append("│  [dim]Coğrafi analiz yapılıyor...[/dim]")
            profile = self.geo.analyze_point(lat, lon, launch_lat, launch_lon)

            msi = self.msi_factors.get(orig.get("material", ""), 0.1)
            flag, ec_text = self._ec_flag(
                orig.get('disposal', 'GROUND_IMPACT'),
                profile["density_class"], msi,
                orig.get('empty_mass_kg', 0)
            )
            if is_toxic and orig.get('disposal') == 'GROUND_IMPACT':
                flag = "RED"
                ec_text += " | ⚠ TOKSİK YAKIT (UDMH/N2O4)"

            # Konum bilgileri
            r.append("│")
            r.append(f"│  📍 [bold yellow]KOORDİNATLAR: {lat:.6f}, {lon:.6f}[/bold yellow]")
            r.append(f"│  📏 Fırlatma Üssünden Uzaklık: [bold]{profile['distance_from_launch_km']:.1f} km[/bold]")
            r.append(f"│  🧭 Yön: {profile['bearing_from_launch']}")
            r.append(f"│  📌 Konum: {profile['short_name']}")
            if profile["full_address"] != profile["short_name"]:
                r.append(f"│  📌 Tam Adres: {profile['full_address'][:80]}")
            r.append("│")

            # Arazi ve nüfus
            r.append("│  ── ARAZİ & NÜFUS ANALİZİ ──")
            terrain_emoji = "🌊" if profile["is_ocean"] else "🏔️"
            r.append(f"│  {terrain_emoji} Arazi: {'DENİZ/OKYANUS' if profile['is_ocean'] else 'KARA'}")
            if profile["country"]:
                r.append(f"│  🏳️ Ülke: {profile['country']} ({profile['country_code']})")
            if profile["region"]:
                r.append(f"│  🗺️ Bölge: {profile['region']}")
            if profile["city"]:
                r.append(f"│  🏙️ Şehir: {profile['city']}")
            r.append(f"│  👥 Yoğunluk: [{profile['density_class']}] {profile['density_detail']}")
            r.append("│")

            # Risk değerlendirmesi
            r.append("│  ── RİSK DEĞERLENDİRMESİ ──")
            r.append(f"│  🎯 Casualty Expectancy: [{flag}] {ec_text}")
            r.append(f"│  🔧 Bertaraf Yöntemi: {orig.get('disposal', '?')}")
            r.append(f"│  📦 Parça Kütlesi: {orig.get('empty_mass_kg', 0):,} kg | MSI: {msi}")
            for rf in profile["risk_factors"]:
                r.append(f"│    {rf}")
            r.append("│")

            # Çevresel notlar
            if profile["environmental_notes"]:
                r.append("│  ── ÇEVRESEL ETKİ ──")
                for note in profile["environmental_notes"]:
                    r.append(f"│    {note}")
                r.append("│")

            r.append(f"└{'─' * 70}")

            compliance_flags.append(f"[{flag}] {snum}. Aşama / {imp['name']} ({lat:.2f}, {lon:.2f}) → {profile['short_name']}: {ec_text}")

            # AI Yorumu — şehre özel detaylı
            commentary = f"🔹 {snum}. Aşama ({imp['name']}): "
            if orig.get('disposal') == 'RECOVERY':
                commentary += (
                    f"Yakıtını bitirip ayrıldıktan sonra normalde geri dönüş manevrası ile "
                    f"kurtarılır. Kurtarılamazsa balistik olarak {profile['short_name']} "
                    f"yakınlarına ({lat:.4f}, {lon:.4f}) düşer — fırlatma üssünden "
                    f"{profile['distance_from_launch_km']:.0f} km {profile['bearing_from_launch']} yönünde. "
                )
                if profile["is_ocean"]:
                    commentary += "Düşüş noktası deniz üzerinde, kara riski düşük."
                else:
                    commentary += f"Düşüş noktası {profile['country']} topraklarında — {profile['density_detail']}."
            elif orig.get('disposal') == 'CONTROLLED_DEORBIT':
                commentary += (
                    f"Yörüngeye ulaştıktan sonra kontrollü deorbit manevrası uygulanır. "
                    f"Balistik ayrılma noktası {profile['short_name']} bölgesindedir "
                    f"({lat:.4f}, {lon:.4f}). Kontrollü yanma ile Point Nemo'ya "
                    f"yönlendirilmesi planlanmaktadır."
                )
            else:
                commentary += (
                    f"Yükseliş evresinde yakıtını tükettikten sonra ayrılıp balistik "
                    f"serbest düşüşe geçerek {profile['short_name']} bölgesine "
                    f"({lat:.4f}, {lon:.4f}) düşecektir. Fırlatma üssünden "
                    f"{profile['distance_from_launch_km']:.0f} km {profile['bearing_from_launch']} yönünde. "
                )
                if profile["is_ocean"]:
                    commentary += f"Düşüş noktası {profile['short_name']} üzerinde — kara riski minimal."
                elif profile["density_class"] in ("MEGA_CITY", "URBAN"):
                    commentary += f"⚠️ KRİTİK: {profile['city'] or profile['region']} yerleşim alanı doğrudan tehdit altında!"
                else:
                    commentary += f"Düşüş noktası {profile['density_detail']}."

            ai_commentary.append(commentary)

        # ── Uyumluluk Bayrakları ──
        r.append("\n[bold]COMPLIANCE FLAGS:[/bold]")
        for cf in compliance_flags:
            r.append(f"  {cf}")

        r.append(f"\nCONFIDENCE: [{rocket.get('confidence', 'LOW')}]")

        # ── AI Yorumu ──
        if ai_commentary:
            r.append("\n══════════════════════════════════════════════════════════════════════════════")
            r.append("[bold cyan]HERMES AI COMMENTARY[/bold cyan]")
            for c in ai_commentary:
                r.append(c)
            r.append("")

        return "\n".join(r)
