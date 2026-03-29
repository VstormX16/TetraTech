import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSimStore } from '../store';
import { Zap, ShieldAlert, Orbit, Thermometer } from 'lucide-react';
import { clamp, fmt, gravityAt, airDensityAt, G_SEA } from '../utils/physics';

const FADE_UP = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', damping: 22, stiffness: 120 } }
};
const STAGGER = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.15 } }
};

// ─── Telemetri Metrik Kartı ───
const MetricCard = ({ label, value, unit, isHero }) => (
  <motion.div
    variants={FADE_UP}
    className="glass-panel-light border-white/[0.05] rounded-xl px-4 py-3 min-w-[100px] flex flex-col justify-end relative overflow-hidden hover:bg-white/[0.03] transition-colors"
  >
    <span className="text-[8px] font-black tracking-[0.15em] text-white/35 uppercase mb-1.5 antialiased">{label}</span>
    <div className="flex items-baseline gap-1">
      <span className={`data-value font-black leading-none antialiased ${isHero ? 'text-[var(--color-plasma-blue)] text-3xl tracking-tighter' : 'text-white text-xl'}`}>
        {value}
      </span>
      <span className="data-value text-white/40 text-[9px] font-bold">{unit}</span>
    </div>
  </motion.div>
);

// ═══════════════════════ TELEMETRY OVERLAY ═══════════════════════
export function TelemetryOverlay() {
  const { metrics, params } = useSimStore();

  return (
    <motion.div
      variants={STAGGER}
      initial="hidden"
      animate="show"
      className="absolute top-0 left-0 right-0 p-5 z-20 pointer-events-none antialiased"
    >
      <div className="flex flex-wrap gap-3 mb-4">
        <MetricCard
          label="İRTİFA"
          value={metrics.alt > 1000 ? fmt(metrics.alt / 1000, 2) : fmt(metrics.alt, 0)}
          unit={metrics.alt > 1000 ? 'KM' : 'M'}
          isHero
        />
        <MetricCard
          label="HIZ"
          value={fmt(Math.sqrt(metrics.velY ** 2 + (metrics.velX || 0) ** 2), 0)}
          unit="M/S"
        />
        <MetricCard
          label="MACH"
          value={fmt(metrics.mach || 0, 2)}
          unit=""
        />
        <MetricCard
          label="G-KUVVETİ"
          value={fmt(metrics.accY / G_SEA, 2)}
          unit="G"
        />
        <MetricCard
          label="SAPMA"
          value={metrics.xDist > 100 ? fmt(metrics.xDist / 1000, 2) : fmt(metrics.xDist, 1)}
          unit={metrics.xDist > 100 ? 'KM' : 'M'}
        />
        <MetricCard label="T+" value={fmt(metrics.t, 1)} unit="S" />
      </div>

      {/* Yakıt barı */}
      <motion.div
        variants={FADE_UP}
        className="glass-panel-light rounded-xl p-4 w-56 pointer-events-auto border-white/[0.05] antialiased"
      >
        <div className="flex justify-between items-center mb-2.5">
          <span className="text-[9px] font-black tracking-[0.15em] text-[var(--color-plasma-blue)] uppercase flex items-center gap-1.5">
            <Zap size={12} className="animate-pulse" /> YAKIT
          </span>
          <span className="font-mono text-lg font-black">
            {fmt(metrics.fuel, 1)} <span className="text-[10px] text-white/35">KG</span>
          </span>
        </div>
        <div className="h-1.5 w-full bg-black/50 rounded-full overflow-hidden border border-white/[0.04]">
          <div
            className="h-full bg-gradient-to-r from-[var(--color-plasma-blue)] to-white/80 transition-all duration-75 rounded-full"
            style={{ width: `${clamp((metrics.fuel / params.fuelMass) * 100, 0, 100)}%` }}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}

// ═══════════════════════ ENVIRONMENT HUD ═══════════════════════
export function EnvironmentHud() {
  const { metrics } = useSimStore();

  return (
    <div className="absolute top-5 right-5 z-20 pointer-events-none flex flex-col gap-3 items-end antialiased">
      {/* Kármán Çizgisi Uyarısı */}
      <AnimatePresence>
        {metrics.alt > 100000 && (
          <motion.div
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 40, opacity: 0 }}
            className="glass-panel border-[#00FFF0]/40 bg-[#00FFF0]/10 px-6 py-3 rounded-full flex items-center gap-3 shadow-[0_0_25px_rgba(0,255,240,0.15)]"
          >
            <Orbit className="text-[#00F0FF] animate-spin" style={{ animationDuration: '4s' }} size={16} />
            <span className="text-[#00F0FF] font-black text-[11px] tracking-[0.2em] uppercase">KÁRMÁN ÇİZGİSİ — UZAY</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Max-Q Uyarısı */}
      <AnimatePresence>
        {metrics.q > 10000 && (
          <motion.div
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 40, opacity: 0 }}
            className="glass-panel border-[var(--color-thrust-orange)]/40 bg-[var(--color-thrust-orange)]/10 px-6 py-3 rounded-full flex items-center gap-3 shadow-[0_0_25px_rgba(255,107,44,0.15)]"
          >
            <ShieldAlert className="text-[var(--color-thrust-orange)] animate-pulse" size={16} />
            <span className="text-[var(--color-thrust-orange)] font-black text-[11px] tracking-[0.2em] uppercase">MAX-Q</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Çevre Bilgi Paneli */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="glass-panel-light p-5 rounded-2xl border-white/[0.06] w-64 mt-2 antialiased flex flex-col gap-1.5"
      >
        <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
          <span className="text-[9px] uppercase font-black text-white/30 tracking-[0.15em]">KATMAN</span>
          <span className="text-[var(--color-success-green)] font-mono text-[12px] font-black tracking-widest uppercase">{metrics.layer}</span>
        </div>
        <div className="flex items-center justify-between py-1.5">
          <span className="text-[9px] uppercase font-black text-white/30 tracking-[0.15em]">DİN. BASINÇ</span>
          <span className="text-white font-mono text-sm font-bold">
            {fmt(metrics.q / 1000, 2)} <span className="text-[9px] text-white/30">kPa</span>
          </span>
        </div>
        <div className="flex items-center justify-between py-1.5">
          <span className="text-[9px] uppercase font-black text-white/30 tracking-[0.15em]">YERÇEKİMİ</span>
          <span className="text-white font-mono text-sm font-bold">
            {fmt(gravityAt(metrics.alt), 3)} <span className="text-[9px] text-white/30">m/s²</span>
          </span>
        </div>
        <div className="flex items-center justify-between py-1.5">
          <span className="text-[9px] uppercase font-black text-white/30 tracking-[0.15em]">HAVA YOĞUNLUĞU</span>
          <span className="text-white font-mono text-sm font-bold">
            {fmt(airDensityAt(metrics.alt), 4)} <span className="text-[9px] text-white/30">kg/m³</span>
          </span>
        </div>
      </motion.div>
    </div>
  );
}

// ═══════════════════════ LIVE LOG CONSOLE ═══════════════════════
export function LiveLogConsole() {
  const logs = useSimStore((s) => s.logs);

  return (
    <div
      className="absolute bottom-5 left-5 w-80 max-h-[200px] pointer-events-none flex flex-col-reverse justify-start gap-1.5 z-20 antialiased overflow-hidden mask-fade-top"
    >
      <AnimatePresence>
        {logs.map((log) => (
          <motion.div
            key={log.id}
            initial={{ opacity: 0, x: -15, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="glass-panel-light p-2.5 rounded-lg border-l-2 border-[var(--color-plasma-blue)]/60 bg-black/40 flex gap-2.5 items-start"
          >
            <span className="font-mono text-[var(--color-plasma-blue)] text-[9px] whitespace-nowrap opacity-70 mt-0.5">
              T+{fmt(log.time, 1)}s
            </span>
            <p className="font-mono text-[10px] text-white/70 leading-relaxed">{log.msg}</p>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
