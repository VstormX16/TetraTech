const normalizeBaseUrl = (value, fallback) => {
  const raw = (value || fallback || '').trim();
  if (!raw) {
    return '';
  }

  return raw.endsWith('/') ? raw.slice(0, -1) : raw;
};

const joinUrl = (base, path = '') => {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  if (!base) {
    return normalizedPath;
  }

  return `${base}${normalizedPath}`;
};

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL, '/api');
export const SIM_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_SIM_BASE_URL, '/sim');
export const USER_MODEL_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_USER_MODEL_BASE_URL, '/user-models');

export const apiUrl = (path) => joinUrl(API_BASE_URL, path);
export const simUrl = (path) => joinUrl(SIM_BASE_URL, path);
export const userModelUrl = (fileName) => joinUrl(USER_MODEL_BASE_URL, fileName);

export const getRocketModelUrl = (rocket) => {
  if (!rocket?.filename) {
    return null;
  }

  if (rocket.modelPath) {
    return rocket.modelPath;
  }

  return rocket.isCustom ? userModelUrl(rocket.filename) : `/models/${rocket.filename}`;
};
