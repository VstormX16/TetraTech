# 🚀 Solar AI: Roket Fırlatma Güneş Risk Analizi - Kullanım Rehberi

Bu proje, bir roketin fırlatılması için Dünya'nın atmosferi dışındaki uzay hava durumunu (Space Weather) analiz eden bir Yapay Zeka sistemidir. Sistem, **NOAA** ve **NASA DONKI** API'lerinden aldığı gerçek zamanlı güneş verilerini (Güneş patlamaları, güneş rüzgarları, jeomanyetik fırtınalar vb.) değerlendirerek fırlatma alanının güvenliğini ölçer.

**En önemli özelliği:** Model, hiçbir hazır makine öğrenimi kütüphanesi kullanılmadan tamamen sıfırdan (`numpy` modülü ile matematiksel olarak) kodlanmıştır.

---

## 1. Proje Yapısı ve Mimari
Kodları incelemek istersen hangi dosyanın tam olarak ne yaptığını burada görebilirsin:

- **`main.py`**: Arayüzümüz. Tüm hesaplamaları başlatıp sonuçları renkli ve okunabilir bir şekilde terminale basan ana dosya.
- **`core/` (Yapay Zeka Çekirdeği)**
  - `neural_network.py`: Sıfırdan yazılmış Tam Bağlantılı (Dense) Sinir Ağı. Geri yayılım (backpropagation) ve Batch Normalization içerir.
  - `activations.py`: Yapay sinir hücrelerinin ateşlenme kuralları (ReLU, Sigmoid, Softmax).
  - `optimizers.py`: Ağırlıkların güncellenmesini hızlandıran Adam ve SGD algoritmaları.
  - `data_processor.py`: Ham uzay matematiğini (X-ray logaritmaları, Kp indeksleri) AI'nin anlayacağı 0-1 arası sayılara çevirir.
- **`data/` (Veri Kaynakları)**
  - `nasa_api.py`: NOAA SWPC ve NASA DONKI'den anlık veri çeker.
  - `synthetic_generator.py`: Modeli eğitmek için güneş fiziki kurallarına dayalı on binlerce sentetik eğitim senaryosu yaratır.
- **`models/` (Model Mantığı)**
  - `risk_assessor.py`: Eğitilmiş modeli kullanarak 15 farklı değişkenden risk değerini (0=Güvenli'den 3=Kritik'e kadar) hesaplar.
- **`training/` (Öğrenme Sistemi)**
  - `trainer.py`: Yapay zekanın öğrenme döngüsünü (epoch/mini-batch) yönetir.

---

## 2. İlk Kurulum ve Ön Hazırlık

Sistem sadece iki adet temel Python kütüphanesine ihtiyaç duyar. Visual Studio Code veya PowerShell terminallerinden proje klasöründe (Masaüstündeki `güneş patlaseks` klasöründe) olduğundan emin ol ve şu komutu çalıştır:

```bash
pip install numpy requests
```

*(Not: Bunu zaten senin için arka planda çalıştırdım, şu anda sistem kullanıma hazır!)*

---

## 3. Sistemi Çalıştırma (Kullanım Senaryoları)

Terminali aç ve klasör içerisindeyken aşağıdaki komutları dene:

### Senaryo A: İnteraktif Mod (Önerilen)
Sana hangi konumdan fırlatma yapmak istediğini canlı sorar:
```bash
python main.py
```
> **Nasıl çalışır:** İlk açılışta AI Modeli yoksa kendini eğitir. Ardından NASA/NOAA'dan 6-48 saatlik taze verileri çekip risk analizini başlatır.
> **İpucu:** Konum olarak `kennedy`, `istanbul`, `39.9, 32.8` vb. girebilirsin. Liste görmek için interaktif moda `liste` yaz.

### Senaryo B: Belirli Bir Konumu Doğrudan Analiz Etmek
Terminalden direkt olarak hedef şehri vererek modeli başlatabilirsin:
```bash
python main.py --location "istanbul"
# veya uzay istasyonu ismiyle:
python main.py --location kennedy
# veya koordinatlarla:
python main.py --lat 28.5 --lon -80.6
```

### Senaryo C: Tüm Fırlatma Üslerini Karşılaştırma
Dünyadaki ana fırlatma alanlarını analiz edip hangisinin o anki fırtınaya karşı daha güvenli olduğunu listeler:
```bash
python main.py --demo
```

---

## 4. Çevrimdışı / İnternetsiz Mod
Eğer bir nedenden dolayı NASA ya da NOAA API'leri yanıt vermezse, ya da hızlıca test etmek istersen `offline` bayrağını kullanabilirsin. Bu mod, yapay (ancak gerçekçi) bir X-sınıfı/C-sınıfı patlama senaryosu kullanır:

```bash
python main.py --offline --location baikonur
```

## 5. Yapay Zekayı Yeniden Eğitmek
Ağırlıkları baştan oluşturup eğitimi ve kayıp fonksiyonundaki iyileşmeyi (loss curve) canlı izlemek istersen şu komutu kullanabilirsin:
```bash
python main.py --retrain
```
Bu komut 12,000 sentetik yapay uzay fırtınası verisini üretir, `Adam Optimizer` kullanıp modeli en iyi doğruluk oranına (genellikle ~%99.9) kadar öğrenmesini sağlar.
