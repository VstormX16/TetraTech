import React, { useRef, useEffect } from 'react';
import { useSimStore } from '../store';
import { clamp, getAtmosphereLayer, Particle } from '../utils/physics';

export default function RocketCanvas() {
  const canvasRef = useRef(null);
  const frameRef = useRef(null);
  const simRef = useRef({
    alt: 0, velY: 0, accY: 0, x: 0, velX: 0,
    fuel: 0, t: 0, phase: 'IDLE',
    particles: [], stars: [],
    accum: 0, q: 0, mach: 0,
    layer: 'TROPOSFER',
    localEvents: null, lastUI: 0,
    activeIndex: 0, falling: [], shakeTime: 0, flipStart: 0, crashTime: 0,
    cameraX: 0, cameraY: 0,
    prevActiveIndex: 0, sepFlashTime: 0
  });

  useEffect(() => {
    simRef.current.stars = Array.from({ length: 350 }, () => ({
      x: Math.random(), y: Math.random(),
      size: Math.random() * 2 + 0.5,
      b: Math.random(),
      depth: Math.random() * 0.8 + 0.2,
    }));
  }, []);

  useEffect(() => {
    const unsub = useSimStore.subscribe((state, prev) => {
      if (state.running && !prev.running) {
        simRef.current = {
          ...simRef.current,
          alt: 0, velY: 0, accY: 0, x: 0, velX: 0,
          t: 0, phase: 'IGNITION', particles: [],
          accum: 0, q: 0, mach: 0,
          layer: 'TROPOSFER', localEvents: null, lastUI: 0,
          activeIndex: 0, falling: [], shakeTime: 0, flipStart: 0, crashTime: 0,
          cameraX: 0, cameraY: 0,
          prevActiveIndex: 0, sepFlashTime: 0
        };
      }
      if (!state.running && prev.running && state.phase === 'IDLE') {
        simRef.current = {
          ...simRef.current,
          alt: 0, velY: 0, accY: 0, x: 0, velX: 0,
          t: 0, phase: 'IDLE', particles: [],
          accum: 0, q: 0, mach: 0,
          layer: 'TROPOSFER', localEvents: null, lastUI: 0,
          activeIndex: 0, falling: [], shakeTime: 0, flipStart: 0, crashTime: 0,
          cameraX: 0, cameraY: 0,
          prevActiveIndex: 0, sepFlashTime: 0
        };
      }
    });
    return unsub;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false });
    let lastTime = performance.now();

    const loop = (time) => {
      try {
        const state = useSimStore.getState();
        const { params, running } = state;
        const parts = params.parts || [];

        const dtFrame = Math.min((time - lastTime) / 1000, 0.1);
        lastTime = time;
        const sim = simRef.current;
        sim.accum += dtFrame;

        if (running && state.trajectory && state.phase !== 'CALCULATING') {
          sim.t += dtFrame;
          const tick = Math.min(Math.floor(sim.t / 0.016666), state.trajectory.length - 1);
          const frame = state.trajectory[tick];

          if (frame) {
            sim.alt = frame.alt;
            sim.velY = frame.velY;
            sim.accY = frame.accY;
            sim.x = frame.x;
            sim.velX = frame.velX;
            sim.fuel = frame.fuel;
            sim.mach = frame.mach || 0;
            sim.q = frame.q || 0;
            sim.layer = getAtmosphereLayer(sim.alt);

            // Ayrılma Tespiti
            const prevIdx = sim.activeIndex;
            const nextIdx = frame.activeIndex !== undefined ? frame.activeIndex : 0;
            
            // Ayrılma anında küçük bir görsel flash efekti
            if (nextIdx > prevIdx) {
              sim.sepFlashTime = 0.5; // 0.5 saniyelik ayrılma flash'ı
            }
            
            sim.activeIndex = nextIdx;
            sim.prevActiveIndex = prevIdx;
            sim.falling = frame.falling || [];

            if (sim.phase !== frame.phase) {
              // 💥 CRASH TESPİTİ: Devasa patlama efekti
              if (frame.phase === 'CRASH' && sim.phase !== 'CRASH') {
                sim.shakeTime = 2.0; // Uzun kamera sarsıntısı
                sim.crashTime = time;
                // Devasa patlama partikülleri
                for (let i = 0; i < 120; i++) {
                  // Ateş topu
                  sim.particles.push(new Particle(
                    (Math.random() - 0.5) * 60, (Math.random() - 0.5) * 40,
                    (Math.random() - 0.5) * 500, -Math.random() * 400 - 100,
                    Math.random() * 2.0 + 0.5,
                    Math.random() * 25 + 15,
                    1
                  ));
                  // Duman
                  sim.particles.push(new Particle(
                    (Math.random() - 0.5) * 100, (Math.random() - 0.5) * 30,
                    (Math.random() - 0.5) * 200, -Math.random() * 150,
                    Math.random() * 1.5 + 0.5,
                    Math.random() * 30 + 20,
                    0
                  ));
                }
              }
              sim.phase = frame.phase;
              state.setPhase(frame.phase);
            }

            if (!sim.localEvents) sim.localEvents = [...(state.futureEvents || [])];
            while (sim.localEvents.length > 0 && sim.localEvents[0].time <= sim.t) {
              const ev = sim.localEvents.shift();
              state.addLog(ev.msg);
            }

            if (sim.phase === 'IGNITION' && Math.random() < 0.7) {
              const altRatio = clamp(sim.alt / 30000, 0, 1);
              const spread = 8 + altRatio * 120;
              const speed = 120 + altRatio * 180;
              sim.particles.push(new Particle(
                (Math.random() - 0.5) * spread, 0,
                (Math.random() - 0.5) * spread * 0.15,
                Math.random() * speed + speed * 0.5,
                Math.random() * 0.3 + 0.08,
                Math.random() * (5 + altRatio * 8) + 2,
                sim.alt > 25000 ? 3 : 1
              ));
              if (Math.random() < 0.2) {
                sim.particles.push(new Particle(
                  (Math.random() - 0.5) * spread * 2, 10,
                  (Math.random() - 0.5) * 15,
                  Math.random() * 30 + 40,
                  Math.random() * 0.6 + 0.3,
                  Math.random() * 12 + 6,
                  0
                ));
              }
            }
          }

          if (!sim.lastUI || time - sim.lastUI > 100 || sim.phase === 'TOUCHDOWN') {
            sim.lastUI = time;
            state.setMetrics((m) => ({
              alt: sim.alt, velY: sim.velY, accY: sim.accY,
              xDist: sim.x, velX: sim.velX,
              fuel: sim.fuel, t: sim.t,
              maxAlt: Math.max(m.maxAlt, sim.alt),
              maxVel: Math.max(m.maxVel, Math.sqrt(sim.velY ** 2 + sim.velX ** 2)),
              maxQ: Math.max(m.maxQ || 0, sim.q),
              q: sim.q, layer: sim.layer, mach: sim.mach,
            }));
          }
        } else if (!running) {
          sim.localEvents = null;
          sim.alt = 0;
          sim.t = 0;
        }

        sim.particles.forEach((p) => p.update(dtFrame));
        sim.particles = sim.particles.filter((p) => p.life > 0 && p.size > 0.3);

        // ─── CANVAS SETUP ───
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
          canvas.width = rect.width * dpr;
          canvas.height = rect.height * dpr;
        }
        const W = rect.width;
        const H = rect.height;

        // ─── DİNAMİK ZOOM & ODAKLAMA: Roketin burnu her zaman merkezde olsun ───
        let rawTotalH = 0;
        let rawPayloadH = 0;
        for (let i = sim.activeIndex; i < parts.length; i++) {
          const isP = parts[i]?.type === 'payload';
          const pw1 = clamp(14 + Number(parts[i]?.diameter || 0.15) * 100, 12, 50);
          const ph1 = isP ? pw1 * 3.5 : clamp(50 + Number(parts[i]?.diameter || 0.15) * 400, 40, 150);
          rawTotalH += ph1;
          if (isP) rawPayloadH = ph1;
        }

        // SMOOTH CAMERA (LERP): Mevcut X'i hedef X'e yavaşça yaklaştır (%8 her frame)
        sim.cameraX += (sim.x - sim.cameraX) * 0.08;

        // Zoom: Roket sığsın
        const autoZoom = rawTotalH > 0 ? clamp((H * 0.55) / rawTotalH, 0.15, 2.0) : 1.0;
        const zoom = autoZoom;
        const ppm = zoom;

        const totalH = rawTotalH * zoom;
        const payloadH = rawPayloadH * zoom;
        
        // ODAK NOKTASI: Roketi ekranın biraz üst kısmına koy (H/2.2)
        // Aşağıda düşen parçaları görmek için alan bırak
        // Düşen parça varsa kamerayı biraz daha aşağı kaydır
        let cameraYTarget = H / 2.2;
        if (sim.falling.length > 0) {
          // Düşen parçalar varken kamerayı biraz yukarı çek ki aşağıdaki parçalar görünsün
          const lowestFalling = Math.min(...sim.falling.filter(f => !f.landed).map(f => f.y));
          const altDiff = sim.alt - lowestFalling;
          if (altDiff > 0 && altDiff < 5000) {
            // Düşen parça ile roket arasındaki fark kadar kamerayı yukarı kaydır
            cameraYTarget = H / 2.2 - clamp(altDiff * ppm * 0.15, 0, H * 0.15);
          }
        }
        // Smooth camera Y geçişi
        if (!sim.cameraY) sim.cameraY = cameraYTarget;
        sim.cameraY += (cameraYTarget - sim.cameraY) * 0.03;
        
        const noseToEngine = totalH - payloadH / 2;
        const baseEnginePosition = sim.cameraY;
        const baseEngineY = baseEnginePosition + noseToEngine;
        const gY = baseEngineY + sim.alt * ppm;

        // FIX: ctx.resetTransform + scale ÖNCE yapılıyor, shake sonra
        ctx.resetTransform();
        ctx.scale(dpr, dpr);

        // Camera Shake — zoom artık tanımlı
        if (sim.shakeTime > 0) {
          const mag = Math.min(sim.shakeTime * 15, 20);
          const shakeX = (Math.random() - 0.5) * mag * zoom;
          const shakeY = (Math.random() - 0.5) * mag * zoom;
          ctx.translate(shakeX, shakeY);
          sim.shakeTime -= dtFrame;
        }

        // ─── GÖKYÜZÜ ───
        const altFactor = clamp(sim.alt / 35000, 0, 1);
        const skyGrad = ctx.createLinearGradient(0, 0, 0, H);
        skyGrad.addColorStop(0, `rgb(${30 - 30 * altFactor}, ${90 - 90 * altFactor}, ${190 - 190 * altFactor})`);
        skyGrad.addColorStop(1, `rgb(${155 - 155 * altFactor}, ${210 - 200 * altFactor}, ${240 - 210 * altFactor})`);
        ctx.fillStyle = skyGrad;
        ctx.fillRect(0, 0, W, H);

        // ─── YILDIZLAR ───
        if (altFactor > 0.04) {
          const starlight = clamp((altFactor - 0.04) * 3, 0, 1);
          sim.stars.forEach((s) => {
            ctx.globalAlpha = starlight * s.b * (0.4 + 0.6 * Math.sin(time / 500 + s.x * 100));
            ctx.fillStyle = '#ffffff';
            const px = ((s.x * W + sim.cameraX * s.depth * 0.5) % W + W) % W;
            const dy = ((s.y * H + (sim.alt / 80) * s.depth) % H + H) % H;
            ctx.beginPath(); ctx.arc(px, dy, s.size, 0, Math.PI * 2); ctx.fill();
          });
          ctx.globalAlpha = 1.0;
        }

        // ─── ZEMİN ───
        if (gY < H + 400) {
          ctx.globalAlpha = clamp(1 - sim.alt / 2500, 0, 1);
          const pX = W / 2 - (sim.x - sim.cameraX) * zoom;

          ctx.fillStyle = '#7a6748';
          ctx.beginPath(); ctx.moveTo(0, gY);
          const hX = (pX * 0.1) % 400;
          for (let i = -400; i < W + 400; i += 200) {
            ctx.quadraticCurveTo(i + hX + 100, gY - 50 * zoom, i + hX + 200, gY);
          }
          ctx.lineTo(W, H + 400); ctx.lineTo(0, H + 400); ctx.fill();

          ctx.fillStyle = '#4ade80';
          ctx.fillRect(0, gY, W, H + 400 - gY);

          ctx.fillStyle = '#64748b'; ctx.fillRect(pX - 70 * zoom, gY - 8 * zoom, 140 * zoom, 8 * zoom);
          ctx.fillStyle = '#475569'; ctx.fillRect(pX - 85 * zoom, gY, 170 * zoom, H + 400 - gY);
          ctx.fillStyle = '#334155'; ctx.fillRect(pX - 35 * zoom, gY - 140 * zoom, 10 * zoom, 140 * zoom);

          ctx.fillStyle = '#1e293b';
          ctx.beginPath(); ctx.moveTo(pX - 25 * zoom, gY - 120 * zoom); ctx.lineTo(pX - 12 * zoom, gY - 128 * zoom); ctx.lineTo(pX - 25 * zoom, gY - 110 * zoom); ctx.fill();
          ctx.beginPath(); ctx.moveTo(pX - 25 * zoom, gY - 60 * zoom); ctx.lineTo(pX - 12 * zoom, gY - 68 * zoom); ctx.lineTo(pX - 25 * zoom, gY - 50 * zoom); ctx.fill();
          ctx.globalAlpha = 1.0;
        }

        // ─── AYRILMA FLASH EFEKTİ ───
        if (sim.sepFlashTime > 0) {
          sim.sepFlashTime -= dtFrame;
          const flashAlpha = clamp(sim.sepFlashTime * 2, 0, 0.4);
          ctx.save();
          ctx.globalCompositeOperation = 'screen';
          const flashGrad = ctx.createRadialGradient(W/2, baseEngineY, 0, W/2, baseEngineY, 60 * zoom);
          flashGrad.addColorStop(0, `rgba(255, 255, 200, ${flashAlpha})`);
          flashGrad.addColorStop(0.5, `rgba(255, 200, 100, ${flashAlpha * 0.5})`);
          flashGrad.addColorStop(1, 'rgba(255, 150, 50, 0)');
          ctx.fillStyle = flashGrad;
          ctx.beginPath();
          ctx.arc(W/2, baseEngineY, 60 * zoom, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }

        // ─── DÜŞEN KADEMELER (YUMUŞAK AYRILMA + SÜZÜLME + DÜŞÜŞ) ───
        sim.falling.forEach(f => {
          const fp = parts.find(px => px.id === f.id) || { diameter: 0.15 };
          const fallW = clamp(14 + Number(fp.diameter) * 100, 12, 50) * zoom;
          const fallH = clamp(50 + Number(fp.diameter) * 400, 40, 150) * zoom;
          const fallY = baseEngineY - (f.y - sim.alt) * ppm;
          const fallX = W / 2 + (f.x - sim.x) * zoom;

          // Ekranın dışındaysa çizme (performans)
          if (fallY < -200 || fallY > H + 200 || fallX < -200 || fallX > W + 200) return;

          // 💨 DÜŞEN PARÇA PARTİKÜLLERİ (Smoke Trail) — Daha yoğun ve uzun
          if (!f.landed && Math.random() < 0.6) {
            sim.particles.push(new Particle(
              (fallX - W/2) + (Math.random() - 0.5) * fallW * 0.3,
              (fallY - baseEngineY) + (Math.random() - 0.5) * fallH * 0.3,
              (Math.random() - 0.5) * 8,
              Math.random() * 15 + 5,
              Math.random() * 1.2 + 0.5,  // Daha uzun ömürlü
              Math.random() * 5 + 3,      // Daha büyük
              0
            ));
          }

          // ═══ SAYDAM KONTROL ═══
          // Ayrılma anında tam görünür, düşerken yukarı çıktıkça (ekranın üstüne doğru) fade
          // Yere indiyse yavaşça sönümle
          let fallAlpha = 1.0;
          if (f.landed) {
            fallAlpha = 0.5;
          } else {
            // Ekranın altına doğru gidiyorsa (aşağı düşüyorsa) tam görünür
            // Ekranın üst sınırına yaklaşırsa yavaşça kaybol
            if (fallY < 50) {
              fallAlpha = clamp(fallY / 50, 0, 1);
            }
          }
          
          ctx.save();
          ctx.globalAlpha = fallAlpha;
          ctx.translate(fallX, fallY - fallH / 2);
          ctx.rotate(f.rot);

          // Temiz gövde (Ayrılan parça rengi değişmesin)
          const fallShade = ctx.createLinearGradient(-fallW / 2, 0, fallW / 2, 0);
          fallShade.addColorStop(0, 'rgba(0,0,0,0.4)');
          fallShade.addColorStop(0.3, 'rgba(255,255,255,0.7)');
          fallShade.addColorStop(1, 'rgba(0,0,0,0.25)');
          
          ctx.fillStyle = '#f1f5f9';
          ctx.fillRect(-fallW / 2, -fallH / 2, fallW, fallH);
          ctx.fillStyle = fallShade;
          ctx.fillRect(-fallW / 2, -fallH / 2, fallW, fallH);

          // Siyah şeritler (kademe detayı)
          ctx.fillStyle = '#111827';
          ctx.fillRect(-fallW / 2, -fallH * 0.3, fallW, fallH * 0.04);
          ctx.fillRect(-fallW / 2, fallH * 0.1, fallW, fallH * 0.04);

          // Kırık nozul (Alt kısım)
          ctx.fillStyle = '#1e293b';
          ctx.beginPath();
          ctx.moveTo(-fallW * 0.35, fallH / 2); ctx.lineTo(-fallW * 0.45, fallH / 2 + fallH * 0.08);
          ctx.lineTo(fallW * 0.45, fallH / 2 + fallH * 0.08); ctx.lineTo(fallW * 0.35, fallH / 2);
          ctx.fill();

          // Üst kısmı (ayrılma yüzeyi) — Hafif yanık efekti
          ctx.fillStyle = 'rgba(80, 50, 20, 0.4)';
          ctx.fillRect(-fallW / 2, -fallH / 2 - 2, fallW, 4);

          ctx.restore();
        });

        // ─── ANA ROKET ───
        // BURNU AŞAĞI DÜŞME MEKANİĞİ + RÜZGAR SAVRULMASI
        let tilt = 0;
        const windStr = Number(params.windSpeed || 0);
        
        if (sim.phase === 'IGNITION' && sim.alt > 10 && sim.velY > 5) {
          // Uçuş sırasında: rüzgar etkisiyle hafif eğilme + rüzgar savrulması
          tilt = Math.atan2(sim.velX, sim.velY) * 0.7;
          // Şiddetli rüzgar savrulması (rüzgar > 10 m/s ise titreşim)
          if (windStr > 10) {
            tilt += Math.sin(time / 200) * (windStr - 10) * 0.002;
          }
        } else if (sim.phase === 'COAST' || sim.phase === 'DESCENT') {
          // YAKIT BİTTİ veya DÜŞÜŞ: Burnu yavaşça aşağı dönmeye başlar
          // Zamanla artan bir açı (smooth, dramatik)
          if (!sim.flipStart) sim.flipStart = time;
          const flipElapsed = (time - sim.flipStart) / 1000; // saniye
          const flipAngle = clamp(flipElapsed * 0.9, 0, Math.PI * 0.85); // %50 Daha Hızlandırıldı (x6)
          // Rüzgar yönüne göre hangi tarafa döneceğini belirle
          const flipDir = sim.velX >= 0 ? 1 : -1;
          tilt = flipAngle * flipDir;
          // Rüzgar savrulması (düşerken daha agresif)
          if (windStr > 5) {
            tilt += Math.sin(time / 150) * (windStr - 5) * 0.004;
          }
        } else {
          sim.flipStart = 0;
        }
        
        const activeParts = parts.slice(sim.activeIndex);

        // CRASH durumunda roket gövdesini çizme — patladı!
        if (sim.phase === 'CRASH') {
          // Patlama ışık topu
          ctx.save();
          ctx.globalCompositeOperation = 'screen';
          const crashGlow = ctx.createRadialGradient(W/2, baseEngineY, 0, W/2, baseEngineY, 80 * zoom);
          crashGlow.addColorStop(0, 'rgba(255, 200, 50, 0.9)');
          crashGlow.addColorStop(0.3, 'rgba(255, 100, 0, 0.5)');
          crashGlow.addColorStop(1, 'rgba(255, 50, 0, 0)');
          ctx.fillStyle = crashGlow;
          ctx.beginPath();
          ctx.arc(W/2, baseEngineY, 80 * zoom, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        } else {
          // Normal roket çizimi
          ctx.save();
          ctx.translate(W / 2, baseEngineY);
          ctx.rotate(tilt);

        let currentStackY = 0;
        activeParts.forEach((p, idx) => {
          const isPayload = p.type === 'payload';
          const pW = clamp(14 + Number(p.diameter) * 100, 12, 50) * zoom;
          // Burun konisini devasa uzunluğa (pW * 3.5) çekiyoruz ki harika bir uçuş profili olsun
          const pH = isPayload ? pW * 3.5 : (clamp(50 + Number(p.diameter) * 400, 40, 150) * zoom);

          ctx.save();
          ctx.translate(0, -currentStackY);

          if (isPayload) {
            // Beyaz gövde kısmını %50, turuncu sivri burnu %50 yapıyoruz (beyaz 2x uzatıldı)
            const bodyH = pH * 0.5;
            const coneH = pH * 0.5;
            
            // 1) Beyaz Gövde
            const pbShade = ctx.createLinearGradient(-pW / 2, 0, pW / 2, 0);
            pbShade.addColorStop(0, 'rgba(0,0,0,0.55)');
            pbShade.addColorStop(0.3, 'rgba(255,255,255,0.8)');
            pbShade.addColorStop(1, 'rgba(0,0,0,0.35)');
            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(-pW / 2, -bodyH, pW, bodyH);
            ctx.fillStyle = pbShade;
            ctx.fillRect(-pW / 2, -bodyH, pW, bodyH);

            // 2) Siyah Şerit (Konektör)
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(-pW / 2, -bodyH + 2, pW, pH * 0.03);

            // 3) Çok Uzun ve Sivri Turuncu Burun Konisi (Needle / İğne ucu Ogive tarzı)
            const noseGrad = ctx.createLinearGradient(-pW / 2, -pH * 0.3, pW / 2, -pH * 0.3);
            noseGrad.addColorStop(0, '#9a3412'); noseGrad.addColorStop(0.4, '#ea580c'); noseGrad.addColorStop(1, '#7c2d12');
            ctx.fillStyle = noseGrad;
            ctx.beginPath();
            ctx.moveTo(-pW / 2, -bodyH);
            
            // X eksenini 0'a daha yakın tutarak (10 değerlerinde) eğimi yukarıya hapsediyoruz
            ctx.quadraticCurveTo(-pW / 5, -bodyH - coneH * 0.6, 0, -pH);
            ctx.quadraticCurveTo(pW / 5, -bodyH - coneH * 0.6, pW / 2, -bodyH);
            ctx.fill();
          } else {
            const bodyShade = ctx.createLinearGradient(-pW / 2, 0, pW / 2, 0);
            bodyShade.addColorStop(0, 'rgba(0,0,0,0.55)');
            bodyShade.addColorStop(0.3, 'rgba(255,255,255,0.7)');
            bodyShade.addColorStop(1, 'rgba(0,0,0,0.35)');
            ctx.fillStyle = '#f1f5f9';
            ctx.fillRect(-pW / 2, -pH, pW, pH);
            ctx.fillStyle = bodyShade;
            ctx.fillRect(-pW / 2, -pH, pW, pH);

            ctx.fillStyle = '#111827';
            ctx.fillRect(-pW / 2, -pH * 0.8, pW, pH * 0.06);
            if (idx === 0) ctx.fillRect(-pW / 2, -pH * 0.4, pW, pH * 0.06);

            if (idx === 0 && sim.activeIndex === 0) {
              ctx.fillStyle = '#1e293b';
              const finW = pW * 0.55;
              const finH = pH * 0.25;
              ctx.beginPath(); ctx.moveTo(-pW / 2, -finH - pH * 0.1); ctx.lineTo(-pW / 2 - finW, 0); ctx.lineTo(-pW / 2, 0); ctx.fill();
              ctx.beginPath(); ctx.moveTo(pW / 2, -finH - pH * 0.1); ctx.lineTo(pW / 2 + finW, 0); ctx.lineTo(pW / 2, 0); ctx.fill();
            }

            ctx.fillStyle = '#374151';
            const nzH = pH * 0.08;
            ctx.beginPath();
            ctx.moveTo(-pW * 0.3, 0); ctx.lineTo(-pW * 0.4, nzH); ctx.lineTo(pW * 0.4, nzH); ctx.lineTo(pW * 0.3, 0);
            ctx.fill();
          }
          currentStackY += pH;
          ctx.restore();
        });
        ctx.restore();
        } // else block kapanışı (CRASH vs normal roket çizimi)

        // ─── PARTİKÜL & MOTOR IŞIMASI ───
        ctx.save();
        ctx.globalCompositeOperation = 'source-over';

        sim.particles.forEach((p) => {
          const fAlpha = clamp(p.life / p.maxLife, 0, 1);
          ctx.beginPath();
          ctx.arc(W / 2 + p.x, baseEngineY + p.y + 10 * zoom, Math.max(0.1, p.size), 0, Math.PI * 2);
          if (p.type === 1) {
            ctx.globalCompositeOperation = 'screen';
            ctx.fillStyle = `rgba(255, ${Math.floor(190 * fAlpha)}, ${Math.floor(40 * fAlpha)}, ${fAlpha})`;
          } else if (p.type === 3) {
            ctx.globalCompositeOperation = 'screen';
            ctx.fillStyle = `rgba(${Math.floor(80 * fAlpha)}, ${Math.floor(140 * fAlpha)}, 255, ${fAlpha * 0.7})`;
          } else {
            ctx.globalCompositeOperation = 'source-over';
            ctx.fillStyle = `rgba(140, 140, 145, ${fAlpha * 0.35})`;
          }
          ctx.fill();
        });

        ctx.globalCompositeOperation = 'source-over';

        if (sim.phase === 'IGNITION') {
          const lowestPart = activeParts[0];
          const pW = clamp(14 + Number(lowestPart?.diameter || 0.15) * 100, 12, 50) * zoom;
          ctx.globalCompositeOperation = 'screen';
          
          // VAKUM ETKİSİ: İrtifa arttıkça plume (alev) genişler
          // alt=0 -> factor=1, alt=100km -> factor=4.0
          const plumeExpand = clamp(1 + (sim.alt / 25000), 1, 4.0);
          const glowR = (pW * 2.5 + Math.random() * 6) * (plumeExpand * 0.7);
          
          const glow = ctx.createRadialGradient(W / 2, baseEngineY, 0, W / 2, baseEngineY, glowR);
          glow.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
          // İrtifa arttıkça renk turuncudan mavimsi plazmaya döner
          if (sim.alt > 35000) {
            glow.addColorStop(0.2, 'rgba(100, 200, 255, 0.7)');
            glow.addColorStop(1, 'rgba(0, 50, 255, 0)');
          } else {
            glow.addColorStop(0.2, 'rgba(255, 200, 50, 0.8)');
            glow.addColorStop(0.5, 'rgba(255, 100, 0, 0.4)');
            glow.addColorStop(1, 'rgba(255, 50, 0, 0)');
          }
          
          ctx.fillStyle = glow;
          ctx.beginPath();
          // Vakumda alev aşağı doğru daha uzun ve yayvan olur
          ctx.ellipse(W / 2, baseEngineY + glowR * 0.4, glowR * 0.8, glowR * 1.5, 0, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.restore();

        // ─── TELEMETRİ OVERLAY GÜNCELLEME (Mach Eklendi) ───
        const machEl = document.getElementById('mach-val');
        if (machEl) machEl.innerText = `M ${sim.mach.toFixed(2)}`;

        // Rapor butonunu göster / gizle (SADECE BAŞARILI UÇUŞTA)
        const btn = document.getElementById('report-btn');
        if (state.running && state.trajectory && sim.t >= state.trajectory.length * 0.016666 && sim.phase !== 'CRASH') {
           if (btn) btn.style.display = 'flex';
        } else {
           if (btn) btn.style.display = 'none';
        }

        frameRef.current = requestAnimationFrame(loop);
      } catch (err) {
        console.error('[RocketCanvas] Render loop crashed:', err);
        frameRef.current = requestAnimationFrame(loop);
      }
    };

    frameRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameRef.current);
  }, []);

  const [modalOpen, setModalOpen] = React.useState(false);
  const reportData = useSimStore(s => s.reportData);
  const phase = useSimStore(s => s.phase);

  return (
    <>
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full z-0 block" />
      
      {/* 💥 CRASH BAŞARISIZLIK OVERLAY */}
      {phase === 'CRASH' && (
        <div className="absolute inset-0 z-40 flex flex-col items-center justify-center pointer-events-none">
          <div className="bg-red-950/60 backdrop-blur-sm border-2 border-red-500/50 rounded-2xl px-12 py-8 flex flex-col items-center gap-4 shadow-[0_0_80px_rgba(255,0,0,0.3)] animate-pulse pointer-events-auto">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
            <div className="text-3xl font-black text-red-500 tracking-[0.3em] uppercase">
              SİMÜLASYON BAŞARISIZ
            </div>
            <div className="text-sm text-red-300/70 text-center">Roket yere çakılarak imha oldu ve tüm veriler kayboldu!</div>
          </div>
        </div>
      )}

      {/* HUD GİZLİ RAPOR BUTONU (başarılı uçuş için) */}
      <button 
        id="report-btn"
        className="hidden absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-[var(--color-plasma-blue)] hover:bg-[#00e5ff] text-black px-8 py-4 rounded-full font-black tracking-widest uppercase shadow-[0_0_30px_var(--color-plasma-blue-dim)] transition-all animate-bounce items-center gap-3"
        style={{ display: 'none' }}
        onClick={() => setModalOpen(true)}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        SİMÜLASYON RAPORUNU GÖR
      </button>

      {/* RAPOR MODALI */}
      {modalOpen && reportData && (
        <div className="absolute inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center p-8">
           <div className="bg-[var(--color-space-900)] border border-[var(--color-plasma-blue)]/30 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-[0_0_60px_var(--color-plasma-blue-dim)] flex flex-col">
              <div className="sticky top-0 bg-[var(--color-space-900)]/90 backdrop-blur border-b border-white/10 p-5 pl-7 flex items-center justify-between z-10">
                 <div>
                    <h2 className="text-xl font-black text-white flex items-center gap-2">
                       <svg className="text-[var(--color-plasma-blue)]" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                       SİMÜLASYON RAPORU
                    </h2>
                    <p className="text-[10px] uppercase tracking-[0.2em] text-white/50 mt-1">Sistem Fiziği (fizik.txt) Uyumlu Analiz</p>
                 </div>
                 <button onClick={() => setModalOpen(false)} className="text-white/50 hover:text-white p-2 bg-white/5 hover:bg-white/10 rounded-full transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                 </button>
              </div>

              <div className="p-7">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                   <div className="bg-[var(--color-thrust-orange)]/10 border border-[var(--color-thrust-orange)]/20 p-4 rounded-xl">
                      <div className="text-[10px] uppercase text-[var(--color-thrust-orange)] font-bold mb-1">Maks İrtifa</div>
                      <div className="text-2xl font-black text-white">{reportData.ozet.maks_irtifa_m.toLocaleString()}<span className="text-sm text-white/50 font-normal">m</span></div>
                   </div>
                   <div className="bg-[var(--color-plasma-blue)]/10 border border-[var(--color-plasma-blue)]/20 p-4 rounded-xl">
                      <div className="text-[10px] uppercase text-[var(--color-plasma-blue)] font-bold mb-1">Maks Hız</div>
                      <div className="text-2xl font-black text-white">{reportData.ozet.maks_hiz_ms.toLocaleString()}<span className="text-sm text-white/50 font-normal">m/s</span></div>
                   </div>
                   <div className="bg-white/5 border border-white/10 p-4 rounded-xl">
                      <div className="text-[10px] uppercase text-white/60 font-bold mb-1">Uçuş Süresi</div>
                      <div className="text-2xl font-black text-white">{reportData.ozet.toplam_ucus_suresi_s.toLocaleString()}<span className="text-sm text-white/50 font-normal">s</span></div>
                   </div>
                   <div className="bg-white/5 border border-white/10 p-4 rounded-xl">
                      <div className="text-[10px] uppercase text-white/60 font-bold mb-1">Maks İvme</div>
                      <div className="text-2xl font-black text-white">{reportData.ozet.maks_ivme_ms2.toLocaleString()}<span className="text-sm text-white/50 font-normal">m/s²</span></div>
                   </div>
                </div>

                <div className="mb-8">
                   <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2 border-b border-white/10 pb-2">
                       Aşama (Kademe) Fizik Verileri
                   </h3>
                   <div className="overflow-x-auto">
                     <table className="w-full text-left text-sm text-white">
                        <thead>
                           <tr className="bg-white/5 text-[10px] uppercase tracking-widest text-white/50">
                              <th className="p-3 rounded-tl-lg">Kademe</th>
                              <th className="p-3">Ayrılma Zamanı</th>
                              <th className="p-3">Ayrılma İrtifası</th>
                              <th className="p-3 rounded-tr-lg">Hız & Delta-V</th>
                           </tr>
                        </thead>
                        <tbody>
                           {reportData.kademeler.map((k, i) => (
                              <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                                 <td className="p-3 font-bold text-[var(--color-plasma-blue)]">{k.kademe_no}. Kademe</td>
                                 <td className="p-3 font-mono">{k.ayrilma_zamani_s} s</td>
                                 <td className="p-3 font-mono text-[var(--color-thrust-orange)]">{k.ayrilma_irtifasi_m} m</td>
                                 <td className="p-3 font-mono">
                                    {k.ayrilma_hizi_ms} m/s 
                                    <span className="text-white/40 ml-2 text-xs">(Δv: {k.delta_v_ms})</span>
                                 </td>
                              </tr>
                           ))}
                           {reportData.kademeler.length === 0 && (
                              <tr>
                                <td colSpan={4} className="p-5 text-center text-white/40 italic">Kademe ayrılması gerçekleşmedi.</td>
                              </tr>
                           )}
                        </tbody>
                     </table>
                   </div>
                </div>

                {/* 🧠 ENKAZ ANALİZİ — Monte Carlo */}
                {reportData.enkaz_analizi && reportData.enkaz_analizi.length > 0 && (
                   <div className="mb-8">
                     <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2 border-b border-red-500/30 pb-2">
                         <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                         <span className="text-red-400">Enkaz Düşüş Bölgesi Analizi</span>
                         <span className="text-[9px] text-white/30 font-normal ml-auto">Monte Carlo × 200 simülasyon</span>
                     </h3>
                     <div className="flex flex-col gap-4">
                        {reportData.enkaz_analizi.map((d, i) => (
                           <div key={i} className="bg-red-950/20 border border-red-500/15 rounded-xl p-5">
                              <div className="flex items-center justify-between mb-3">
                                 <div className="text-sm font-bold text-red-400">{d.kademe_adi}</div>
                                 <div className="text-[10px] text-white/40 uppercase">Ayrılma: {d.ayrilma_irtifasi_m}m</div>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                 <div className="bg-black/30 rounded-lg p-3">
                                    <div className="text-[9px] uppercase text-red-400/70 font-bold mb-1">Tehlike Yarıçapı</div>
                                    <div className="text-xl font-black text-red-400">{d.maks_sapma_yaricapi_km}<span className="text-xs text-white/40 font-normal"> km</span></div>
                                 </div>
                                 <div className="bg-black/30 rounded-lg p-3">
                                    <div className="text-[9px] uppercase text-white/50 font-bold mb-1">Toplam Yayılım</div>
                                    <div className="text-xl font-black text-white">{d.toplam_yayilim_km}<span className="text-xs text-white/40 font-normal"> km</span></div>
                                 </div>
                                 <div className="bg-black/30 rounded-lg p-3">
                                    <div className="text-[9px] uppercase text-white/50 font-bold mb-1">Ort. Düşüş</div>
                                    <div className="text-xl font-black text-white">{d.ortalama_dusus_mesafesi_m}<span className="text-xs text-white/40 font-normal"> m</span></div>
                                 </div>
                              </div>
                              <div className="mt-3 text-[10px] text-white/30 flex justify-between">
                                 <span>Min: {d.min_dusus_m}m | Max: {d.max_dusus_m}m</span>
                                 <span>{d.simulasyon_sayisi} simülasyon</span>
                              </div>
                           </div>
                        ))}
                     </div>
                   </div>
                )}

                {reportData.uyarilar && reportData.uyarilar.length > 0 && (
                   <div>
                     <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                         Son Uçuş Bildirimleri
                     </h3>
                     <div className="bg-black/40 rounded-xl p-4 border border-white/5 flex flex-col gap-2">
                        {reportData.uyarilar.map((u, i) => (
                           <div key={i} className="flex gap-3 text-xs text-white/70">
                               <span className="text-[var(--color-plasma-blue)]">›</span> {u}
                           </div>
                        ))}
                     </div>
                   </div>
                )}
              </div>
           </div>
        </div>
      )}
    </>
  );
}
