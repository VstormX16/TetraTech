"""
NASA DONKI + NOAA Space Weather API'den gerçek zamanlı veri çekme
"""
import requests
import json
from datetime import datetime, timedelta
import time


NASA_API_KEY = "DEMO_KEY"  # Ücretsiz NASA API anahtarı (rate limit var)
NOAA_BASE = "https://services.swpc.noaa.gov"
NASA_BASE = "https://api.nasa.gov/DONKI"


def _safe_get(url, timeout=10, retries=2, verbose=False):
    """HTTP GET ile güvenli veri çekme"""
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if verbose and attempt == retries - 1:
                print(f"  [UYARI] HTTP hatası ({url}): {e}")
        except requests.exceptions.ConnectionError:
            if verbose and attempt == retries - 1:
                print(f"  [UYARI] Bağlantı hatası ({url})")
        except requests.exceptions.Timeout:
            if verbose and attempt == retries - 1:
                print(f"  [UYARI] Zaman aşımı ({url})")
        except Exception as e:
            if verbose and attempt == retries - 1:
                print(f"  [UYARI] Bilinmeyen hata ({url}): {e}")
        if attempt < retries - 1:
            time.sleep(1)
    return None


# ─── NOAA Veri Çekiciler ───────────────────────────────────────────────────────

def get_noaa_xray_flux():
    """GOES X-ışını akısı (son 6 dakika)"""
    url = f"{NOAA_BASE}/json/goes/secondary/xrays-6-hour.json"
    data = _safe_get(url)
    if data and len(data) > 0:
        latest = data[-1]
        flux_long = float(latest.get('flux', 1e-8) or 1e-8)
        return {
            'xray_flux': flux_long,
            'time': latest.get('time_tag', 'N/A'),
            'satellite': latest.get('satellite', 'N/A'),
        }
    return {'xray_flux': 1e-8, 'time': 'N/A', 'satellite': 'N/A'}


def get_noaa_geomag():
    """Jeomanyetik Kp indeksi (son 3 saatlik)"""
    url = f"{NOAA_BASE}/products/noaa-planetary-k-index.json"
    data = _safe_get(url)
    if data and len(data) > 1:
        # İlk satır başlık, son satır en güncel
        latest = data[-1]
        try:
            kp = float(latest[1]) if latest[1] else 0.0
            return {
                'kp_index': kp,
                'time': latest[0] if latest[0] else 'N/A',
                'geomag_storm_level': _kp_to_g_level(kp),
            }
        except (IndexError, ValueError, TypeError):
            pass
    return {'kp_index': 0.0, 'time': 'N/A', 'geomag_storm_level': 0}


def get_noaa_solar_wind():
    """ACE/DSCOVR güneş rüzgarı verileri"""
    url = f"{NOAA_BASE}/products/solar-wind/plasma-6-hour.json"
    data = _safe_get(url)
    result = {'solar_wind_speed': 400.0, 'solar_wind_density': 5.0, 'time': 'N/A', 'solar_wind_history': []}

    if data and len(data) > 1:
        history = []
        for row in data[1:]:
            try:
                if row[2]: history.append(float(row[2]))
            except:
                pass
                
        latest = data[-1]
        try:
            result['solar_wind_speed'] = float(latest[2] or 400)
            result['solar_wind_density'] = float(latest[1] or 5)
            result['time'] = latest[0]
            result['solar_wind_history'] = history[-50:] # Son 50 ölçümü alalım (ortalama son birkaç saat)
        except (IndexError, ValueError, TypeError):
            pass

    return result


def get_noaa_imf():
    """IMF (Interplanetary Magnetic Field) Bz bileşeni"""
    url = f"{NOAA_BASE}/products/solar-wind/mag-6-hour.json"
    data = _safe_get(url)
    result = {'bz_component': 0.0, 'bt_total': 5.0, 'time': 'N/A'}

    if data and len(data) > 1:
        latest = data[-1]
        try:
            result['bz_component'] = float(latest[3] or 0)  # Bz GSM
            result['bt_total'] = float(latest[6] or 5)       # Bt total
            result['time'] = latest[0]
        except (IndexError, ValueError, TypeError):
            pass

    return result


def get_noaa_proton_flux():
    """GOES proton akısı (> 10 MeV)"""
    url = f"{NOAA_BASE}/json/goes/primary/integral-protons-6-hour.json"
    data = _safe_get(url)
    result = {'proton_flux': 0.1, 'radiation_storm_level': 0}

    if data and len(data) > 0:
        # > 10 MeV kanalını bul
        for entry in reversed(data):
            if entry.get('energy') == '>=10 MeV':
                try:
                    flux = float(entry.get('flux', 0.1) or 0.1)
                    result['proton_flux'] = flux
                    result['radiation_storm_level'] = _proton_to_s_level(flux)
                    break
                except (ValueError, TypeError):
                    pass

    return result


def get_noaa_latest_flare():
    """NOAA SWPC'den son güneş patlaması"""
    url = f"{NOAA_BASE}/json/goes/primary/xrays-6-hour.json"
    data = _safe_get(url)
    result = {
        'xray_class': 'A1',
        'flare_duration_hours': 0.0,
        'radio_blackout_level': 0,
    }

    if data and len(data) > 0:
        # X-ray akısından sınıf tahmin et (NOAA standartları)
        latest = data[-1]
        try:
            flux = float(latest.get('flux', 1e-8) or 1e-8)
            cls, level = _flux_to_class_and_rlevel(flux)
            result['xray_class'] = cls
            result['radio_blackout_level'] = level
        except Exception:
            pass

    return result


def get_nasa_cme():
    """NASA DONKI - Son Koronal Kütle Atımları (CME)"""
    end_date = datetime.utcnow().strftime('%Y-%m-%d')
    start_date = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%d')
    url = f"{NASA_BASE}/CME?startDate={start_date}&endDate={end_date}&api_key={NASA_API_KEY}"
    data = _safe_get(url)

    result = {'cme_speed': 0.0, 'cme_count_3d': 0}

    if data and isinstance(data, list):
        result['cme_count_3d'] = len(data)
        max_speed = 0.0
        for cme in data:
            analyses = cme.get('cmeAnalyses', [])
            for ana in analyses:
                speed = ana.get('speed')
                if speed:
                    try:
                        s = float(speed)
                        if s > max_speed:
                            max_speed = s
                    except (ValueError, TypeError):
                        pass
        result['cme_speed'] = max_speed

    return result


def get_nasa_sep():
    """NASA DONKI - Güneş Energetik Parçacıkları"""
    end_date = datetime.utcnow().strftime('%Y-%m-%d')
    start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"{NASA_BASE}/SEP?startDate={start_date}&endDate={end_date}&api_key={NASA_API_KEY}"
    data = _safe_get(url)

    result = {'sep_flux': 0.0, 'sep_count_24h': 0}

    if data and isinstance(data, list):
        result['sep_count_24h'] = len(data)
        result['sep_flux'] = float(len(data))  # SEP olay sayısı proxy olarak

    return result


def get_nasa_flares():
    """NASA DONKI - Son güneş patlamaları"""
    end_date = datetime.utcnow().strftime('%Y-%m-%d')
    start_date = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d')
    url = f"{NASA_BASE}/FLR?startDate={start_date}&endDate={end_date}&api_key={NASA_API_KEY}"
    data = _safe_get(url)

    result = {'nasa_flare_class': 'A1', 'nasa_flare_count': 0, 'flare_duration_hours': 0.0}

    if data and isinstance(data, list):
        result['nasa_flare_count'] = len(data)
        if data:
            # En son ve en güçlü patlama
            strongest = None
            class_order = {'A': 0, 'B': 1, 'C': 2, 'M': 3, 'X': 4}
            for flare in data:
                cls = flare.get('classType', 'A1')
                if cls and len(cls) > 0:
                    letter = cls[0].upper()
                    if strongest is None:
                        strongest = flare
                    else:
                        prev_letter = strongest.get('classType', 'A')[0].upper()
                        if class_order.get(letter, 0) > class_order.get(prev_letter, 0):
                            strongest = flare

            if strongest:
                result['nasa_flare_class'] = strongest.get('classType', 'A1')
                # Süreyi hesapla
                begin = strongest.get('beginTime')
                end = strongest.get('endTime')
                if begin and end:
                    try:
                        fmt = '%Y-%m-%dT%H:%MZ'
                        t1 = datetime.strptime(begin, fmt)
                        t2 = datetime.strptime(end, fmt)
                        dur = (t2 - t1).total_seconds() / 3600.0
                        result['flare_duration_hours'] = max(0, dur)
                    except Exception:
                        pass

    return result


# ─── Yardımcı Dönüşüm Fonksiyonları ──────────────────────────────────────────

def _kp_to_g_level(kp):
    """Kp indeksini G seviyesine çevir (G0-G5)"""
    if kp < 5:
        return 0
    elif kp < 6:
        return 1
    elif kp < 7:
        return 2
    elif kp < 8:
        return 3
    elif kp < 9:
        return 4
    else:
        return 5


def _proton_to_s_level(pfu):
    """Proton akısını S seviyesine çevir"""
    if pfu < 10:
        return 0
    elif pfu < 100:
        return 1
    elif pfu < 1000:
        return 2
    elif pfu < 10000:
        return 3
    elif pfu < 100000:
        return 4
    else:
        return 5


def _flux_to_class_and_rlevel(flux):
    """X-ışını akısından sınıf ve R seviyesi"""
    if flux < 1e-8:
        return 'A1', 0
    elif flux < 1e-7:
        scale = flux / 1e-8
        return f'A{scale:.0f}', 0
    elif flux < 1e-6:
        scale = flux / 1e-7
        return f'B{scale:.0f}', 0
    elif flux < 1e-5:
        scale = flux / 1e-6
        return f'C{scale:.0f}', 0
    elif flux < 1e-4:
        scale = flux / 1e-5
        return f'M{scale:.0f}', 1
    else:
        scale = flux / 1e-4
        level = min(5, int(scale) + 2) if scale >= 2 else 1
        return f'X{scale:.0f}', level


def get_noaa_alerts():
    """NOAA SWPC'den güncel uzay havası uyarıları"""
    url = f"{NOAA_BASE}/products/alerts.json"
    data = _safe_get(url)
    if data and isinstance(data, list):
        # Sadece en son ve aktif uyarıyı döndürelim (veya tümünü listeyelim)
        return {"all_alerts": data[:5]}
    return {"all_alerts": []}


# ─── Ana Veri Toplama Fonksiyonu ───────────────────────────────────────────────

def fetch_all_solar_data(verbose=True):
    """
    Tüm NOAA + NASA kaynaklarından gerçek zamanlı güneş verisi topla
    """
    if verbose:
        print("\n[VERİ] Güneş verileri çekiliyor...")

    all_data = {}

    sources = [
        ("X-Ray Flux (NOAA GOES)", get_noaa_xray_flux),
        ("Jeomanyetik Kp (NOAA)", get_noaa_geomag),
        ("Güneş Rüzgarı Plazma (NOAA)", get_noaa_solar_wind),
        ("IMF Bz (NOAA)", get_noaa_imf),
        ("Proton Akısı (NOAA GOES)", get_noaa_proton_flux),
        ("X-Ray Sınıf (NOAA)", get_noaa_latest_flare),
        ("CME (NASA DONKI)", get_nasa_cme),
        ("SEP Olayları (NASA DONKI)", get_nasa_sep),
        ("Güneş Patlamaları (NASA DONKI)", get_nasa_flares),
        ("NOAA Alerts", get_noaa_alerts),
    ]

    for name, func in sources:
        if verbose:
            print(f"  → {name}...", end=' ', flush=True)
        result = func()
        if result:
            all_data.update(result)
            if verbose:
                print("✓")
        else:
            if verbose:
                print("✗ (varsayılan kullanıldı)")

    # NASA DONKI patlama sınıfı NOAA'yı override et (daha detaylı)
    if 'nasa_flare_class' in all_data and all_data['nasa_flare_class'] != 'A1':
        all_data['xray_class'] = all_data['nasa_flare_class']

    if verbose:
        print("[VERİ] Tüm veriler toplandı.\n")

    return all_data
