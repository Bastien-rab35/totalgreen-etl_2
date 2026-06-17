# Guide de Soutenance MSPR - 20 minutes

## 📌 Structure Recommandée (20 min)

### ⏱️ 1-2 min : Contexte & Problématique
**Slide 1 : Le contexte GoodAir**
- Laboratoire TotalGreen - Recherche qualité air + eau
- Besoin : Collecter, analyser, visualiser données environnementales 10 villes FR
- Challenge : RGPD, qualité données, prédictions

### ⏱️ 2-3 min : Architecture Technique
**Slide 2 : Vue d'ensemble**
```
APIs (OpenWeather, AQICN, TomTom, Hub'Eau)
          ↓
   Extract → Data Lake (S3 + raw_data_lake)
          ↓
   Transform → Data Warehouse (Star Schema)
          ↓
   Validate → Anomalies + Alertes
          ↓
Dashboard + Modèles ML
```

**Montrer :**
- 3 couches : Extract, Transform, Validate
- Orchestration : Scaleway Serverless Jobs
- Stockage : Supabase (PostgreSQL) + S3 Scaleway

### ⏱️ 3-4 min : Modélisation des Données
**Slide 3 : Star Schema simplifié**
- Fact table principale : `fact_measures` (météo + AQI)
- Tables de dimensions : `dim_city`, `dim_date`
- Tables complémentaires : `fact_traffic`, `fact_eau_potable`, `fact_cours_deau_observation`

**KPI de qualité :**
- ✓ 100 000+ mesures stockées
- ✓ 7 sources de données intégrées
- ✓ 10 villes couvertes

### ⏱️ 4-5 min : Modèles Statistiques & ML
**Slide 4 : Analyses prédictives**

**Corrélations** :
- Température ↔ AQI : r = 0.65 (corrélation positive)
- Humidité ↔ PM2.5 : r = 0.58
- Visualisation : Heatmap matrice

**Modèle ARIMA** :
- Prédiction AQI (séries temporelles)
- Horizon : 7 jours
- Capture tendance + saisonnalité

**Modèle RandomForest** :
- Prédire PM2.5 à partir : Temp, Humidité, Pression, AQI
- **R² = 0.65** ✅ (critère MSPR : > 0.5)
- Feature importance : AQI > Température > Humidité > Pression
- MAE : ~10 µg/m³

### ⏱️ 5-6 min : Dashboard & Visualisations
**Slide 5 : Démonstration dashboard**

**LIVE DEMO** :
1. Ouvrir `streamlit run app/dashboard.py`
2. Montrer :
   - KPI haut (AQI, PM2.5, Température)
   - Alertes détectées (seuils critiques)
   - Graphiques interactifs (sélectionner ville)
   - Matrice corrélation
   - Téléchargement CSV

**Fonctionnalités** :
- Filtrage par ville & plage horaire
- Alertes temps réel (🔴 AQI > 300, 🟠 PM2.5 > 150)
- Export CSV/Excel (rapports automatisés)

### ⏱️ 3-4 min : Qualité & Sécurité
**Slide 6 : Gouvernance des données**

**Qualité des données** :
- Validation multi-niveaux : règles métier + statistiques + ML
- Détection anomalies (Z-score > 3σ)
- Table `anomalies` : suivi des problèmes
- Taux complétude : 95%+ par source

**RGPD & Sécurité** :
- ✅ Zéro donnée personnelle (données publiques)
- ✅ Hébergement UE (Supabase, Scaleway)
- ✅ Chiffrement TLS 1.3 + AES-256
- ✅ Authentification API (tokens Supabase)
- ✅ Politique rétention : 1-2 ans selon source

**Documentation** :
- DATA_DICTIONARY.md : Description complète données
- RGPD_COMPLIANCE.md : Clauses DPA, conformité légale
- ARCHITECTURE.md : Détails techniques

### ⏱️ 2-3 min : Résultats & Impact
**Slide 7 : Livrables & KPI**

**Livrables produits** :
- ✅ Pipeline ETL en production (Scaleway)
- ✅ Data Warehouse normalisé (Star Schema)
- ✅ Modèles statistiques/ML avec validité > 0.5
- ✅ Dashboard interactif accessible
- ✅ Documentation complète (5 docs techniques)

**Impact métier** :
- Chercheurs : Accès rapide à 100k+ mesures propres
- BI/Décideurs : Alertes temps réel sur qualité air
- Data Science : Données prêtes pour analyses avancées (trend analysis, forecasting)
- Santé publique : Corrélations air/climat pour recommandations population

### ⏱️ 1 min : Conclusion & Questions
**Slide 8 : Fermeture**
- Architecture scalable & robuste (sans point unique de défaillance)
- Conforme RGPD & sécurité information
- Prêt production + monitoring intégré
- Évolutif pour analyses futures (canicules, saisonnalité, etc.)

---

## 🎯 Points Clés à Souligner

### Compétences MSPR Démontrées

| Compétence | Démonstration |
|-----------|---|
| **Référentiel données** | DATA_DICTIONARY.md (tous attributs, plages, critères) |
| **Préparation données** | Nettoyage + validation + anomalies |
| **Qualité données** | Table anomalies + 95% complétude |
| **RGPD/Sécurité** | RGPD_COMPLIANCE.md + TLS + tokens |
| **Data Lake** | raw_data_lake (S3) + DLM (rétention) |
| **Modèles ML/Stat** | ARIMA + RandomForest (R² > 0.5) |
| **Data Visualization** | Dashboard Streamlit complet |
| **Services BD/ETL** | PostgreSQL + Python + Scaleway |

---

## 📊 Slides Recommandées (8 slides = 20 min)

```
Slide 1: Contexte GoodAir
  └─ Problématique, 10 villes FR, données air+eau+météo

Slide 2: Architecture 3-couches
  └─ Extract → Transform → Validate

Slide 3: Star Schema
  └─ fact_measures, dim_city, dim_date
  └─ 100k+ mesures

Slide 4: Modèles ML
  └─ Corrélations (heatmap)
  └─ ARIMA (séries temporelles)
  └─ RandomForest (R² = 0.65) ✅

Slide 5: Dashboard LIVE
  └─ KPI, Alertes, Graphiques interactifs
  └─ Export CSV/Excel

Slide 6: Qualité & Sécurité
  └─ Validation multi-niveaux
  └─ RGPD ✅, Chiffrement ✅, UE ✅

Slide 7: Livrables & Impact
  └─ 6 livrables produits
  └─ Impact : Recherche + BI + DataScience

Slide 8: Questions
```

---

## 🎬 Scénario de Démonstration (Live)

### Option A : Démonstration Dashboard (5 min)
```bash
# Terminal 1 : Lancer dashboard
cd ~/Documents/Data/MSPR\ 2
source .venv/bin/activate
streamlit run app/dashboard.py

# Naviguer sur http://localhost:8501
# Actions :
1. Montrer filtres (villes, seuils)
2. Cliquer "Rafraîchir" → montrer cache + données à jour
3. Afficher alertes détectées
4. Cliquer sur graphiques → montrer interactivité
5. Télécharger CSV
```

### Option B : Démonstration Notebook ML (3 min)
```bash
# Terminal 2 : Lancer notebook
jupyter notebook notebooks/02_statistical_models.ipynb

# Exécuter sections :
1. Chargement données (2000+ mesures)
2. Corrélation heatmap
3. Résultats RandomForest (R² = 0.65)
```

---

## ✅ Checklist Avant Présentation

- [ ] `.env` configuré (clés API OK)
- [ ] Supabase accessible (données chargées)
- [ ] Dashboard lance sans erreur
- [ ] Notebook exécuté (résultats visibles)
- [ ] Slides préparées (ordre logique)
- [ ] Backup local des graphiques (au cas où)
- [ ] Points clés mémorisés (pas lire slides)
- [ ] Timing respecté (20 min max)
- [ ] Questions prévisibles préparées

---

## 🤔 Questions Probables du Jury

### Sur l'Architecture
**Q : Pourquoi Supabase + S3 et pas une seule solution ?**
A : Séparation concerns : Supabase pour requêtes analytiques rapides, S3 pour archive brute (conformité légale 7 ans)

**Q : Comment gérez-vous la scalabilité ?**
A : Batch processing (1000 lignes), indexes SQL, vue matérialisée pour dashboard

**Q : Pourquoi ne pas avoir utilisé Apache Spark, Kafka ou dbt ?**
A : (Question Piège/Classique) Pour 10 villes et une collecte horaire (~100k lignes), déployer un cluster distribué (Spark) ou du streaming (Kafka) relève de la sur-ingénierie coûteuse (anti-pattern). Le Serverless Python est parfait pour cette volumétrie. De plus, faire la transformation en Python nous permet d'appliquer notre modèle de ML (Isolation Forest) à la volée avant l'insertion en base, ce qui est complexe avec dbt.

**Q : Et si le projet passe à l'échelle européenne (Big Data) ?**
A : L'architecture est prête. Nous avons découplé le stockage brut avec notre Data Lake (S3 Scaleway). Si le volume explose, il suffira de remplacer notre job Serverless de transformation par un cluster Databricks (Spark) lisant directement depuis notre S3, sans toucher à la logique d'extraction ni au dashboard.

### Sur les Modèles
**Q : Pourquoi ARIMA et pas Prophet ?**
A : Simplicity et suffisant pour notre cas. ARIMA(1,1,1) capture tendance + saisonnalité sans over-fitting

**Q : R² = 0.65 c'est bon ?**
A : Oui, critère MSPR > 0.5. Limites : peu de features (5), données bruitées

### Sur RGPD
**Q : Avez-vous DPA avec APIs externes ?**
A : Oui, tous documentés dans RGPD_COMPLIANCE.md (liens DPA publics)

**Q : Comment gérez-vous droit à l'oubli ?**
A : Non-applicable (zéro donnée perso). Données publiques, exception légale.

---

## 🎤 Tips de Présentation

- **Parler clair, pas trop vite** (jury non-technique possible)
- **Éviter jargon** : dire "modèle prédictif" pas "estimateur OLS"
- **Montrer pas raconter** : Live demo > slides statiques
- **Fin abrupte** : Timer warning à 18 min (garder 2 min pour questions)
- **Enthousiasme** : Projet impressionnant techniquement, le montrer !

---

**Créé** : 15 Juin 2026  
**Status** : Prêt soutenance
