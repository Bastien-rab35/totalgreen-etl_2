# Documentation - TotalGreen ETL

Index de la documentation technique du projet.

## Fichiers disponibles

- `docs/ARCHITECTURE.md`
	- Vue systeme, composants ETL et modele de donnees.
	- Positionnement entre schema historique (`dim_time`) et cible (`dim_date`).
- `docs/SECURITE.md`
	- Conformite RGPD, gestion des secrets, recommandations d'exploitation.
- `docs/SCALEWAY_SERVERLESS.md`
	- Build, push, provisioning et exploitation des jobs serverless Scaleway.

## Documentation connexe

- `README.md` (racine): quick start et execution locale.
- `scripts/README.md`: detail des scripts Python d'exploitation.
- `sql/README.md`: ordre d'execution et description des scripts SQL.
- `CHANGELOG.md`: historique des evolutions.

## Point d'entree recommande

1. Lire `README.md` pour la mise en route.
2. Executer les scripts SQL (`sql/star_schema.sql`, `sql/create_dim_date.sql`, `sql/anomalies_table.sql`).
3. Lancer le cycle ETL local (`extract`, `transform`, `validate`).
4. Passer a `docs/SCALEWAY_SERVERLESS.md` pour la production.

## Date de mise a jour

- `17 avril 2026`
