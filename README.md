# TetraTech Birleşik Görev Kontrol ve Simülasyon Sistemi

TetraTech; uçuş simülasyonu, çevresel risk analizi ve enkaz takip sistemlerini tek bir taktiksel panelde birleştiren yüksek sadakatli bir havacılık ve uzay görev yönetim platformudur. Proje, uzay ajansları ve görev planlayıcıları için fırlatma hazırlığı ve fırlatma sonrası güvenlik analizi süreçlerinde deterministik, hızlı ve güvenilir bir iş akışı sunmayı amaçlar.

## Sistem Mimarisi

Uygulama, üç ana katmandan oluşan dağıtık bir mikro hizmet yapısı üzerine inşa edilmiştir:

1. **Görev Kontrol Arayüzü (Frontend):** React tabanlı, yüksek performanslı ve taktiksel "savaşa hazır" (combat-ready) kullanıcı deneyimi sunan kontrol paneli.
2. **Hermes AI Motoru (API Katmanı):** 8010 portunda çalışan; topografik veri analizi, hava sahası kısıtlamaları (NOTAM) ve tahmini enkaz ayak izi modellemesini yöneten Python tabanlı servis.
3. **Uçuş Fizik Motoru (Simülasyon Katmanı):** 5000 portunda çalışan; gerçek zamanlı telemetri görselleştirmesi için Three.js ve aerodinamik hesaplamalar için Python kullanan 3D simülasyon ortamı.

## Temel Özellikler ve Detaylar

### 1. 7 Adımlı Birleşik Simülasyon Hattı
TetraTech sisteminin kalbi, görev hazırlığı sırasında hiçbir kritik veri noktasının atlanmamasını sağlayan doğrusal, 7 adımlı akış sihirbazıdır:

- **Adım 1: Araç Konfigürasyonu:** Envanterdeki yüksek sadakatli roket modellerinden (Falcon 9, Ares-1B, Jupiter vb.) seçim yapılması veya kütle, itki ve yakıt profilleri belirlenerek özel araç oluşturulması.
- **Adım 2: Uzay Üssü Lojistiği:** Fırlatma sahalarının (KSC, Kourou, Baikonur vb.) coğrafi seçimi ve gerçek zamanlı enlem/boylam haritalaması.
- **Adım 3: Zamansal Planlama:** Öngörülen çevresel koşulların entegrasyonu ile fırlatma tarihi ve saat penceresinin belirlenmesi.
- **Adım 4: Fırlatma Öncesi AI Konsensüsü:** Uzay havası, yüzey hava durumu ve NOTAM verilerinin ilişkilendirilerek "GO/NO-GO" (Fırlat/Dur) puanının hesaplandığı kapsamlı sistem kontrolü.
- **Adım 5: 3D Uçuş Simülasyonu:** Aerodinamik stresin, hız vektörlerinin ve yakıt tüketiminin gerçek zamanlı olarak izlendiği tam ekran, yüksek çözünürlüklü yörünge simülasyonu.
- **Adım 6: Canlı Enkaz Analizi (Hermes):** Balistik katsayılar ve çevresel parametreler kullanılarak hesaplanan roket kademelerinin tahmini düşüş bölgelerinin görselleştirilmesi.
- **Adım 7: Nihai Görev Raporu:** Tüm telemetri verilerini, risk puanlarını ve stratejik AI yorumlarını içeren, tek sayfalık kurumsal görev özetinin (PDF) oluşturulması.

### 2. Uzay Havası İstihbaratı
- **NOAA Entegrasyonu:** Uydu iletişim parazitlerini öngörmek için Kp-Indeksi ve güneş patlaması aktivitesinin (solar flare) gerçek zamanlı takibi.
- **Jeomanyetik Uyarılar:** Güneş parçacık yoğunluğuna dayalı otomatik uyarı sistemi (Yeşil, Turuncu, Kırmızı durumları).

### 3. Hermes AI Enkaz Tahmini
- **Balistik Ayak İzi Modellemesi:** Atmosferik sürüklenme ve irtifa verilerine dayanarak harcanan kademelerin nereye düşeceğini %98 doğrulukla tahmin eder.
- **Risk Bölgeleme:** Deniz ve kara güvenliğini sağlamak için etki bölgelerini "Sivil Güvenli", "Yüksek Risk" veya "Kritik" olarak kategorize eder.

### 4. Çevresel ve Hava Sahası Uyumluluğu
- **Gerçek Zamanlı Hava Sahası Analizi:** Aktif gökyüzü kısıtlamaları için entegre NOTAM (Havacılara Duyuru) sorgulama sistemi.
- **Topografik Arazi Haritalaması:** Kademe ayrılması sırasında uçuş yolu güvenliğini sağlamak için arazi yüksekliklerinin analizi.

### 5. Otomatik PDF Raporlama
- Görev telemetrisini, risk grafiklerini ve AI stratejik yorumlarını profesyonel, tek sayfalık bir PDF belgesinde toplayan raporlama motoru.

## Kurulum ve Yapılandırma

### 1. Gereksinimler
- **Node.js:** v18 veya üzeri (Frontend için)
- **Python:** 3.9 veya üzeri (API ve Simülasyon Sunucusu için)
- **Git**

### 2. Backend (Arka Uç) Kurulumu
Veri işleme ve API iletişimi için gerekli Python kütüphanelerini kurun:
```bash
pip install flask flask-cors requests pandas numpy
```

### 3. Frontend (Ön Yüz) Kurulumu
Frontend dizinine gidin ve UI bağımlılıklarını yükleyin:
```bash
cd frontend
npm install
```

## Çalıştırma Talimatları

Tam sistemi devreye almak için aşağıdaki sırayı takip edin:

### A. Hermes AI API (Port 8010)
Proje kök dizininden çalıştırın:
```bash
python api.py
```

### B. Simülasyon Motoru (Port 5000)
Kök dizinden ilgili klasöre gidip çalıştırın:
```bash
cd "Roket Simulasyon Aracı/roketsim-main"
python server.py
```

### C. Görev Kontrol Paneli (Port 5173)
Frontend dizininden çalıştırın:
```bash
npm run dev
```

## Dağıtım ve Yayınlama

TetraTech dağıtık yayını desteklemektedir:
- **Frontend:** Netlify, Vercel veya statik site barındırma hizmetleri için optimize edilmiştir.
- **Backend API'leri:** Render, Railway veya standart bulut sunucularında Docker üzerinden çalıştırılacak şekilde tasarlanmıştır.

## Lisans

Telif Hakkı © 2026 TetraTech Aerospace Systems. Tüm hakları saklıdır. Sadece profesyonel kullanım içindir.
