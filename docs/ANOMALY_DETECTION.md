# Guide de mise en place de la détection d'anomalies ML

## Prérequis

1. **Installation des dépendances ML**
   ```bash
   pip install -r requirements.txt
   ```
   Cela installe :
   - `scikit-learn==1.5.2` (Isolation Forest)
   - `numpy==1.26.4` (calculs matriciels)

## Déploiement

### Étape 1 : Déployer le schéma sur Supabase

Dans l'éditeur SQL Supabase, exécutez dans l'ordre :

```sql
-- 1. Créer la table anomalies et les champs dans fact_measures
\i sql/anomaly_detection_schema.sql

-- 2. Créer les fonctions utilitaires
\i sql/anomaly_functions.sql
```

### Étape 2 : Tester la détection

```bash
# Exécuter le pipeline Transform avec ML
cd src
python etl_transform_to_db.py
```

Le système :
1. Entraîne automatiquement le modèle Isolation Forest sur 5000 mesures historiques
2. Analyse chaque nouvelle mesure avec 3 niveaux :
   - **Règles métier** : température < -50°C ou > 60°C
   - **Statistiques** : Z-score > 3σ (écart-type)
   - **ML** : Isolation Forest (anomalies multivariées)
3. Rejette les anomalies critiques
4. Flagge les anomalies low/medium/high (insérées avec `is_anomaly=true`)

## Validation de la qualité des données

### Script de validation automatique

Un script de validation est disponible pour vérifier l'intégrité et la qualité des données après import :

```bash
# Valider les données des dernières 24h
python scripts/validate_data_quality.py

# Valider une période spécifique (48h)
python scripts/validate_data_quality.py --hours 48

# Mode strict (échoue si warnings)
python scripts/validate_data_quality.py --strict
```

### Vérifications effectuées

**1. Intégrité structurelle**
- Clés étrangères NULL (city_id, capture_date, captured_at)
- Doublons (même city_id + captured_at)
- Cohérence des FK avec dim_city

**2. Cohérence temporelle**
- created_at < captured_at (incohérences)
- Dates dans le futur
- Gaps temporels (>2h sans données par ville)

**3. Limites physiques (business rules)**
- Température : -50°C à 60°C
- Humidité : 0% à 100%
- Pression : 870 à 1084 hPa
- AQI : 0 à 500
- PM2.5/PM10 : 0 à 1000/2000 µg/m³

**4. Couverture des données**
- Toutes les 10 villes présentes
- Volume de données par ville (détection villes sous-représentées)

**5. Outliers statistiques**
- Détection valeurs aberrantes (>3σ) par champ
- Calcul Z-score pour température, humidité, pression, AQI, PM2.5, PM10

### Intégration GitHub Actions

Le script est conçu pour être exécuté après chaque import de données :

**Exit codes** :
- `0` : Validation OK (aucun problème critique)
- `1` : Problèmes critiques détectés (échec)
- `2` : Erreur d'exécution

**Exemple workflow GitHub Actions** :

```yaml
name: Validate Data Quality

on:
  schedule:
    - cron: '15 * * * *'  # 15 minutes après chaque heure
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Validate data quality
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: python scripts/validate_data_quality.py --hours 2
      
      - name: Notify on failure
        if: failure()
        run: echo "Data quality issues detected!"
        # Ajouter notification Slack/Email ici
```

### Rapport de validation

Le script génère un rapport détaillé :

```
======================================================================
VALIDATION QUALITÉ DES DONNÉES
======================================================================

Période analysée: 24h (depuis 2026-03-04T10:30:00)

Chargement des données...

1. Vérification intégrité structurelle...
   Total mesures: 240
   Doublons: 0
   Valeurs NULL: 0

2. Vérification cohérence temporelle...
   Incohérences temporelles: 5
   Dates futures: 0
   Gaps temporels: 2

3. Vérification limites physiques...
   Violations: 0 types différents

4. Vérification couverture des données...
   Villes avec données: 10/10
   Villes manquantes: 0
      - Paris: 24 mesures
      - Marseille: 24 mesures
      - Lyon: 24 mesures
      ...

5. Détection outliers statistiques...
   Outliers détectés: 1 champs
      - pm25: 3 (1.2%) - max Z=3.2

======================================================================
RAPPORT DE VALIDATION
======================================================================

Total problèmes: 8
   CRITICAL: 0
   WARNING:  5
   INFO:     3

WARNING:

   [temporal_coherence] 5 mesures avec created_at < captured_at

INFO:

   [statistical_outliers] 3 outliers statistiques détectés (>3σ)
      outliers: {'pm25': {...}}

======================================================================
STATUT: validation OK
======================================================================
```

## Analyse des anomalies

### Requête : Résumé des anomalies par ville

```sql
SELECT * FROM get_anomaly_summary(7);  -- 7 derniers jours
```

### Requête : Anomalies critiques récentes

```sql
SELECT * FROM v_critical_anomalies;
```

### Requête : Mesures flaggées comme anomalies

```sql
SELECT 
    dt.date_full,
    dt.hour_24,
    dc.city_name,
    fm.temperature,
    fm.aqi,
    fm.anomaly_score,
    aq.level_name
FROM fact_measures fm
JOIN dim_time dt ON fm.time_id = dt.time_id
JOIN dim_city dc ON fm.city_id = dc.city_id
LEFT JOIN dim_air_quality_level aq ON fm.aqi_level_id = aq.aqi_level_id
WHERE fm.is_anomaly = TRUE
ORDER BY fm.anomaly_score DESC
LIMIT 20;
```

### Requête : Statistiques par ville

```sql
-- Température moyenne, écart-type, min, max
SELECT * FROM get_city_stats('Paris', 30);  -- 30 derniers jours
```

## Types d'anomalies détectées

### 1. Règles métier (business_rule)
- **Température** : < -50°C ou > 60°C
- **Humidité** : < 0% ou > 100%
- **AQI** : < 0 ou > 500
- **PM2.5** : < 0 ou > 1000 µg/m³

**Action** : REJET automatique

### 2. Anomalies statistiques (statistical)
- **Z-score** : écart de 2σ à 4σ de la moyenne historique
- Calculé sur température, humidité, pression, AQI
- Basé sur 30 jours d'historique

**Action** : FLAGGED (low/medium/high) ou REJET (critical si >4σ)

### 3. Anomalies ML (ml_isolation_forest)
- **Isolation Forest** : détecte les combinaisons anormales de valeurs
- Ex: température 15°C + humidité 90% + AQI 200 peut être anormal même si chaque valeur est OK individuellement
- Score d'anomalie : -1.0 (très anormal) à 0.0 (normal)

**Action** : 🚨 FLAGGED ou ❌ REJET selon le score

## 📈 Métriques de performance

Le modèle ML s'adapte automatiquement :
- **Entraînement** : Sur les 5000 dernières mesures normales (`is_anomaly=false`)
- **Contamination** : 5% (taux d'anomalies attendu)
- **Ré-entraînement** : À chaque exécution du pipeline Transform

## 🔧 Configuration avancée

### Modifier le seuil de contamination

Dans `src/etl_transform_to_db.py` :
```python
self.anomaly_service = AnomalyDetectionService(contamination=0.05)  # 5%
# contamination=0.01 : plus strict (1% anomalies)
# contamination=0.10 : plus permissif (10% anomalies)
```

### Modifier les règles métier

Dans `src/services/anomaly_detection_service.py` :
```python
BUSINESS_RULES = {
    'temperature': {'min': -50, 'max': 60, 'unit': '°C'},  # Ajuster min/max
    # ...
}
```

### Modifier les seuils Z-score

```python
Z_SCORE_THRESHOLD = {
    'low': 2.0,      # 95% des valeurs
    'medium': 2.5,   # 98.8%
    'high': 3.0,     # 99.7%
    'critical': 4.0  # Très rare
}
```

## 🎓 Valeur ajoutée pour le projet

✅ **+5 points** : Détection d'anomalies ML (Isolation Forest)
✅ **Qualité des données** : Filtrage automatique des valeurs aberrantes
✅ **Traçabilité** : Historique complet des anomalies détectées
✅ **Analyse** : Vues SQL pour diagnostiquer les problèmes de capteurs

## 📚 Documentation technique

- **Isolation Forest** : [scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- **Z-score** : Mesure statistique de l'écart d'une valeur par rapport à la moyenne
- **Contamination** : Proportion estimée d'anomalies dans les données

## 🚨 Dépannage

### Le modèle ML ne s'entraîne pas

```bash
# Vérifier qu'il y a assez de données historiques (min: 100)
python scripts/check_bdd_status.py
```

**Solution** : Lancer plusieurs fois `etl_extract_to_lake.py` + `etl_transform_to_db.py` pour accumuler des mesures.

### Trop d'anomalies détectées

```sql
-- Vérifier le taux d'anomalies
SELECT 
    COUNT(*) FILTER (WHERE is_anomaly = TRUE) * 100.0 / COUNT(*) as anomaly_rate
FROM fact_measures;
```

**Solution** : Si > 10%, augmenter la contamination à 0.10 dans le code.

### Pas assez d'anomalies détectées

**Solution** : Réduire la contamination à 0.01 pour être plus strict.
