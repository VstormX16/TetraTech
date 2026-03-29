"""
HERMES Trajectory AI - NumPy Tabanlı Sinir Ağı
Roket parametrelerinden enkaz düşüş mesafesini tahmin eder.
Fizik motorundan üretilen verilerle eğitilir.
"""
import numpy as np
import os


class TrajectoryAI:
    """
    3 gizli katmanlı feedforward sinir ağı.
    Input:  [thrust_kn, prop_mass, empty_mass, burn_time, diameter, upper_mass, stage_num, wind_speed, humidity, launch_alt]
    Output: [total_downrange_km]
    """

    def __init__(self, layer_sizes=None):
        if layer_sizes is None:
            layer_sizes = [10, 128, 64, 32, 1]

        self.n_layers = len(layer_sizes) - 1
        self.weights = []
        self.biases = []

        # He initialization
        for i in range(self.n_layers):
            w = np.random.randn(layer_sizes[i], layer_sizes[i + 1]) * np.sqrt(2.0 / layer_sizes[i])
            b = np.zeros(layer_sizes[i + 1])
            self.weights.append(w)
            self.biases.append(b)

        # Normalizasyon parametreleri
        self.X_mean = None
        self.X_std = None
        self.y_mean = None
        self.y_std = None

        # Adam optimizer durumu
        self.adam = {}
        self.trained = False

    # ─── Aktivasyon ───
    def _relu(self, x):
        return np.maximum(0, x)

    def _relu_deriv(self, x):
        return (x > 0).astype(float)

    # ─── Normalizasyon ───
    def _fit_normalize(self, X, y):
        self.X_mean = np.mean(X, axis=0)
        self.X_std = np.std(X, axis=0) + 1e-8
        self.y_mean = np.mean(y)
        self.y_std = np.std(y) + 1e-8

    def _norm_X(self, X):
        return (X - self.X_mean) / self.X_std

    def _norm_y(self, y):
        return (y - self.y_mean) / self.y_std

    def _denorm_y(self, y_n):
        return y_n * self.y_std + self.y_mean

    # ─── İleri Yayılım (Forward) ───
    def forward(self, X):
        self.activations = [X]
        self.z_values = []
        out = X
        for i in range(self.n_layers):
            z = out @ self.weights[i] + self.biases[i]
            self.z_values.append(z)
            if i < self.n_layers - 1:
                out = self._relu(z)
            else:
                out = z  # Son katman lineer
            self.activations.append(out)
        return out

    # ─── Geri Yayılım (Backpropagation) + Adam ───
    def backward(self, X, y_true, y_pred, lr):
        m = X.shape[0]
        delta = 2.0 * (y_pred - y_true) / m

        for i in reversed(range(self.n_layers)):
            dW = self.activations[i].T @ delta
            db = np.sum(delta, axis=0)

            # Adam güncelleme
            for tag, param, grad in [
                (f'W{i}', self.weights[i], dW),
                (f'b{i}', self.biases[i], db),
            ]:
                if tag not in self.adam:
                    self.adam[tag] = {'m': np.zeros_like(param), 'v': np.zeros_like(param), 't': 0}
                st = self.adam[tag]
                st['t'] += 1
                st['m'] = 0.9 * st['m'] + 0.1 * grad
                st['v'] = 0.999 * st['v'] + 0.001 * grad ** 2
                m_hat = st['m'] / (1 - 0.9 ** st['t'])
                v_hat = st['v'] / (1 - 0.999 ** st['t'])
                update = lr * m_hat / (np.sqrt(v_hat) + 1e-8)

                if tag.startswith('W'):
                    self.weights[i] -= update
                else:
                    self.biases[i] -= update

            if i > 0:
                delta = (delta @ self.weights[i].T) * self._relu_deriv(self.z_values[i - 1])

    # ─── Eğitim ───
    def train(self, X_raw, y_raw, epochs=2000, lr=0.001, batch_size=64, verbose_fn=None):
        self._fit_normalize(X_raw, y_raw)
        X = self._norm_X(X_raw)
        y = self._norm_y(y_raw).reshape(-1, 1)

        history = []
        for epoch in range(epochs):
            idx = np.random.permutation(X.shape[0])
            for start in range(0, X.shape[0], batch_size):
                bi = idx[start:start + batch_size]
                pred = self.forward(X[bi])
                self.backward(X[bi], y[bi], pred, lr)

            # Epoch sonu değerlendirme
            full_pred = self.forward(X)
            mse = float(np.mean((full_pred - y) ** 2))
            history.append(mse)

            if epoch % 200 == 0 or epoch == epochs - 1:
                pred_km = self._denorm_y(full_pred.flatten())
                mae = float(np.mean(np.abs(pred_km - y_raw)))
                msg = f"  Epoch {epoch:4d}/{epochs} | MSE: {mse:.6f} | MAE: {mae:.1f} km"
                if verbose_fn:
                    verbose_fn(msg)
                else:
                    print(msg)

        self.trained = True
        return history

    # ─── Tahmin ───
    def predict(self, X_raw):
        if not self.trained:
            raise RuntimeError("Model henüz eğitilmedi! Önce 'train' komutunu çalıştırın.")
        X_n = self._norm_X(np.array(X_raw, dtype=float))
        if X_n.ndim == 1:
            X_n = X_n.reshape(1, -1)
        y_n = self.forward(X_n)
        return self._denorm_y(y_n.flatten())

    # ─── Kaydet / Yükle ───
    def save(self, path):
        data = {
            'X_mean': self.X_mean, 'X_std': self.X_std,
            'y_mean': np.array(self.y_mean), 'y_std': np.array(self.y_std),
        }
        for i in range(self.n_layers):
            data[f'W{i}'] = self.weights[i]
            data[f'b{i}'] = self.biases[i]
        np.savez(path, **data)

    def load(self, path):
        d = np.load(path)
        self.X_mean = d['X_mean']
        self.X_std = d['X_std']
        self.y_mean = float(d['y_mean'])
        self.y_std = float(d['y_std'])
        for i in range(self.n_layers):
            self.weights[i] = d[f'W{i}']
            self.biases[i] = d[f'b{i}']
        self.trained = True


MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hermes_trajectory_model.npz')


def get_or_load_model():
    """Eğitilmiş modeli yükler veya yeni bir model nesnesi döner."""
    model = TrajectoryAI()
    if os.path.exists(MODEL_PATH):
        model.load(MODEL_PATH)
    return model
