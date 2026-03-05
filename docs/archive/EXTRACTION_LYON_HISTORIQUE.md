# Extraction Données Historiques Lyon Centre

## 🎯 Objectif

Remplacer les données de qualité de l'air de Lyon par celles de la station **Lyon Centre** (UID 3028) qui est plus fiable que la station actuelle (Lyon Trafic Jaurès).

## 📊 Problème Identifié

- **Station actuelle** : Lyon Trafic Jaurès (UID 10050) - Station de trafic
- **Données historiques** : AQI anormalement bas (moyenne 16.5 au lieu de 45)
- **Période problématique** : 12/01/2024 au 04/03/2026
- **Station recommandée** : Lyon Centre (UID 3028) - Station représentative

## 📡 Stations Disponibles pour Lyon

| Station | UID | Type | AQI Actuel | GPS |
|---------|-----|------|------------|-----|
| **Lyon Centre** ⭐ | 3028 | Urbaine | 87 | [45.758, 4.854] |
| Lyon Trafic Jaurès | 10050 | Trafic | 62 | [45.750, 4.844] |
| Lyon Gerland | 3029 | Urbaine | 74 | [45.735, 4.830] |
| Vaulx en Velin | 3026 | Périphérie | 78 | [45.779, 4.925] |

## ⚠️ Contrainte API

**L'API AQICN gratuite ne fournit PAS d'historique complet.**

Seules les données actuelles sont disponibles via l'API standard.

## 🔧 Solutions Disponibles

### Solution 1 : AQICN Data Platform (RECOMMANDÉ) ✅

#### Avantages
- ✅ **Gratuit** après inscription
- ✅ **Historique complet** depuis 2020
- ✅ **Toutes les stations** françaises disponibles
- ✅ **Tous les polluants** (PM2.5, PM10, NO2, O3, SO2, CO)
- ✅ **Format CSV** facile à traiter

#### Inconvénients
- ⚠️ Nécessite inscription manuelle
- ⚠️ Téléchargement manuel du fichier CSV

#### Étapes

1. **S'inscrire sur la plateforme**
   ```
   URL: https://aqicn.org/data-platform/covid19/
   ```

2. **Sélectionner les données**
   - Pays: France
   - Région: Rhône-Alpes / Auvergne-Rhône-Alpes
   - Ville: Lyon
   - Station: Lyon Centre (si disponible) ou toutes les stations Lyon

3. **Télécharger le CSV**
   - Période: 01/01/2024 à 05/03/2026
   - Format: CSV
   - Placer le fichier dans `data/lyon_historical.csv`

4. **Convertir et importer**
   ```bash
   # Test d'abord (simulation)
   python scripts/import_lyon_historical.py data/lyon_historical.csv
   
   # Si OK, insertion réelle
   python scripts/import_lyon_historical.py data/lyon_historical.csv --insert
   ```

5. **Traiter les données**
   ```bash
   # Transformer les nouvelles données brutes
   python src/etl_transform_to_db.py
   ```

6. **Vérifier la qualité**
   ```bash
   # Analyser les nouvelles données
   python scripts/check_lyon_aqi.py
   ```

### Solution 2 : Collecte Prospective (À partir d'aujourd'hui) 🔄

#### Principe
Modifier le code pour collecter les données de Lyon Centre dès maintenant, et accumuler progressivement l'historique.

#### Avantages
- ✅ Automatique
- ✅ Pas de manipulation manuelle
- ✅ Données fiables dès maintenant

#### Inconvénients
- ❌ Pas d'historique antérieur
- ❌ Nécessite plusieurs mois pour construire l'historique

#### Modification à faire

**Fichier**: `src/services/air_quality_service.py`

```python
def fetch_air_quality_data(self, city_name: str) -> Optional[Dict]:
    """Récupère les données AQI"""
    
    # Mapping ville → UID station préférée
    PREFERRED_STATIONS = {
        'Lyon': 3028,  # Lyon Centre au lieu de GPS
        'Paris': ...,  # etc.
    }
    
    # Si ville a une station préférée, utiliser l'UID
    if city_name in PREFERRED_STATIONS:
        uid = PREFERRED_STATIONS[city_name]
        url = f"https://api.waqi.info/feed/@{uid}/"
    else:
        # Sinon, utiliser le nom de ville (comportement actuel)
        url = f"{self.base_url}/{city_name}/"
    
    # ... reste du code inchangé
```

### Solution 3 : API Historical Data (PAYANTE) 💰

#### Principe
Contacter AQICN pour accès à l'API historique complète.

#### Avantages
- ✅ Accès programmatique
- ✅ Toutes les données
- ✅ Automatisable

#### Inconvénients
- ❌ Payant
- ❌ Coût selon volume

#### Contact
```
Email: contact@aqicn.org
Objet: Historical Data API Access Request
```

## 📋 Scripts Disponibles

### 1. `extract_lyon_centre_data.py`

**Usage** : Test de disponibilité et comparaison
```bash
python scripts/extract_lyon_centre_data.py
```

**Fonctionnalités** :
- ✅ Teste les endpoints API
- ✅ Récupère données actuelles Lyon Centre
- ✅ Compare avec station actuelle
- ✅ Génère exemple au format `raw_data_lake`

**Sortie** :
- Fichier : `scripts/lyon_centre_sample.json`
- Exemple de donnée formatée pour insertion

### 2. `import_lyon_historical.py`

**Usage** : Convertir CSV → raw_data_lake
```bash
# Simulation (dry-run)
python scripts/import_lyon_historical.py data/lyon_historical.csv

# Insertion réelle
python scripts/import_lyon_historical.py data/lyon_historical.csv --insert
```

**Fonctionnalités** :
- ✅ Parse fichier CSV AQICN
- ✅ Convertit au format `raw_data_lake`
- ✅ Insère dans Supabase
- ✅ Statistiques et validation

**Paramètres attendus CSV** :
```
Date,PM2.5,PM10,O3,NO2,SO2,CO
2024-01-12 00:00:00,25.3,45.2,12.1,35.4,5.2,0.8
...
```

### 3. `check_available_stations.py`

**Usage** : Lister toutes les stations disponibles
```bash
python scripts/check_available_stations.py
```

**Fonctionnalités** :
- ✅ Liste stations Lille et Lyon
- ✅ Affiche GPS, UID, AQI actuel
- ✅ Compare avec station actuellement utilisée

## 🔍 Validation des Données

Après importation, vérifier la qualité :

```bash
# 1. Vérifier les données brutes
python -c "
from src.services.database_service import DatabaseService
from src.config import Config

db = DatabaseService(Config.SUPABASE_URL, Config.SUPABASE_KEY)
result = db.client.table('raw_data_lake').select('*').eq('city_name', 'Lyon').eq('processed', False).count('exact').execute()
print(f'Nouvelles données brutes: {result.count}')
"

# 2. Transformer en fact_measures
python src/etl_transform_to_db.py

# 3. Analyser la qualité
python scripts/check_lyon_aqi.py
python scripts/diagnostic_lyon_aqi.py
```

## 📊 Format des Données

### `raw_data_lake`

```json
{
  "city_id": 3,
  "city_name": "Lyon",
  "source": "aqicn",
  "collected_at": "2024-01-12T00:00:00",
  "processed": false,
  "processed_at": null,
  "raw_data": {
    "status": "ok",
    "data": {
      "aqi": 45,
      "idx": 3028,
      "city": {
        "name": "Lyon Centre, France",
        "geo": [45.758, 4.854],
        "url": "https://aqicn.org/city/@3028"
      },
      "iaqi": {
        "pm25": {"v": 45},
        "pm10": {"v": 52},
        "no2": {"v": 38},
        "o3": {"v": 12}
      },
      "time": {
        "s": "2024-01-12 00:00:00",
        "v": 1705017600,
        "iso": "2024-01-12T00:00:00+01:00"
      }
    }
  }
}
```

## 🎯 Recommandation Finale

**Solution recommandée** : **Solution 1 (AQICN Data Platform)**

**Raison** :
- ✅ Gratuit et complet
- ✅ Données historiques fiables
- ✅ Permet remplacement complet de l'historique problématique
- ✅ Process validé et documenté

**Plan d'action** :
1. ✅ S'inscrire sur AQICN Data Platform
2. ✅ Télécharger CSV Lyon Centre (01/01/2024 → 05/03/2026)
3. ✅ Lancer import avec `import_lyon_historical.py`
4. ✅ Transformer avec `etl_transform_to_db.py`
5. ✅ Valider avec `diagnostic_lyon_aqi.py`
6. ✅ Si validation OK → Supprimer anciennes données Lyon
7. ✅ Modifier code pour utiliser UID 3028 à l'avenir (Solution 2)

## 📞 Support

Si problème, vérifier :
- ✅ Connexion Supabase OK (`Config.SUPABASE_URL`, `Config.SUPABASE_KEY`)
- ✅ Format CSV correct (colonnes attendues)
- ✅ Période des données cohérente
- ✅ Pas de doublons dans raw_data_lake

## 📚 Documentation Complémentaire

- [AQICN API Documentation](https://aqicn.org/api/)
- [AQICN Data Platform](https://aqicn.org/data-platform/)
- [Architecture du projet](docs/ARCHITECTURE.md)
- [Schéma ETL](docs/schema_flux_etl.md)
