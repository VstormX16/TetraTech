"""
Sentetik Eğitim Verisi Üreteci
Gerçek güneş fizik kurallarına dayalı veri oluşturma
"""
import numpy as np
from core.data_processor import (
    NUM_FEATURES, FEATURE_MEANS, FEATURE_STDS,
    normalize, encode_flare_class, safe_log10
)


# Risk sınıfları
# 0: GÜVENLİ   - Fırlatma için ideal
# 1: UYARI     - Dikkatli izleme gerekli
# 2: TEHLİKELİ - Fırlatma ertelenmeli
# 3: KRİTİK    - Kesinlikle fırlatma yasak


def _one_hot(label, num_classes=4):
    oh = np.zeros(num_classes, dtype=np.float32)
    oh[label] = 1.0
    return oh


def _make_safe_sample(rng):
    """Güvenli koşul: sakin güneş, düşük Kp, normal rüzgar"""
    xray_flux_log = rng.uniform(-8.5, -6.5)   # A/B sınıfı
    xray_class_enc = rng.uniform(0, 1.5)
    proton_flux_log = rng.uniform(-1, 1)
    kp = rng.uniform(0, 2)
    sw_speed = rng.uniform(300, 450)
    sw_density = rng.uniform(2, 8)
    bz = rng.uniform(-3, 3)
    cme_speed = rng.uniform(0, 200)
    sep_flux = rng.uniform(0, 0.5)
    radio = rng.uniform(0, 0.5)
    geomag = rng.choice([0, 0, 0, 1])
    radiation = rng.choice([0, 0, 0])
    flare_dur = rng.uniform(0, 0.5)
    lat_factor = rng.uniform(0, 0.8)
    lt_factor = rng.uniform(0, 1)
    return np.array([
        xray_flux_log, xray_class_enc, proton_flux_log, kp,
        sw_speed, sw_density, bz, cme_speed, sep_flux,
        radio, geomag, radiation, flare_dur, lat_factor, lt_factor
    ], dtype=np.float32)


def _make_warning_sample(rng):
    """Uyarı koşulu: orta şiddette aktivite"""
    xray_flux_log = rng.uniform(-6.5, -5.5)   # C sınıfı
    xray_class_enc = rng.uniform(1.5, 3.0)
    proton_flux_log = rng.uniform(0.5, 1.5)
    kp = rng.uniform(3, 5)
    sw_speed = rng.uniform(450, 600)
    sw_density = rng.uniform(6, 15)
    bz = rng.uniform(-8, -2)
    cme_speed = rng.uniform(200, 600)
    sep_flux = rng.uniform(0.5, 2)
    radio = rng.uniform(0.5, 1.5)
    geomag = rng.choice([1, 2])
    radiation = rng.choice([0, 1])
    flare_dur = rng.uniform(0.5, 2)
    lat_factor = rng.uniform(0.3, 1.0)
    lt_factor = rng.uniform(0, 1)
    return np.array([
        xray_flux_log, xray_class_enc, proton_flux_log, kp,
        sw_speed, sw_density, bz, cme_speed, sep_flux,
        radio, geomag, radiation, flare_dur, lat_factor, lt_factor
    ], dtype=np.float32)


def _make_dangerous_sample(rng):
    """Tehlikeli koşul: yüksek aktivite"""
    xray_flux_log = rng.uniform(-5.5, -4.5)   # M sınıfı
    xray_class_enc = rng.uniform(3.0, 4.0)
    proton_flux_log = rng.uniform(1.5, 3.0)
    kp = rng.uniform(5, 7)
    sw_speed = rng.uniform(600, 800)
    sw_density = rng.uniform(12, 25)
    bz = rng.uniform(-15, -8)
    cme_speed = rng.uniform(600, 1200)
    sep_flux = rng.uniform(2, 5)
    radio = rng.uniform(2, 3)
    geomag = rng.choice([2, 3, 4])
    radiation = rng.choice([1, 2])
    flare_dur = rng.uniform(1, 4)
    lat_factor = rng.uniform(0.5, 1.0)
    lt_factor = rng.uniform(0, 1)
    return np.array([
        xray_flux_log, xray_class_enc, proton_flux_log, kp,
        sw_speed, sw_density, bz, cme_speed, sep_flux,
        radio, geomag, radiation, flare_dur, lat_factor, lt_factor
    ], dtype=np.float32)


def _make_critical_sample(rng):
    """Kritik koşul: şiddetli güneş fırtınası"""
    xray_flux_log = rng.uniform(-4.5, -3.0)   # X sınıfı
    xray_class_enc = rng.uniform(4.0, 6.0)
    proton_flux_log = rng.uniform(3.0, 5.0)
    kp = rng.uniform(7, 9)
    sw_speed = rng.uniform(800, 1500)
    sw_density = rng.uniform(20, 50)
    bz = rng.uniform(-30, -15)
    cme_speed = rng.uniform(1200, 3000)
    sep_flux = rng.uniform(4, 8)
    radio = rng.uniform(3, 5)
    geomag = rng.choice([4, 5])
    radiation = rng.choice([3, 4, 5])
    flare_dur = rng.uniform(2, 8)
    lat_factor = rng.uniform(0.4, 1.0)
    lt_factor = rng.uniform(0, 1)
    return np.array([
        xray_flux_log, xray_class_enc, proton_flux_log, kp,
        sw_speed, sw_density, bz, cme_speed, sep_flux,
        radio, geomag, radiation, flare_dur, lat_factor, lt_factor
    ], dtype=np.float32)


def generate_training_data(n_samples=10000, seed=42):
    """
    Dengeli sentetik eğitim verisi üret
    Class dağılımı: 30% güvenli, 30% uyarı, 25% tehlikeli, 15% kritik
    """
    rng = np.random.RandomState(seed)

    n_safe = int(n_samples * 0.30)
    n_warn = int(n_samples * 0.30)
    n_dang = int(n_samples * 0.25)
    n_crit = n_samples - n_safe - n_warn - n_dang

    generators = [
        (_make_safe_sample, n_safe, 0),
        (_make_warning_sample, n_warn, 1),
        (_make_dangerous_sample, n_dang, 2),
        (_make_critical_sample, n_crit, 3),
    ]

    X_list, y_list = [], []

    for gen_func, count, label in generators:
        for _ in range(count):
            raw = gen_func(rng)
            # Küçük gürültü ekle (genelleşme için)
            noise = rng.normal(0, 0.05, raw.shape).astype(np.float32)
            raw = raw + noise
            
            lat_f = raw[13]
            lt_f = raw[14]
            
            # Enlem ve zamana gör gerçek risk seviyesini hesapla
            # Kutuplara yaklaştıkça ve öğle saatlerine yaklaştıkça risk artar
            base_risk = label
            # Ekvator(0) -> * 0.5, Kutup(1) -> * 1.5
            lat_multiplier = 0.5 + lat_f
            lt_multiplier = 0.8 + 0.4 * lt_f # Gece(0) -> * 0.8, Öğle(1) -> * 1.2
            
            # Formüle göre son skor
            if base_risk == 0:
                # Güvenli koşul genelde her yerde güvenlidir ama en ufak gürültüde etkilenmesin
                final_label = 0
            else:
                final_score = base_risk * lat_multiplier * lt_multiplier
                final_label = int(np.clip(round(final_score), 0, 3))

            x_norm = normalize(raw)
            X_list.append(x_norm)
            y_list.append(_one_hot(final_label))

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)

    # Karıştır
    indices = rng.permutation(len(X))
    return X[indices], y[indices]


def generate_validation_data(n_samples=2000, seed=99):
    return generate_training_data(n_samples=n_samples, seed=seed)
