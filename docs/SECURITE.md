# Securite et Conformite

Synthese des mesures de securite et des points RGPD pour TotalGreen ETL.

## Perimetre des donnees

Le projet manipule des donnees environnementales:

- meteo (temperature, pression, humidite, vent)
- qualite de l'air (AQI, PM2.5, PM10, NO2, O3, SO2, CO)
- metadonnees geographiques publiques de villes

Aucune donnee personnelle utilisateur n'est collecte dans le flux ETL standard.

## Conformite RGPD

- Hebergement cible: region UE.
- Donnees non personnelles: risque RGPD limite.
- Principe de minimisation: seules les donnees utiles a l'analyse sont conservees.

## Gestion des secrets

Variables sensibles attendues:

```env
OPENWEATHER_API_KEY=...
AQICN_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

Bonnes pratiques appliquees:

- pas de secrets en dur dans le code
- chargement via `.env` en local
- gestion centralisee par Secret Manager en serverless
- validation de presence via `config.validate()`

## Controle d'acces

- Execution locale: acces limite a l'environnement qui porte le `.env`.
- Execution serverless: secrets injectes au runtime, non commites.
- Base de donnees: acces API par cle de service dediee.

## Securite reseau

- Communications API externes via HTTPS.
- Connexion a Supabase via TLS.
- Pas d'exposition directe d'endpoint d'administration dans le depot.

## Journalisation et audit

- Logs applicatifs ETL dans `logs/` en local.
- Logs d'execution serverless disponibles cote plateforme.
- Anomalies qualite historisees en base via table `anomalies`.

## Retention recommandee

Politique recommandee (a adapter au besoin metier):

- `raw_data_lake`: 30 jours
- `fact_measures`: 12 mois ou plus selon besoins analytiques
- `anomalies`: 12 mois
- logs techniques: 30 a 90 jours

## Checklist operationnelle

- [x] Secrets externalises (`.env` local ou Secret Manager)
- [x] Aucune donnee personnelle dans le flux standard
- [x] Communications chiffrees (HTTPS/TLS)
- [x] Validation qualite des donnees automatisee
- [ ] Rotation planifiee des cles API
- [ ] Politique formelle de purge automatisee
- [ ] Revue periodique des droits de service

Derniere mise a jour: `26 mars 2026`
