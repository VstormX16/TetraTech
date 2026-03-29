// === Fizik Sabitleri ===
export const G_SEA = 9.80665;
export const R_EARTH = 6371000;
export const RHO_SEA = 1.225;
export const DT = 1 / 240;

// === Yardımcı Fonksiyonlar ===
export const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
export const fmt = (n, d = 2) => Number(n).toFixed(d);
export const lerp = (a, b, t) => a + (b - a) * t;

// === Yerçekimi (Somigliana + ters kare) ===
export const gravityAt = (h) => G_SEA * Math.pow(R_EARTH / (R_EARTH + Math.max(0, h)), 2);

// === Hava Yoğunluğu (üstel azalma yaklaşımı) ===
export const airDensityAt = (h) => RHO_SEA * Math.exp(-Math.max(0, h) / 8500);

// === Atmosfer Katmanı ===
export const getAtmosphereLayer = (alt) => {
  if (alt > 100000) return 'UZAY';
  if (alt > 85000) return 'TERMOSFER';
  if (alt > 50000) return 'MEZOSFER';
  if (alt > 12000) return 'STRATOSFER';
  return 'TROPOSFER';
};

// === Partikül Sistemi ===
export class Particle {
  constructor(x, y, vx, vy, life, size, type) {
    this.x = x;
    this.y = y;
    this.vx = vx;
    this.vy = vy;
    this.life = life;
    this.maxLife = life;
    this.size = size;
    this.type = type;
  }
  update(dt) {
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.life -= dt;
    this.size *= 0.94;
  }
}
