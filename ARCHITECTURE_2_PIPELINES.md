# Architecture ETL en 2 Pipelines Séparés

## 🎯 Objectif

Découpler la **collecte de données** (fréquente) du **traitement/chargement** (moins fréquent) pour optimiser les performances et les coûts d'API.

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE 1 : EXTRACTION                   │
│                   Toutes les heures (7h-0h)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   OpenWeather    │
                    │      AQICN       │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   DATA LAKE      │
                    │  (JSONB Supabase)│
                    │   processed=false│
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 PIPELINE 2 : TRANSFORMATION                  │
│                    1x par jour (0h)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Lecture Data Lake│
                    │  (processed=false)│
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Transformation  │
                    │    + Validation   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    BDD measures   │
                    │  (données normalisées)│
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Mise à jour     │
                    │  processed=true   │
                    └──────────────────┘
```

---

## 🔧 Fichiers Créés

### **1. Pipeline d'Extraction**
**Fichier:** [src/etl_extract_to_lake.py](../src/etl_extract_to_lake.py)

**Fonction:**
- Collecte les données des APIs (OpenWeather + AQICN)
- Stocke les JSON bruts dans `raw_data_lake`
- Logs: `logs/etl_extract.log`

**Workflow GitHub Actions:** [.github/workflows/etl-extract.yml](../.github/workflows/etl-extract.yml)
- **Fréquence:** Toutes les heures de 6h à 23h UTC (7h à 0h heure française)
- **Déclenchement manuel:** Actions → "1️⃣ Extract vers Data Lake"

### **2. Pipeline de Transformation**
**Fichier:** [src/etl_transform_to_db.py](../src/etl_transform_to_db.py)

**Fonction:**
- Lit les données non traitées du Data Lake (`processed=false`)
- Parse et transforme les données JSON
- Charge dans la table `measures`
- Marque les données comme traitées (`processed=true`)
- Logs: `logs/etl_transform.log`

**Workflow GitHub Actions:** [.github/workflows/etl-transform.yml](../.github/workflows/etl-transform.yml)
- **Fréquence:** 1x par jour à 23h UTC (0h heure française)
- **Déclenchement manuel:** Actions → "2️⃣ Transform vers BDD"

---

## ⚙️ Configuration GitHub Actions

Les **mêmes 4 secrets** sont nécessaires pour les 2 workflows :

```
OPENWEATHER_API_KEY
AQICN_API_KEY
SUPABASE_URL
SUPABASE_KEY
```

➡️ Configuration : `Settings → Secrets and variables → Actions`

---

## 🚀 Utilisation

### **Test Local**

```bash
# 1. Extraction (collecte les données)
cd src
python etl_extract_to_lake.py

# 2. Transformation (traite les données)
python etl_transform_to_db.py
```

### **Test GitHub Actions**

1. Aller dans **Actions** → **"1️⃣ Extract vers Data Lake"**
2. Cliquer sur **"Run workflow"** → Attendre 1-2 min
3. Vérifier les logs ✅
4. Aller dans **"2️⃣ Transform vers BDD"**
5. Cliquer sur **"Run workflow"** → Attendre ~30s
6. Vérifier les logs ✅

---

## 📈 Avantages

| Aspect | Pipeline Unique | Pipelines Séparés |
|--------|----------------|-------------------|
| **Collecte données** | 1x/heure | 1x/heure (Extract) |
| **Traitement BDD** | 1x/heure | 1x/jour (Transform) |
| **Consommation API** | 10 villes × 2 APIs × 18h = 360 calls/jour | 360 calls/jour (identique) |
| **Écritures BDD** | ~360 inserts/jour | ~360 inserts groupés/jour |
| **Résilience** | Échec = perte données | Données conservées en Data Lake |
| **Retraitement** | Impossible | Possible (processed=false) |
| **Maintenance** | 1 script | 2 scripts indépendants |

---

## 📊 Monitoring

### **Supabase - Table `raw_data_lake`**

```sql
-- Voir les données non traitées
SELECT id, city_name, source, collected_at, processed
FROM raw_data_lake
WHERE processed = false
ORDER BY collected_at DESC;

-- Statistiques
SELECT 
    source,
    processed,
    COUNT(*) as total
FROM raw_data_lake
GROUP BY source, processed;
```

### **Supabase - Table `etl_logs`**

```sql
-- Logs d'extraction
SELECT * FROM etl_logs
WHERE source = 'extract'
ORDER BY execution_time DESC
LIMIT 10;

-- Logs de transformation
SELECT * FROM etl_logs
WHERE source = 'transform'
ORDER BY execution_time DESC
LIMIT 10;
```

---

## 🔄 Migration depuis Pipeline Unique

Si vous utilisez déjà [etl_pipeline.py](../src/etl_pipeline.py), vous pouvez :

**Option 1: Garder les 2 versions**
- Pipeline unique: Pour tests locaux rapides
- Pipelines séparés: Pour production GitHub Actions

**Option 2: Migration complète**
1. Désactiver [.github/workflows/etl-pipeline.yml](../.github/workflows/etl-pipeline.yml)
2. Activer les 2 nouveaux workflows
3. Tester manuellement avant activation automatique

---

## 🛠️ Personnalisation

### **Modifier la fréquence d'extraction**

Éditer [.github/workflows/etl-extract.yml](../.github/workflows/etl-extract.yml):

```yaml
schedule:
  # Toutes les 30 minutes de 6h à 23h
  - cron: '*/30 6-23 * * *'
```

### **Modifier la fréquence de transformation**

Éditer [.github/workflows/etl-transform.yml](../.github/workflows/etl-transform.yml):

```yaml
schedule:
  # 2x par jour (12h et 0h)
  - cron: '0 0,12 * * *'
```

---

## ❓ FAQ

**Q: Que se passe-t-il si la transformation échoue ?**  
R: Les données restent dans le Data Lake avec `processed=false`. La prochaine exécution les retraitera automatiquement.

**Q: Peut-on lancer la transformation plusieurs fois ?**  
R: Oui, mais seules les données `processed=false` seront traitées. Pas de doublon.

**Q: Combien de données dans le Data Lake ?**  
R: 10 villes × 2 sources × 18h/jour × 30 jours = ~10 800 entrées/mois (~11 MB)

**Q: Faut-il purger le Data Lake ?**  
R: Optionnel. Vous pouvez supprimer les données `processed=true` de plus de 90 jours pour économiser l'espace.

---

## 📝 Logs

**Extraction:** `logs/etl_extract.log`  
**Transformation:** `logs/etl_transform.log`  
**GitHub Actions:** Onglet "Actions" → Workflow → "etl" job → Logs téléchargeables

---

**Auteur:** TotalGreen ETL  
**Dernière mise à jour:** 20 janvier 2026
