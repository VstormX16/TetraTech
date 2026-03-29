import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRocketSimStore } from './rocketSimStore';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import WarningIcon from '@mui/icons-material/Warning';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import AirIcon from '@mui/icons-material/Air';
import LayersIcon from '@mui/icons-material/Layers';
import InventoryIcon from '@mui/icons-material/Inventory';
import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing';

const PRESET_ROCKETS = {
  custom: { name: 'Özel Tasarım (Custom)', parts: [] },
  falcon_9: {
    name: 'SpaceX Falcon 9 (Block 5)',
    parts: [
      { id: 'f9_s1', type: 'motor', name: '1. Kademe (Booster)', dryMass: '25600', fuelMass: '395700', thrust: '7607000', burnTime: '162', sepAlt: '65000', cd: '0.4', diameter: '3.7' },
      { id: 'f9_s2', type: 'motor', name: '2. Kademe', dryMass: '3900', fuelMass: '92670', thrust: '981000', burnTime: '397', sepAlt: '200000', cd: '0.3', diameter: '3.7' },
      { id: 'f9_pay', type: 'payload', name: 'Burun (Fairing + Yük)', dryMass: '22800', cd: '0.2', diameter: '5.2', noTumble: true }
    ]
  },
  saturn_v: {
    name: 'NASA Saturn V (Apollo)',
    parts: [
      { id: 'sv_s1', type: 'motor', name: 'S-IC (1. Kademe)', dryMass: '130000', fuelMass: '2160000', thrust: '35000000', burnTime: '168', sepAlt: '67000', cd: '0.5', diameter: '10.1' },
      { id: 'sv_s2', type: 'motor', name: 'S-II (2. Kademe)', dryMass: '36000', fuelMass: '440000', thrust: '5000000', burnTime: '360', sepAlt: '175000', cd: '0.4', diameter: '10.1' },
      { id: 'sv_s3', type: 'motor', name: 'S-IVB (3. Kademe)', dryMass: '10000', fuelMass: '109000', thrust: '1000000', burnTime: '165', sepAlt: '300000', cd: '0.3', diameter: '6.6' },
      { id: 'sv_pay', type: 'payload', name: 'Apollo Komuta & Ay Modülü', dryMass: '45000', cd: '0.25', diameter: '3.9', noTumble: true }
    ]
  },
  electron: {
    name: 'Rocket Lab Electron',
    parts: [
      { id: 'el_s1', type: 'motor', name: 'Rutherford (1. Kademe)', dryMass: '950', fuelMass: '9250', thrust: '224000', burnTime: '150', sepAlt: '70000', cd: '0.35', diameter: '1.2' },
      { id: 'el_s2', type: 'motor', name: 'Rutherford (2. Kademe)', dryMass: '250', fuelMass: '2150', thrust: '25800', burnTime: '330', sepAlt: '300000', cd: '0.3', diameter: '1.2' },
      { id: 'el_pay', type: 'payload', name: 'Uydu Yükü (Küpsat)', dryMass: '300', cd: '0.2', diameter: '1.2', noTumble: true }
    ]
  }
};

export default function RocketSimSidebar() {
  const { params, updateParam, updateParts, initiateLaunch, running, phase, resetSim } = useRocketSimStore();
  
  const [selectedPreset, setSelectedPreset] = useState('custom');
  const [dbRockets, setDbRockets] = useState({});

  useEffect(() => {
    fetch('http://127.0.0.1:8010/api/hermes/rockets')
      .then(res => res.json())
      .then(data => {
        if (data.rockets) {
          const fresh = {};
          data.rockets.forEach(r => {
            const parts = r.stages.map((st, idx) => ({
              id: 'sys_' + Math.random().toString(36).substr(2, 5),
              type: st.type || 'motor',
              name: st.name || `Kademe ${idx+1}`,
              dryMass: (st.dryMass || 0).toString(),
              fuelMass: (st.propellantMass || 0).toString(),
              thrust: (st.thrust || 0).toString(),
              burnTime: (st.burnTime || 0).toString(),
              sepAlt: ((idx + 1) * 75000).toString(), // Akıllı ayrılma yüksekliği varsayımı
              cd: st.type === 'payload' ? '0.2' : '0.4',
              diameter: (st.diameter || 2.0).toString(),
              noTumble: st.type === 'payload' ? true : false
            }));
            fresh['sys_' + r.name.replace(/\s+/g, '_')] = { name: `${r.name} (Sistem Envanteri)`, parts };
          });

          // TT-Rockets (Local Kullanıcı Araçları)
          try {
             const localStr = localStorage.getItem('tt_rockets');
             if (localStr) {
                const local = JSON.parse(localStr);
                local.forEach((r, idx) => {
                   let dM = parseFloat(r.dry_mass?.toString().replace(/,/g,'')) || 500;
                   let thr = parseFloat(r.thrust?.toString().replace(/,/g,'')) || 8000;
                   let pl = parseFloat(r.payload?.toString().replace(/,/g,'')) || 0;
                   const parts = [{
                     id: 'usr_m_' + Math.random().toString(36).substr(2, 5),
                     type: 'motor',
                     name: 'Kasa + Motor',
                     dryMass: dM.toString(),
                     fuelMass: (dM * 2.5).toString(), // Kaba Oran
                     thrust: thr.toString(),
                     burnTime: '25',
                     sepAlt: '80000',
                     cd: '0.4',
                     diameter: (parseFloat(r.diameter) || 0.5).toString(),
                     noTumble: false
                   }];
                   if (pl > 0) {
                      parts.push({
                        id: 'usr_p_' + Math.random().toString(36).substr(2, 5),
                        type: 'payload',
                        name: 'Faydalı Yük',
                        dryMass: pl.toString(),
                        cd: '0.2',
                        diameter: (parseFloat(r.diameter) || 0.5).toString(),
                        noTumble: true
                      });
                   }
                   fresh['loc_' + idx] = { name: `${r.name} (Sizin Envanteriniz)`, parts };
                });
             }
          } catch(e) { console.error(e); }

          setDbRockets(fresh);
        }
      })
      .catch(e => console.error("Sistem envanteri okunamadı:", e));
  }, []);

  const combinedPresets = useMemo(() => ({ ...PRESET_ROCKETS, ...dbRockets }), [dbRockets]);

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

  const handlePresetSelect = (presetKey) => {
    setSelectedPreset(presetKey);
    setErrors({});
    if (presetKey !== 'custom' && combinedPresets[presetKey]) {
      const presetData = combinedPresets[presetKey].parts.map(p => ({ ...p }));
      setLocalParts(presetData);
    }
  };

  const [wind, setWind] = useState(params.windSpeed.toString());
  const [temp, setTemp] = useState(params.temperature?.toString() || "15");
  const [pressure, setPress] = useState(params.pressure?.toString() || "1013");
  const [errors, setErrors] = useState({});

  const [isLocked, setIsLocked] = useState(false);
  const [lockedData, setLockedData] = useState(null);

  useEffect(() => {
    const lockStr = localStorage.getItem('tt_mission_lock');
    if (lockStr) {
      try {
        const lock = JSON.parse(lockStr);
        setIsLocked(true);
        setLockedData(lock);
        
        if (lock.rocket) {
          const r = lock.rocket;
          let dM = parseFloat(r.dry_mass?.toString().replace(/,/g,'')) || 500;
          let thr = parseFloat(r.thrust?.toString().replace(/,/g,'')) || 8000;
          let pl = parseFloat(r.payload?.toString().replace(/,/g,'')) || 0;
          
          const parts = [{
            id: 'lock_m_1',
            type: 'motor',
            name: `${r.name} Ana GövdeMotor`,
            dryMass: dM.toString(),
            fuelMass: (dM * 2.5).toString(),
            thrust: thr.toString(),
            burnTime: '25',
            sepAlt: '80000',
            cd: '0.4',
            diameter: (parseFloat(r.diameter) || 0.5).toString(),
            noTumble: false
          }];
          if (pl > 0) {
            parts.push({
              id: 'lock_p_1',
              type: 'payload',
              name: 'Görev FaydalıYükü',
              dryMass: pl.toString(),
              cd: '0.2',
              diameter: (parseFloat(r.diameter) || 0.5).toString(),
              noTumble: true
            });
          }
          setLocalParts(parts);
          setSelectedPreset('custom');
        }

        if (lock.weather) {
          setWind(lock.weather.wind_speed?.toString() || "0");
          setTemp(lock.weather.temp?.toString() || "15");
          setPress(lock.weather.pressure?.toString() || "1013");
        }
      } catch (e) { console.warn("Kilit okunurken hata:", e); }
    }
  }, []);

  const handleFetchLiveWeather = async () => {
    const city = prompt("Hangi şehir için gerçek zamanlı hava verisi çekilsin?", "Ankara");
    if (!city) return;
    try {
      const res = await fetch(`http://localhost:8010/api/weather?city=${city}`);
      if (res.ok) {
        const cData = await res.json();
        setWind(cData.wind?.toString() || "0");
        setTemp(cData.temp?.toString() || "15");
        setPress(cData.pressure?.toString() || "1013");
      } else {
        alert("Şehir bulunamadı veya API hatası.");
      }
    } catch(e) { alert("Bağlantı hatası."); }
  };

  const validateAll = () => {
    let isValid = true;
    const currentErrors = {};
    const parsedParts = [];
    
    if (isNaN(Number(wind)) || Number(wind) < 0) { currentErrors['global_wind'] = "Geçersiz değer"; isValid = false; }
    if (isNaN(Number(temp))) { currentErrors['global_temp'] = "Geçersiz değer"; isValid = false; }
    if (isNaN(Number(pressure)) || Number(pressure) < 500) { currentErrors['global_press'] = "Geçersiz değer"; isValid = false; }

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
      updateParam('temperature', Number(temp));
      updateParam('pressure', Number(pressure));
      initiateLaunch();
    }
  };

  const addPart = (type) => {
    setSelectedPreset('custom');
    const newId = 'p' + Math.random().toString(36).substr(2, 5);
    const newPart = type === 'motor' 
      ? { id: newId, type: 'motor', name: `${localParts.length + 1}. Kademe`, dryMass: '50', fuelMass: '150', thrust: '3000', burnTime: '12', sepAlt: '2000', cd: '0.45', diameter: '0.15' }
      : { id: newId, type: 'payload', name: 'Yeni Faydalı Yük', dryMass: '10', cd: '0.3', diameter: '0.15' };

    setLocalParts(prev => {
      if (type === 'payload') return [...prev, newPart];
      const payloads = prev.filter(p => p.type === 'payload');
      const motors = prev.filter(p => p.type === 'motor');
      return [...motors, newPart, ...payloads];
    });
  };

  const removePart = (id) => {
    setSelectedPreset('custom');
    setLocalParts(localParts.filter(p => p.id !== id));
  };

  const handleChange = (id, field, value) => {
    setSelectedPreset('custom');
    const sanitized = field !== 'name' ? value.replace(',', '.') : value;
    setLocalParts(localParts.map(p => p.id === id ? { ...p, [field]: sanitized } : p));
    if (errors[`${id}_${field}`]) {
      setErrors(prev => ({ ...prev, [`${id}_${field}`]: null }));
    }
  };

  const renderInputRow = (id, label, field, unit, value) => (
    <div style={{ marginBottom: '0.6rem' }} key={`${id}_${field}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <label style={{ fontSize: '0.65rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.7)', letterSpacing: '0.5px' }}>{label}</label>
        <span style={{ fontSize: '0.55rem', fontWeight: 800, color: '#CE1212', background: 'rgba(206, 18, 18, 0.08)', padding: '2px 6px', borderRadius: '4px' }}>{unit}</span>
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => handleChange(id, field, e.target.value)}
        disabled={isLocked}
        style={{
          width: '100%',
          background: '#ffffff',
          border: errors[`${id}_${field}`] ? '1.5px solid #CE1212' : '1.5px solid rgba(27, 23, 23, 0.1)',
          borderRadius: '4px',
          padding: '0.5rem 0.6rem',
          color: '#1B1717',
          fontSize: '0.75rem',
          fontFamily: "'Inter', sans-serif",
          fontWeight: 700,
          outline: 'none',
          transition: 'all 0.2s',
          boxSizing: 'border-box',
        }}
        onFocus={(e) => { e.target.style.borderColor = '#CE1212'; e.target.style.boxShadow = '0 0 0 3px rgba(206, 18, 18, 0.08)'; }}
        onBlur={(e) => { if (!errors[`${id}_${field}`]) { e.target.style.borderColor = 'rgba(27, 23, 23, 0.1)'; e.target.style.boxShadow = 'none'; } }}
      />
      {errors[`${id}_${field}`] && (
        <span style={{ color: '#CE1212', fontSize: '0.55rem', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '3px', fontWeight: 800 }}>
          <WarningIcon style={{ fontSize: '0.7rem' }} /> {errors[`${id}_${field}`]}
        </span>
      )}
    </div>
  );

  const sidebarStyle = {
    width: '400px',
    minWidth: '400px',
    background: '#EEEBDD',
    borderLeft: '1px solid rgba(27, 23, 23, 0.08)',
    zIndex: 30,
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    position: 'relative',
    boxShadow: '-8px 0 30px rgba(0,0,0,0.06)',
    fontFamily: "'Inter', sans-serif",
  };

  return (
    <div style={sidebarStyle}>
      {/* HEADER */}
      <div style={{ padding: '1.2rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem', flexShrink: 0, borderBottom: '1px solid rgba(27, 23, 23, 0.08)' }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '4px', background: 'rgba(206, 18, 18, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <LayersIcon style={{ color: '#CE1212', fontSize: '1.2rem' }} />
        </div>
        <div>
          <h1 style={{ margin: 0, fontSize: '1rem', fontWeight: 900, color: '#1B1717', letterSpacing: '1px' }}>ROKET MİMARİSİ</h1>
          <p style={{ margin: 0, fontSize: '0.55rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase', letterSpacing: '1.5px' }}>Çok Kademeli Uçuş & Balistik Ayrılma</p>
        </div>
      </div>

      {/* SCROLLABLE CONTENT */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem 1.5rem' }}>
        {/* PRESET ROCKETS */}
        <div style={{ marginBottom: '1rem', background: '#ffffff', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(206, 18, 18, 0.1)', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.6rem' }}>
            <PrecisionManufacturingIcon style={{ fontSize: '0.9rem', color: '#CE1212' }} />
            <h3 style={{ margin: 0, fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '1.5px', color: '#1B1717', fontWeight: 900 }}>HAZIR ARAÇ KÜTÜPHANESİ</h3>
          </div>
          <select
            value={selectedPreset}
            onChange={(e) => handlePresetSelect(e.target.value)}
            style={{
              width: '100%',
              background: '#f8f9fa',
              border: '1.5px solid rgba(27, 23, 23, 0.1)',
              borderRadius: '4px',
              padding: '0.6rem',
              color: '#1B1717',
              fontSize: '0.75rem',
              fontWeight: 800,
              outline: 'none',
              cursor: 'pointer',
              appearance: 'none',
              backgroundImage: 'linear-gradient(45deg, transparent 50%, #CE1212 50%), linear-gradient(135deg, #CE1212 50%, transparent 50%)',
              backgroundPosition: 'calc(100% - 15px) calc(1em + 2px), calc(100% - 10px) calc(1em + 2px)',
              backgroundSize: '5px 5px, 5px 5px',
              backgroundRepeat: 'no-repeat',
            }}
          >
            {Object.entries(combinedPresets).map(([key, data]) => {
              const isSystem = key.startsWith('sys_');
              return (
                <option key={key} value={key} style={{ fontWeight: 700, color: isSystem ? '#CE1212' : '#1B1717' }}>
                  {isSystem ? 'SİSTEM: ' : ''}{data.name}
                </option>
              );
            })}
          </select>
        </div>

        {/* RÜZGAR & HAVA DURUMU */}
        <div style={{ marginBottom: '1rem', background: 'rgba(206, 18, 18, 0.04)', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(206, 18, 18, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AirIcon style={{ fontSize: '0.9rem', color: '#CE1212' }} />
              <h3 style={{ margin: 0, fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '1.5px', color: '#1B1717', fontWeight: 900 }}>Çevre Koşulları</h3>
            </div>
            <button onClick={handleFetchLiveWeather} style={{ background: '#1B1717', color: 'white', border: 'none', padding: '4px 8px', borderRadius: '4px', fontSize: '0.55rem', fontWeight: 900, cursor: 'pointer' }}>ANLIK VERİ ÇEK</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <label style={{ fontSize: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.7)' }}>Rüzgar</label>
                <span style={{ fontSize: '0.5rem', fontWeight: 800, color: '#CE1212', background: 'rgba(206, 18, 18, 0.08)', padding: '2px 4px', borderRadius: '4px' }}>m/s</span>
              </div>
              <input type="text" value={wind} onChange={(e) => { setWind(e.target.value); setErrors({...errors, global_wind: null}); }}
                style={{ width: '100%', border: errors['global_wind'] ? '1.5px solid #CE1212' : '1px solid rgba(27, 23, 23, 0.1)', borderRadius: '4px', padding: '0.4rem', fontSize: '0.75rem', outline: 'none', boxSizing: 'border-box' }} />
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <label style={{ fontSize: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.7)' }}>Sıcaklık</label>
                <span style={{ fontSize: '0.5rem', fontWeight: 800, color: '#CE1212', background: 'rgba(206, 18, 18, 0.08)', padding: '2px 4px', borderRadius: '4px' }}>°C</span>
              </div>
              <input type="text" value={temp} onChange={(e) => { setTemp(e.target.value); setErrors({...errors, global_temp: null}); }}
                style={{ width: '100%', border: errors['global_temp'] ? '1.5px solid #CE1212' : '1px solid rgba(27, 23, 23, 0.1)', borderRadius: '4px', padding: '0.4rem', fontSize: '0.75rem', outline: 'none', boxSizing: 'border-box' }} />
            </div>
            <div style={{ gridColumn: '1 / span 2' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <label style={{ fontSize: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.7)' }}>Atmosferik Basınç</label>
                <span style={{ fontSize: '0.5rem', fontWeight: 800, color: '#CE1212', background: 'rgba(206, 18, 18, 0.08)', padding: '2px 4px', borderRadius: '4px' }}>hPa</span>
              </div>
              <input type="text" value={pressure} onChange={(e) => { setPress(e.target.value); setErrors({...errors, global_press: null}); }}
                style={{ width: '100%', border: errors['global_press'] ? '1.5px solid #CE1212' : '1px solid rgba(27, 23, 23, 0.1)', borderRadius: '4px', padding: '0.4rem', fontSize: '0.75rem', outline: 'none', boxSizing: 'border-box' }} />
            </div>
          </div>
        </div>

        {/* KADEMELER */}
        <AnimatePresence>
          {localParts.map((part, index) => (
            <motion.div 
              key={part.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{
                marginBottom: '0.8rem',
                padding: '0.8rem',
                borderRadius: '4px',
                border: part.type === 'motor' ? '1px solid rgba(27, 23, 23, 0.08)' : '1px solid rgba(206, 18, 18, 0.15)',
                background: part.type === 'motor' ? '#ffffff' : 'rgba(206, 18, 18, 0.03)',
                position: 'relative',
                boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem', borderBottom: '1px solid rgba(27, 23, 23, 0.05)', paddingBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {part.type === 'motor' 
                    ? <RocketLaunchIcon style={{ fontSize: '0.9rem', color: '#CE1212' }} /> 
                    : <InventoryIcon style={{ fontSize: '0.9rem', color: '#CE1212' }} />
                  }
                  <input
                    type="text"
                    value={part.name}
                    onChange={(e) => handleChange(part.id, 'name', e.target.value)}
                    style={{ background: 'transparent', fontSize: '0.8rem', fontWeight: 900, color: '#1B1717', outline: 'none', border: 'none', borderBottom: '1px solid transparent', width: '120px', padding: 0, transition: 'border 0.2s' }}
                    onFocus={(e) => e.target.style.borderBottomColor = 'rgba(27, 23, 23, 0.2)'}
                    onBlur={(e) => e.target.style.borderBottomColor = 'transparent'}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.5rem', color: 'rgba(27, 23, 23, 0.4)', textTransform: 'uppercase', letterSpacing: '1.5px', fontWeight: 900 }}>
                    {index === 0 ? 'İLK ATEŞLEME' : (part.type === 'payload' ? 'YÜK' : 'ÜST KADEME')}
                  </span>
                  {localParts.length > 1 && (
                    <button onClick={() => removePart(part.id)} style={{ background: 'rgba(27, 23, 23, 0.05)', border: 'none', padding: '4px', borderRadius: '4px', cursor: 'pointer', display: 'flex', color: 'rgba(27, 23, 23, 0.3)', transition: 'all 0.2s' }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = '#CE1212'; e.currentTarget.style.background = 'rgba(206, 18, 18, 0.08)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = 'rgba(27, 23, 23, 0.3)'; e.currentTarget.style.background = 'rgba(27, 23, 23, 0.05)'; }}
                    >
                      <DeleteIcon style={{ fontSize: '0.8rem' }} />
                    </button>
                  )}
                </div>
              </div>

              {part.type === 'motor' ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 0.6rem' }}>
                  {renderInputRow(part.id, "Kuru Kütle", "dryMass", "kg", part.dryMass)}
                  {renderInputRow(part.id, "Yakıt Kütlesi", "fuelMass", "kg", part.fuelMass)}
                  {renderInputRow(part.id, "Motor İtkisi", "thrust", "N", part.thrust)}
                  {renderInputRow(part.id, "Yanma Süresi", "burnTime", "s", part.burnTime)}
                  {renderInputRow(part.id, "Ayrılma İrt.", "sepAlt", "m", part.sepAlt)}
                  {renderInputRow(part.id, "Sür. Katsayısı", "cd", "Cd", part.cd)}
                  {renderInputRow(part.id, "Çap", "diameter", "m", part.diameter)}
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 0.6rem' }}>
                  {renderInputRow(part.id, "Görev Yükü", "dryMass", "kg", part.dryMass)}
                  {renderInputRow(part.id, "Sür. Katsayısı", "cd", "Cd", part.cd)}
                  {renderInputRow(part.id, "Çap", "diameter", "m", part.diameter)}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* EKLE BUTONLARI */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <button onClick={() => addPart('motor')} style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
            padding: '0.6rem', borderRadius: '4px', background: 'rgba(27, 23, 23, 0.04)', border: '1px solid rgba(27, 23, 23, 0.06)',
            color: 'rgba(27, 23, 23, 0.6)', fontSize: '0.6rem', fontWeight: 900, letterSpacing: '1px', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s',
          }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(27, 23, 23, 0.08)'; e.currentTarget.style.color = '#1B1717'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(27, 23, 23, 0.04)'; e.currentTarget.style.color = 'rgba(27, 23, 23, 0.6)'; }}
          >
            <AddIcon style={{ fontSize: '0.8rem' }} /> Motor Kademe
          </button>
          <button onClick={() => addPart('payload')} style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
            padding: '0.6rem', borderRadius: '4px', background: 'rgba(206, 18, 18, 0.04)', border: '1px solid rgba(206, 18, 18, 0.08)',
            color: '#CE1212', fontSize: '0.6rem', fontWeight: 900, letterSpacing: '1px', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s',
          }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(206, 18, 18, 0.1)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(206, 18, 18, 0.04)'; }}
          >
            <AddIcon style={{ fontSize: '0.8rem' }} /> Faydalı Yük
          </button>
        </div>
      </div>

      {/* FOOTER — STATUS + LAUNCH */}
      <div style={{ padding: '1rem 1.5rem', background: '#EEEBDD', borderTop: '1px solid rgba(27, 23, 23, 0.08)', flexShrink: 0 }}>
        {/* Status + Reset Row */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div style={{
            flex: 1, borderRadius: '4px', fontWeight: 900, fontSize: '0.65rem', letterSpacing: '1.5px',
            border: '1px solid rgba(27, 23, 23, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            background: '#fff', padding: '0.6rem', color: phase === 'TOUCHDOWN' ? '#10b981' : '#CE1212',
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: phase === 'IDLE' ? 'rgba(27, 23, 23, 0.2)' : (phase === 'TOUCHDOWN' ? '#10b981' : '#CE1212'), animation: phase !== 'IDLE' && phase !== 'TOUCHDOWN' ? 'pulse 2s infinite' : 'none' }}></span>
            {phase}
          </div>
          <button onClick={resetSim} style={{
            background: '#fff', border: '1px solid rgba(27, 23, 23, 0.08)', padding: '0.6rem 1rem', borderRadius: '4px',
            fontWeight: 900, fontSize: '0.6rem', letterSpacing: '1px', color: 'rgba(27, 23, 23, 0.5)', cursor: 'pointer', transition: 'all 0.2s', textTransform: 'uppercase',
          }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#CE1212'; e.currentTarget.style.borderColor = '#CE1212'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'rgba(27, 23, 23, 0.5)'; e.currentTarget.style.borderColor = 'rgba(27, 23, 23, 0.08)'; }}
          >
            SIFIRLA
          </button>
        </div>

        {/* LAUNCH BUTTON */}
        <button
          onClick={handleStartSimulation}
          disabled={running}
          style={{
            width: '100%',
            background: running ? 'rgba(206, 18, 18, 0.2)' : '#CE1212',
            color: running ? 'rgba(27, 23, 23, 0.4)' : '#EEEBDD',
            border: 'none',
            padding: '1rem',
            borderRadius: '4px',
            fontWeight: 900,
            fontSize: '0.8rem',
            letterSpacing: '2px',
            textTransform: 'uppercase',
            cursor: running ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            transition: 'all 0.3s',
            boxShadow: running ? 'none' : '0 4px 12px rgba(206, 18, 18, 0.15)',
            opacity: running ? 0.5 : 1,
          }}
        >
          <RocketLaunchIcon style={{ fontSize: '1.1rem' }} />
          {running ? 'HESAPLANIYOR...' : 'AYRILMALI UÇUŞU BAŞLAT'}
        </button>
      </div>
    </div>
  );
}
