# Guide GitHub Actions - TotalGreen

## 🚀 Configuration en 5 minutes

### Étape 1 : Préparer le dépôt Git

```bash
cd "/Users/bastienrabane/Documents/Data/MSPR 1"

# Initialiser Git (si pas déjà fait)
git init

# Ajouter tous les fichiers
git add .

# Créer le premier commit
git commit -m "Initial commit - TotalGreen ETL Pipeline"

# Définir la branche principale
git branch -M main
```

### Étape 2 : Créer le dépôt sur GitHub

1. Aller sur https://github.com
2. Cliquer sur le **+** en haut à droite → **New repository**
3. Remplir :
   - Repository name: `totalgreen-etl`
   - Description: `Pipeline ETL automatique pour collecte de données environnementales`
   - Visibilité: **Private** (recommandé pour les clés API)
4. **NE PAS** cocher "Initialize with README"
5. Cliquer sur **Create repository**

### Étape 3 : Connecter et pusher

```bash
# Remplacer VOTRE_USERNAME par votre nom d'utilisateur GitHub
git remote add origin https://github.com/VOTRE_USERNAME/totalgreen-etl.git

# Pousser le code
git push -u origin main
```

**⚠️ Si demande de credentials :**
- Username: votre nom GitHub
- Password: utiliser un **Personal Access Token** (pas votre mot de passe)
  - Aller sur : https://github.com/settings/tokens
  - Generate new token (classic)
  - Cocher : `repo` (full control)
  - Copier le token généré

### Étape 4 : Configurer les Secrets GitHub

1. Sur GitHub, aller dans votre dépôt
2. Cliquer sur **Settings** (⚙️)
3. Dans le menu gauche : **Secrets and variables** → **Actions**
4. Cliquer sur **New repository secret**
5. Ajouter ces 4 secrets un par un :

| Name | Value |
|------|-------|
| `OPENWEATHER_API_KEY` | `609ad105ddbd235791b96988f7bd8f07` |
| `AQICN_API_KEY` | `210c46f5e48b5bddecd7e53273d7fb2b9cd8415c` |
| `SUPABASE_URL` | `https://uqntmecpgswkdchcfwxe.supabase.co` |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxbnRtZWNwZ3N3a2RjaGNmd3hlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg5MDYzMzQsImV4cCI6MjA4NDQ4MjMzNH0.B3oic2-DHih3Sou79qJgkC1eEek3kyDwD6fPlpFmdQc` |

**Pour chaque secret :**
- Cliquer sur **New repository secret**
- Name: copier le nom exact (ex: `OPENWEATHER_API_KEY`)
- Secret: coller la valeur
- Cliquer sur **Add secret**

### Étape 5 : Vérifier le Workflow

1. Dans votre dépôt GitHub, cliquer sur l'onglet **Actions**
2. Vous devriez voir : "Pipeline ETL Automatique"
3. Le workflow s'exécutera automatiquement :
   - **Toutes les heures** entre 6h et 23h UTC
   - **Manuellement** via le bouton "Run workflow"

### Étape 6 : Tester l'exécution manuelle

1. Aller dans **Actions**
2. Cliquer sur **Pipeline ETL Automatique** (à gauche)
3. Cliquer sur **Run workflow** (bouton à droite)
4. Sélectionner la branche `main`
5. Cliquer sur **Run workflow**
6. Attendre ~30 secondes, rafraîchir la page
7. Cliquer sur le workflow en cours
8. Voir les logs en temps réel

---

## 📋 Commandes de maintenance

### Modifier le planning (cron)

Éditer `.github/workflows/etl-pipeline.yml` :

```yaml
schedule:
  # Toutes les heures 24/7
  - cron: '0 * * * *'
  
  # Toutes les 2 heures
  - cron: '0 */2 * * *'
  
  # Seulement entre 8h et 20h UTC
  - cron: '0 8-20 * * *'
  
  # Toutes les 30 minutes
  - cron: '*/30 * * * *'
```

Puis :
```bash
git add .github/workflows/etl-pipeline.yml
git commit -m "Update schedule"
git push
```

### Voir les logs

1. GitHub → Actions → Cliquer sur un workflow
2. Cliquer sur "run-etl" → "Run ETL Pipeline"
3. Voir les logs complets

### Télécharger les logs archivés

1. Actions → Workflow terminé
2. Scroll en bas → "Artifacts"
3. Télécharger `etl-logs-XXX`

---

## 🔍 Debugging

### Le workflow ne démarre pas ?

✅ Vérifier :
1. Secrets bien configurés (Settings → Secrets)
2. Workflow activé (Actions → workflow → bouton "Enable")
3. Fichier `.github/workflows/etl-pipeline.yml` présent

### Erreur "Invalid API key" ?

✅ Vérifier :
1. Secrets correctement nommés (respecter majuscules)
2. Pas d'espaces dans les valeurs
3. Copier-coller complet des clés

### Tester localement avant de pusher

```bash
cd src
python etl_pipeline.py
```

Si ça marche localement, ça marchera sur GitHub Actions !

---

## 📊 Monitoring

### Voir l'état actuel

```bash
# Installer GitHub CLI (optionnel)
brew install gh

# Se connecter
gh auth login

# Voir les workflows
gh workflow list

# Voir les runs récents
gh run list --limit 10

# Voir les logs du dernier run
gh run view --log
```

### Notifications par email

GitHub envoie automatiquement un email si un workflow échoue.

Configurer : Settings → Notifications → Actions

---

## 💡 Astuces

### Désactiver temporairement

Actions → Pipeline ETL Automatique → **⋮** → Disable workflow

### Exécution unique sans attendre le cron

Actions → Run workflow (bouton vert)

### Voir la consommation

Settings → Billing → Actions minutes used

Plan gratuit : 2000 minutes/mois (votre projet utilise ~10 min/mois)

---

## ✅ Checklist finale

- [ ] Dépôt GitHub créé
- [ ] Code pushé
- [ ] 4 secrets configurés
- [ ] Workflow visible dans Actions
- [ ] Test manuel réussi
- [ ] Premier run automatique ok

🎉 **C'est tout ! Votre pipeline tourne automatiquement dans le cloud !**
