# SQL - TotalGreen ETL

Reference des scripts SQL presents dans le depot.

## Scripts disponibles

- `star_schema.sql`
  - Schema analytique principal (dimensions + `fact_measures`).
  - Fonctions utilitaires SQL (ex: mapping niveau AQI).

- `create_dim_date.sql`
  - Cree et peuple `dim_date` (2024-2027).
  - Oriente le modele vers une dimension date simplifiee.

- `anomalies_table.sql`
  - Cree la table `anomalies` et la vue `anomalies_daily_stats`.
  - Utilisee par `scripts/validate_data_quality.py`.

- `migrate_anomalies_table.sql`
  - Migration destructive de l'ancienne table `anomalies` vers le schema actuel.
  - A utiliser uniquement si vous avez un ancien schema incompatible.

- `queries_olap.sql`
  - Collection de requetes analytiques et d'exploration.

- `UPDATE_FUNCTIONS.sql`
  - Script de rappel/mise a jour lie a la transition vers `dim_date`.

## Ordre recommande pour une nouvelle installation

```sql
\i sql/star_schema.sql
\i sql/create_dim_date.sql
\i sql/anomalies_table.sql
```

Ensuite, executer les requetes d'analyse au besoin:

```sql
\i sql/queries_olap.sql
```

## Notes importantes

- Certaines requetes historiques peuvent encore s'appuyer sur `dim_time`.
- L'architecture cible documentee privilegie `dim_date`.
- Verifier les jointures temporelles selon votre etat de schema (historique vs cible).

## Bonnes pratiques

- Sauvegarder la base avant toute migration structurelle.
- Executer les scripts dans l'editeur SQL Supabase avec un compte habilite.
- Verifier les index et comptes de lignes apres deploiement.

Derniere mise a jour: `26 mars 2026`
