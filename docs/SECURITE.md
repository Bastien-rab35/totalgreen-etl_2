# Sécurité et Conformité RGPD

Documentation de conformité pour le projet TotalGreen ETL.

---

## 🔐 Conformité RGPD

### Hébergement et Souveraineté des Données

**Région** : Union Européenne  
**Provider** : Supabase (AWS)  
**Zone géographique** : eu-central-1 (Francfort, Allemagne)

✅ **100% conforme RGPD** - Aucune donnée ne quitte l'UE

### Nature des Données

| Type | Classification | Données personnelles |
|------|----------------|---------------------|
| Température, pression, vent | Environnementales | ❌ NON |
| Qualité de l'air (PM2.5, AQI) | Environnementales | ❌ NON |
| Coordonnées GPS villes | Géographiques publiques | ❌ NON |

**Conclusion** : Aucune donnée personnelle collectée (pas de nom, email, IP, tracking utilisateur).

---

## 🔒 Sécurité

### Gestion des Secrets

**Variables d'environnement (.env)** :
```env
OPENWEATHER_API_KEY=***
AQICN_API_KEY=***
SUPABASE_URL=https://***.supabase.co
SUPABASE_KEY=***
```

**Protections** :
- ✅ `.env` exclu de Git (.gitignore)
- ✅ `.env.example` fourni (sans valeurs réelles)
- ✅ Validation au démarrage (config.validate())
- ✅ Aucune clé en dur dans le code

### Authentification

| Service | Méthode | Sécurité |
|---------|---------|----------|
| Supabase | Service Key | 🟢 Haute |
| OpenWeather | API Key | 🟢 Haute |
| AQICN | Token API | 🟢 Haute |

**Recommandation** : Rotation des clés tous les 6 mois.

### Base de Données

**Connexions** :
- ✅ HTTPS/TLS uniquement
- ✅ Service Key (non exposée publiquement)
- ✅ Row Level Security (RLS) disponible

**Politiques RLS** :
```sql
ALTER TABLE raw_data_lake ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_measures ENABLE ROW LEVEL SECURITY;
ALTER TABLE etl_logs ENABLE ROW LEVEL SECURITY;
```

---

## 🛡️ Contrôle d'Accès

### Accès Pipeline ETL

| Composant | Accès | Contrôle |
|-----------|-------|----------|
| GitHub Actions | Automatisé | Secrets GitHub |
| Scripts Python | Serveur/Local | .env requis |
| Base Supabase | Service Key | Authentification |

**Principe** : Aucun accès public au pipeline.

### Accès Données (Lecture)

Pour phase future (dashboard/API) :
- Authentification requise
- Row Level Security activé
- Accès lecture seule par défaut
- Logs d'audit activés

---

## 📊 Conservation des Données

| Table | Durée de rétention | Justification |
|-------|-------------------|---------------|
| `raw_data_lake` | 30 jours | Cache temporaire |
| `fact_measures` | 1 an | Analyses historiques |
| `dim_*` | Permanentes | Tables de référence |
| `etl_logs` | 90 jours | Audit et debug |

**Purge automatique** : Script de maintenance à créer (Phase 4).

---

## ✅ Checklist de Sécurité

- [x] Hébergement UE (RGPD)
- [x] Aucune donnée personnelle
- [x] Secrets dans .env
- [x] .env exclu de Git
- [x] Connexions HTTPS/TLS
- [x] Authentification API forte
- [x] Logs de traçabilité
- [ ] RLS activé (Phase 4)
- [ ] Rotation clés programmée (Phase 4)
- [ ] Purge automatique données (Phase 4)

---

## 📞 Contact Sécurité

**RSSI** : À définir  
**DPO** : À définir

---

**Dernière révision** : 2026-02-09  
**Version** : 1.1
