"""
Kayıp Fonksiyonları - Sıfırdan yazılmış
"""
import numpy as np


def mse_loss(y_pred, y_true):
    """Mean Squared Error"""
    return np.mean((y_pred - y_true) ** 2)


def mse_derivative(y_pred, y_true):
    return 2 * (y_pred - y_true) / y_true.size


def cross_entropy_loss(y_pred, y_true):
    """Kategorik Cross Entropy (softmax çıktısı için)"""
    eps = 1e-12
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(np.sum(y_true * np.log(y_pred), axis=-1))


def cross_entropy_derivative(y_pred, y_true):
    """Softmax + Cross Entropy birleşik türev"""
    return y_pred - y_true


def binary_cross_entropy(y_pred, y_true):
    eps = 1e-12
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
