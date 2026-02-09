# Correction de l'horodatage des données

**Date de correction :** 4 février 2026  
**Problème identifié :** Les timestamps utilisaient le moment de chargement en BDD au lieu du moment réel de collecte des données par les APIs.

## 🔧 Modifications apportées

### 1. Services de collecte
- **[weather_service.py](../src/services/weather_service.py)** : Ajout de `get_timestamp()` pour extraire le champ `dt` de l'API OpenWeather
- **[air_quality_service.py](../src/services/air_quality_service.py)** : Ajout de `get_timestamp()` pour extraire le champ `time.v` de l'API AQICN

### 2. Service Data Lake
- **[data_lake_service.py](../src/services/data_lake_service.py)** : Modification de `store_raw_data()` pour accepter un timestamp optionnel

### 3. Pipelines ETL
- **[etl_extract_to_lake.py](../src/etl_extract_to_lake.py)** : Extraction et transmission des timestamps réels des APIs
- **[etl_transform_to_db.py](../src/etl_transform_to_db.py)** : Utilisation du timestamp du data lake (provenant de l'API) au lieu de `datetime.utcnow()`

## ✅ Résultat

**AVANT :**
```
collected_at → datetime.utcnow() (moment du chargement)
captured_at  → datetime.utcnow() (moment du chargement)
```

**APRÈS :**
```
collected_at → timestamp de l'API (moment réel de la mesure)
captured_at  → timestamp du data lake (provenant de l'API)
```

## 📊 Exemple de timestamps réels

```
Heure de test : 2026-02-04 17:20:24

Data Lake :
- OpenWeather Paris : 2026-02-04 17:18:04 (mesure réelle)
- AQICN Paris       : 2026-02-04 15:00:00 (mesure réelle)
```

Les timestamps reflètent maintenant **le moment exact de la mesure par les capteurs**, et non plus le moment du chargement en base de données.

## 🎯 Avantages

1. **Traçabilité précise** : Connaissance du moment exact de la mesure
2. **Conformité RGPD** : Horodatage authentique des données collectées
3. **Analyses temporelles fiables** : Les analyses basées sur le temps sont maintenant exactes
4. **Détection d'anomalies** : Possibilité de détecter les retards de collecte

## ⚠️ Note importante

Les APIs peuvent avoir des décalages :
- **OpenWeather** : Mise à jour toutes les ~10-15 minutes
- **AQICN** : Mise à jour horaire (à l'heure pile)

Ces décalages sont normaux et reflètent la fréquence réelle de mise à jour des capteurs.
