# Guide de Déploiement Automatique - TotalGreen

## 🎯 Solutions GRATUITES pour automatiser le projet

### ✅ Solution 1 : GitHub Actions (RECOMMANDÉ)

**Avantages :**
- 100% gratuit (2000 minutes/mois)
- Aucun serveur à gérer
- Logs intégrés
- Exécution fiable

**Configuration :**

1. **Créer un dépôt GitHub**
   ```bash
   cd "/Users/bastienrabane/Documents/Data/MSPR 1"
   git init
   git add .
   git commit -m "Initial commit - TotalGreen ETL"
   git branch -M main
   git remote add origin https://github.com/VOTRE_USERNAME/totalgreen.git
   git push -u origin main
   ```

2. **Ajouter les secrets GitHub**
   - Aller sur : `https://github.com/VOTRE_USERNAME/totalgreen/settings/secrets/actions`
   - Cliquer sur "New repository secret"
   - Ajouter :
     * `OPENWEATHER_API_KEY` : 609ad105ddbd235791b96988f7bd8f07
     * `AQICN_API_KEY` : 210c46f5e48b5bddecd7e53273d7fb2b9cd8415c
     * `SUPABASE_URL` : https://uqntmecpgswkdchcfwxe.supabase.co
     * `SUPABASE_KEY` : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

3. **Activer le workflow**
   - Le fichier `.github/workflows/etl-pipeline.yml` est déjà créé
   - Push vers GitHub
   - Aller dans l'onglet "Actions"
   - Le pipeline s'exécutera automatiquement toutes les heures

**Modifications du cron :**
```yaml
# Toutes les heures 24/7
- cron: '0 * * * *'

# Toutes les 2 heures
- cron: '0 */2 * * *'

# Seulement entre 8h et 20h
- cron: '0 8-20 * * *'
```

**Coût :** 0€ (2000 min/mois = ~33h d'exécution)

---

### 🔄 Solution 2 : Render.com (Alternative)

**Avantages :**
- Gratuit avec cron jobs
- Facile à configurer
- Bon pour les petits projets

**Configuration :**

1. Créer compte sur https://render.com
2. Créer un "Cron Job"
3. Connecter votre dépôt GitHub
4. Configurer :
   - Command: `cd src && python etl_pipeline.py`
   - Schedule: `0 * * * *` (toutes les heures)
5. Ajouter les variables d'environnement

**Limitations :**
- Service gratuit s'endort après 15 min d'inactivité
- Redémarre au cron suivant

**Coût :** 0€

---

### ☁️ Solution 3 : PythonAnywhere

**Avantages :**
- Interface web simple
- Scheduled tasks gratuits

**Configuration :**

1. Créer compte sur https://www.pythonanywhere.com
2. Upload du code via Files
3. Scheduled Tasks → Add a new one
4. Command: `/home/USERNAME/totalgreen/src/etl_pipeline.py`

**Limitations :**
- 1 tâche planifiée par jour (offre gratuite)
- Pas idéal pour du horaire

**Coût :** 0€ (ou 5$/mois pour scheduled tasks illimités)

---

### 🚀 Solution 4 : Google Cloud Platform (Free Tier)

**Avantages :**
- Cloud Functions + Cloud Scheduler
- Free tier généreux
- Scalable

**Configuration :**

1. Créer projet GCP
2. Activer Cloud Functions et Cloud Scheduler
3. Déployer fonction :
   ```bash
   gcloud functions deploy etl-pipeline \
     --runtime python312 \
     --trigger-http \
     --entry-point run_etl
   ```
4. Créer Cloud Scheduler :
   ```bash
   gcloud scheduler jobs create http etl-job \
     --schedule="0 * * * *" \
     --uri="https://REGION-PROJECT_ID.cloudfunctions.net/etl-pipeline"
   ```

**Coût :** 0€ (dans les limites du free tier)

---

## 📊 Comparaison des solutions

| Solution | Coût | Fréquence max | Difficulté | Fiabilité |
|----------|------|---------------|------------|-----------|
| **GitHub Actions** | 0€ | Toutes les 5 min | ⭐ Facile | ⭐⭐⭐⭐⭐ |
| Render.com | 0€ | Toutes les heures | ⭐⭐ Moyenne | ⭐⭐⭐⭐ |
| PythonAnywhere | 0€ | 1×/jour | ⭐ Facile | ⭐⭐⭐ |
| GCP Free Tier | 0€ | Temps réel | ⭐⭐⭐ Complexe | ⭐⭐⭐⭐⭐ |

---

## 🎯 Recommandation

**Pour votre projet :** **GitHub Actions**

**Pourquoi :**
- ✅ 100% gratuit
- ✅ Toutes les heures possible
- ✅ Aucune configuration serveur
- ✅ Logs intégrés GitHub
- ✅ Secrets sécurisés
- ✅ Exécution dans le cloud
- ✅ Compatible avec votre stack

**Mise en place en 5 minutes :**

```bash
# 1. Initialiser git (si pas déjà fait)
git init
git add .
git commit -m "TotalGreen ETL Pipeline"

# 2. Créer repo GitHub (via web)
# https://github.com/new

# 3. Pusher le code
git remote add origin https://github.com/VOTRE_USERNAME/totalgreen.git
git branch -M main
git push -u origin main

# 4. Ajouter secrets (via GitHub UI)
# Settings → Secrets → Actions → New repository secret

# 5. C'est tout ! Le pipeline s'exécutera automatiquement
```

Le workflow GitHub Actions est déjà configuré dans `.github/workflows/etl-pipeline.yml`
