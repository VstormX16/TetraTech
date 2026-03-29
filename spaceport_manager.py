from geopy.geocoders import Nominatim
import math

class SpaceportManager:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="TetraTech_Launcher")
        self.spaceports = [
            # Kuzey Amerika
            {"name": "Kennedy Space Center (LC-39A/B)", "region": "🇺🇸 Kuzey Amerika", "location": "Florida, USA", "lat": 28.5729, "lon": -80.6490, "desc": "NASA'nın ana üssü, Falcon Heavy ve SLS buradan kalkar."},
            {"name": "Cape Canaveral Space Force Station", "region": "🇺🇸 Kuzey Amerika", "location": "Florida, USA", "lat": 28.4889, "lon": -80.5778, "desc": "Falcon 9, Atlas V ve Vulcan için çok sayıda pad (SLC-40, SLC-41 vb.) bulunur."},
            {"name": "Vandenberg Space Force Base", "region": "🇺🇸 Kuzey Amerika", "location": "California, USA", "lat": 34.7420, "lon": -120.5724, "desc": "Kutupsal yörünge (polar orbit) fırlatmaları için ana merkez."},
            {"name": "Starbase (Boca Chica)", "region": "🇺🇸 Kuzey Amerika", "location": "Texas, USA", "lat": 25.9973, "lon": -97.1557, "desc": "SpaceX'in Starship fırlatma merkezi."},
            {"name": "Wallops Flight Facility", "region": "🇺🇸 Kuzey Amerika", "location": "Virginia, USA", "lat": 37.9386, "lon": -75.4572, "desc": "Antares ve küçük roketler için."},
            {"name": "Pacific Spaceport Complex", "region": "🇺🇸 Kuzey Amerika", "location": "Alaska, USA", "lat": 57.4358, "lon": -152.3378, "desc": "Kodiak Adası. Kutupsal fırlatmalar için ticari üs."},
            {"name": "Spaceport America", "region": "🇺🇸 Kuzey Amerika", "location": "New Mexico, USA", "lat": 32.9904, "lon": -106.9750, "desc": "Virgin Galactic'in suborbital üssü."},
            
            # Avrasya
            {"name": "Baikonur Cosmodrome", "region": "🇰🇿 & 🇷🇺 Avrasya", "location": "Kazakhstan", "lat": 45.9646, "lon": 63.3052, "desc": "Dünyanın en çok fırlatma yapılan tarihi üssü (Soyuz, Proton)."},
            {"name": "Plesetsk Cosmodrome", "region": "🇰🇿 & 🇷🇺 Avrasya", "location": "Russia", "lat": 62.9257, "lon": 40.5777, "desc": "Askeri ve kutupsal uydu fırlatmaları."},
            {"name": "Vostochny Cosmodrome", "region": "🇰🇿 & 🇷🇺 Avrasya", "location": "Russia", "lat": 51.8844, "lon": 128.3339, "desc": "Rusya'nın en yeni sivil ana üssü."},
            {"name": "Kapustin Yar", "region": "🇰🇿 & 🇷🇺 Avrasya", "location": "Russia", "lat": 48.5678, "lon": 46.2543, "desc": "Daha çok test ve küçük uydu fırlatmaları için."},
            
            # Asya
            {"name": "Jiuquan Satellite Launch Center", "region": "🇨🇳 Asya", "location": "China", "lat": 40.9578, "lon": 100.2917, "desc": "Gobi Çölü. Çin'in insanlı uçuş merkezi."},
            {"name": "Xichang Satellite Launch Center", "region": "🇨🇳 Asya", "location": "China", "lat": 28.2460, "lon": 102.0281, "desc": "İletişim uyduları için (iç bölgede)."},
            {"name": "Taiyuan Satellite Launch Center", "region": "🇨🇳 Asya", "location": "China", "lat": 38.8487, "lon": 111.6080, "desc": "Güneş eşzamanlı yörüngeler için."},
            {"name": "Wenchang Space Launch Site", "region": "🇨🇳 Asya", "location": "China", "lat": 19.6144, "lon": 110.9511, "desc": "Hainan Adası. Çin'in en yeni, denize kıyısı olan (ağır yük) üssü."},
            {"name": "Satish Dhawan Space Centre", "region": "Asya", "location": "India", "lat": 13.7196, "lon": 80.2304, "desc": "Sriharikota. Hindistan'un ana üssü."},
            {"name": "Tanegashima Space Center", "region": "Asya", "location": "Japan", "lat": 30.3748, "lon": 130.9577, "desc": "JAXA'nın ana fırlatma merkezi."},
            {"name": "Uchinoura Space Center", "region": "Asya", "location": "Japan", "lat": 31.2519, "lon": 131.0825, "desc": "Küçük ve bilimsel roketler için."},
            {"name": "Naro Space Center", "region": "Asya", "location": "South Korea", "lat": 34.4319, "lon": 127.5351, "desc": "Güney Kore'nin ana üssü."},
            {"name": "Sohae Satellite Launching Station", "region": "Asya", "location": "North Korea", "lat": 39.6601, "lon": 124.7053, "desc": "Kuzey Kore'nin ana üssü."},
            {"name": "Semnan Space Center", "region": "Asya", "location": "Iran", "lat": 35.2346, "lon": 53.9208, "desc": "İran'ın yörüngesel fırlatma merkezi."},
            {"name": "Palmachim Airbase", "region": "Asya", "location": "Israel", "lat": 31.8848, "lon": 34.6802, "desc": "İsrail'in Shavit roketleri buradan kalkar."},
            
            # Avrupa ve Diğer
            {"name": "Guiana Space Centre", "region": "🇪🇺 Avrupa & Diğer", "location": "French Guiana", "lat": 5.2394, "lon": -52.7685, "desc": "ESA/Fransa işletiyor. Ariane 6 ve Vega buradan kalkar."},
            {"name": "Andøya Spaceport", "region": "🇪🇺 Avrupa & Diğer", "location": "Norway", "lat": 69.2941, "lon": 16.0305, "desc": "Avrupa'nın yeni yörüngesel fırlatma noktası."},
            {"name": "Esrange Space Center", "region": "🇪🇺 Avrupa & Diğer", "location": "Sweden", "lat": 67.8847, "lon": 21.0617, "desc": "Küçük uydular için yörüngesel fırlatma kapasitesi."},
            {"name": "SaxaVord Spaceport", "region": "🇪🇺 Avrupa & Diğer", "location": "Scotland", "lat": 60.8173, "lon": -0.8309, "desc": "İskoçya mikro-fırlatıcı üssü."},
            {"name": "Rocket Lab Launch Complex 1", "region": "Avrupa & Diğer", "location": "New Zealand", "lat": -39.2604, "lon": 177.8654, "desc": "Dünyanın en aktif ticari küçük uydu üssü."},
            {"name": "Alcântara Launch Center", "region": "Avrupa & Diğer", "location": "Brazil", "lat": -2.3164, "lon": -44.3676, "desc": "Ekvatora en yakın üslerden biri."},
            {"name": "Luigi Broglio Space Center", "region": "Avrupa & Diğer", "location": "Kenya", "lat": -2.9961, "lon": 40.2131, "desc": "San Marco deniz platformu (Durgun)."}
        ]

    def get_all(self):
        return self.spaceports
