import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.risk_assessor import load_or_train_model, SolarRiskAssessor

print("Modeli yüklüyorum...")
model = load_or_train_model(retrain=False, verbose=False)
assessor = SolarRiskAssessor(model)

# Synthetic moderately dangerous data
solar_data = {
    'xray_flux': 1e-5, # M-class
    'xray_class': 'M3.5',
    'proton_flux': 50,
    'kp_index': 6,
    'solar_wind_speed': 600,
    'solar_wind_density': 15,
    'bz_component': -10,
    'cme_speed': 800,
    'sep_flux': 2,
    'radio_blackout_level': 2,
    'geomag_storm_level': 3,
    'radiation_storm_level': 1,
    'flare_duration_hours': 2,
}

print("Sentetik (orta seviye fırtına) verisi ile test ediliyor...\n")
locations = {
    'Ekvator (Kourou)': (5.2, -52.7),
    'Orta Enlem (Kennedy)': (28.5, -80.6),
    'Yüksek Enlem (Baikonur)': (45.9, 63.3),
    'Kuzey Kutbu (Svalbard)': (78.2, 15.6),
}

for name, coords in locations.items():
    # Test at noon UTC
    res = assessor.assess(solar_data, coords[0], coords[1], utc_hour=12)
    print(f"{name:>25} (Enlem: {coords[0]:5.1f}) | Risk: {res['risk_info']['name']:>10} | Oranlar: Güvenli {res['probabilities']['GUVENLI']:>5.1f}%, Uyarı {res['probabilities']['UYARI']:>5.1f}%, Tehlike {res['probabilities']['TEHLIKELI']:>5.1f}%")

