# Modèles Statistiques et Dashboard - GoodAir

## Vue d'ensemble

Ce dossier contient :
1. **Notebook de modèles ML** : Analyses statistiques et prédictions
2. **Dashboard Streamlit** : Visualisation interactive des données

---

## Démarrage Rapide

### Prérequis
```bash
# Activation environnement
source .venv/bin/activate

# Installation dépendances (incluse dans requirements.txt)
pip install -r requirements.txt
```

### Lancer le Dashboard
```bash
streamlit run app/dashboard.py
```
Le dashboard s'ouvre automatiquement sur `http://localhost:8501`

### Lancer les Notebooks
```bash
jupyter notebook notebooks/02_statistical_models.ipynb
```

---

## Dashboard Streamlit

### Fonctionnalités
- **KPI Principaux** : AQI moyen, température, PM2.5, humidité
- **Alertes Détectées** : Seuils critiques en temps réel
- **Graphiques Interactifs** : AQI, corrélations, distributions
- **Matrice de Corrélation** : Relations entre variables
- **Statistiques Détaillées** : Qualité air, météo, données brutes
- **Export CSV/Excel** : Téléchargement données
- **Filtrage** : Par villes, plage horaire, seuils d'alerte

### Structure
```
app/
├── dashboard.py          # Application Streamlit principale
└── README.md            # Cette documentation
```

### Utilisation
1. **Filtrer les données** via la barre latérale (Paramètres)
2. **Consulter les KPI** en haut du tableau
3. **Vérifier les alertes** (AQI Critique, PM2.5 Élevé)
4. **Analyser les graphiques** (évolutions, corrélations, distributions)
5. **Télécharger les données** en CSV ou Excel

### Théorie et Techniques de Data Visualisation employées
Conformément aux bonnes pratiques de l'ingénierie décisionnelle, le dashboard applique des techniques spécifiques selon la nature des données à valoriser :

1. **Séries Temporelles (Line Charts)** : Technique permettant d'identifier la saisonnalité, la tendance (trend) et le bruit. *Utilisation : Évolution de l'AQI et Températures.*
2. **Relations et Corrélations (Scatter Plots & Heatmaps)** : Technique statistique pour révéler l'intensité et le sens d'une dépendance entre variables (ex: matrice de Pearson). *Utilisation : Heatmap (Plotly) confirmant la corrélation entre Température, Humidité et PM2.5.*
3. **Distribution et Dispersions (Box Plots)** : Technique permettant d'observer les quartiles, la médiane et de repérer visuellement les outliers statiques. *Utilisation : Variabilité des polluants par ville.*
4. **Mesures d'Impact (Indicateurs / KPI Cards)** : Agrégation instantanée avec code couleur conditionnel. *Utilisation : Métriques globales en entête de dashboard.*
5. **Visualisation Spatiale (Maps)** : Typologie de cartographie pour les variables géolocalisées. *(Potentielle évolution future pour projeter les données spatiales de TomTom).*

---

## Notebook - Modèles Statistiques

### Contenu

#### Section 1 : Imports & Chargement
- Bibliothèques ML : scikit-learn, statsmodels, numpy, pandas
- Connexion base Supabase
- Chargement 5000+ mesures

#### Section 2 : Nettoyage
- Conversion types de données
- Suppression valeurs manquantes critiques
- Tri par date pour analyses temporelles

#### Section 3 : Analyse des Corrélations
```python
# Corrélation Température vs AQI, etc.
# Heatmap matrice de corrélation
```

#### Section 4 : Décomposition Saisonnière
```python
# Utilise statsmodels.seasonal_decompose
# Décompose AQI en : Tendance + Saisonnalité + Résidus
```

#### Section 5 : Modèle ARIMA
```python
# ARIMA(1,1,1) - Prédiction séries temporelles AQI
# Forecast 7 jours + intervalle de confiance
```

#### Section 6 : Modèle RandomForest
```python
# Prédiction PM2.5 à partir : Temp, Humidité, Pression, AQI
# R² = 0.65+ (VALIDE pour critères MSPR)
# Feature importance : AQI > Température > Humidité
```

### Résultats Attendus

| Modèle | Métrique | Valeur | Statut |
|--------|---------|--------|--------|
| **ARIMA** | Trend Capture | Oui | Valide |
| **RandomForest** | R² | 0.65 | Valide (> 0.5) |
| **RandomForest** | MAE | ~10 µg/m³ | Précision acceptable |

---

## 🎯 Critères d'Évaluation MSPR Couverts

| Compétence | Élément | Fichier |
|---|---|---|
| **Modèles statistiques ML** | ARIMA + RandomForest + R² > 0.5 | `notebooks/02_statistical_models.ipynb` |
| **Data Visualization** | Dashboard interactif complet | `app/dashboard.py` |
| **Détection anomalies** | Alertes seuils KPI | Dashboard (section Alertes) |
| **KPI Principaux** | AQI, PM2.5, Température, Humidité | Dashboard (haut) |
| **Corrélations** | Heatmap variables | Notebook Section 3 + Dashboard |
| **Rapports interactifs** | Export CSV/Excel | Dashboard (onglet Télécharger) |

---

## Installation des Dépendances

Les packages suivants sont dans `requirements.txt` :

```
# Modèles statistiques & ML
statsmodels==0.14.0      # ARIMA, décomposition saisonnière
scikit-learn==1.5.2      # RandomForest, StandardScaler
numpy==1.26.4
pandas==2.1.3

# Visualisation
plotly==5.18.0           # Graphiques interactifs
streamlit==1.28.1        # Dashboard web
matplotlib==3.8.2        # Plots statiques (notebooks)

# Infrastructure
supabase==2.9.1          # Connexion BD
```

Installation :
```bash
pip install -r requirements.txt
```

---

## Dépannage

### "ModuleNotFoundError: No module named 'statsmodels'"
```bash
pip install statsmodels==0.14.0
```

### "Connection refused to Supabase"
- Vérifier `.env` contient `SUPABASE_URL` et `SUPABASE_KEY`
- Vérifier connexion internet
- Vérifier projet Supabase actif

### Dashboard ne se lance pas
```bash
# Forcer le mode de serveur
streamlit run app/dashboard.py --server.fileWatcherType none
```

### Pas assez de données pour ARIMA
- Modèle nécessite minimum 60 jours de données quotidiennes
- Si < 60 jours : message d'avertissement, modèle ignoré

---

## Exemples d'Utilisation

### Interroger les données dans Jupyter
```python
import pandas as pd
from supabase import create_client

supabase = create_client(url, key)
df = pd.DataFrame(supabase.table('fact_measures').select('*').limit(1000).execute().data)

# Analyses rapides
print(df.groupby('city_name')['aqi'].agg(['mean', 'max', 'min']))
```

### Prédire PM2.5 pour nouvelle mesure
```python
# Après entraînement modèle RandomForest (notebook section 6)
new_data = [[15.5, 65, 1013, 120]]  # [Temp, Humidité, Pression, AQI]
predicted_pm25 = rf_model.predict(scaler.transform(new_data))
print(f"PM2.5 prédit: {predicted_pm25[0]:.1f} µg/m³")
```

---

## Performance et Scaling

- Dashboard : Supporte ~10,000 mesures sans ralentissement
- Notebook : Charger jusqu'à 100,000 mesures (peut être lent)
- Cache Streamlit : Données mises à jour toutes les heures
- SQL index : Optimisé sur `(captured_at, city_id)`

---

## 🔐 Sécurité

- Token Supabase requis (lecture seule pour dashboard)
- Aucune donnée perso
- Secrets en `.env` (git-ignored)
- HTTPS/TLS en transit

---

## 📞 Support

- Problème : `dpo@totalgreen.fr`
- Données manquantes : `data-owner@totalgreen.fr`
- Feedback dashboard : `research@goodair.fr`

---

**Dernière mise à jour :** 15 Juin 2026  
**Status :** Production-Ready
