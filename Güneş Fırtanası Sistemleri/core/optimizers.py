"""
Adam ve SGD Optimizer - Sıfırdan yazılmış
"""
import numpy as np


class SGD:
    """Stochastic Gradient Descent + Momentum"""

    def __init__(self, learning_rate=0.01, momentum=0.9):
        self.lr = learning_rate
        self.momentum = momentum
        self.velocity = {}

    def update(self, param_id, param, grad):
        if param_id not in self.velocity:
            self.velocity[param_id] = np.zeros_like(param)
        v = self.velocity[param_id]
        v = self.momentum * v - self.lr * grad
        self.velocity[param_id] = v
        return param + v


class Adam:
    """Adam Optimizer - Adaptive Moment Estimation"""

    def __init__(self, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8):
        self.lr = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.m = {}  # 1. moment (momentum)
        self.v = {}  # 2. moment (RMSprop)
        self.t = 0   # adım sayısı

    def update(self, param_id, param, grad):
        self.t += 1

        if param_id not in self.m:
            self.m[param_id] = np.zeros_like(grad)
            self.v[param_id] = np.zeros_like(grad)

        # Momentleri güncelle
        self.m[param_id] = self.beta1 * self.m[param_id] + (1 - self.beta1) * grad
        self.v[param_id] = self.beta2 * self.v[param_id] + (1 - self.beta2) * (grad ** 2)

        # Bias düzeltmesi
        m_hat = self.m[param_id] / (1 - self.beta1 ** self.t)
        v_hat = self.v[param_id] / (1 - self.beta2 ** self.t)

        # Parametre güncelleme
        return param - self.lr * m_hat / (np.sqrt(v_hat) + self.epsilon)
