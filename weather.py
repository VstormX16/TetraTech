import os

import requests

def get_weather_data(lat=40.2, lon=29.0, city=None):
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        return {"city": "Hata", "coord": "-", "temp": "-", "feels_like": "-", "temp_min": "-", "temp_max": "-", "humidity": "-", "pressure": "-", "wind": "-", "clouds": "-", "visibility": "-", "desc": "OPENWEATHER_API_KEY tanimli degil"}

    if city:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=tr"
    else:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=tr"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            coord = data.get("coord", {})
            return {
                "city": f"{data.get('name', 'Bilinmiyor')}, {data.get('sys', {}).get('country', '')}",
                "coord": f"{coord.get('lat', '')}, {coord.get('lon', '')}",
                "temp": f"{data['main']['temp']}",
                "feels_like": f"{data['main']['feels_like']}",
                "temp_min": f"{data['main'].get('temp_min', '')}",
                "temp_max": f"{data['main'].get('temp_max', '')}",
                "humidity": f"{data['main']['humidity']}",
                "pressure": f"{data['main']['pressure']}",
                "wind": f"{data['wind']['speed']}",
                "clouds": f"{data.get('clouds', {}).get('all', 0)}",
                "visibility": f"{data.get('visibility', 0) / 1000}",
                "desc": data["weather"][0]["description"].upper() if "weather" in data and len(data["weather"]) > 0 else "N/A"
            }
        return {"city": "Sehir Bulunamadi", "coord": "-", "temp": "-", "feels_like": "-", "temp_min": "-", "temp_max": "-", "humidity": "-", "pressure": "-", "wind": "-", "clouds": "-", "visibility": "-", "desc": "Gecersiz Konum"}
    except:
        return {"city": "Hata", "coord": "-", "temp": "-", "feels_like": "-", "temp_min": "-", "temp_max": "-", "humidity": "-", "pressure": "-", "wind": "-", "clouds": "-", "visibility": "-", "desc": "Baglanti Hatasi"}

if __name__ == "__main__":
    print(get_weather_data(city="Ankara"))
