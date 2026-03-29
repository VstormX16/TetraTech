"""
Güneş Patlaması Risk Değerlendirme Modeli
"""
import numpy as np
import os
from core.neural_network import NeuralNetwork
from core.data_processor import (
    build_feature_vector, FEATURE_NAMES, NUM_FEATURES,
    latitude_to_factor, local_time_to_factor
)


# Risk seviyeleri
RISK_LEVELS = {
    0: {
        'name': 'GÜVENLİ',
        'tr': 'Fırlatma için uygun koşullar',
        'symbol': '🟢',
        'ascii': '[GUVENLI]',
        'color': 'green',
        'recommendation': 'Fırlatma penceresi açık. Güneş aktivitesi minimal.',
    },
    1: {
        'name': 'UYARI',
        'tr': 'Dikkatli izleme gerekli',
        'symbol': '🟡',
        'ascii': '[UYARI  ]',
        'color': 'yellow',
        'recommendation': 'Fırlatma mümkün ancak sürekli izleme şart. Durum kötüleşirse ertele.',
    },
    2: {
        'name': 'TEHLİKELİ',
        'tr': 'Fırlatma ertelenmeli',
        'symbol': '🔴',
        'ascii': '[TEHLIKE]',
        'color': 'red',
        'recommendation': 'Fırlatmayı ertele. Yüksek güneş aktivitesi mevcut.',
    },
    3: {
        'name': 'KRİTİK',
        'tr': 'Fırlatma KESİNLİKLE yasak',
        'symbol': '⚫',
        'ascii': '[KRITIK ]',
        'color': 'dark_red',
        'recommendation': 'Fırlatma yasak! Şiddetli güneş fırtınası. Elektronik ve iletişim tehlikede.',
    },
}

# Faktör açıklamaları
RISK_FACTORS = {
    'xray_flux_log': 'X-Işını Akısı',
    'xray_class_encoded': 'Patlama Sınıfı',
    'proton_flux_log': 'Proton Akısı',
    'kp_index': 'Kp İndeksi (Jeomanyetik)',
    'solar_wind_speed': 'Güneş Rüzgar Hızı',
    'solar_wind_density': 'Plazma Yoğunluğu',
    'bz_component': 'IMF Bz Bileşeni',
    'cme_speed': 'CME Hızı',
    'sep_flux': 'SEP Olayları',
    'radio_blackout_level': 'Radyo Karartma (R)',
    'geomag_storm_level': 'Jeomanyetik Fırtına (G)',
    'radiation_storm_level': 'Radyasyon Fırtınası (S)',
    'flare_duration_hours': 'Patlama Süresi',
    'latitude_factor': 'Enlem Risk Faktörü',
    'local_time_factor': 'Yerel Zaman Faktörü',
}

WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'models', 'solar_weights.npy')


def build_model(learning_rate=0.001):
    """Ana risk değerlendirme modelini oluştur"""
    model = NeuralNetwork(
        layer_sizes=[NUM_FEATURES, 64, 32, 16, 4],
        activations=['relu', 'relu', 'relu', 'softmax'],
        dropout_rates=[0.2, 0.15, 0.1, 0.0],
        learning_rate=learning_rate
    )
    return model


def load_or_train_model(retrain=False, verbose=True):
    """
    Model ağırlıklarını yükle ya da yoksa eğit
    """
    from data.synthetic_generator import generate_training_data, generate_validation_data
    from training.trainer import Trainer

    model = build_model()

    if not retrain and os.path.exists(WEIGHTS_FILE):
        if verbose:
            print(f"[MODEL] Kaydedilmiş ağırlıklar yükleniyor...")
        model.load_weights(WEIGHTS_FILE)
        return model

    if verbose:
        print("[MODEL] Eğitim verisi üretiliyor...")

    X_train, y_train = generate_training_data(n_samples=12000, seed=42)
    X_val, y_val = generate_validation_data(n_samples=2000, seed=99)

    trainer = Trainer(model, batch_size=64, patience=20)
    trainer.train(
        X_train, y_train,
        X_val, y_val,
        epochs=300,
        verbose=verbose
    )

    # Ağırlıkları kaydet
    os.makedirs(os.path.dirname(WEIGHTS_FILE), exist_ok=True)
    model.save_weights(WEIGHTS_FILE)

    return model


class SolarRiskAssessor:
    """
    Ana risk değerlendirici sınıfı
    """

    def __init__(self, model: NeuralNetwork):
        self.model = model

    def assess(self, solar_data: dict, lat: float, lon: float, utc_hour: int = None):
        """
        Güneş verisi + konum → Risk değerlendirmesi

        Returns:
            dict: risk_level, probabilities, factors, recommendation
        """
        import datetime
        if utc_hour is None:
            utc_hour = datetime.datetime.utcnow().hour

        # Özellik vektörü oluştur
        x = build_feature_vector(solar_data, lat, lon, utc_hour)

        # Tahmin yap
        self.model.set_training(False)
        probs = self.model.predict(x.reshape(1, -1))[0]
        risk_level = int(np.argmax(probs))

        # Güven skoru
        confidence = float(probs[risk_level]) * 100

        # Risk katkı faktörleri (hangi özellik ne kadar etki etti)
        factor_impacts = self._compute_factor_impacts(x, solar_data, lat, lon, utc_hour)

        return {
            'risk_level': risk_level,
            'risk_info': RISK_LEVELS[risk_level],
            'probabilities': {
                'GUVENLI': float(probs[0]) * 100,
                'UYARI': float(probs[1]) * 100,
                'TEHLIKELI': float(probs[2]) * 100,
                'KRITIK': float(probs[3]) * 100,
            },
            'confidence': confidence,
            'factor_impacts': factor_impacts,
            'latitude': lat,
            'longitude': lon,
            'utc_hour': utc_hour,
        }

    def _compute_factor_impacts(self, x_norm, solar_data, lat, lon, utc_hour):
        """
        Basit pertürbasyon tabanlı özellik önemi
        """
        base_pred = self.model.predict(x_norm.reshape(1, -1))[0]
        base_risk = int(np.argmax(base_pred))
        base_conf = float(base_pred[base_risk])

        impacts = {}
        x_copy = x_norm.copy()

        for i, fname in enumerate(FEATURE_NAMES):
            # Özelliği sıfırla ve tahmin farkını gör
            x_perturbed = x_copy.copy()
            x_perturbed[i] = 0.0  # Ortalamaya sıfırla (normalize edilmiş)
            pred_p = self.model.predict(x_perturbed.reshape(1, -1))[0]
            delta = float(np.abs(pred_p[base_risk] - base_pred[base_risk]))
            impacts[RISK_FACTORS.get(fname, fname)] = round(delta * 100, 2)

        # Sırala (en etkili önce)
        return dict(sorted(impacts.items(), key=lambda x: x[1], reverse=True))
