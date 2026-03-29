import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSimStore } from '../store';
import { Rocket, AlertTriangle, Plus, Trash2, Layers, Package, Wind } from 'lucide-react';

export default function Sidebar() {
  const { params, updateParam, updateParts, initiateLaunch, running } = useSimStore();
  
  // Create an editable deep copy of parts
  const [localParts, setLocalParts] = useState(
    params.parts.map(p => ({
      ...p,
      dryMass: p.dryMass.toString(),
      fuelMass: (p.fuelMass || 0).toString(),
      thrust: (p.thrust || 0).toString(),
      burnTime: (p.burnTime || 0).toString(),
      sepAlt: (p.sepAlt || 0).toString(),
      cd: p.cd.toString(),
      diameter: p.diameter.toString(),
    }))
  );

  const [wind, setWind] = useState(params.windSpeed.toString());
  const [errors, setErrors] = useState({});

  const validateAll = () => {
    let isValid = true;
    const currentErrors = {};
    const parsedParts = [];
    
    // Wind validation
    if (isNaN(Number(wind)) || Number(wind) < 0) {
      currentErrors['global_wind'] = "Rüzgar negatif veya tanımsız olamaz!";
      isValid = false;
    }

    localParts.forEach((p, idx) => {
      const parsed = { ...p };
      const fields = p.type === 'motor' ? ['name', 'dryMass', 'fuelMass', 'thrust', 'burnTime', 'sepAlt', 'cd', 'diameter'] 
                                        : ['name', 'dryMass', 'cd', 'diameter'];
      
      fields.forEach(f => {
        const val = p[f];
        if (f !== 'name') {
           if (val === undefined || val === null || val.trim() === '') {
             currentErrors[`${p.id}_${f}`] = "Boş bırakılamaz!";
             isValid = false;
           } else if (isNaN(Number(val))) {
             currentErrors[`${p.id}_${f}`] = "Sayı olmalı!";
             isValid = false;
           } else if (Number(val) < 0) {
             currentErrors[`${p.id}_${f}`] = "Negatif olmaz!";
             isValid = false;
           } else {
             parsed[f] = Number(val);
           }
        } else {
           if (!val || val.trim() === '') {
             currentErrors[`${p.id}_${f}`] = "İsim boş olamaz!";
             isValid = false;
           }
        }
      });
      parsedParts.push(parsed);
    });

    setErrors(currentErrors);
    return { isValid, parsedParts };
  };

  const handleStartSimulation = () => {
    if (running) return;
    const { isValid, parsedParts } = validateAll();
    
    if (isValid) {
      updateParts(parsedParts);
      updateParam('windSpeed', Number(wind));
      
      console.log("=========================================");
      console.log("KADEMELER & FAYDALI YÜKLER SÖZLÜĞÜ (JSON)");
      console.log("=========================================");
      console.table(parsedParts);

      initiateLaunch();
    }
  };

  const addPart = (type) => {
    const newId = 'p' + Math.random().toString(36).substr(2, 5);
    const newPart = type === 'motor' 
      ? { id: newId, type: 'motor', name: `${localParts.length + 1}. Kademe`, dryMass: '50', fuelMass: '150', thrust: '3000', burnTime: '12', sepAlt: '2000', cd: '0.45', diameter: '0.15' }
      : { id: newId, type: 'payload', name: 'Yeni Faydalı Yük', dryMass: '10', cd: '0.3', diameter: '0.15' };

    setLocalParts(prev => {
      if (type === 'payload') return [...prev, newPart];
      // Eğer motorsa, listedeki tüm motorları al, sonra yeni motoru ekle, sonra yukleri ekle
      const payloads = prev.filter(p => p.type === 'payload');
      const motors = prev.filter(p => p.type === 'motor');
      return [...motors, newPart, ...payloads];
    });
  };

  const removePart = (id) => {
    setLocalParts(localParts.filter(p => p.id !== id));
  };

  const handleChange = (id, field, value) => {
    const sanitized = field !== 'name' ? value.replace(',', '.') : value;
    setLocalParts(localParts.map(p => p.id === id ? { ...p, [field]: sanitized } : p));
    if (errors[`${id}_${field}`]) {
      setErrors(prev => ({ ...prev, [`${id}_${field}`]: null }));
    }
  };

  const InputRow = ({ id, label, field, unit, placeholder, value }) => (
    <div className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <label className="text-[11px] font-bold text-white/70">{label}</label>
        <span className="text-[9px] text-[var(--color-plasma-blue)] bg-[var(--color-plasma-blue)]/10 px-1.5 py-0.5 rounded border border-[var(--color-plasma-blue)]/20">{unit}</span>
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => handleChange(id, field, e.target.value)}
        placeholder={placeholder}
        className={`w-full bg-black/40 border ${errors[`${id}_${field}`] ? 'border-red-500' : 'border-white/10'} rounded-lg px-2 py-2 text-white text-[12px] font-mono focus:outline-none focus:border-[var(--color-plasma-blue)] transition-colors`}
      />
      {errors[`${id}_${field}`] && (
        <span className="text-red-400 text-[9px] flex items-center gap-1 mt-1 font-bold">
          <AlertTriangle size={10} /> {errors[`${id}_${field}`] && errors[`${id}_${field}`].substring ? errors[`${id}_${field}`].substring(0, 15) : errors[`${id}_${field}`]}
        </span>
      )}
    </div>
  );

  return (
    <div className="w-[440px] min-w-[440px] bg-[var(--color-space-900)]/95 backdrop-blur-[50px] border-l border-white/[0.06] z-30 flex flex-col h-full relative">
      <div className="px-7 pt-7 pb-5 flex items-center gap-4 shrink-0 border-b border-white/[0.04]">
        <div className="w-11 h-11 rounded-xl bg-[var(--color-plasma-blue)]/10 border border-[var(--color-plasma-blue)]/25 flex items-center justify-center">
          <Layers className="text-[var(--color-plasma-blue)] w-5 h-5" />
        </div>
        <div>
          <h1 className="text-lg font-black text-white leading-tight">ROKET MİMARİSİ</h1>
          <p className="text-[9px] uppercase text-[var(--color-plasma-blue)]/70 tracking-widest mt-0.5">
            Çok Kademeli Uçuş & Balistik Ayrılma
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-7 py-6 custom-scrollbar">
        {/* Çevre Koşulu */}
        <div className="mb-6 bg-[var(--color-thrust-orange)]/5 p-4 rounded-xl border border-[var(--color-thrust-orange)]/10">
          <div className="flex items-center gap-2 mb-3">
             <Wind size={14} className="text-[var(--color-thrust-orange)]" />
             <h3 className="text-xs uppercase tracking-widest text-white/90 font-bold">Çevre Koşulları</h3>
          </div>
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[11px] font-bold text-white/70">Rüzgar Hızı</label>
              <span className="text-[9px] text-[var(--color-thrust-orange)] bg-[var(--color-thrust-orange)]/10 px-1.5 py-0.5 rounded border border-[var(--color-thrust-orange)]/20">m/s</span>
            </div>
            <input
              type="text"
              value={wind}
              onChange={(e) => { setWind(e.target.value); setErrors({...errors, global_wind: null}); }}
              className={`w-full bg-black/40 border ${errors['global_wind'] ? 'border-red-500' : 'border-white/10'} rounded-lg px-3 py-2 text-white text-[12px] font-mono`}
            />
            {errors['global_wind'] && <span className="text-red-400 text-[9px] flex items-center gap-1 mt-1 font-bold"><AlertTriangle size={10} /> {errors['global_wind']}</span>}
          </div>
        </div>

        <AnimatePresence>
          {localParts.map((part, index) => (
            <motion.div 
              key={part.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`mb-5 p-4 rounded-xl border relative shadow-lg ${part.type === 'motor' ? 'bg-black/20 border-white/10' : 'bg-[var(--color-plasma-blue)]/5 border-[var(--color-plasma-blue)]/20'}`}
            >
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
                <div className="flex items-center gap-2">
                  {part.type === 'motor' ? <Rocket size={16} className="text-[var(--color-thrust-orange)]" /> : <Package size={16} className="text-[var(--color-plasma-blue)]" />}
                  <input
                    type="text"
                    value={part.name}
                    onChange={(e) => handleChange(part.id, 'name', e.target.value)}
                    className="bg-transparent text-sm font-black text-white outline-none w-32 border-b border-transparent focus:border-white/20 transition-all"
                  />
                  {errors[`${part.id}_name`] && <AlertTriangle size={12} className="text-red-400" />}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] text-white/40 uppercase tracking-widest">{index === 0 ? 'İLK ATEŞLEME' : (part.type === 'payload' ? 'YÜK' : 'ÜST KADEME')}</span>
                  {localParts.length > 1 && (
                    <button onClick={() => removePart(part.id)} className="text-white/20 hover:text-red-500 transition-colors bg-black/40 p-1.5 rounded-md">
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              </div>

              {part.type === 'motor' ? (
                <>
                  <div className="grid grid-cols-2 gap-3" style={{gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)'}}>
                    <InputRow id={part.id} label="Kuru Kütle" field="dryMass" unit="kg" value={part.dryMass} />
                    <InputRow id={part.id} label="Yakıt Kütlesi" field="fuelMass" unit="kg" value={part.fuelMass} />
                    <InputRow id={part.id} label="Motor İtkisi" field="thrust" unit="N" value={part.thrust} />
                    <InputRow id={part.id} label="Yanma Süresi" field="burnTime" unit="s" value={part.burnTime} />
                    <InputRow id={part.id} label="Ayrılma İrtifası" field="sepAlt" unit="m" value={part.sepAlt} />
                    <InputRow id={part.id} label="Sür. Katsayısı" field="cd" unit="Cd" value={part.cd} />
                    <InputRow id={part.id} label="Çap" field="diameter" unit="m" value={part.diameter} />
                  </div>
                </>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <InputRow id={part.id} label="Görev Yükü (Kütle)" field="dryMass" unit="kg" value={part.dryMass} />
                    <InputRow id={part.id} label="Sür. Katsayısı" field="cd" unit="Cd" value={part.cd} />
                    <InputRow id={part.id} label="Çap" field="diameter" unit="m" value={part.diameter} />
                  </div>
                </>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        <div className="flex gap-2">
          <button onClick={() => addPart('motor')} className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white/70 text-[10px] uppercase font-black tracking-widest transition-all hover:text-white border border-white/5">
            <Plus size={12} /> Motor Kademe Ekle
          </button>
          <button onClick={() => addPart('payload')} className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-[var(--color-plasma-blue)]/5 hover:bg-[var(--color-plasma-blue)]/15 border border-[var(--color-plasma-blue)]/10 text-[var(--color-plasma-blue)] text-[10px] uppercase font-black tracking-widest transition-all">
            <Plus size={12} /> Faydalı Yük Ekle
          </button>
        </div>
      </div>

      <div className="px-7 py-6 bg-[var(--color-space-900)] border-t border-white/[0.04] shrink-0">
        <button
          onClick={handleStartSimulation}
          disabled={running}
          className={`w-full text-black font-black text-sm tracking-[0.15em] py-5 rounded-2xl transition-all flex items-center justify-center gap-3 ${running ? 'bg-white/20 opacity-50 cursor-not-allowed' : 'bg-gradient-to-r from-[var(--color-plasma-blue)] to-[#0099ff] hover:from-[#00e5ff] hover:to-[#0088ff] shadow-[0_4px_20px_var(--color-plasma-blue-dim)] hover:shadow-[0_4px_30px_rgba(0,240,255,0.4)] hover:scale-[1.01] active:scale-[0.98]'}`}
        >
          <Rocket size={18} />
          {running ? 'HESAPLANIYOR...' : 'AYRILMALI UÇUŞU BAŞLAT'}
        </button>
      </div>
    </div>
  );
}
