# SLIDE 2 : DÉVELOPPEMENT

## Structure de la slide

### TITRE
**"Développement & Implémentation"**

---

## DISPOSITION EN 3 COLONNES

### COLONNE 1 : PIPELINE ETL & ARCHITECTURE

**Pipeline Python en 2 Étapes**

```
┌─────────────────────────────┐
│   ÉTAPE 1 : EXTRACT         │
│   etl_extract_to_lake.py    │
├─────────────────────────────┤
│ • Collecte 10 villes/heure  │
│ • 2 APIs parallélisées      │
│ • Format JSONB              │
│ • Stockage Data Lake        │
│ • Horodatage automatique    │
└─────────────────────────────┘
           ⬇
┌─────────────────────────────┐
│   ÉTAPE 2 : TRANSFORM       │
│   etl_transform_to_db.py    │
├─────────────────────────────┤
│ • Lecture processed=false   │
│ • Normalisation données     │
│ • Enrichissement            │
│ • Insertion Star Schema     │
│ • Marquage processed=true   │
└─────────────────────────────┘
```

**Architecture Modulaire**
```
src/services/
├── weather_service.py
├── air_quality_service.py
├── data_lake_service.py
└── database_service.py
```

**Gestion d'erreurs robuste**
- Try/catch à chaque niveau
- Logging complet (ETL)
- Retry automatique
- Traçabilité complète

---

### COLONNE 2 : QUALITÉ DES DONNÉES

**Validation Qualité Automatisée**

| Vérification | Fréquence | Résultat |
|--------------|-----------|----------|
| Doublons | 2×/jour | 0 actuellement |
| Dates futures | 2×/jour | 0 actuellement |
| Limites physiques | 2×/jour | 100% conforme |
| Complétude | 2×/jour | ✓ |
| Outliers statistiques | 2×/jour | Détection active |

**Script : validate_data_quality.py**
- 5 niveaux de validation
- Exit codes (0/1/2)
- Intégré GitHub Actions

**Contrôles de Qualité Multi-niveaux**

```
┌─────────────────────────────────┐
│  Validation en 5 étapes     │
├─────────────────────────────────┤
│ 1. Intégrité structurelle   │
│    - Doublons                 │
│    - Valeurs NULL             │
│    - Clés étrangères         │
│                               │
│ 2. Cohérence temporelle     │
│    - Dates futures            │
│    - Gaps temporels           │
│    - Timestamps                │
│                               │
│ 3. Limites physiques        │
│    - Temp: -50°C à 60°C      │
│    - AQI: 0 à 500             │
│    - Pression: 870-1084 hPa   │
│                               │
│ 4. Couverture               │
│    - 10 villes présentes      │
│    - Volume par ville         │
│                               │
│ 5. Outliers statistiques    │
│    - Z-score > 3σ            │
│    - Par champ                │
└─────────────────────────────────┘
```

**Nettoyage Automatique**
- Script : cleanup_data_quality_issues.py
- Batch processing (50 items)
- Dry-run mode
- **Résultat** : 125 doublons supprimés

**Stations AQI Optimisées**
- Lyon : Station "Lyon Centre" (idx 3028, france/rhonealpes/rhone/lyon-centre)
- Lille : Station Roubaix (métropole lilloise, données actuelles 2026)
- Données fiables et précises

---

### COLONNE 3 : STACK & PERFORMANCES

**Stack Technologique**

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.12 |
| Base de données | PostgreSQL (Supabase EU) | 15 |
| HTTP | requests | 2.31+ |
| Client DB | supabase-py | 2.0+ |
| Calcul | numpy | 1.26+ |
| Env | python-dotenv | 1.0+ |
| CI/CD | GitHub Actions | - |

**Orchestration GitHub Actions**

| Workflow | CRON | Durée |
|----------|------|-------|
| ETL Extract | Toutes les heures (:00) | ~20s |
| ETL Transform | Toutes les heures (:15) | ~3s |
| Validation Qualité | 2×/jour (00:15, 12:15) | ~30s |

**Performances Mesurées**

```
┌────────────────────────────┐
│   MÉTRIQUES CLÉS           │
├────────────────────────────┤
│ Collecte 10 villes : ~20s  │
│ • OpenWeather : ~10s       │
│ • AQICN : ~10s             │
│                            │
│ Transform 100 entrées : 3s │
│ • Lecture lake : 0.5s      │
│ • Normalisation : 1s       │
│ • Insertion : 1.5s         │
│                            │
│ Stockage quotidien : 737Ko │
│ Validation qualité : ~30s  │
│ Requêtes OLAP : 40ms       │
└────────────────────────────┘
```

**Optimisations Base de Données**

Index créés :
- GIN sur JSONB (data lake)
- B-Tree sur FK (fact_measures)
- Composite (time_id, city_id)
- Index AQI, température

**Production**
- **11 878 mesures** collectées
- **371 mesures/jour** (moyenne 7 jours)
- **Validation active** : 5 niveaux automatisés
- **Stockage** : 37 MB (32.5 Data Lake + 4.5 DW)

---

## FOOTER DE LA SLIDE

**"Pipeline opérationnel | 11 878 mesures | Validation 5 niveaux | 371 mesures/jour | 37 MB stockage"**

---

## NOTES POUR L'ORAL (3-4 minutes)

### Introduction (30 secondes)
*"Le développement s'articule autour de 3 piliers : un pipeline ETL robuste, une architecture modulaire Python, et un système de validation qualité avancé."*

### Partie 1 : Pipeline ETL (1 minute)
**Montrer COLONNE 1**

*"Notre pipeline ETL fonctionne en 2 étapes distinctes :"*

1. **Extract** (etl_extract_to_lake.py)
   - *"Toutes les heures, on collecte 10 villes via 2 APIs en parallèle"*
   - *"Les données brutes sont stockées en JSONB dans le Data Lake"*
   - *"Cela prend environ 20 secondes pour 10 villes"*

2. **Transform** (etl_transform_to_db.py)
   - *"15 minutes après, le Transform lit les données non traitées"*
   - *"On normalise, enrichit avec les dimensions, et insère dans le Star Schema"*
   - *"Temps de traitement : 3 secondes pour 100 entrées"*

**Architecture modulaire**
- *"4 services Python séparés pour la maintenabilité"*
- *"Gestion d'erreurs robuste à chaque niveau avec logging complet"*

### Partie 2 : Qualité des Données (1.5 minutes)
**Montrer COLONNE 2**

*"La qualité des données est garantie par un système automatisé multi-niveaux :"*

**Validation automatisée**
- *"Script validate_data_quality.py exécuté 2 fois par jour"*
- *"5 types de vérifications : doublons, dates, limites physiques, couverture, outliers"*
- *"Détection active : 26 doublons historiques identifiés, script cleanup disponible"*
- *"Traçabilité complète : table anomalies (v2.3) avec sauvegarde automatique"*

**Contrôles de Qualité**
- *"5 niveaux de validation automatique :"*
  1. *"Intégrité structurelle : doublons, valeurs NULL, clés étrangères"*
  2. *"Cohérence temporelle : dates futures, gaps temporels"*
  3. *"Limites physiques : température entre -50 et 60°C, AQI entre 0 et 500, pression 870-1084 hPa"*
  4. *"Couverture : vérification des 10 villes"*
  5. *"Outliers statistiques : Z-score > 3σ"*

**Nettoyage automatique**
- *"Script cleanup_data_quality_issues.py"*
- *"On a nettoyé 125 doublons lors de la mise en production"*

**Stations AQI Optimisées**
- *"Lyon : Station Lyon Centre (idx 3028) pour données fiables"*
- *"Lille : Station Roubaix (métropole lilloise, données actuelles)"*
- *"Amélioration de la qualité et précision des données"*

### Partie 3 : Stack & Performances (1 minute)
**Montrer COLONNE 3**

*"Notre stack technique est moderne et performant :"*

**Technologies**
- *"Python 3.12 avec bibliothèques modernes"*
- *"PostgreSQL 15 hébergé sur Supabase en UE"*
- *"GitHub Actions pour l'orchestration automatique"*

**Orchestration**
- *"3 workflows automatisés :"*
  - *"Extract toutes les heures"*
  - *"Transform 15 minutes après"*
  - *"Validation 2 fois par jour pour optimiser les coûts"*

**Performances**
- *"Collecte : ~20 secondes pour 10 villes"*
- *"Transform : ~3 secondes par batch"*
- *"Stockage : 737 KB par jour (37 MB total)"*
- *"Validation qualité : ~30 secondes"*
- *"Requêtes : 40ms pour 100 mesures"*

**Optimisations**
- *"Index GIN sur JSONB pour requêtes JSON rapides"*
- *"Index B-Tree et composites pour jointures optimisées"*

**En production**
- *"11 878 mesures collectées"*
- *"371 mesures par jour (moyenne 7j)"*
- *"Validation active : 26 doublons historiques détectés"*
- *"Traçabilité : table anomalies v2.3"*

### Conclusion (30 secondes)
*"En résumé : pipeline ETL robuste et automatisé, architecture modulaire maintenable, système de validation qualité 5 niveaux avec traçabilité, stations AQI optimisées, et performances optimales en production avec 11 878 mesures collectées."*

---

## VISUELS RECOMMANDÉS

### Schéma 1 : Pipeline ETL (à afficher en COLONNE 1)
```
APIs → Extract (20s) → Data Lake → Transform (3s) → Star Schema
        ↓                            ↓
    Logging                    ML Detection
```

### Schéma 2 : Validation Qualité (à afficher en COLONNE 2)
```
       ┌─────────────────┐
       │  Measure Input  │
       └────────┬────────┘
                │
        ┌───────┴───────┐
        │               │
    ┌───▼───┐     ┌────▼────┐     ┌───────▼────┐
    │Business│     │Structural│    │ Statistical│
    │ Rules  │     │Integrity │    │  Outliers  │
    └───┬───┘     └────┬────┘     └───────┬────┘
        │              │                   │
        └──────────────┴───────────────────┘
                       │
              ┌────────▼────────┐
              │  VALID / WARN / │
              │     REJECT      │
              └─────────────────┘
```

### Tableau Performances (à afficher en COLONNE 3)
Déjà inclus ci-dessus dans le format tableau markdown.

---

## ÉLÉMENTS À PRÉPARER

1. **Capture d'écran** : GitHub Actions workflows en cours
2. **Capture d'écran** : Logs ETL avec succès
3. **Capture d'écran** : Supabase dashboard (optionnel)
4. **Code snippet** : Exemple d'une fonction ML (optionnel)

---

## QUESTIONS ANTICIPÉES

**Q: "Pourquoi 2 étapes séparées (Extract/Transform) ?"**
R: "Séparation des responsabilités : si Transform échoue, les données brutes sont conservées. On peut réingérer sans rappeler les APIs. Aussi, cela permet de paralléliser et optimiser chaque étape indépendamment."

**Q: "Comment gérez-vous les pannes API ?"**
R: "Try/catch dans chaque service, retry automatique avec backoff exponentiel, logging détaillé. Les données non traitées restent marquées processed=false et seront reprises au prochain cycle."

**Q: "Comment garantissez-vous la qualité des données ?"**
R: "Validation automatisée 5 niveaux : intégrité structurelle, cohérence temporelle, limites physiques, couverture, et outliers statistiques. Script Python exécuté 2 fois par jour avec exit codes pour intégration CI/CD."

**Q: "Pourquoi validation seulement 2×/jour et pas après chaque import ?"**
R: "Optimisation des coûts et ressources. Valider toutes les heures serait redondant. 2×/jour suffit pour détecter les problèmes rapidement tout en économisant 90% des exécutions."

**Q: "Pourquoi des stations AQI spécifiques pour Lyon et Lille ?"**
R: "Pour améliorer la fiabilité des données. Lyon utilise la station Lyon Centre (idx 3028) et Lille la station Roubaix (métropole lilloise) qui fournissent des mesures actuelles 2026 plus précises et cohérentes."

**Q: "Scalabilité pour 100 villes ?"**
R: "Oui, l'architecture est prête : APIs parallélisées, batch processing, index optimisés. On estime ~3 minutes pour 100 villes en Extract, Transform reste à 3s grâce aux index."

---

## CHIFFRES CLÉS À RETENIR

- **2 étapes** ETL (Extract + Transform)
- **4 services** Python modulaires
- **5 niveaux** de validation qualité
- **3 workflows** GitHub Actions automatisés
- **11 878 mesures** en production
- **371 mesures/jour** (moyenne 7j)
- **~20 secondes** temps de collecte
- **~3 secondes** temps de transformation
- **40 ms** requêtes (100 mesures)
- **26 doublons** historiques détectés
- **2 stations AQI** optimisées (Lyon Centre, Roubaix)
- **37 MB** stockage total
- **737 KB/jour** croissance
- **Validation** : table anomalies v2.3
