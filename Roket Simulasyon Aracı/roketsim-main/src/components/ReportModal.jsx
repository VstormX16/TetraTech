import React, { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSimStore } from '../store';
import { DownloadCloud, RotateCcw, Rocket } from 'lucide-react';
import { fmt } from '../utils/physics';

const MagneticButton = ({ children, onClick, className }) => {
  const ref = useRef(null);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const handleMouse = (e) => {
    const { height, width, left, top } = ref.current.getBoundingClientRect();
    setPos({
      x: (e.clientX - (left + width / 2)) * 0.12,
      y: (e.clientY - (top + height / 2)) * 0.12
    });
  };
  return (
    <motion.button
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={() => setPos({ x: 0, y: 0 })}
      animate={{ x: pos.x, y: pos.y }}
      transition={{ type: 'spring', stiffness: 150, damping: 15, mass: 0.1 }}
      onClick={onClick}
      className={className}
      whileTap={{ scale: 0.96 }}
    >
      {children}
    </motion.button>
  );
};

export default function ReportModal() {
  const { phase, metrics, params, resetSim } = useSimStore();
  const [hashId] = useState(() => `#${(Math.random() * 100000 | 0).toString(16).toUpperCase()}-SBY`);

  const totalMass = params.dryMass + params.fuelMass + params.payloadMass;
  const refArea = Math.PI * Math.pow(params.diameter / 2, 2);

  const generatePDF = () => {
    window.print();
  };

  return (
    <AnimatePresence>
      {phase === 'TOUCHDOWN' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          className="fixed inset-0 z-[100] bg-[#010205]/95 backdrop-blur-[50px] flex items-center justify-center overflow-y-auto overflow-x-hidden w-full h-full antialiased no-print-bg p-8"
        >
          <motion.div
            id="awwwards-report"
            initial={{ scale: 0.93, y: 40 }}
            animate={{ scale: 1, y: 0 }}
            transition={{ type: 'spring', damping: 22 }}
            className="bg-[var(--color-space-800)] border border-white/[0.06] rounded-[2.5rem] p-12 max-w-5xl w-full shadow-[0_0_80px_rgba(0,0,0,0.9)] relative print-modal"
          >
            {/* Grid overlay */}
            <div className="absolute inset-0 opacity-[0.02] pointer-events-none rounded-[2.5rem]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '3rem 3rem' }} />

            {/* Header */}
            <div className="flex justify-between items-end border-b border-white/[0.06] pb-10 mb-12 relative z-10">
              <div>
                <div className="inline-flex items-center gap-3 px-5 py-2 rounded-full bg-[var(--color-plasma-blue-dim)] border border-[var(--color-plasma-blue)]/15 mb-6 no-print">
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-plasma-blue)] animate-pulse" />
                  <span className="text-[10px] font-black uppercase tracking-[0.25em] text-[var(--color-plasma-blue)]">Görev Tamamlandı</span>
                </div>
                <h2 className="text-6xl font-black tracking-tighter text-white mb-2 leading-none">
                  UÇUŞ <br />
                  <span className="text-[var(--color-plasma-blue)]">RAPORU_</span>
                </h2>
              </div>
              <div className="text-right">
                <p className="text-base font-mono text-white/40 mb-2">{hashId}</p>
                <p className="text-sm font-black tracking-[0.3em] text-white/70">SKYBOUNDARY</p>
              </div>
            </div>

            {/* Data Grid */}
            <div className="grid grid-cols-2 gap-12 relative z-10 mb-12">
              {/* Kinematik */}
              <div className="bg-black/30 p-10 rounded-[2rem] border border-white/[0.04] space-y-8">
                <h4 className="text-[12px] uppercase font-black tracking-[0.3em] text-[var(--color-plasma-blue)] border-b border-[var(--color-plasma-blue)]/15 pb-4">
                  Kinematik Veriler
                </h4>
                <ReportRow label="MAKSİMUM İRTİFA" value={metrics.maxAlt > 1000 ? fmt(metrics.maxAlt / 1000, 2) : fmt(metrics.maxAlt, 1)} unit={metrics.maxAlt > 1000 ? 'km' : 'm'} />
                <ReportRow label="MAKSİMUM HIZ" value={fmt(metrics.maxVel, 1)} unit="m/s" />
                <ReportRow label="MAKSİMUM MACH" value={fmt(metrics.mach, 2)} unit="" />
                <ReportRow label="TOPLAM UÇUŞ SÜRESİ" value={fmt(metrics.t, 1)} unit="s" />
                <ReportRow label="MAKSİMUM DİN. BASINÇ" value={fmt((metrics.maxQ || 0) / 1000, 2)} unit="kPa" />
              </div>

              {/* Parametreler */}
              <div className="bg-black/30 p-10 rounded-[2rem] border border-white/[0.04] space-y-8">
                <h4 className="text-[12px] uppercase font-black tracking-[0.3em] text-[var(--color-plasma-blue)] border-b border-[var(--color-plasma-blue)]/15 pb-4">
                  Roket Parametreleri
                </h4>
                <ReportRow label="TOPLAM KÜTLE" value={fmt(totalMass, 1)} unit="kg" />
                <ReportRow label="YAKIT KÜTLESİ" value={fmt(params.fuelMass, 1)} unit="kg" />
                <ReportRow label="MOTOR İTKİSİ" value={fmt(params.thrust, 0)} unit="N" />
                <ReportRow label="YANMA SÜRESİ" value={fmt(params.burnTime, 1)} unit="s" />
                <ReportRow label="RÜZGAR SAPMASI" value={fmt(metrics.xDist, 1)} unit="m" />
                <ReportRow label="SÜR. KATSAYISI (Cd)" value={fmt(params.cd, 2)} unit="" />
                <ReportRow label="KESİT ALANI" value={refArea.toFixed(6)} unit="m²" />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-6 relative z-10 no-print">
              <MagneticButton
                onClick={generatePDF}
                className="flex-1 py-6 rounded-2xl bg-white text-black font-black text-sm tracking-[0.3em] flex items-center justify-center gap-4 hover:bg-[var(--color-plasma-blue)] hover:text-white transition-all shadow-2xl"
              >
                <DownloadCloud size={20} /> RAPORU İNDİR
              </MagneticButton>
              <MagneticButton
                onClick={resetSim}
                className="px-12 py-6 rounded-2xl glass-panel text-white font-black text-sm tracking-[0.3em] flex items-center justify-center gap-4 hover:border-white/15 transition-all shadow-2xl"
              >
                <RotateCcw size={20} /> YENİ UÇUŞ
              </MagneticButton>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ─── Report Row Component ───
function ReportRow({ label, value, unit }) {
  return (
    <div className="flex justify-between items-end group">
      <span className="text-sm font-bold text-white/40 tracking-wider">{label}</span>
      <span className="font-mono text-3xl font-black text-white group-hover:text-[var(--color-plasma-blue)] transition-colors">
        {value}
        {unit && <span className="text-lg opacity-35 ml-1.5">{unit}</span>}
      </span>
    </div>
  );
}
