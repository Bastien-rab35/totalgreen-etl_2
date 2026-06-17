import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Connexion à la base de données
db_user = "postgres"
db_password = os.getenv("DB_PASSWORD")

if not db_password:
    raise ValueError("⚠️  La variable d'environnement DB_PASSWORD est manquante dans le fichier .env")

# Extraction du host depuis SUPABASE_URL si présent (ex: https://xyz.supabase.co -> db.xyz.supabase.co)
supabase_url = os.getenv("SUPABASE_URL", "")
if not supabase_url.startswith("https://"):
    raise ValueError("⚠️  La variable d'environnement SUPABASE_URL est manquante ou invalide dans le fichier .env")

ref = supabase_url.split("//")[1].split(".")[0]
db_host = f"db.{ref}.supabase.co"

db_port = "5432"
db_name = "postgres"

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Requête SQL pour l'entraînement
query_train = """
    SELECT 
        fm.captured_at,
        dc.city_name,
        fm.temperature, 
        fm.humidity, 
        fm.wind_speed, 
        fm.aqi_index
    FROM fact_measures fm
    JOIN dim_city dc ON fm.city_id = dc.city_id
    WHERE fm.aqi_index IS NOT NULL
      AND fm.captured_at IS NOT NULL
    ORDER BY fm.captured_at
"""

# Chargement et préparation des données
df_train = pd.read_sql(query_train, engine)
df_train['datetime'] = pd.to_datetime(df_train['captured_at'])
df_train = df_train.sort_values(by=['city_name', 'datetime'])

df_train['aqi_lag_24'] = df_train.groupby('city_name')['aqi_index'].shift(24)
df_train = df_train.dropna()

df_train['mois'] = df_train['datetime'].dt.month
df_train['jour_semaine'] = df_train['datetime'].dt.dayofweek
df_train['heure'] = df_train['datetime'].dt.hour
df_train = pd.get_dummies(df_train, columns=['city_name'], drop_first=True)

features = [col for col in df_train.columns if col not in ['captured_at', 'datetime', 'aqi_index']]
X = df_train[features]
y = df_train['aqi_index']

# Séparation Train / Test
split_index = int(len(df_train) * 0.8)
X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

# Entraînement du modèle
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Prédiction et évaluation
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("Performances du modele de serie temporelle :")
print(f"RMSE : {rmse:.2f}")
print(f"Score R2 : {r2:.2f}")

# Extraction de l'importance des variables
feature_importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': model.feature_importances_
}).sort_values(by='Importance', ascending=False)

print("\nImportance des variables :")
print(feature_importances.head(10))

# ==========================================
# CRÉATION DES GRAPHIQUES
# ==========================================

sns.set_theme(style="whitegrid")

plt.figure(figsize=(10, 6))
sns.barplot(x='Importance', y='Feature', data=feature_importances.head(10), palette='viridis', hue='Feature', legend=False)
plt.title("Top 10 des variables impactant la qualité de l'air (AQI)", fontsize=14, fontweight='bold')
plt.xlabel("Niveau d'importance", fontsize=12)
plt.ylabel("Variables", fontsize=12)
plt.tight_layout()
plt.savefig('graph_importance_variables.png')
print("\n=> Graphique 'graph_importance_variables.png' généré avec succès.")

plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.4, color='#2ab7ca', edgecolors='w', linewidth=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2) 
plt.title("Modèle d'IA : Valeurs Réelles vs Prédictions de l'AQI", fontsize=14, fontweight='bold')
plt.xlabel("Index AQI Réel", fontsize=12)
plt.ylabel("Index AQI Prédit par le modèle", fontsize=12)
plt.tight_layout()
plt.savefig('graph_realite_vs_prediction.png')
print("=> Graphique 'graph_realite_vs_prediction.png' généré avec succès.")

# ==========================================
# FAIRE UNE VÉRITABLE PRÉDICTION POUR DEMAIN
# ==========================================

date_cible = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
date_cible_str = date_cible.strftime('%Y-%m-%d %H:%M:%S')

query_predict = f"""
    WITH LatestAQI AS (
        SELECT city_id, aqi_index, 
               ROW_NUMBER() OVER(PARTITION BY city_id ORDER BY captured_at DESC) as rn
        FROM fact_measures
        WHERE aqi_index IS NOT NULL
    ),
    ForecastData AS (
        SELECT fwf.forecast_id, fwf.city_id, dc.city_name, fwf.temperature, fwf.humidity, fwf.wind_speed, fwf.forecast_timestamp
        FROM fact_weather_forecast fwf
        JOIN dim_city dc ON fwf.city_id = dc.city_id
        WHERE DATE(fwf.forecast_timestamp) = DATE('{date_cible_str}')
    )
    SELECT f.forecast_id, f.city_id, f.city_name, f.temperature, f.humidity, f.wind_speed, f.forecast_timestamp, l.aqi_index as aqi_lag_24
    FROM ForecastData f
    JOIN LatestAQI l ON f.city_id = l.city_id AND l.rn = 1
"""

print("\n--- APPLICATION METIER ---")
df_predict = pd.read_sql(query_predict, engine)

if not df_predict.empty:
    predictions_to_insert = []
    for index, row in df_predict.iterrows():
        df_city = pd.DataFrame({
            'temperature': [row['temperature']],
            'humidity': [row['humidity']],
            'wind_speed': [row['wind_speed']],
            'aqi_lag_24': [row['aqi_lag_24']],
            'mois': [row['forecast_timestamp'].month],
            'jour_semaine': [row['forecast_timestamp'].weekday()],
            'heure': [row['forecast_timestamp'].hour]
        })
        
        for col in features:
            if col not in df_city.columns:
                df_city[col] = 0
                
        col_ville = f"city_name_{row['city_name']}"
        if col_ville in df_city.columns:
            df_city[col_ville] = 1
            
        df_city = df_city[features]
        prediction = model.predict(df_city)[0]
        
        if row['city_name'] == 'Paris':
            print(f"Alerte GoodAir : L'indice de qualité de l'air prévu demain à Paris à 14h est de : {prediction:.0f}")
            
        predictions_to_insert.append({
            'city_id': row['city_id'],
            'forecast_timestamp': row['forecast_timestamp'],
            'predicted_aqi_index': float(prediction),
            'based_on_forecast_id': row['forecast_id'],
            'model_version': 'RandomForest_v1'
        })
        
    if predictions_to_insert:
        df_to_insert = pd.DataFrame(predictions_to_insert)
        df_to_insert.to_sql('fact_aqi_predictions', engine, if_exists='append', index=False)
        print(f"{len(predictions_to_insert)} prédictions insérées dans la base de données.")
else:
    print(f"Aucune donnée de prévision météo trouvée pour {date_cible_str}. Impossible de faire la prédiction métier.")