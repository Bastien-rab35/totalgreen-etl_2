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
4 Services Python
├─ weather_service.py
├─ air_quality_service.py
├─ data_lake_service.py
└─ database_service.py
```

**Robustesse**
- Try/catch multi-niveaux
- Logging complet
- Retry automatique
- Traçabilité 100%

---

### COLONNE CENTRALE
## Qualité des Données

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

**Validation 5 Niveaux**

1️⃣ **Intégrité Structurelle**
   - Doublons
   - Valeurs NULL
   - Clés étrangères

2️⃣ **Cohérence Temporelle**
   - Dates futures
   - Gaps temporels
   - Timestamps

3️⃣ **Limites Physiques**
   - Temp: -50°C à 60°C
   - AQI: 0 à 500
   - Pression: 870-1084 hPa

4️⃣ **Couverture**
   - 10 villes présentes
   - Volume par ville

5️⃣ **Outliers Statistiques**
   - Z-score > 3σ
   - Par champ

---

**Nettoyage Auto**
Script : `cleanup_data_quality_issues.py`
- **26 doublons** historiques détectés
- Batch 50 items
- Dry-run mode

**Stations AQI Optimisées**
- Lyon : Station Lyon Centre (idx 3028)
- Lille : Station Roubaix (métropole)
- Données fiables et précises

---

### COLONNE DROITE
## Stack & Performances

**Technologies**

| Composant | Tech | Version |
|-----------|------|---------|
| Langage | Python | 3.12 |
| BDD | PostgreSQL (EU) | 15 |
| Calcul | numpy | 1.26+ |
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
11 878 mesures collectées
371 mesures/jour
10 villes × 24h

⚡ PERFORMANCES
Collecte    : 20s (10 villes)
Transform   : 3s (100 entrées)
Requêtes   : 40ms (100 mesures)
Stockage    : 737 KB/jour
Total       : 37 MB (DL + DW)

✅ QUALITÉ
Validation 5 niveaux
26 doublons détectés
Cleanup disponible
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
**Pipeline opérationnel | 11 878 mesures | Validation 5 niveaux | 371 mesures/jour**

---

## SCRIPT ORAL (3-4 min)

### [30s] Introduction
"Le développement repose sur 3 piliers : pipeline ETL robuste, architecture modulaire, et système de qualité ML."

### [1 min] Pipeline ETL
"Pipeline en 2 étapes : Extract collecte 10 villes toutes les heures via 2 APIs en 20 secondes. Transform normalise et insère dans le Star Schema en 3 secondes. Architecture modulaire avec 5 services Python et gestion d'erreurs complète."

### [1.5 min] Qualité & Validation
"Validation automatisée 5 niveaux exécutée 2×/jour : intégrité structurelle, cohérence temporelle, limites physiques, couverture, et détection outliers statistiques. 26 doublons historiques identifiés avec script cleanup disponible. Validation enregistrée en BDD pour traçabilité complète. Exit codes pour intégration CI/CD."

### [1 min] Stack & Performances
"Stack moderne : Python 3.12, PostgreSQL 15, numpy. 3 workflows GitHub Actions orchestrés. En production : 11 878 mesures, 371/jour, validation 5 niveaux active, disponibilité 100%. Performances optimales : 40ms requêtes, 737 KB/jour stockage, index GIN et B-Tree."

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
- **5** niveaux validation
- **11 878** mesures
- **371** mesures/jour
- **20s** collecte
- **3s** transform
- **40ms** requêtes
- **37 MB** stockage total
- **737 KB/jour** croissance
- **100%** disponibilité

---

## COULEURS SUGGÉRÉES

- **Pipeline ETL** : Orange (#FFF3E0)
- **Qualité/ML** : Vert clair (#E8F5E9)
- **Stack/Perfs** : Bleu clair (#E3F2FD)
- **Chiffres clés** : Rouge/Orange vif
- **Succès (✓)** : Vert foncé
