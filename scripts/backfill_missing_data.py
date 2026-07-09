import os
import requests
import psycopg2
from datetime import datetime, timedelta
import time
from urllib.parse import urlparse

# Chargement de la configuration via le fichier .env (doit être sourcé avant)
SUPABASE_URL = os.getenv('SUPABASE_URL')
DB_PASSWORD = os.getenv('DB_PASSWORD')

if not SUPABASE_URL or not DB_PASSWORD:
    raise ValueError("SUPABASE_URL et DB_PASSWORD doivent être définis")

# Parse de l'URL Supabase pour construire la chaîne de connexion PostgreSQL
parsed_url = urlparse(SUPABASE_URL)
ref = parsed_url.hostname.split('.')[0]
DB_HOST = f"db.{ref}.supabase.co"
DB_USER = "postgres"
DB_NAME = "postgres"

START_DATE = "2026-05-29"
END_DATE = "2026-06-16"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        port=5432
    )

def fetch_weather_history(lat, lon, start_date, end_date):
    """Récupère l'historique météo depuis Open-Meteo"""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Erreur météo: {response.text}")
    return None

def fetch_aqi_history(lat, lon, start_date, end_date):
    """Récupère l'historique AQI depuis Open-Meteo"""
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "us_aqi,pm10,pm2_5,nitrogen_dioxide,ozone,sulphur_dioxide,carbon_monoxide"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Erreur AQI: {response.text}")
    return None

def main():
    print("Démarrage du script de backfill...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer les villes
    cursor.execute("SELECT city_id, city_name, latitude, longitude FROM dim_city WHERE latitude IS NOT NULL")
    cities = cursor.fetchall()
    
    total_inserted = 0
    
    for city in cities:
        city_id, name, lat, lon = city
        print(f"Traitement de {name} ({lat}, {lon})...")
        
        weather_data = fetch_weather_history(lat, lon, START_DATE, END_DATE)
        aqi_data = fetch_aqi_history(lat, lon, START_DATE, END_DATE)
        
        if not weather_data or not aqi_data:
            print(f"  -> Données manquantes pour {name}, on passe.")
            continue
            
        # Parcourir les heures
        w_times = weather_data.get('hourly', {}).get('time', [])
        
        for i, time_str in enumerate(w_times):
            # Filtrer pour ne garder que la mesure de 12:00 UTC (14h heure française en été)
            if not time_str.endswith("12:00"):
                continue
                
            captured_at = datetime.fromisoformat(time_str)
            capture_date = captured_at.date()
            
            # Extraction météo
            temp = weather_data['hourly']['temperature_2m'][i]
            hum = weather_data['hourly']['relative_humidity_2m'][i]
            wind = weather_data['hourly']['wind_speed_10m'][i]
            
            # Extraction AQI
            aqi_times = aqi_data.get('hourly', {}).get('time', [])
            try:
                a_idx = aqi_times.index(time_str)
            except ValueError:
                continue
                
            us_aqi = aqi_data['hourly']['us_aqi'][a_idx]
            pm10 = aqi_data['hourly']['pm10'][a_idx]
            pm25 = aqi_data['hourly']['pm2_5'][a_idx]
            no2 = aqi_data['hourly']['nitrogen_dioxide'][a_idx]
            o3 = aqi_data['hourly']['ozone'][a_idx]
            so2 = aqi_data['hourly']['sulphur_dioxide'][a_idx]
            co = aqi_data['hourly']['carbon_monoxide'][a_idx]
            
            # Vérifier que les données principales sont présentes
            if temp is None or us_aqi is None:
                continue
            
            # Obtenir l'aqi_level_id via la fonction SQL
            cursor.execute("SELECT public.get_aqi_level_id(%s)", (us_aqi,))
            aqi_level_id_row = cursor.fetchone()
            aqi_level_id = aqi_level_id_row[0] if aqi_level_id_row else None
            
            # On utilise le weather_condition par défaut (Unknown / Clear)
            # Idéalement 1 correspond à Clear dans notre init
            weather_condition_id = 1 
            
            # Vérifier si la ligne n'existe pas déjà pour cette ville et cette date
            cursor.execute("SELECT 1 FROM fact_measures WHERE city_id = %s AND capture_date = %s LIMIT 1", (city_id, capture_date))
            if cursor.fetchone():
                continue
                
            # Insérer la ligne
            insert_query = """
                INSERT INTO fact_measures (
                    city_id, capture_date, captured_at, 
                    weather_condition_id, aqi_level_id, 
                    temperature, humidity, wind_speed,
                    aqi_index, pm10, pm25, no2, o3, so2, co
                ) VALUES (
                    %s, %s, %s, 
                    %s, %s, 
                    %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            try:
                cursor.execute(insert_query, (
                    city_id, capture_date, captured_at,
                    weather_condition_id, aqi_level_id,
                    temp, hum, wind,
                    us_aqi, pm10, pm25, no2, o3, so2, co
                ))
                total_inserted += 1
            except Exception as e:
                print(f"Erreur SQL pour {name} à {capture_date}: {e}")
                conn.rollback()
                continue
        
        # Commit par ville
        conn.commit()
        time.sleep(1) # Respect du rate limit Open-Meteo

    print(f"Terminé ! {total_inserted} lignes insérées dans fact_measures.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
