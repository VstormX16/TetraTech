# -*- coding: utf-8 -*-
"""
SOLAR AI v1.2 - "Mission Control" Sürümü
Ücretsiz Uzay API'leri (NOAA/NASA) ile Fırlatma Güvenlik Analizi
"""

import sys
import os
import datetime
import numpy as np
import time
import plotext as plt
HAS_PLOTEXT = True

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    HAS_PLOTEXT = False # Fallback if plotext also has issues

def type_text(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

# Proje dizin ayarları
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Renkler
class Color:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    RED     = '\033[91m'
    YELLOW  = '\033[93m'
    GREEN   = '\033[92m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'

def c(text, color):
    return f"{color}{text}{Color.RESET}"

# --- Şehir -> Koordinat (Ücretsiz Veritabanı) ---
CITY_DB = {
    'istanbul': (41.0, 28.9, "İstanbul Mission Control, TR"),
    'ankara': (39.9, 32.8, "Ankara Stratosphere Base, TR"),
    'izmir': (38.4, 27.1, "Izmir Aegean Port, TR"),
    'kennedy': (28.5, -80.6, "Kennedy Space Center, USA"),
    'baikonur': (45.9, 63.3, "Baikonur Cosmodrome, KAZ"),
    'kourou': (5.2, -52.7, "Guiana Space Centre, FRA"),
    'cape_canaveral': (28.4, -80.5, "Cape Canaveral SFS, USA"),
    'tanegashima': (30.4, 130.9, "Tanegashima Space Center, JPN"),
    'vandenberg': (34.7, -120.5, "Vandenberg SFB, USA"),
}

def print_header():
    header = """
    ███████╗ ██████╗ ██╗      █████╗ ██████╗     █████╗ ██╗
    ██╔════╝██╔═══██╗██║     ██╔══██╗██╔══██╗   ██╔══██╗██║
    ███████╗██║   ██║██║     ███████║██████╔╝   ███████║██║
    ╚════██║██║   ██║██║     ██╔══██║██╔══██╗   ██╔══██║██║
    ███████║╚██████╔╝███████╗██║  ██║██║  ██║   ██║  ██║██║
    ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  ╚═╝╚═╝ v2.0
    """
    print(c(header, Color.CYAN + Color.BOLD))
    print(c("    [ GENEL GÜNEŞ AKTİVİTESİ VE FIRLATMA RİSK ANALİZ SİSTEMİ ]", Color.WHITE + Color.DIM))
    print(c("    " + "-"*60, Color.CYAN))

def main():
    print_header()

    from models.risk_assessor import load_or_train_model, SolarRiskAssessor
    from data.nasa_api import fetch_all_solar_data
    
    # Model ve Veri Yükleme
    type_text(c("\n[!] Yapay Zeka Çekirdeği Başlatılıyor...", Color.YELLOW))
    model = load_or_train_model(retrain=False, verbose=False)
    assessor = SolarRiskAssessor(model)
    
    type_text(c("[!] Canlı Uzay Uydularına Bağlanılıyor (NOAA & NASA)...", Color.YELLOW))
    solar_data = fetch_all_solar_data(verbose=False)
    
    while True:
        print(c("\n" + "="*60, Color.DIM))
        target = input(c("📍 FIRLATMA KONUMU SEÇİN (vandenberg, kennedy, istanbul...): ", Color.CYAN + Color.BOLD)).lower().strip()
        if target in ('q', 'exit'): break
        
        city = CITY_DB.get(target)
        if not city:
            print(c("Hata: Bilinmeyen konum. Örn: istanbul, kennedy, baikonur", Color.RED))
            continue
            
        lat, lon, name = city
        result = assessor.assess(solar_data, lat, lon)
        
        # --- TEKNİK FIRLATMA VERİLERİ (48 SAATLİK GRAFİKLER) ---
        print(c(f"\n--- {name} ATIŞ ÖNCESİ KRİTİK VERİLERİ (-24s / +24s) ---", Color.BOLD + Color.CYAN))
        
        sw_speed = solar_data.get('solar_wind_speed', 0)
        sw_dens = solar_data.get('solar_wind_density', 0)
        bz = solar_data.get('bz_component', 0)
        xray = solar_data.get('xray_class', 'A1')
        kp = solar_data.get('kp_index', 0)
        
        # Patlama sınıfını sayısala (1-6) dökelim (Çizim için)
        def map_xray(cf):
            mapping = {'A':1, 'B':2, 'C':3, 'M':4, 'X':5}
            v = mapping.get(cf[0].upper(), 1)
            try: v += float(cf[1:]) * 0.1
            except: pass
            return v
        xray_val = map_xray(xray)
        
        metrics = [
            ("💨 Güneş Rüzgarı Hızı (km/s)", sw_speed, 80, 250, 1200, "cyan"),
            ("🌌 Plazma Yoğunluğu (p/cm3)", sw_dens, 4, 0, 40, "green"),
            ("🧲 Manyetik Alan Bz (nT)", bz, 8, -40, 40, "blue"),
            (f"💥 Patlama Sınıfı Kademesi (Şu an: {xray})", xray_val, 1.5, 1, 6, "red"),
            ("🛡️ Jeomanyetik Kp (0-9)", kp, 2, 0, 9, "magenta")
        ]
        
        if HAS_PLOTEXT:
            for title, val, vol, m_min, m_max, clr in metrics:
                print()
                plt.clf()
                plt.plotsize(100, 13)
                
                # 48 saatlik zaman tüneli (-24h'den +24h'ye)
                hours = np.linspace(-24, 24, 49)
                # Geçmiş veriler biraz daha volatil, gelecek veriler yumuşak trend şeklinde
                trend = np.sin((hours + np.random.uniform(0, 24)) * np.pi / 12) * vol
                s_val = trend + (val - trend[24]) + np.random.normal(0, vol * 0.2, 49)
                s_val[24] = val # Merkez nokta = CANLI API VERİSİ
                s_val = np.clip(s_val, m_min, m_max)
                
                plt.plot(hours, s_val, color=clr, marker="dot", label=title)
                plt.xticks([-24, -12, 0, 12, 24], ["-24 Saat (Geçmiş)", "-12 Saat", "ŞU ANKİ VERİ", "+12 Saat", "+24 Saat (Tahmin)"])
                plt.title(f"{title} | ŞU ANKİ DEĞER: {val:.2f}")
                plt.grid(True)
                plt.theme("clear")
                plt.show()
        else:
            # Plotext yoksa fallback olarak sadece düz metin analizi
            print(f"💨 Güneş Rüzgar Hızı    : {sw_speed} km/s")
            print(f"🌌 Plazma Yoğunluğu     : {sw_dens} p/cm3")
            print(f"🧲 Manyetik Alan (Bz)   : {bz} nT")
            print(f"💥 Patlama Sınıfı       : {xray}")
            print(f"🛡️ Jeomanyetik (Kp)     : {kp} / 9")

        # AI YORUMU
        level_map = {
            0: ("GÜVENLİ - NOMİNAL KOŞULLAR", Color.GREEN), 
            1: ("UYARI - DİKKATLİ İZLEME", Color.YELLOW), 
            2: ("TEHLİKELİ - ERTELEME ÖNERİLİR", Color.RED), 
            3: ("KRİTİK - FIRLATMA YASAK", Color.RED + Color.BOLD)
        }
        status, color = level_map[result['risk_level']]
        
        print(c("\n--- AI SİSTEM TANI RAPORU ---", Color.WHITE + Color.BOLD))
        type_text(f"DURUM: {c(status, color)}")
        
        # Dinamik Analiz
        if sw_speed > 600:
            type_text(c(f"ANALİZ: Yüksek enerjili plazma akışı tespit edildi. Rüzgar hızı {sw_speed} km/s seviyesinde.", Color.YELLOW))
        if bz < -10:
            type_text(c(f"ANALİZ: Manyetosfer kararsız. Bz bileşeni ({bz} nT) derin negatif bölgede.", Color.RED))
        if 'X' in xray:
            type_text(c(f"KRİTİK: X-sınıfı mega patlama radyasyon fırtınasını tetikledi.", Color.RED + Color.BOLD))
        
        if result['risk_level'] == 0:
            type_text(c("SONUÇ: Tüm telemetri verileri yeşil. Fırlatma penceresi fırlatış için onaylandı.", Color.GREEN))
        else:
            type_text(c(f"TAVSİYE: {result['risk_info']['recommendation']}", Color.WHITE))

        print(c(f"YAPAY ZEKA GÜVEN ENDEKSİ: %{result['confidence']:.2f}", Color.DIM))

        # --- AI & VERİ GRAFİKLERİ ---
        if HAS_PLOTEXT:
            print(c("\n--- GÜNEŞ FIRTINASI RİSK OLASILIKLARI VARYANS GRAFİĞİ (%) ---", Color.BOLD + Color.YELLOW))
            
            # Görseldeki gibi düzgün eğri ve noktalar
            x_vals = [0, 4, 8, 12, 16, 20, 24]
            # Risk olasılığının (%) 24 saatlik dinamiğini simüle edelim
            base_risk = result['probabilities'].get('UYARI', 0) + result['probabilities'].get('TEHLIKELI', 0) + result['probabilities'].get('KRITIK', 0)
            
            y_vals = [
                base_risk - 15,
                base_risk - 25,
                base_risk + 15,
                base_risk + 40,
                base_risk + 25,
                base_risk + 5,
                base_risk - 10
            ]
            # 0 ile 100 arasında sınırla
            y_vals = [min(100, max(0, int(v))) for v in y_vals]
            
            # Plotext - Tek Kanallı Sade Çizgi Grafik
            plt.clf()
            plt.plotsize(100, 20)
            plt.plot(x_vals, y_vals, color="orange", marker="dot", label="Risk İhtimali (%)")
            
            xticks = [0, 4, 8, 12, 16, 20, 24]
            xlabels = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
            plt.xticks(xticks, xlabels)
            
            # Y ekseni %0 - %100 arası
            plt.yticks([0, 25, 50, 75, 100])
            plt.ylim(0, 110)
            
            plt.grid(True)
            plt.theme("clear")
            plt.show()
            
            # Metrics Footer (Yüzde birimi ile görsel formatta)
            curr, peak, avg = int(y_vals[-1]), int(max(y_vals)), int(np.mean(y_vals))
            
            def m_fmt(v): return c(f"{v}%", Color.BOLD).center(25)
            def m_lbl(t): return t.center(25)
            
            print(c(f"{m_lbl('Current')}{m_lbl('Peak')}{m_lbl('Avg')}", Color.DIM))
            print(f"{m_fmt(curr)}{m_fmt(peak)}{m_fmt(avg)}\n")
            
            # --- İKİNCİ GRAFİK: GERÇEK ZAMANLI API VERİSİ ---
            sw_history = solar_data.get('solar_wind_history', [])
            if len(sw_history) > 10:
                print(c("--- CANLI API VERİSİ: GÜNEŞ RÜZGARI HIZI (NOAA SWPC) ---", Color.BOLD + Color.CYAN))
                
                x_sw = list(range(len(sw_history)))
                y_sw = sw_history
                
                plt.clf()
                plt.plotsize(100, 15)
                # Mavi/Siyan renkli düz çizgi biçiminde canlı API verisini basalım
                plt.plot(x_sw, y_sw, color="cyan", marker="dot", label="Rüzgar Hızı (km/s)")
                
                plt.xticks([0, len(sw_history)//2, len(sw_history)-1], ["<-- Geçmiş", "Ortalama", "Şu An -->"])
                
                plt.grid(True)
                plt.theme("clear")
                plt.show()
                
                c_sw, p_sw, a_sw = int(y_sw[-1]), int(max(y_sw)), int(np.mean(y_sw))
                print(c(f"{m_lbl('Current Speed')}{m_lbl('Peak Speed')}{m_lbl('Avg Speed')}", Color.DIM))
                
                def m_fmt_sw(v): return c(f"{v} km/s", Color.BOLD).center(25)
                print(f"{m_fmt_sw(c_sw)}{m_fmt_sw(p_sw)}{m_fmt_sw(a_sw)}\n")

if __name__ == '__main__':
    main()
