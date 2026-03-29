"""
Güneş Verisi İşleme - Normalizasyon ve özellik mühendisliği
"""
import numpy as np


# ─── Özellik İsimleri ──────────────────────────────────────────────────────────
FEATURE_NAMES = [
    "xray_flux_log",          # 0  GOES X-ışın akısı (log10 W/m²)
    "xray_class_encoded",     # 1  A=0, B=1, C=2, M=3, X=4
    "proton_flux_log",        # 2  >10 MeV proton akısı (log10 pfu)
    "kp_index",               # 3  Jeomanyetik Kp (0-9)
    "solar_wind_speed",       # 4  Güneş rüzgar hızı (km/s)
    "solar_wind_density",     # 5  Plazma yoğunluğu (n/cm³)
    "bz_component",           # 6  IMF Bz bileşeni (nT)
    "cme_speed",              # 7  CME hızı (km/s), yok=0
    "sep_flux",               # 8  Güneş enerjili parçacık akısı
    "radio_blackout_level",   # 9  R0-R5 radyo karartma
    "geomag_storm_level",     # 10 G0-G5 jeomanyetik fırtına
    "radiation_storm_level",  # 11 S0-S5 radyasyon fırtınası
    "flare_duration_hours",   # 12 Patlama süresi (saat)
    "latitude_factor",        # 13 Enlemin güneş açısına etkisi (0-1)
    "local_time_factor",      # 14 Yerel zamanın etkisi (0-1)
]

NUM_FEATURES = len(FEATURE_NAMES)

# ─── Normalizasyon Parametreleri (gerçek verilere göre) ────────────────────────
FEATURE_MEANS = np.array([
    -6.5,   # xray_flux_log (tipik: -7 ile -4 arası)
    1.5,    # xray_class (ortalama C sınıfı)
    1.0,    # proton_flux_log
    2.5,    # kp_index (0-9)
    425.0,  # solar_wind_speed (km/s)
    6.5,    # solar_wind_density
    0.0,    # bz_component (ortalama 0)
    200.0,  # cme_speed
    1.5,    # sep_flux
    0.5,    # radio_blackout
    0.5,    # geomag_storm
    0.5,    # radiation_storm
    1.0,    # flare_duration
    0.5,    # latitude_factor
    0.5,    # local_time_factor
], dtype=np.float32)

FEATURE_STDS = np.array([
    1.5,    # xray_flux_log
    1.2,    # xray_class
    1.5,    # proton_flux_log
    2.0,    # kp_index
    100.0,  # solar_wind_speed
    5.0,    # solar_wind_density
    8.0,    # bz_component
    400.0,  # cme_speed
    1.5,    # sep_flux
    1.5,    # radio_blackout
    1.5,    # geomag_storm
    1.5,    # radiation_storm
    2.0,    # flare_duration
    0.3,    # latitude_factor
    0.3,    # local_time_factor
], dtype=np.float32)


# ─── Güneş patlaması sınıfını encode et ───────────────────────────────────────
def encode_flare_class(class_str):
    """'X2.3' -> 4 + 2.3/10 gibi sürekli değer"""
    if not class_str or class_str == 'N/A':
        return 0.0
    class_str = str(class_str).strip().upper()
    mapping = {'A': 0, 'B': 1, 'C': 2, 'M': 3, 'X': 4}
    letter = class_str[0] if class_str else 'A'
    base = mapping.get(letter, 0)
    try:
        num = float(class_str[1:]) if len(class_str) > 1 else 1.0
        return base + num / 10.0
    except:
        return float(base)


def safe_log10(value, default=-8.0):
    """Güvenli log10 (sıfır ve negatifler için default)"""
    if value is None or value <= 0:
        return default
    return np.log10(float(value))


def normalize(x, mean=None, std=None):
    """Z-score normalizasyonu"""
    if mean is None:
        mean = FEATURE_MEANS
    if std is None:
        std = FEATURE_STDS
    return (x - mean) / (std + 1e-8)


def denormalize(x_norm, mean=None, std=None):
    if mean is None:
        mean = FEATURE_MEANS
    if std is None:
        std = FEATURE_STDS
    return x_norm * std + mean


def latitude_to_factor(lat_deg):
    """
    Enlem bazlı risk faktörü.
    Yüksek enlemler kutup ışığı bölgesi → daha yüksek jeomanyetik risk
    0 faktör = ekvator (en düşük risk)
    1 faktör = kutup (en yüksek risk)
    """
    lat_rad = np.deg2rad(abs(lat_deg))
    return float(np.sin(lat_rad))


def local_time_to_factor(hour_utc, longitude_deg):
    """
    Yerel güneş zamanı faktörü.
    Gündüz tarafı (güneşe dönük) x-ışını etkisine daha açık
    """
    local_hour = (hour_utc + longitude_deg / 15.0) % 24
    # Gündüz pikini modelleyelim (12:00 en kötü)
    angle = 2 * np.pi * (local_hour - 6) / 24.0
    return float(max(0, np.sin(angle)))


def build_feature_vector(solar_data, lat, lon, utc_hour):
    """
    Ham güneş verisi + konum → normalize edilmiş özellik vektörü
    """
    xray_flux = solar_data.get('xray_flux', 1e-8)
    xray_class = solar_data.get('xray_class', 'A1')
    proton_flux = solar_data.get('proton_flux', 0.1)
    kp_index = solar_data.get('kp_index', 0.0)
    sw_speed = solar_data.get('solar_wind_speed', 400.0)
    sw_density = solar_data.get('solar_wind_density', 5.0)
    bz = solar_data.get('bz_component', 0.0)
    cme_speed = solar_data.get('cme_speed', 0.0)
    sep_flux = solar_data.get('sep_flux', 0.0)
    r_level = solar_data.get('radio_blackout_level', 0.0)
    g_level = solar_data.get('geomag_storm_level', 0.0)
    s_level = solar_data.get('radiation_storm_level', 0.0)
    flare_dur = solar_data.get('flare_duration_hours', 0.0)

    raw = np.array([
        safe_log10(xray_flux, -8.0),
        encode_flare_class(xray_class),
        safe_log10(proton_flux, 0.0),
        float(kp_index),
        float(sw_speed),
        float(sw_density),
        float(bz),
        float(cme_speed),
        float(sep_flux),
        float(r_level),
        float(g_level),
        float(s_level),
        float(flare_dur),
        latitude_to_factor(lat),
        local_time_to_factor(utc_hour, lon),
    ], dtype=np.float32)

    return normalize(raw)
