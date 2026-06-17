# Dictionnaire des Données - GoodAir

## Vue d'ensemble

Document formalisé décrivant toutes les sources de données, leurs attributs, unités, plages de validité et critères de sélection/rejet pour le projet GoodAir.

---

## 1. Sources de Données Intégrées

| Source | API | Fréquence | Couverture | Format |
|--------|-----|-----------|-----------|--------|
| **OpenWeather** | openweathermap.org/api | Temps réel (toutes les heures) | 10 villes FR | JSON |
| **AQICN** | aqicn.org/json-api | Temps réel (toutes les heures) | 10 villes FR | JSON |
| **TomTom Traffic** | api.tomtom.com | Temps réel (15 min) | Routes principales FR | JSON |
| **Hub'Eau** | hubeau.eaufrance.fr | Temps réel (hourly) | Stations cours d'eau + eau potable | JSON |

---

## 2. Dimensions Principales

### `dim_city`
Référentiel des villes analysées.

| Colonne | Type | Unité | Plage valide | Commentaire |
|---------|------|-------|-------------|------------|
| `city_id` | INTEGER | - | 1-10 | Clé primaire |
| `city_name` | VARCHAR(255) | - | - | Paris, Lyon, Marseille, ... |
| `latitude` | DOUBLE | degrés | -90 à 90 | Coordonnées géographiques |
| `longitude` | DOUBLE | degrés | -180 à 180 | Coordonnées géographiques |
| `country_code` | CHAR(2) | - | FR | Code ISO pays |
| `population` | INTEGER | habitants | > 0 | Population approximative |

### `dim_date`
Dimension temporelle.

| Colonne | Type | Unité | Plage valide | Commentaire |
|---------|------|-------|-------------|------------|
| `date_value` | DATE | - | 2024-01-01+ | Date au format YYYY-MM-DD |
| `day_of_week` | INTEGER | - | 0-6 | Lundi=0, Dimanche=6 |
| `week_of_year` | INTEGER | - | 1-53 | Semaine de l'année |
| `month` | INTEGER | - | 1-12 | Numéro du mois |
| `quarter` | INTEGER | - | 1-4 | Trimestre |
| `year` | INTEGER | - | 2024+ | Année |

---

## 3. Tables de Faits - Mesures Environnementales

### `fact_measures` (Météo + Qualité de l'air)
Table principale combinant données OpenWeather et AQICN.

#### Variables Météorologiques

| Colonne | Type | Unité | Min | Max | Règle Rejet |
|---------|------|-------|-----|-----|------------|
| `temperature` | DOUBLE | °C | -50 | 60 | Hors limites → rejeté |
| `feels_like` | DOUBLE | °C | -60 | 70 | Hors limites → rejeté |
| `humidity` | INTEGER | % | 0 | 100 | Hors limites → rejeté |
| `pressure` | INTEGER | hPa | 800 | 1100 | Hors limites → rejeté |
| `wind_speed` | DOUBLE | m/s | 0 | 150 | Hors limites → rejeté |
| `wind_gust` | DOUBLE | m/s | 0 | 200 | Hors limites → rejeté |
| `clouds` | INTEGER | % | 0 | 100 | Hors limites → rejeté |
| `visibility` | INTEGER | m | 0 | 50000 | Hors limites → rejeté |
| `uvi` | DOUBLE | index | 0 | 15 | Hors limites → rejeté |

#### Variables Qualité de l'Air

| Colonne | Type | Unité | Min | Max | Seuil Alerte | Commentaire |
|---------|------|-------|-----|-----|------------|------------|
| `aqi` | INTEGER | index | 0 | 500 | > 300 | Air Quality Index (1=bon, 5=très mauvais) |
| `pm2_5` | DOUBLE | µg/m³ | 0 | 1000 | > 150 | Particules fines < 2.5 µm |
| `pm10` | DOUBLE | µg/m³ | 0 | 2000 | > 300 | Particules fines < 10 µm |
| `no2` | DOUBLE | µg/m³ | 0 | 500 | > 200 | Dioxyde d'azote |
| `o3` | DOUBLE | µg/m³ | 0 | 800 | > 500 | Ozone |
| `so2` | DOUBLE | µg/m³ | 0 | 500 | > 350 | Dioxyde de soufre |
| `co` | DOUBLE | µg/m³ | 0 | 50000 | > 10000 | Monoxyde de carbone |

#### Métadonnées

| Colonne | Type | Contenu |
|---------|------|---------|
| `captured_at` | TIMESTAMP | Horodatage UTC de la capture |
| `processed_at` | TIMESTAMP | Horodatage UTC du traitement |
| `request_id` | UUID | Identifiant unique de la requête |
| `latence_ms` | INTEGER | Latence API en millisecondes |

---

### `fact_traffic_flow`
Données de trafic TomTom.

| Colonne | Type | Unité | Plage | Commentaire |
|---------|------|-------|-------|------------|
| `speed` | DOUBLE | km/h | 0-150 | Vitesse moyenne segment |
| `free_flow_speed` | DOUBLE | km/h | 0-150 | Vitesse non congestionée |
| `congestion_level` | VARCHAR(50) | - | 'flowing', 'slow', 'heavy', 'jammed' | État du trafic |
| `current_travel_time` | INTEGER | secondes | > 0 | Temps de trajet actuel |

**Règles de sélection:**
- Rejeter si `speed` est négatif ou > 200 km/h
- Rejeter si `current_travel_time` < 0

---

### `fact_eau_potable`
Qualité de l'eau potable.

| Colonne | Type | Unité | Plage | Commentaire |
|---------|------|-------|-------|------------|
| `libelle_parametre` | VARCHAR(255) | - | - | Nom du paramètre mesuré |
| `resultat_numerique` | DOUBLE | (paramètre-dépendant) | > 0 | Valeur numérique |
| `libelle_unite` | VARCHAR(50) | - | - | Unité de mesure |
| `conclusion_conformite_prelevement` | VARCHAR(50) | - | CONFORME/NON-CONFORME | Conformité normative |
| `date_prelevement` | TIMESTAMP | - | - | Date du prélèvement |

**Critères de validité:**
- Paramètres acceptés : pH, turbidité, bactéries, nitrates, pesticides
- Rejeter si `resultat_numerique` est négatif

---

### `fact_cours_deau_observation`
Observations physico-chimiques des cours d'eau.

| Colonne | Type | Unité | Plage | Commentaire |
|---------|------|-------|-------|------------|
| `libelle_parametre` | VARCHAR(255) | - | - | pH, température, conductivité, etc. |
| `resultat` | DOUBLE | (paramètre-dépendant) | Variable | Valeur mesurée |
| `symbole_unite` | VARCHAR(50) | - | - | Unité |
| `date_prelevement` | TIMESTAMP | - | - | Date du prélèvement |

---

## 4. Critères de Sélection et Validation des Données

### Phase de Découverte
1. **Identité des données** : Source confirmée, horodatage présent
2. **Complétude** : Minimum 80% des attributs requis non-nulls
3. **Plausibilité** : Valeurs dans plages physiquement possibles

### Phase de Structuration
1. Conversion des types (timestamps en ISO 8601, températures en °C)
2. Normalisation des unités
3. Jointure ville ↔ coordonnées géographiques

### Phase de Nettoyage
1. **Valeurs manquantes** :
   - < 5% → imputation par moyenne/médiane
   - > 5% → suppression de la ligne
2. **Doublons** : Suppression basée sur `(city_id, captured_at, source)`
3. **Outliers statistiques** :
   - Détection : Z-score > 3σ
   - Action : Marquage en table `anomalies`, rejet optionnel

### Phase de Validation
1. **Intégrité structurelle** : Types, clés étrangères
2. **Cohérence temporelle** : `processed_at` > `captured_at`
3. **Couverture spatiale** : Au minimum une ville par jour
4. **Limites métier** : Seuils d'alerte franchis → log en `anomalies`

---

## 5. Traçabilité et Qualité

### Champs de traçabilité (dans chaque fact table)

| Champ | Signification |
|-------|--------------|
| `request_id` | UUID unique pour chaque appel API |
| `latence_ms` | Latence API (qualité de la connexion) |
| `processed_at` | Quand les données ont été intégrées |
| `source` | OpenWeather, AQICN, TomTom, Hub'Eau |

### Table `anomalies` (Suivi QA)

| Colonne | Contenu |
|---------|---------|
| `anomaly_id` | Clé primaire |
| `table_name` | Table affectée |
| `field_name` | Champ problématique |
| `anomaly_type` | 'business_rule', 'statistical', 'missing_data' |
| `severity` | 'low', 'medium', 'high', 'critical' |
| `details` | Description textuelle |
| `detected_at` | Timestamp de détection |

---

## 6. Cas d'Usage et Recommandations

### Pour Data Scientists
- **Séries temporelles** : Utiliser `fact_measures` avec agrégation quotidienne
- **Corrélations** : AQI fortement corrélé avec température et humidité
- **Prédictions** : ML sur PM2.5 possible (R² > 0.6)

### Pour BI/Dashboards
- **KPI principaux** : AQI moyen, PM2.5 max, températures extrêmes
- **Alertes** : Déclencher si AQI > 300 ou PM2.5 > 150
- **Cartes** : Visualiser stations par géolocalisation

### Pour Chercheurs
- **Changement climatique** : Analyser tendances annuelles (température, saisonnalité)
- **Santé publique** : Corréler AQI avec événements météorologiques
- **Études comparatives** : Comparer villes sur même période

---

## 7. Conformité RGPD

✅ **Aucune donnée personnelle** collectée dans le flux standard
- Données publiques (météo, air)
- Données institutionnelles (cours d'eau, eau potable)
- Métadonnées géographiques (villes, stations)

⚠️ **Recommandations:**
- Politique de rétention : 2 ans de données actives minimum
- Accès : Authentication API requise
- Chiffrement : En transit (HTTPS), au repos (Supabase encrypted)

---

## 8. Contact et Gouvernance

**Data Owner** : Équipe GoodAir  
**Techniquement Responsable** : ETL Pipeline Manager  
**Dernière révision** : 2026-06-15  
**Prochaine revue** : Q3 2026
