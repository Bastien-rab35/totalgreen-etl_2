import os
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from supabase import create_client
from dotenv import load_dotenv

# Importation conditionnelle pour l'environnement Serverless
is_serverless = os.getenv("JOB_TYPE") is not None
if not is_serverless:
    import matplotlib.pyplot as plt
    import seaborn as sns

load_dotenv()

# ============================================================
# CONNEXION via Supabase REST API (HTTPS 443)
# SQLAlchemy/psycopg2 (TCP 5432) est bloqué sur Scaleway
# Serverless Jobs — on passe exclusivement par l'API REST.
# ============================================================
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")

if not supabase_url or not supabase_url.startswith("https://"):
    raise ValueError("⚠️  La variable d'environnement SUPABASE_URL est manquante ou invalide")
if not supabase_key:
    raise ValueError("⚠️  La variable d'environnement SUPABASE_KEY est manquante")

supabase = create_client(supabase_url, supabase_key)

# ============================================================
# CHARGEMENT DES DONNÉES D'ENTRAÎNEMENT
# ============================================================
print("Chargement des données d'entraînement (fact_measures)...")

# Charger fact_measures par pages de 10 000 lignes
all_rows = []
page_size = 10_000
offset = 0
while True:
    resp = (
        supabase.table("fact_measures")
        .select("captured_at, city_id, temperature, humidity, wind_speed, aqi_index")
        .not_.is_("aqi_index", "null")
        .not_.is_("captured_at", "null")
        .order("captured_at")
        .range(offset, offset + page_size - 1)
        .execute()
    )
    batch = resp.data
    if not batch:
        break
    all_rows.extend(batch)
    if len(batch) < page_size:
        break
    offset += page_size

print(f"   {len(all_rows)} mesures chargées.")

if not all_rows:
    print("Aucune donnée trouvée dans fact_measures. Arrêt.")
    raise SystemExit(0)

df_measures = pd.DataFrame(all_rows)

# Charger dim_city pour le mapping city_id → city_name
resp_cities = supabase.table("dim_city").select("city_id, city_name").execute()
df_cities = pd.DataFrame(resp_cities.data)

# Fusion
df_train = df_measures.merge(df_cities, on="city_id", how="left")
df_train["datetime"] = pd.to_datetime(df_train["captured_at"])
df_train = df_train.sort_values(by=["city_name", "datetime"])

df_train["aqi_lag_24"] = df_train.groupby("city_name")["aqi_index"].shift(24)
df_train = df_train.dropna()

df_train["mois"] = df_train["datetime"].dt.month
df_train["jour_semaine"] = df_train["datetime"].dt.dayofweek
df_train["heure"] = df_train["datetime"].dt.hour
df_train = pd.get_dummies(df_train, columns=["city_name"], drop_first=True)

features = [
    col for col in df_train.columns
    if col not in ["captured_at", "datetime", "aqi_index", "city_id"]
]
X = df_train[features]
y = df_train["aqi_index"]

# ============================================================
# SÉPARATION TRAIN / TEST
# ============================================================
split_index = int(len(df_train) * 0.8)
X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

# ============================================================
# ENTRAÎNEMENT DU MODÈLE
# ============================================================
print("Entraînement du modèle RandomForest...")
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
    "Feature": X.columns,
    "Importance": model.feature_importances_
}).sort_values(by="Importance", ascending=False)

print("\nImportance des variables :")
print(feature_importances.head(10))

# ============================================================
# GRAPHIQUES (environnement local uniquement)
# ============================================================
if not is_serverless:
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(10, 6))
    sns.barplot(
        x="Importance", y="Feature",
        data=feature_importances.head(10),
        palette="viridis", hue="Feature", legend=False
    )
    plt.title("Top 10 des variables impactant la qualité de l'air (AQI)", fontsize=14, fontweight="bold")
    plt.xlabel("Niveau d'importance", fontsize=12)
    plt.ylabel("Variables", fontsize=12)
    plt.tight_layout()
    plt.savefig("graph_importance_variables.png")
    print("\n=> Graphique 'graph_importance_variables.png' généré avec succès.")

    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.4, color="#2ab7ca", edgecolors="w", linewidth=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2)
    plt.title("Modèle d'IA : Valeurs Réelles vs Prédictions de l'AQI", fontsize=14, fontweight="bold")
    plt.xlabel("Index AQI Réel", fontsize=12)
    plt.ylabel("Index AQI Prédit par le modèle", fontsize=12)
    plt.tight_layout()
    plt.savefig("graph_realite_vs_prediction.png")
    print("=> Graphique 'graph_realite_vs_prediction.png' généré avec succès.")
else:
    print("\n=> Environnement Serverless détecté : génération des graphiques désactivée.")

# ============================================================
# PRÉDICTION POUR DEMAIN
# ============================================================
date_cible = (datetime.now() + timedelta(days=1)).replace(
    hour=14, minute=0, second=0, microsecond=0
)
date_cible_date = date_cible.strftime("%Y-%m-%d")

print("\n--- APPLICATION METIER ---")
print(f"Prédiction pour le {date_cible_date} à 14h...")

# Dernier AQI connu par ville (aqi_lag_24)
resp_latest = (
    supabase.table("fact_measures")
    .select("city_id, aqi_index, captured_at")
    .not_.is_("aqi_index", "null")
    .order("captured_at", desc=True)
    .limit(10_000)
    .execute()
)
df_latest_raw = pd.DataFrame(resp_latest.data)
df_latest_aqi = (
    df_latest_raw
    .sort_values("captured_at", ascending=False)
    .groupby("city_id")
    .first()
    .reset_index()[["city_id", "aqi_index"]]
    .rename(columns={"aqi_index": "aqi_lag_24"})
)

# Prévisions météo pour demain
resp_forecast = (
    supabase.table("fact_weather_forecast")
    .select("forecast_id, city_id, temperature, humidity, wind_speed, forecast_timestamp")
    .gte("forecast_timestamp", f"{date_cible_date}T00:00:00")
    .lte("forecast_timestamp", f"{date_cible_date}T23:59:59")
    .execute()
)
df_forecast = pd.DataFrame(resp_forecast.data)

if df_forecast.empty:
    print(f"Aucune donnée de prévision météo trouvée pour {date_cible_date}. Impossible de faire la prédiction métier.")
    raise SystemExit(0)

# Fusion forecast + city_name + aqi_lag_24
df_predict = df_forecast.merge(df_cities, on="city_id", how="left")
df_predict = df_predict.merge(df_latest_aqi, on="city_id", how="inner")
df_predict["forecast_timestamp"] = pd.to_datetime(df_predict["forecast_timestamp"])

predictions_to_insert = []
for _, row in df_predict.iterrows():
    df_city = pd.DataFrame({
        "temperature": [row["temperature"]],
        "humidity": [row["humidity"]],
        "wind_speed": [row["wind_speed"]],
        "aqi_lag_24": [row["aqi_lag_24"]],
        "mois": [row["forecast_timestamp"].month],
        "jour_semaine": [row["forecast_timestamp"].weekday()],
        "heure": [row["forecast_timestamp"].hour],
    })

    for col in features:
        if col not in df_city.columns:
            df_city[col] = 0

    col_ville = f"city_name_{row['city_name']}"
    if col_ville in df_city.columns:
        df_city[col_ville] = 1

    df_city = df_city[features]
    prediction = model.predict(df_city)[0]

    if row["city_name"] == "Paris":
        print(
            f"Alerte GoodAir : L'indice de qualité de l'air prévu demain à Paris à 14h est de : {prediction:.0f}"
        )

    predictions_to_insert.append({
        "city_id": row["city_id"],
        "forecast_timestamp": row["forecast_timestamp"].isoformat(),
        "predicted_aqi_index": float(prediction),
        "based_on_forecast_id": row["forecast_id"],
        "model_version": "RandomForest_v1",
    })

if predictions_to_insert:
    # Insérer via REST API (pas de SQLAlchemy)
    supabase.table("fact_aqi_predictions").insert(predictions_to_insert).execute()
    print(f"{len(predictions_to_insert)} prédictions insérées dans la base de données.")