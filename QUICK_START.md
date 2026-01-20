# 🚀 GUIDE DE DÉMARRAGE RAPIDE
## Projet TotalGreen - Installation et Configuration

---

## ⚡ Installation en 5 minutes

### 1️⃣ Installation de Python et dépendances

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate  # macOS/Linux
# OU
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2️⃣ Configuration des clés API

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos clés (les clés sont déjà dans .env)
# Mais vous devez configurer Supabase
```

**Fichier `.env` actuel** :
```
OPENWEATHER_API_KEY=609ad105ddbd235791b96988f7bd8f07  ✅
AQICN_API_KEY=210c46f5e48b5bddecd7e53273d7fb2b9cd8415c  ✅
SUPABASE_URL=https://votre-projet.supabase.co  ⚠️ À CONFIGURER
SUPABASE_KEY=votre_clé_service  ⚠️ À CONFIGURER
```

### 3️⃣ Configuration Supabase

#### A. Créer un projet Supabase

1. Aller sur [supabase.com](https://supabase.com)
2. Créer un compte (gratuit)
3. Créer un nouveau projet :
   - **Nom** : TotalGreen
   - **Région** : **Europe (Frankfurt)** ou **Europe (Paris)** ⚠️ IMPORTANT RGPD
   - **Mot de passe** : Choisir un mot de passe fort

#### B. Récupérer les clés

1. Dans votre projet Supabase, aller dans **Settings** → **API**
2. Copier :
   - **URL** : `https://xxxxx.supabase.co`
   - **anon/public key** (ou **service_role key** pour plus de permissions)

#### C. Mettre à jour `.env`

```bash
SUPABASE_URL=https://votre-id-projet.supabase.co
SUPABASE_KEY=votre_clé_récupérée
```

#### D. Créer les tables

1. Dans Supabase, aller dans **SQL Editor**
2. Copier-coller le contenu de `sql/schema.sql`
3. Exécuter (bouton Run)
4. Copier-coller le contenu de `sql/insert_cities.sql`
5. Exécuter (bouton Run)

### 4️⃣ Tests de validation

```bash
cd src
python test_connections.py
```

**Résultat attendu** :
```
✓ Configuration: OK
✓ API OpenWeather: OK
  Température à Paris: XX.XX°C
✓ API AQICN: OK
  AQI à Paris: XX
✓ Connexion Supabase: OK
  Nombre de villes: 10
✓ Quota respecté
```

### 5️⃣ Première collecte manuelle

```bash
# Toujours dans src/
python etl_pipeline.py
```

**Résultat attendu** :
```
Pipeline terminé - Succès: 10/10 - Durée: XX.XXs
```

---

## 🔄 Lancement automatique (horaire)

```bash
cd src
python scheduler.py
```

Le scheduler va :
- Exécuter immédiatement une première collecte
- Répéter toutes les 60 minutes
- Logger toutes les exécutions dans `logs/`

**Pour arrêter** : `Ctrl+C`

---

## 📊 Vérifier les données dans Supabase

1. Aller dans **Table Editor** → **measures**
2. Vous devriez voir les données collectées pour les 10 villes
3. Vérifier la vue **v_measures_complete** pour une vue consolidée

---

## 🛠️ Commandes utiles

```bash
# Voir les logs en temps réel
tail -f logs/etl.log

# Voir les dernières exécutions
tail -20 logs/scheduler.log

# Réactiver l'environnement virtuel
source venv/bin/activate
```

---

## ❓ Problèmes fréquents

### Erreur : "Variables d'environnement manquantes"
➜ Vérifiez que `.env` est bien configuré avec toutes les clés

### Erreur : "Connection to Supabase failed"
➜ Vérifiez `SUPABASE_URL` et `SUPABASE_KEY` dans `.env`

### Erreur : "No cities found"
➜ Exécutez `sql/insert_cities.sql` dans Supabase

### Quota API dépassé
➜ Vérifiez vos quotas sur les dashboards OpenWeather/AQICN

---

## 📞 Support

Consultez :
- [README.md](README.md) - Documentation complète
- [docs/AUDIT_PHASE1.md](docs/AUDIT_PHASE1.md) - Audit technique
- [docs/SECURITE_RGPD.md](docs/SECURITE_RGPD.md) - Conformité RGPD

---

**Bon déploiement ! 🚀**
