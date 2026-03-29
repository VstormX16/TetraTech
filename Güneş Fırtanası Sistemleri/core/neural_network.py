"""
Tamamen Sıfırdan Yazılmış Derin Sinir Ağı
Backpropagation, Forward pass, her şey numpy ile
"""
import numpy as np
from core.activations import relu, relu_derivative, softmax, sigmoid, sigmoid_derivative
from core.loss_functions import cross_entropy_loss, cross_entropy_derivative
from core.optimizers import Adam


class Layer:
    """Tam bağlantılı (Dense) katman"""

    def __init__(self, input_size, output_size, activation='relu', dropout_rate=0.0):
        self.input_size = input_size
        self.output_size = output_size
        self.activation_name = activation
        self.dropout_rate = dropout_rate
        self.training = True

        # Xavier/He başlatma
        if activation == 'relu':
            scale = np.sqrt(2.0 / input_size)  # He başlatma
        else:
            scale = np.sqrt(1.0 / input_size)  # Xavier başlatma

        self.W = np.random.randn(input_size, output_size) * scale
        self.b = np.zeros((1, output_size))

        # Batch Normalization parametreleri
        self.use_bn = False
        self.gamma = np.ones((1, output_size))
        self.beta = np.zeros((1, output_size))
        self.bn_mean = np.zeros((1, output_size))
        self.bn_var = np.ones((1, output_size))
        self.running_mean = np.zeros((1, output_size))
        self.running_var = np.ones((1, output_size))
        self.bn_momentum = 0.9

        # Gradyanlar
        self.dW = None
        self.db = None
        self.dgamma = None
        self.dbeta = None

        # Forward geçiş önbelleği
        self.cache = {}

    def enable_batch_norm(self):
        self.use_bn = True
        return self

    def _batch_norm_forward(self, z):
        if self.training:
            mean = np.mean(z, axis=0, keepdims=True)
            var = np.var(z, axis=0, keepdims=True)
            self.bn_mean = mean
            self.bn_var = var
            # Running istatistikleri güncelle
            self.running_mean = self.bn_momentum * self.running_mean + (1 - self.bn_momentum) * mean
            self.running_var = self.bn_momentum * self.running_var + (1 - self.bn_momentum) * var
        else:
            mean = self.running_mean
            var = self.running_var

        z_norm = (z - mean) / np.sqrt(var + 1e-8)
        return self.gamma * z_norm + self.beta, z_norm

    def _batch_norm_backward(self, dout, z_norm, z):
        N = dout.shape[0]
        self.dgamma = np.sum(dout * z_norm, axis=0, keepdims=True)
        self.dbeta = np.sum(dout, axis=0, keepdims=True)

        dz_norm = dout * self.gamma
        dvar = np.sum(dz_norm * (z - self.bn_mean) * -0.5 *
                      (self.bn_var + 1e-8) ** (-1.5), axis=0, keepdims=True)
        dmean = np.sum(dz_norm * -1 / np.sqrt(self.bn_var + 1e-8), axis=0, keepdims=True)
        dz = (dz_norm / np.sqrt(self.bn_var + 1e-8) +
              dvar * 2 * (z - self.bn_mean) / N +
              dmean / N)
        return dz

    def forward(self, x):
        self.cache['x'] = x
        z = x @ self.W + self.b
        self.cache['z_pre_bn'] = z

        if self.use_bn:
            z, z_norm = self._batch_norm_forward(z)
            self.cache['z_norm'] = z_norm

        self.cache['z'] = z

        # Dropout (sadece eğitimde)
        if self.dropout_rate > 0 and self.training:
            mask = (np.random.rand(*z.shape) > self.dropout_rate) / (1 - self.dropout_rate)
            self.cache['dropout_mask'] = mask
            z = z * mask
        else:
            self.cache['dropout_mask'] = None

        # Aktivasyon uygula
        if self.activation_name == 'relu':
            out = relu(z)
        elif self.activation_name == 'sigmoid':
            out = sigmoid(z)
        elif self.activation_name == 'softmax':
            out = softmax(z)
        elif self.activation_name == 'linear':
            out = z
        else:
            out = relu(z)

        self.cache['out'] = out
        return out

    def backward(self, dout):
        x = self.cache['x']
        z = self.cache['z']
        out = self.cache['out']
        mask = self.cache.get('dropout_mask')

        # Dropout geri yayılım
        if mask is not None:
            dout = dout * mask

        # Aktivasyon türevi
        if self.activation_name == 'relu':
            dz = dout * relu_derivative(z)
        elif self.activation_name == 'sigmoid':
            dz = dout * sigmoid_derivative(z)
        elif self.activation_name == 'softmax':
            # Softmax + CrossEntropy birleşik türev (önceden hesaplandı)
            dz = dout
        elif self.activation_name == 'linear':
            dz = dout
        else:
            dz = dout * relu_derivative(z)

        # Batch norm geri yayılım
        if self.use_bn:
            z_norm = self.cache['z_norm']
            z_pre = self.cache['z_pre_bn']
            dz = self._batch_norm_backward(dz, z_norm, z_pre)

        # Ağırlık gradyanları
        self.dW = x.T @ dz
        self.db = np.sum(dz, axis=0, keepdims=True)

        # Önceki katmana geçecek gradyan
        dx = dz @ self.W.T
        return dx


class NeuralNetwork:
    """
    Tamamen Sıfırdan Yazılmış Derin Sinir Ağı
    - İleri Yayılım (Forward Propagation)
    - Geri Yayılım (Backpropagation)
    - Adam Optimizer
    - Batch Normalization
    - Dropout Regularization
    """

    def __init__(self, layer_sizes, activations, dropout_rates=None, learning_rate=0.001):
        """
        layer_sizes: [input, hidden1, hidden2, ..., output]
        activations: ['relu', 'relu', ..., 'softmax']
        """
        self.layers = []
        self.optimizer = Adam(learning_rate=learning_rate)
        self.param_counter = 0

        if dropout_rates is None:
            dropout_rates = [0.0] * (len(layer_sizes) - 1)

        for i in range(len(layer_sizes) - 1):
            layer = Layer(
                input_size=layer_sizes[i],
                output_size=layer_sizes[i + 1],
                activation=activations[i],
                dropout_rate=dropout_rates[i]
            )
            # Ara katmanlara BN ekle
            if activations[i] == 'relu' and i < len(layer_sizes) - 2:
                layer.enable_batch_norm()
            self.layers.append(layer)

        print(f"[AI] Sinir ağı oluşturuldu: {layer_sizes}")
        total_params = sum(
            l.W.size + l.b.size for l in self.layers
        )
        print(f"[AI] Toplam parametre sayısı: {total_params:,}")

    def set_training(self, mode):
        for layer in self.layers:
            layer.training = mode

    def forward(self, x):
        if x.ndim == 1:
            x = x.reshape(1, -1)
        out = x
        for layer in self.layers:
            out = layer.forward(out)
        return out

    def backward(self, loss_grad):
        grad = loss_grad
        for layer in reversed(self.layers):
            grad = layer.backward(grad)

    def update_params(self):
        """Adam ile tüm parametreleri güncelle"""
        for i, layer in enumerate(self.layers):
            layer.W = self.optimizer.update(f"W_{i}", layer.W, layer.dW)
            layer.b = self.optimizer.update(f"b_{i}", layer.b, layer.db)
            if layer.use_bn:
                layer.gamma = self.optimizer.update(f"gamma_{i}", layer.gamma, layer.dgamma)
                layer.beta = self.optimizer.update(f"beta_{i}", layer.beta, layer.dbeta)

    def predict(self, x):
        self.set_training(False)
        out = self.forward(x)
        self.set_training(True)
        return out

    def save_weights(self, filepath):
        weights = []
        for layer in self.layers:
            w_dict = {
                'W': layer.W,
                'b': layer.b,
                'gamma': layer.gamma,
                'beta': layer.beta,
                'running_mean': layer.running_mean,
                'running_var': layer.running_var,
            }
            weights.append(w_dict)
        np.save(filepath, weights, allow_pickle=True)
        print(f"[AI] Ağırlıklar kaydedildi: {filepath}")

    def load_weights(self, filepath):
        weights = np.load(filepath, allow_pickle=True)
        for i, w_dict in enumerate(weights):
            self.layers[i].W = w_dict['W']
            self.layers[i].b = w_dict['b']
            self.layers[i].gamma = w_dict['gamma']
            self.layers[i].beta = w_dict['beta']
            self.layers[i].running_mean = w_dict['running_mean']
            self.layers[i].running_var = w_dict['running_var']
        print(f"[AI] Ağırlıklar yüklendi: {filepath}")
