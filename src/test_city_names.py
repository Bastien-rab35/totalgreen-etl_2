"""
Test de récupération de données avec le nom des villes
au lieu des coordonnées GPS
"""
import requests
import json
from config import config

def test_openweather_by_city_name():
    """Test OpenWeather avec le nom de la ville"""
    print("\n" + "="*60)
    print("TEST OPENWEATHER - Nom de ville")
    print("="*60)
    
    city_name = "Paris"
    
    # Méthode 1: API Geocoding pour obtenir les coordonnées
    print(f"\n1️⃣ Recherche de '{city_name}' via Geocoding API...")
    geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        'q': f"{city_name},FR",  # Ville, Code pays
        'limit': 1,
        'appid': config.OPENWEATHER_API_KEY
    }
    
    try:
        response = requests.get(geocoding_url, params=params, timeout=10)
        response.raise_for_status()
        geo_data = response.json()
        
        if geo_data:
            print(f"✅ Ville trouvée:")
            print(f"   Nom: {geo_data[0].get('name')}")
            print(f"   Latitude: {geo_data[0].get('lat')}")
            print(f"   Longitude: {geo_data[0].get('lon')}")
            print(f"   Pays: {geo_data[0].get('country')}")
            
            # Maintenant on peut utiliser ces coordonnées
            lat = geo_data[0].get('lat')
            lon = geo_data[0].get('lon')
            
            print(f"\n2️⃣ Récupération météo avec ces coordonnées...")
            weather_url = config.OPENWEATHER_BASE_URL
            weather_params = {
                'lat': lat,
                'lon': lon,
                'appid': config.OPENWEATHER_API_KEY,
                'units': 'metric',
                'exclude': 'minutely,hourly,daily,alerts'
            }
            
            weather_response = requests.get(weather_url, params=weather_params, timeout=10)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
            current = weather_data.get('current', {})
            print(f"✅ Données météo récupérées:")
            print(f"   Température: {current.get('temp')}°C")
            print(f"   Ressenti: {current.get('feels_like')}°C")
            print(f"   Humidité: {current.get('humidity')}%")
            print(f"   Vent: {current.get('wind_speed')} m/s")
            
            return True
        else:
            print(f"❌ Aucune ville trouvée pour '{city_name}'")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_openweather_current_weather_api():
    """Test avec l'API Current Weather (plus simple, sans coordonnées)"""
    print("\n" + "="*60)
    print("TEST OPENWEATHER - API Current Weather (nom direct)")
    print("="*60)
    
    city_name = "Paris,FR"
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        'q': city_name,
        'appid': config.OPENWEATHER_API_KEY,
        'units': 'metric'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Données récupérées pour {data.get('name')}:")
        print(f"   Température: {data['main']['temp']}°C")
        print(f"   Ressenti: {data['main']['feels_like']}°C")
        print(f"   Humidité: {data['main']['humidity']}%")
        print(f"   Pression: {data['main']['pressure']} hPa")
        print(f"   Vent: {data['wind']['speed']} m/s")
        print(f"   Description: {data['weather'][0]['description']}")
        
        print(f"\n⚠️  NOTE: Cette API ne fournit pas toutes les données de OneCall")
        print(f"   (pas de UV index, dew_point, etc.)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_aqicn_by_city_name():
    """Test AQICN avec le nom de la ville"""
    print("\n" + "="*60)
    print("TEST AQICN - Nom de ville")
    print("="*60)
    
    # Méthode 1: Recherche par nom de ville
    city_name = "Paris"
    url = f"https://api.waqi.info/feed/{city_name}/"
    
    params = {'token': config.AQICN_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'ok':
            aqi_data = data.get('data', {})
            print(f"✅ Données AQI récupérées:")
            print(f"   Station: {aqi_data.get('city', {}).get('name')}")
            print(f"   AQI: {aqi_data.get('aqi')}")
            
            iaqi = aqi_data.get('iaqi', {})
            print(f"   PM2.5: {iaqi.get('pm25', {}).get('v', 'N/A')}")
            print(f"   PM10: {iaqi.get('pm10', {}).get('v', 'N/A')}")
            print(f"   NO2: {iaqi.get('no2', {}).get('v', 'N/A')}")
            print(f"   O3: {iaqi.get('o3', {}).get('v', 'N/A')}")
            
            geo = aqi_data.get('city', {}).get('geo', [])
            if geo:
                print(f"   Coordonnées GPS: {geo[0]}, {geo[1]}")
            
            return True
        else:
            print(f"❌ Statut: {data.get('status')}")
            print(f"   Message: {data.get('data')}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_all_cities():
    """Test avec toutes les villes françaises"""
    print("\n" + "="*60)
    print("TEST AVEC TOUTES LES 10 VILLES")
    print("="*60)
    
    cities = [
        "Paris", "Marseille", "Lyon", "Toulouse", "Nice",
        "Nantes", "Montpellier", "Strasbourg", "Bordeaux", "Lille"
    ]
    
    results = {}
    
    for city in cities:
        print(f"\n🔍 Test: {city}")
        
        # Test AQICN (plus simple)
        url = f"https://api.waqi.info/feed/{city}/"
        params = {'token': config.AQICN_API_KEY}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'ok':
                aqi = data.get('data', {}).get('aqi')
                station = data.get('data', {}).get('city', {}).get('name')
                print(f"   ✅ AQICN: {station} - AQI: {aqi}")
                results[city] = 'OK'
            else:
                print(f"   ❌ AQICN: Échec")
                results[city] = 'FAIL'
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[city] = 'ERROR'
    
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    success = sum(1 for v in results.values() if v == 'OK')
    print(f"Réussite: {success}/{len(cities)}")
    
    for city, status in results.items():
        icon = "✅" if status == "OK" else "❌"
        print(f"{icon} {city}: {status}")

def main():
    """Point d'entrée principal"""
    print("🧪 TEST DE RÉCUPÉRATION PAR NOM DE VILLE")
    print("="*60)
    
    # Validation de la config
    try:
        config.validate()
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return
    
    # Tests
    test_openweather_current_weather_api()
    test_openweather_by_city_name()
    test_aqicn_by_city_name()
    test_all_cities()
    
    print("\n" + "="*60)
    print("📊 CONCLUSION")
    print("="*60)
    print("""
    ✅ OPENWEATHER:
       - API Current Weather: Fonctionne avec nom de ville
       - Limitation: Moins de données que OneCall (pas de UV, dew_point)
       - Geocoding API: Permet de convertir nom → coordonnées
    
    ✅ AQICN:
       - Fonctionne directement avec le nom de ville
       - Format: https://api.waqi.info/feed/{city_name}/
       - Plus simple que la méthode GPS
    
    💡 RECOMMANDATION:
       - AQICN: Utiliser le nom de ville (plus simple)
       - OpenWeather: Garder les coordonnées GPS pour OneCall API
         (données plus complètes)
    """)

if __name__ == "__main__":
    main()
