# SLIDE DÉVELOPPEMENT - Version PowerPoint Condensée

---

## [TITRE SLIDE]
# DÉVELOPPEMENT & IMPLÉMENTATION

---

## [3 COLONNES - DISPOSITION]

### COLONNE GAUCHE
## Pipeline ETL Python

**2 Étapes Automatisées**

**EXTRACT** (toutes les heures)
- 10 villes collectées
- 2 APIs parallélisées
- Stockage JSONB Data Lake
- Durée : ~20 secondes

⬇

**TRANSFORM** (+15 min)
- Normalisation données
- Enrichissement dimensions
- Insertion Star Schema
- Durée : ~3 secondes

---

**Architecture Modulaire**
```
5 Services Python
├─ weather_service.py
├─ air_quality_service.py
├─ data_lake_service.py
├─ database_service.py
└─ anomaly_detection_service.py
```

**Robustesse**
- Try/catch multi-niveaux
- Logging complet
- Retry automatique
- Traçabilité 100%

---

### COLONNE CENTRALE
## Qualité & Machine Learning

**Validation Automatisée**
Script : `validate_data_quality.py`

| Contrôle | Résultat |
|----------|----------|
| Doublons | **0** ✓ |
| Dates futures | **0** ✓ |
| Limites physiques | **100%** ✓ |
| Complétude | **✓** |
| Outliers | Actif |

Fréquence : **2× par jour**

---

**ML - Isolation Forest**

**3 Niveaux de Détection**

1️⃣ **Règles Métier**
   - Température : -50°C à 60°C
   - AQI : 0 à 500
   - Pression : 870-1084 hPa

2️⃣ **Statistiques**
   - Z-score : 2σ, 2.5σ, 3σ, 4σ
   - Comparaison historique

3️⃣ **ML Multivariée**
   - 6 métriques (temp, humidity, pressure, aqi, pm25, pm10)
   - Entraînement : **5000 mesures**
   - Prédiction : **<100ms**

**Classification**
- NORMAL → Insertion
- FLAGGED → Insertion avec flag
- REJET → Suppression

---

**Nettoyage Auto**
Script : `cleanup_data_quality_issues.py`
- **125 doublons** supprimés
- Batch 50 items
- Dry-run mode

---

### COLONNE DROITE
## Stack & Performances

**Technologies**

| Composant | Tech | Version |
|-----------|------|---------|
| Langage | Python | 3.12 |
| BDD | PostgreSQL | 15 |
| ML | scikit-learn | 1.5.2 |
| Hébergement | Supabase | UE |
| CI/CD | GitHub Actions | - |

---

**Orchestration**

| Workflow | CRON | Durée |
|----------|------|-------|
| Extract | Hourly :00 | 20s |
| Transform | Hourly :15 | 3s |
| Validation | 2×/day | 30s |

---

**Métriques Production**

```
📊 DONNÉES
11 453 mesures collectées
339 mesures/jour
10 villes × 24h

⚡ PERFORMANCES
Collecte    : 20s (10 villes)
Transform   : 3s (100 entrées)
ML Training : 2-3s
ML Predict  : <100ms
Stockage    : 500 Ko/jour

✅ QUALITÉ
0 doublons
0 erreurs critiques
100% disponibilité
```

---

**Optimisations**

Index créés :
- GIN sur JSONB
- B-Tree sur FK
- Composite (time_id, city_id)

---

## [FOOTER]
**Pipeline opérationnel | 11 453 mesures | 0 doublons | ML temps réel**

---

## SCRIPT ORAL (3-4 min)

### [30s] Introduction
"Le développement repose sur 3 piliers : pipeline ETL robuste, architecture modulaire, et système de qualité ML."

### [1 min] Pipeline ETL
"Pipeline en 2 étapes : Extract collecte 10 villes toutes les heures via 2 APIs en 20 secondes. Transform normalise et insère dans le Star Schema en 3 secondes. Architecture modulaire avec 5 services Python et gestion d'erreurs complète."

### [1.5 min] Qualité & ML
"Validation automatisée 2×/jour : 0 doublons, 100% conforme. Machine Learning avec Isolation Forest : 3 approches combinées - règles métier, statistiques Z-score, et ML multivariée sur 6 métriques. Classification NORMAL/FLAGGED/REJET. Entraînement sur 5000 mesures, prédiction en moins de 100ms. Script de nettoyage a supprimé 125 doublons."

### [1 min] Stack & Performances
"Stack moderne : Python 3.12, PostgreSQL 15, scikit-learn. 4 workflows GitHub Actions orchestrés. En production : 11 453 mesures, 339/jour, 0 erreur critique, disponibilité 100%. Performances optimales avec index GIN et B-Tree."

### [30s] Conclusion
"Pipeline automatisé, qualité garantie par ML, performances optimales en production."

---

## VISUELS À INCLURE

**Diagramme Pipeline** (COLONNE 1)
```
APIs → [Extract 20s] → Lake → [Transform 3s] → Star Schema
                         ↓              ↓
                    Logging        ML Detection
```

**Diagramme ML** (COLONNE 2)
```
Input → [Business Rules] + [Z-score] + [Isolation Forest]
              ↓
    Classification (NORMAL/FLAG/REJECT)
```

**Tableau Métriques** (COLONNE 3)
Déjà présent ci-dessus ✓

---

## CHIFFRES CLÉS SUR LA SLIDE

**À METTRE EN ÉVIDENCE (gros caractères)**

- **2** étapes ETL
- **5** services modulaires
- **3** niveaux ML
- **11 453** mesures
- **339** mesures/jour
- **20s** collecte
- **3s** transform
- **0** doublons
- **100%** disponibilité
- **<100ms** ML predict

---

## COULEURS SUGGÉRÉES

- **Pipeline ETL** : Orange (#FFF3E0)
- **Qualité/ML** : Vert clair (#E8F5E9)
- **Stack/Perfs** : Bleu clair (#E3F2FD)
- **Chiffres clés** : Rouge/Orange vif
- **Succès (✓)** : Vert foncé
