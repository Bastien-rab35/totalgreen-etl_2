# Diagnostic GitHub Actions - Pipeline de Transformation

## 🔍 Problème identifié

Le pipeline de transformation **fonctionne parfaitement en local** mais ne semble pas s'exécuter sur GitHub Actions depuis le 24 janvier 2026.

## ✅ Test local réussi

**Résultats du test manuel (6 février 2026) :**
- Pipeline exécuté avec succès
- 100 entrées transformées (1781 → 1881 mesures)
- Timestamps réels correctement préservés
- 6322 entrées restent en attente de transformation

## 🔎 Actions à vérifier

### 1. GitHub Actions - Vérifications à faire

**Via l'interface GitHub :**
1. Aller sur `Actions` dans le dépôt
2. Vérifier le workflow "2️⃣ Transform vers BDD (1x par jour)"
3. Regarder les dernières exécutions et leurs logs

**Points à vérifier :**
- Le workflow s'est-il déclenché depuis le 24 janvier ?
- Y a-t-il des erreurs dans les logs ?
- Les secrets sont-ils toujours valides ?

### 2. Causes possibles

**a) Workflow désactivé**
- GitHub désactive les workflows inactifs après 60 jours
- Solution : Réactiver manuellement dans l'onglet Actions

**b) Échec d'installation des dépendances**
- Les nouvelles versions de supabase (2.9.1) et websockets (14.0) peuvent causer des problèmes
- Solution : Vérifier les logs d'installation dans GitHub Actions

**c) Problème d'authentification**
- Les secrets SUPABASE_URL ou SUPABASE_KEY ont peut-être expiré
- Solution : Vérifier et mettre à jour les secrets

**d) Quota GitHub Actions dépassé**
- Vérifier les minutes d'exécution disponibles
- Solution : Vérifier l'usage dans Settings > Billing

### 3. Solutions immédiates

**Option 1 : Exécution manuelle**
```bash
# Sur GitHub
1. Aller dans Actions > "2️⃣ Transform vers BDD (1x par jour)"
2. Cliquer sur "Run workflow"
3. Sélectionner la branche "main"
4. Cliquer "Run workflow"
```

**Option 2 : Exécution locale planifiée**
```bash
# Ajouter un cron job local (temporaire)
crontab -e
# Ajouter : 0 23 * * * cd /path/to/project/src && python etl_transform_to_db.py
```

**Option 3 : Transformer toutes les données en attente**
```bash
cd src
# Exécuter plusieurs fois jusqu'à tout traiter
while [ $(python -c "import sys; sys.path.insert(0, '.'); from config import Config; from services.data_lake_service import DataLakeService; dl = DataLakeService(Config.SUPABASE_URL, Config.SUPABASE_KEY); data = dl.get_unprocessed_data(1); print(len(data))") -gt 0 ]; do python etl_transform_to_db.py; done
```

## 📋 Checklist de diagnostic

- [ ] Vérifier que le workflow existe dans `.github/workflows/etl-transform.yml`
- [ ] Vérifier que le workflow n'est pas désactivé
- [ ] Consulter les logs de la dernière exécution réussie (24 janvier)
- [ ] Consulter les logs des exécutions échouées (si présentes)
- [ ] Vérifier la validité des secrets GitHub
- [ ] Tester l'exécution manuelle via l'interface GitHub
- [ ] Vérifier le quota de minutes GitHub Actions

## 🎯 Recommandation

1. **Immédiat** : Exécuter manuellement le workflow sur GitHub
2. **Court terme** : Identifier pourquoi il ne se déclenche plus automatiquement
3. **Long terme** : Ajouter des alertes de monitoring (ex: si aucune transformation depuis 48h)
