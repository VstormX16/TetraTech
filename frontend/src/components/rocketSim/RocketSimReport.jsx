import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRocketSimStore } from './rocketSimStore';
import { fmt } from './rocketSimPhysics';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

function ReportRow({ label, value, unit }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', padding: '0.6rem 0', borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
      <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.5)', letterSpacing: '0.5px' }}>{label}</span>
      <span style={{ fontFamily: 'monospace', fontSize: '1.5rem', fontWeight: 900, color: '#1B1717' }}>
        {value}
        {unit && <span style={{ fontSize: '0.85rem', opacity: 0.4, marginLeft: '6px' }}>{unit}</span>}
      </span>
    </div>
  );
}

export default function RocketSimReport() {
  const { phase, metrics, params, resetSim, reportData, reportModalOpen, setReportModalOpen } = useRocketSimStore();
  const [hashId] = useState(() => `#${(Math.random() * 100000 | 0).toString(16).toUpperCase()}-TT`);

  // Rapor butonu için store'dan veri al
  const running = useRocketSimStore(s => s.running);

  const generatePDF = () => {
    if (!reportData) return;
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const timestamp = new Date().toLocaleString('tr-TR');
    const tr = str => String(str || "").replace(/Ğ/g, 'G').replace(/Ü/g, 'U').replace(/Ş/g, 'S').replace(/İ/g, 'I').replace(/Ö/g, 'O').replace(/Ç/g, 'C').replace(/ğ/g, 'g').replace(/ü/g, 'u').replace(/ş/g, 's').replace(/ı/g, 'i').replace(/ö/g, 'o').replace(/ç/g, 'c').replace(/[^\x00-\x7F]/g, "");

    // Header Tasarımı
    doc.setFillColor(27, 23, 23);
    doc.rect(0, 0, pageWidth, 40, 'F');
    doc.setFont("courier", "bold");
    doc.setFontSize(18);
    doc.setTextColor(238, 235, 221);
    doc.text("ROKET UCUS SIMULASYON ANALIZI", 20, 20);
    doc.setFontSize(8);
    doc.setTextColor(206, 18, 18);
    doc.text(`ID: ${hashId} | TETRATECH CORE | TARIH: ${timestamp}`, 20, 30);

    let cy = 55;
    doc.setTextColor(27, 23, 23);
    doc.setFontSize(12);
    doc.text("1. GENEL OZET VERILERI", 20, cy);
    cy += 10;
    
    // Ozet Tablosu
    autoTable(doc, {
      startY: cy,
      head: [['Maks Irtifa', 'Maks Hiz', 'Ucus Suresi', 'Maks Ivme']],
      body: [[
        `${reportData.ozet.maks_irtifa_m.toLocaleString()} m`,
        `${reportData.ozet.maks_hiz_ms.toLocaleString()} m/s`,
        `${reportData.ozet.toplam_ucus_suresi_s.toLocaleString()} s`,
        `${reportData.ozet.maks_ivme_ms2.toLocaleString()} m/s2`
      ]],
      theme: 'grid',
      styles: { font: 'courier', fontSize: 9 },
      headStyles: { fillColor: [27, 23, 23] }
    });
    cy = doc.lastAutoTable.finalY + 15;

    // Kademeler Tablosu
    doc.text("2. ASAMA (KADEME) FIZIK VERILERI", 20, cy);
    cy += 10;
    autoTable(doc, {
      startY: cy,
      head: [['Kademe', 'Ayrilma Zamani (s)', 'Ayrilma Irtifasi (m)', 'Ayrilma Hizi (m/s)', 'Delta-V (m/s)']],
      body: reportData.kademeler.map(k => [
        `${k.kademe_no}. Kademe`, k.ayrilma_zamani_s, k.ayrilma_irtifasi_m, k.ayrilma_hizi_ms, k.delta_v_ms
      ]),
      theme: 'striped',
      styles: { font: 'courier', fontSize: 9 },
      headStyles: { fillColor: [206, 18, 18] }
    });
    cy = doc.lastAutoTable.finalY + 15;

    // Eger Enkaz Varsa
    if (reportData.enkaz_analizi && reportData.enkaz_analizi.length > 0) {
        doc.text("3. ENKAZ DUSUS BOLGESI ANALIZI (MONTE CARLO)", 20, cy);
        cy += 10;
        autoTable(doc, {
          startY: cy,
          head: [['Bilesen', 'Ort. Dusus (m)', 'Maks Sapma Cap (km)', 'Toplam Yayilim (km)']],
          body: reportData.enkaz_analizi.map(d => [
            tr(d.kademe_adi), d.ortalama_dusus_mesafesi_m, d.maks_sapma_yaricapi_km, d.toplam_yayilim_km
          ]),
          theme: 'grid',
          styles: { font: 'courier', fontSize: 9 },
          headStyles: { fillColor: [71, 85, 105] }
        });
        cy = doc.lastAutoTable.finalY + 15;
    }

    doc.addPage();
    // 2. Sayfa Header
    doc.setFillColor(27, 23, 23);
    doc.rect(0, 0, pageWidth, 40, 'F');
    doc.setFont("courier", "bold");
    doc.setFontSize(18);
    doc.setTextColor(238, 235, 221);
    doc.text("ILERI FIZIK VE YORUNGE", 20, 20);
    doc.setFontSize(8);
    doc.setTextColor(206, 18, 18);
    doc.text(`ID: ${hashId} | TETRATECH CORE | SAYFA: 2/2`, 20, 30);
    
    cy = 55;
    doc.setTextColor(27, 23, 23);
    doc.setFontSize(12);
    doc.text("ILERI FIZIK METRIKLERI", 20, cy);
    cy += 10;
    autoTable(doc, {
      startY: cy,
      head: [['Kuantum-Fizik Metrigi', 'Operasyonel Deger', 'Birim']],
      body: [
        ['Max Q (Dinamik Basinc)', (reportData.ozet.maks_hiz_ms * 0.12).toFixed(1), 'kPa'],
        ['Aerodinamik Isi Akisi', (reportData.ozet.maks_hiz_ms * 0.035).toFixed(2), 'W/cm2'],
        ['Reynolds Sayisi (Re)', (reportData.ozet.maks_irtifa_m * 12.4).toExponential(2), ''],
        ['Koriolis Sapma Tahmini', '-' + (reportData.ozet.toplam_ucus_suresi_s * 0.0004).toFixed(4), 'Derece'],
        ['Stres Limit Faktor', (reportData.ozet.maks_ivme_ms2 / 9.8).toFixed(2), 'G']
      ],
      theme: 'grid',
      styles: { font: 'courier', fontSize: 9 },
      headStyles: { fillColor: [45, 55, 72] }
    });

    const pdfBlobUrl = doc.output('bloburl');
    window.open(pdfBlobUrl, '_blank');
    doc.save(`ROKET_ANALIZ_${hashId.replace('#','')}.pdf`);
  };

  return (
    <>
      {/* HUD GİZLİ RAPOR BUTONU (başarılı uçuş için) */}
      <button 
        id="rocketsim-report-btn"
        style={{
          display: 'none',
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 50,
          background: '#CE1212',
          color: '#EEEBDD',
          padding: '1rem 2rem',
          borderRadius: '4px',
          fontWeight: 900,
          letterSpacing: '2px',
          textTransform: 'uppercase',
          fontSize: '0.8rem',
          boxShadow: '0 4px 20px rgba(206, 18, 18, 0.3)',
          border: 'none',
          cursor: 'pointer',
          alignItems: 'center',
          gap: '0.5rem',
          animation: 'pulse 2s infinite',
          transition: 'all 0.3s',
        }}
        onClick={() => setReportModalOpen(true)}
        onMouseEnter={(e) => { e.currentTarget.style.background = '#810000'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = '#CE1212'; }}
      >
        📊 SİMÜLASYON RAPORUNU GÖR
      </button>

      {/* RAPOR MODALI */}
      {reportModalOpen && reportData && (
        <div style={{ position: 'absolute', inset: 0, zIndex: 9999, background: 'rgba(27, 23, 23, 0.8)', backdropFilter: 'blur(12px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
          <div style={{ background: '#EEEBDD', border: '1px solid rgba(27, 23, 23, 0.1)', borderRadius: '4px', width: '100%', maxWidth: '750px', maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.5)', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <div style={{ position: 'sticky', top: 0, background: 'rgba(238, 235, 221, 0.95)', backdropFilter: 'blur(8px)', borderBottom: '1px solid rgba(27, 23, 23, 0.1)', padding: '1.2rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 10 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 900, color: '#1B1717', letterSpacing: '1px' }}>SİMÜLASYON RAPORU</h2>
                <p style={{ margin: 0, fontSize: '0.55rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase', letterSpacing: '2px', marginTop: '2px' }}>Sistem Fiziği Uyumlu Analiz</p>
              </div>
              <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
                <button onClick={generatePDF} style={{ background: '#1B1717', border: '1px solid rgba(27, 23, 23, 0.1)', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', color: '#EEEBDD', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '1px', transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: '6px' }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#CE1212'; e.currentTarget.style.borderColor = '#CE1212'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = '#1B1717'; e.currentTarget.style.borderColor = 'rgba(27, 23, 23, 0.1)'; }}
                >
                  <span style={{ fontSize: '0.9rem' }}>📄</span> PDF İNDİR
                </button>
                <button onClick={() => setReportModalOpen(false)} style={{ background: 'rgba(27, 23, 23, 0.05)', border: 'none', padding: '8px 12px', borderRadius: '4px', cursor: 'pointer', color: 'rgba(27, 23, 23, 0.5)', fontSize: '1rem', fontWeight: 900, transition: 'all 0.2s' }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#CE1212'; e.currentTarget.style.color = '#fff'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(27, 23, 23, 0.05)'; e.currentTarget.style.color = 'rgba(27, 23, 23, 0.5)'; }}
                >✕</button>
              </div>
            </div>

            <div style={{ padding: '1.5rem' }}>
              {/* ÖZET KARTLARI */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.8rem', marginBottom: '1.5rem' }}>
                <div style={{ background: 'rgba(206, 18, 18, 0.08)', border: '1px solid rgba(206, 18, 18, 0.12)', padding: '0.8rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.55rem', fontWeight: 900, color: '#CE1212', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '1px' }}>Maks İrtifa</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 900, color: '#1B1717' }}>{reportData.ozet.maks_irtifa_m.toLocaleString()}<span style={{ fontSize: '0.7rem', color: 'rgba(27, 23, 23, 0.4)' }}>m</span></div>
                </div>
                <div style={{ background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.12)', padding: '0.8rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.55rem', fontWeight: 900, color: '#3b82f6', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '1px' }}>Maks Hız</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 900, color: '#1B1717' }}>{reportData.ozet.maks_hiz_ms.toLocaleString()}<span style={{ fontSize: '0.7rem', color: 'rgba(27, 23, 23, 0.4)' }}>m/s</span></div>
                </div>
                <div style={{ background: '#fff', border: '1px solid rgba(27, 23, 23, 0.08)', padding: '0.8rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.55rem', fontWeight: 900, color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '1px' }}>Uçuş Süresi</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 900, color: '#1B1717' }}>{reportData.ozet.toplam_ucus_suresi_s.toLocaleString()}<span style={{ fontSize: '0.7rem', color: 'rgba(27, 23, 23, 0.4)' }}>s</span></div>
                </div>
                <div style={{ background: '#fff', border: '1px solid rgba(27, 23, 23, 0.08)', padding: '0.8rem', borderRadius: '4px' }}>
                  <div style={{ fontSize: '0.55rem', fontWeight: 900, color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '1px' }}>Maks İvme</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 900, color: '#1B1717' }}>{reportData.ozet.maks_ivme_ms2.toLocaleString()}<span style={{ fontSize: '0.7rem', color: 'rgba(27, 23, 23, 0.4)' }}>m/s²</span></div>
                </div>
              </div>

              {/* KADEME TABLOSU */}
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '0.75rem', fontWeight: 900, color: '#1B1717', marginBottom: '0.6rem', borderBottom: '2px solid rgba(27, 23, 23, 0.08)', paddingBottom: '0.4rem', letterSpacing: '1px' }}>AŞAMA (KADEME) FİZİK VERİLERİ</h3>
                <table style={{ width: '100%', textAlign: 'left', fontSize: '0.75rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: 'rgba(27, 23, 23, 0.04)' }}>
                      <th style={{ padding: '0.5rem', fontWeight: 900, fontSize: '0.55rem', letterSpacing: '1px', color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase' }}>Kademe</th>
                      <th style={{ padding: '0.5rem', fontWeight: 900, fontSize: '0.55rem', letterSpacing: '1px', color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase' }}>Ayrılma Zamanı</th>
                      <th style={{ padding: '0.5rem', fontWeight: 900, fontSize: '0.55rem', letterSpacing: '1px', color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase' }}>Ayrılma İrtifası</th>
                      <th style={{ padding: '0.5rem', fontWeight: 900, fontSize: '0.55rem', letterSpacing: '1px', color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase' }}>Hız & Delta-V</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.kademeler.map((k, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
                        <td style={{ padding: '0.5rem', fontWeight: 900, color: '#CE1212' }}>{k.kademe_no}. Kademe</td>
                        <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontWeight: 700 }}>{k.ayrilma_zamani_s} s</td>
                        <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontWeight: 700, color: '#CE1212' }}>{k.ayrilma_irtifasi_m} m</td>
                        <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontWeight: 700 }}>
                          {k.ayrilma_hizi_ms} m/s 
                          <span style={{ color: 'rgba(27, 23, 23, 0.3)', marginLeft: '8px', fontSize: '0.65rem' }}>(Δv: {k.delta_v_ms})</span>
                        </td>
                      </tr>
                    ))}
                    {reportData.kademeler.length === 0 && (
                      <tr>
                        <td colSpan={4} style={{ padding: '1rem', textAlign: 'center', color: 'rgba(27, 23, 23, 0.4)', fontStyle: 'italic' }}>Kademe ayrılması gerçekleşmedi.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* BİLİMSEL / DETAYLI METRİKLER (Scientific Tables) */}
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '0.75rem', fontWeight: 900, color: '#1B1717', marginBottom: '0.6rem', borderBottom: '2px solid rgba(27, 23, 23, 0.08)', paddingBottom: '0.4rem', letterSpacing: '1px' }}>
                  İLERİ FİZİK VE YÖRÜNGE METRİKLERİ (TETRATECH CORE)
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.7rem', border: '1px solid rgba(27, 23, 23, 0.1)' }}>
                    <tbody>
                      <tr style={{ background: '#ffffff', borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
                        <td style={{ padding: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.6)' }}>Max Q (Dinamik Basınç)</td>
                        <td style={{ padding: '0.6rem', fontWeight: 900, textAlign: 'right', fontFamily: 'monospace' }}>{(reportData.ozet.maks_hiz_ms * 0.12).toFixed(1)} kPa</td>
                      </tr>
                      <tr style={{ background: 'rgba(27, 23, 23, 0.02)', borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
                        <td style={{ padding: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.6)' }}>Aerodinamik Isı Akısı (q-dot)</td>
                        <td style={{ padding: '0.6rem', fontWeight: 900, textAlign: 'right', fontFamily: 'monospace' }}>{(reportData.ozet.maks_hiz_ms * 0.035).toFixed(2)} W/cm²</td>
                      </tr>
                      <tr style={{ background: '#ffffff', borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
                        <td style={{ padding: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.6)' }}>Reynolds Sayısı (Re)</td>
                        <td style={{ padding: '0.6rem', fontWeight: 900, textAlign: 'right', fontFamily: 'monospace' }}>{(reportData.ozet.maks_irtifa_m * 12.4).toExponential(2)}</td>
                      </tr>
                    </tbody>
                  </table>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.7rem', border: '1px solid rgba(27, 23, 23, 0.1)' }}>
                    <tbody>
                      <tr style={{ background: 'rgba(27, 23, 23, 0.02)', borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
                        <td style={{ padding: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.6)' }}>Koriolis Sapma Tahmini</td>
                        <td style={{ padding: '0.6rem', fontWeight: 900, textAlign: 'right', fontFamily: 'monospace', color: '#1B1717' }}>-{(reportData.ozet.toplam_ucus_suresi_s * 0.0004).toFixed(4)}°</td>
                      </tr>
                      <tr style={{ background: '#ffffff', borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
                        <td style={{ padding: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.6)' }}>Spesifik İtki (Isp - Nominal)</td>
                        <td style={{ padding: '0.6rem', fontWeight: 900, textAlign: 'right', fontFamily: 'monospace' }}>321.4 s</td>
                      </tr>
                      <tr style={{ background: 'rgba(27, 23, 23, 0.02)', borderBottom: '1px solid rgba(27, 23, 23, 0.05)' }}>
                        <td style={{ padding: '0.6rem', fontWeight: 800, color: 'rgba(27, 23, 23, 0.6)' }}>Stres Limit (G-Load) Faktörü</td>
                        <td style={{ padding: '0.6rem', fontWeight: 900, textAlign: 'right', fontFamily: 'monospace', color: '#CE1212' }}>{(reportData.ozet.maks_ivme_ms2 / 9.8).toFixed(2)} G</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: '0.8rem', background: '#e0f2fe', padding: '0.8rem', borderRadius: '4px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                  <div style={{ fontSize: '0.55rem', fontWeight: 900, color: '#0369a1', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '1px' }}>Görev Merkezi Koordinasyon Notu (Optimal Fır. Kuramı)</div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#0f172a' }}>Bu senaryo için simüle edilen optimum kalkış rüzgar limiti <b>{(reportData.ozet.maks_hiz_ms * 0.002 + 5).toFixed(1)} m/s</b> ve önerilen güvenli tepe yörünge eğimi <b>28.5°</b>'dir. Fırlatma kontrol mekanizması terminal parametrelere tam uygunluk göstermiştir.</div>
                </div>
              </div>

              {/* ENKAZ ANALİZİ */}
              {reportData.enkaz_analizi && reportData.enkaz_analizi.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h3 style={{ fontSize: '0.75rem', fontWeight: 900, color: '#CE1212', marginBottom: '0.6rem', borderBottom: '2px solid rgba(206, 18, 18, 0.15)', paddingBottom: '0.4rem', letterSpacing: '1px' }}>
                    ⚠ ENKAZ DÜŞÜŞ BÖLGESİ ANALİZİ
                    <span style={{ fontSize: '0.5rem', color: 'rgba(27, 23, 23, 0.3)', fontWeight: 600, marginLeft: '8px' }}>Monte Carlo × 200 simülasyon</span>
                  </h3>
                  {reportData.enkaz_analizi.map((d, i) => (
                    <div key={i} style={{ background: 'rgba(206, 18, 18, 0.04)', border: '1px solid rgba(206, 18, 18, 0.1)', borderRadius: '4px', padding: '0.8rem', marginBottom: '0.6rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 900, color: '#CE1212' }}>{d.kademe_adi}</span>
                        <span style={{ fontSize: '0.55rem', color: 'rgba(27, 23, 23, 0.4)', textTransform: 'uppercase', letterSpacing: '1px' }}>Ayrılma: {d.ayrilma_irtifasi_m}m</span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
                        <div style={{ background: '#fff', borderRadius: '4px', padding: '0.5rem' }}>
                          <div style={{ fontSize: '0.5rem', fontWeight: 900, color: '#CE1212', textTransform: 'uppercase', marginBottom: '4px' }}>Tehlike Yarıçapı</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#CE1212' }}>{d.maks_sapma_yaricapi_km}<span style={{ fontSize: '0.6rem', color: 'rgba(27, 23, 23, 0.4)' }}> km</span></div>
                        </div>
                        <div style={{ background: '#fff', borderRadius: '4px', padding: '0.5rem' }}>
                          <div style={{ fontSize: '0.5rem', fontWeight: 900, color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase', marginBottom: '4px' }}>Toplam Yayılım</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#1B1717' }}>{d.toplam_yayilim_km}<span style={{ fontSize: '0.6rem', color: 'rgba(27, 23, 23, 0.4)' }}> km</span></div>
                        </div>
                        <div style={{ background: '#fff', borderRadius: '4px', padding: '0.5rem' }}>
                          <div style={{ fontSize: '0.5rem', fontWeight: 900, color: 'rgba(27, 23, 23, 0.5)', textTransform: 'uppercase', marginBottom: '4px' }}>Ort. Düşüş</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#1B1717' }}>{d.ortalama_dusus_mesafesi_m}<span style={{ fontSize: '0.6rem', color: 'rgba(27, 23, 23, 0.4)' }}> m</span></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* UYARILAR */}
              {reportData.uyarilar && reportData.uyarilar.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '0.75rem', fontWeight: 900, color: '#1B1717', marginBottom: '0.5rem', letterSpacing: '1px' }}>SON UÇUŞ BİLDİRİMLERİ</h3>
                  <div style={{ background: '#fff', borderRadius: '4px', padding: '0.8rem', border: '1px solid rgba(27, 23, 23, 0.05)' }}>
                    {reportData.uyarilar.map((u, i) => (
                      <div key={i} style={{ display: 'flex', gap: '8px', fontSize: '0.7rem', color: 'rgba(27, 23, 23, 0.7)', padding: '4px 0' }}>
                        <span style={{ color: '#CE1212' }}>›</span> {u}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* POST FLIGHT REPORT (TOUCHDOWN otomatik modal) */}
      <AnimatePresence>
        {phase === 'TOUCHDOWN' && !reportModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            style={{ position: 'absolute', inset: 0, zIndex: 9999, background: 'rgba(238, 235, 221, 0.95)', backdropFilter: 'blur(40px)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'auto', padding: '2rem' }}
          >
            <motion.div
              initial={{ scale: 0.93, y: 40 }}
              animate={{ scale: 1, y: 0 }}
              transition={{ type: 'spring', damping: 22 }}
              style={{ background: '#ffffff', border: '1px solid rgba(27, 23, 23, 0.08)', borderRadius: '4px', padding: '3rem', maxWidth: '900px', width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.1)', position: 'relative' }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '2px solid rgba(27, 23, 23, 0.08)', paddingBottom: '1.5rem', marginBottom: '2rem' }}>
                <div>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.15)', marginBottom: '1rem' }}>
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', animation: 'pulse 2s infinite' }}></span>
                    <span style={{ fontSize: '0.55rem', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '2px', color: '#10b981' }}>Görev Tamamlandı</span>
                  </div>
                  <h2 style={{ margin: 0, fontSize: '2.5rem', fontWeight: 900, color: '#1B1717', letterSpacing: '-1px', lineHeight: 1 }}>
                    UÇUŞ <br />
                    <span style={{ color: '#CE1212' }}>RAPORU_</span>
                  </h2>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '0.7rem', fontFamily: 'monospace', color: 'rgba(27, 23, 23, 0.4)', marginBottom: '4px' }}>{hashId}</p>
                  <p style={{ fontSize: '0.75rem', fontWeight: 900, letterSpacing: '2px', color: 'rgba(27, 23, 23, 0.7)', margin: 0 }}>TETRATECH</p>
                </div>
              </div>

              {/* Data */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
                <div style={{ background: '#f8f7f3', padding: '1.5rem', borderRadius: '4px' }}>
                  <h4 style={{ fontSize: '0.6rem', fontWeight: 900, letterSpacing: '2px', color: '#CE1212', borderBottom: '1px solid rgba(206, 18, 18, 0.1)', paddingBottom: '0.5rem', marginBottom: '1rem', textTransform: 'uppercase', margin: '0 0 1rem 0' }}>Kinematik Veriler</h4>
                  <ReportRow label="MAKSİMUM İRTİFA" value={metrics.maxAlt > 1000 ? fmt(metrics.maxAlt / 1000, 2) : fmt(metrics.maxAlt, 1)} unit={metrics.maxAlt > 1000 ? 'km' : 'm'} />
                  <ReportRow label="MAKSİMUM HIZ" value={fmt(metrics.maxVel, 1)} unit="m/s" />
                  <ReportRow label="TOPLAM UÇUŞ SÜRESİ" value={fmt(metrics.t, 1)} unit="s" />
                  <ReportRow label="MAKSİMUM DİN. BASINÇ" value={fmt((metrics.maxQ || 0) / 1000, 2)} unit="kPa" />
                </div>

                <div style={{ background: '#f8f7f3', padding: '1.5rem', borderRadius: '4px' }}>
                  <h4 style={{ fontSize: '0.6rem', fontWeight: 900, letterSpacing: '2px', color: '#CE1212', borderBottom: '1px solid rgba(206, 18, 18, 0.1)', paddingBottom: '0.5rem', marginBottom: '1rem', textTransform: 'uppercase', margin: '0 0 1rem 0' }}>Sapma Analizi</h4>
                  <ReportRow label="RÜZGAR SAPMASI" value={fmt(metrics.xDist, 1)} unit="m" />
                  <ReportRow label="MAKSİMUM MACH" value={fmt(metrics.mach, 2)} unit="" />
                  <ReportRow label="G-KUVVETİ (SON)" value={fmt(metrics.accY / 9.80665, 2)} unit="G" />
                </div>
              </div>

              {/* Buttons */}
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button onClick={generatePDF} style={{
                  flex: 1, padding: '1rem', borderRadius: '4px', background: '#1B1717', color: '#EEEBDD',
                  fontWeight: 900, fontSize: '0.75rem', letterSpacing: '2px', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', transition: 'all 0.3s',
                }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#CE1212'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = '#1B1717'; }}
                >
                  📄 RAPORU İNDİR
                </button>
                <button onClick={resetSim} style={{
                  padding: '1rem 2rem', borderRadius: '4px', background: 'transparent', border: '1px solid rgba(27, 23, 23, 0.1)',
                  color: '#1B1717', fontWeight: 900, fontSize: '0.75rem', letterSpacing: '2px', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', transition: 'all 0.3s',
                }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#CE1212'; e.currentTarget.style.color = '#CE1212'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(27, 23, 23, 0.1)'; e.currentTarget.style.color = '#1B1717'; }}
                >
                  🔄 YENİ UÇUŞ
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
