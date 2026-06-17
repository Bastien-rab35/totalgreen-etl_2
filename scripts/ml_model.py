import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# Connexion à la base de données
db_user = "postgres"
db_password = "totalgreen-mspr35000"
db_host = "db.uqntmecpgswkdchcfwxe.supabase.co"
db_port = "5432"
db_name = "postgres"

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Requête SQL
query = """
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
df = pd.read_sql(query, engine)

df['datetime'] = pd.to_datetime(df['captured_at'])
df = df.sort_values(by=['city_name', 'datetime'])

df['aqi_lag_24'] = df.groupby('city_name')['aqi_index'].shift(24)
df = df.dropna()

df['mois'] = df['datetime'].dt.month
df['jour_semaine'] = df['datetime'].dt.dayofweek
df['heure'] = df['datetime'].dt.hour

df = pd.get_dummies(df, columns=['city_name'], drop_first=True)

features = [col for col in df.columns if col not in ['captured_at', 'datetime', 'aqi_index']]
X = df[features]
y = df['aqi_index']

# Séparation Train / Test
split_index = int(len(df) * 0.8)
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

# Configuration du style visuel
sns.set_theme(style="whitegrid")

# Graphique 1 : Feature Importance (Importance des variables)
plt.figure(figsize=(10, 6))
sns.barplot(x='Importance', y='Feature', data=feature_importances.head(10), palette='viridis', hue='Feature', legend=False)
plt.title("Top 10 des variables impactant la qualité de l'air (AQI)", fontsize=14, fontweight='bold')
plt.xlabel("Niveau d'importance", fontsize=12)
plt.ylabel("Variables", fontsize=12)
plt.tight_layout()
plt.savefig('graph_importance_variables.png')
print("\n=> Graphique 'graph_importance_variables.png' généré avec succès.")

# Graphique 2 : Réalité vs Prédiction
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.4, color='#2ab7ca', edgecolors='w', linewidth=0.5)
# Ligne rouge pointillée représentant la prédiction parfaite
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

# Exemple : prédi paris (aqi de 45 ajd)

donnees_demain = pd.DataFrame({
    'temperature': [32.0],       # Prévision météo : 32 degrés
    'humidity': [40],            # Prévision météo : 40% d'humidité
    'wind_speed': [1.5],         # Prévision météo : vent très faible (1.5 km/h)
    'aqi_lag_24': [45],          # L'AQI d'aujourd'hui (qui sera l'AQI de la veille demain)
    'mois': [8],                 # Mois d'août
    'jour_semaine': [2],         # Mercredi (0=Lundi, 2=Mercredi)
    'heure': [14]                # 14h00
})

for col in X.columns:
    if col not in donnees_demain.columns:
        donnees_demain[col] = 0

donnees_demain['city_name_Paris'] = 1

donnees_demain = donnees_demain[X.columns]

prediction_demain = model.predict(donnees_demain)

print("\n--- APPLICATION METIER ---")
print(f"Alerte GoodAir : L'indice de qualité de l'air prévu demain à Paris à 14h est de : {prediction_demain[0]:.0f}")