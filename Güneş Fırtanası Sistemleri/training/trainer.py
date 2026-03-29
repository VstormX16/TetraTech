"""
Model Eğitimi - Mini-batch gradient descent ile
"""
import numpy as np
from core.neural_network import NeuralNetwork
from core.loss_functions import cross_entropy_loss, cross_entropy_derivative


class Trainer:
    """
    Sinir ağı eğitim döngüsü
    - Mini-batch SGD
    - Erken durdurma (Early Stopping)
    - Eğitim / doğrulama ayrımı
    """

    def __init__(self, model: NeuralNetwork, batch_size=64, patience=15):
        self.model = model
        self.batch_size = batch_size
        self.patience = patience
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
        }

    def _compute_accuracy(self, X, y_onehot):
        preds = self.model.predict(X)
        pred_labels = np.argmax(preds, axis=1)
        true_labels = np.argmax(y_onehot, axis=1)
        return np.mean(pred_labels == true_labels)

    def train(self, X_train, y_train, X_val, y_val, epochs=200, verbose=True):
        n = X_train.shape[0]
        best_val_loss = float('inf')
        best_weights = None
        no_improve = 0

        if verbose:
            print(f"\n[EĞİTİM] Başlıyor: {epochs} epoch, batch={self.batch_size}")
            print(f"[EĞİTİM] Eğitim seti: {n} örnek")
            print(f"[EĞİTİM] Doğrulama seti: {X_val.shape[0]} örnek\n")

        for epoch in range(1, epochs + 1):
            self.model.set_training(True)

            # Karıştır
            perm = np.random.permutation(n)
            X_shuf = X_train[perm]
            y_shuf = y_train[perm]

            epoch_loss = 0.0
            n_batches = 0

            # Mini-batch döngüsü
            for start in range(0, n, self.batch_size):
                end = min(start + self.batch_size, n)
                X_batch = X_shuf[start:end]
                y_batch = y_shuf[start:end]

                # İleri yayılım
                y_pred = self.model.forward(X_batch)

                # Kayıp
                loss = cross_entropy_loss(y_pred, y_batch)
                epoch_loss += loss
                n_batches += 1

                # Geri yayılım (softmax + CE birleşik türev)
                grad = cross_entropy_derivative(y_pred, y_batch) / X_batch.shape[0]
                self.model.backward(grad)

                # Parametre güncelleme
                self.model.update_params()

            avg_train_loss = epoch_loss / n_batches

            # Doğrulama
            self.model.set_training(False)
            val_pred = self.model.forward(X_val)
            val_loss = cross_entropy_loss(val_pred, y_val)

            train_acc = self._compute_accuracy(X_train, y_train)
            val_acc = self._compute_accuracy(X_val, y_val)

            self.history['train_loss'].append(avg_train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_acc'].append(val_acc)

            # İlerleme yazdır
            if verbose and (epoch % 10 == 0 or epoch == 1):
                bar_len = 20
                filled = int(bar_len * epoch / epochs)
                bar = '█' * filled + '░' * (bar_len - filled)
                print(
                    f"  Epoch {epoch:3d}/{epochs} [{bar}] "
                    f"| Kayıp: {avg_train_loss:.4f} "
                    f"| Val Kayıp: {val_loss:.4f} "
                    f"| Doğruluk: {val_acc * 100:.1f}%"
                )

            # Erken durdurma
            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                best_weights = self._copy_weights()
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= self.patience:
                    if verbose:
                        print(f"\n[EĞİTİM] Erken durdurma: {epoch}. epoch'ta")
                    break

        # En iyi ağırlıkları geri yükle
        if best_weights:
            self._restore_weights(best_weights)

        if verbose:
            final_acc = self._compute_accuracy(X_val, y_val)
            print(f"\n[EĞİTİM] Tamamlandı!")
            print(f"[EĞİTİM] Final doğrulama doğruluğu: {final_acc * 100:.2f}%")

        return self.history

    def _copy_weights(self):
        """Ağırlıkların derin kopyasını al"""
        weights = []
        for layer in self.model.layers:
            weights.append({
                'W': layer.W.copy(),
                'b': layer.b.copy(),
                'gamma': layer.gamma.copy(),
                'beta': layer.beta.copy(),
                'running_mean': layer.running_mean.copy(),
                'running_var': layer.running_var.copy(),
            })
        return weights

    def _restore_weights(self, weights):
        """Kaydedilen ağırlıkları geri yükle"""
        for i, layer in enumerate(self.model.layers):
            layer.W = weights[i]['W']
            layer.b = weights[i]['b']
            layer.gamma = weights[i]['gamma']
            layer.beta = weights[i]['beta']
            layer.running_mean = weights[i]['running_mean']
            layer.running_var = weights[i]['running_var']
