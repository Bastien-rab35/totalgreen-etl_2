# 🔧 CORRECTION URGENTE - Table Anomalies

## Problème identifié

La table `anomalies` existe dans Supabase avec l'**ancien schéma ML** (supprimé en v2.2), ce qui empêche le script `validate_data_quality.py` de sauvegarder les anomalies.

**Erreur rencontrée** :
```
Could not find the 'category' column of 'anomalies' in the schema cache
```

## Solution

Exécuter le script de migration pour recréer la table avec le bon schéma.

### Étapes dans Supabase SQL Editor

1. **Ouvrir Supabase** → SQL Editor
2. **Copier-coller** le contenu de `sql/migrate_anomalies_table.sql`
3. **Exécuter** le script (RUN)
4. **Vérifier** le résultat :
   ```sql
   SELECT COUNT(*) FROM anomalies;
   -- Devrait retourner 1 (ligne de test de migration)
   ```

### Alternative : Ligne de commande

Si vous avez `psql` installé :

```bash
# Depuis le dossier racine du projet
psql "$SUPABASE_DB_URL" -f sql/migrate_anomalies_table.sql
```

## Test après migration

Exécuter le script de test :

```bash
python scripts/test_anomalies_table.py
```

**Résultat attendu** :
```
✓ Table 'anomalies' existe et accessible
✓ Insertion réussie
✓ Anomalie de test supprimée
✓ Tous les tests ont réussi
```

## Nouvelle structure de la table

```sql
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    validation_run_id UUID NOT NULL,
    severity VARCHAR(20) NOT NULL,        -- critical, warning, info
    category VARCHAR(100) NOT NULL,       -- data_missing, duplicates, etc.
    message TEXT NOT NULL,
    details JSONB,
    detected_at TIMESTAMPTZ NOT NULL,
    validation_period_hours INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Après la migration

Une fois la migration effectuée, le script `validate_data_quality.py` sauvegardera automatiquement toutes les anomalies détectées dans la table.

**Vérification des anomalies** :

```sql
-- Dernières anomalies
SELECT * FROM anomalies ORDER BY detected_at DESC LIMIT 10;

-- Statistiques par jour
SELECT * FROM anomalies_daily_stats;
```
