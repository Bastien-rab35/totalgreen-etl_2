# Conformité RGPD et Sécurité des Données

## 1. Politique de Conformité RGPD

### 1.1 Données Traitées

Le projet GoodAir traite **exclusivement des données non-personnelles** et publiques :

| Type | Exemples | Statut RGPD |
|------|----------|------------|
| **Données environnementales** | Température, humidité, AQI, PM2.5, ozone | ✅ Publiques |
| **Données météorologiques** | Pression, vitesse vent, visibilité | ✅ Publiques |
| **Données institutionnelles** | Qualité eau potable, cours d'eau | ✅ Publiques |
| **Métadonnées géographiques** | Coordonnées villes, stations | ✅ Publiques |
| **Données de trafic** | Débits, congestion, temps trajet | ✅ Non-personnelles |

**❌ Aucune donnée personnelle n'est collectée** (pas de localisation d'utilisateurs, pas de données de santé individuelles, etc.)

### 1.2 Légalité du Traitement

| Base juridique | Application |
|---|---|
| **Obligation légale** (Art. 6(1)(c)) | Conformité avec directives de qualité de l'air (EU 2008/50/CE) |
| **Intérêt public** (Art. 6(1)(e)) | Recherche environnementale pour le bien public |
| **Recherche scientifique** (Art. 89) | Exemption partielle pour données anonymisées |

---

## 2. Principes de Minimisation des Données

### 2.1 Finalité
Chaque donnée collectée répond à une nécessité spécifique :

| Source | Données | Finalité | Rétention |
|--------|---------|----------|-----------|
| **OpenWeather** | T°, humidité, pression | Corrélations avec AQI | 1 an (archives) + 30j (actif) |
| **AQICN** | AQI, PM2.5, PM10, polluants | Alertes qualité air + prédictions | 1 an (archives) + 7j (actif) |
| **TomTom** | Débits trafic, incidents | Analyse impact trafic sur qualité air | 90 jours |
| **Hub'Eau** | Qualité eau potable/rivières | Corrélations avec autres variables | 2 ans (archives) |

### 2.2 Minimisation Techniques
- ✅ Agrégation par jour/heure (pas de granularité <15min sauf trafic)
- ✅ Suppression automatique de données anciennes (scripts `cleanup_data_lake.py`)
- ✅ Conservation uniquement des variables essentielles pour analyses

---

## 3. Droits des Personnes (le cas échéant)

Bien qu'**aucune donnée personnelle** ne soit traitée, les droits RGPD suivants sont respectés :

### 3.1 Droit d'Accès (Art. 15)
- **Qui** : Citoyens, chercheurs
- **Comment** : Dashboard public GoodAir (données agrégées)
- **Délai** : Immédiat (données en temps réel)

### 3.2 Droit à la Rectification (Art. 16)
- **Données affectées** : Métadonnées géographiques (coordonnées villes)
- **Processus** : Ticket technique → correction dans `dim_city`
- **Délai** : 10 jours ouvrables

### 3.3 Droit à l'Oubli (Art. 17)
- **Non applicable** : Données de sources publiques (API OpenWeather, AQICN, Hub'Eau)
- **Exception** : Données internes (logs applicatifs) supprimées après 90 jours

### 3.4 Droit à la Limitation du Traitement (Art. 18)
- Possible pour utilisateurs disputant l'exactitude des données
- Marquage `data_disputed = true` en base → exclusion des analyses jusqu'à vérification

### 3.5 Portabilité (Art. 20)
- ✅ Export CSV/JSON des données via dashboard
- ✅ Format standard, non-propriétaire

---

## 4. Clauses Contractuelles avec Fournisseurs (DPA)

### 4.1 Data Processing Agreements (DPA)

| Fournisseur | Type | Statut DPA | Notes |
|---|---|---|---|
| **OpenWeather** | Sous-traitant (processeur) | ✅ Standard DPA | [openweathermap.org/terms](https://openweathermap.org/terms) |
| **AQICN** | Sous-traitant | ✅ Standard DPA | [aqicn.org/terms](https://aqicn.org/terms) |
| **TomTom** | Sous-traitant | ✅ Enterprise DPA | Clause 28 RGPD incluse |
| **Hub'Eau (Eaufrance)** | Autorité publique (exception) | N/A | Données publiques en accès libre |
| **Supabase** | Sous-traitant (infrastructure) | ✅ DPA signé | Hébergement EU, chiffrement |
| **Scaleway** | Sous-traitant (cloud) | ✅ DPA signé | Serveurs physiquement en France (Fr-par-1) |

### 4.2 Garanties Contractuelles

Tous les DPA incluent :
1. **Confidentialité** : Interdiction divulgation données
2. **Sécurité** : Mesures techniques minimales (chiffrement, authentification)
3. **Durée** : Selon cycle de vie données
4. **Sous-traitants** : Approbation explicite requis avant changement
5. **Droit d'audit** : Droit à contrôle conformité

### 4.3 Propriété Intellectuelle (PI) et Licences d'Utilisation

Le respect de la propriété intellectuelle est fondamental dans la collecte des données pour le laboratoire GoodAir. Toutes les données sont exploitées en conformité avec les licences des fournisseurs :

| Fournisseur | Type de Licence | Droits et Obligations PI |
|---|---|---|
| **OpenWeather** | Commerciale / Propriétaire | Autorisation de stockage et d'analyse interne (TotalGreen). Interdiction de revendre la donnée brute. Attribution requise. |
| **AQICN** | Attribution-NonCommercial (CC BY-NC 4.0) | Utilisation autorisée pour la recherche (GoodAir) et non-commerciale. Obligation de citer le World Air Quality Index project. |
| **TomTom** | Propriétaire Enterprise | Autorisé pour de l'analyse dérivée. Interdiction stricte de faire du reverse engineering sur les algorithmes de routing. |
| **Hub'Eau** | Licence Ouverte / Open Licence 2.0 (Etalab) | Données publiques ouvertes. Libre de reproduire, modifier, et partager sous réserve de mentionner la paternité (Eaufrance). |

**Gouvernance de la Propriété Intellectuelle :**
- Aucun algorithme externe propriétaire n'est copié.
- Les données dérivées générées par nos modèles ML (RandomForest, ARIMA) appartiennent intellectuellement à TotalGreen (Secret de R&D).
- Toutes les visualisations de data-science destinées au public comporteront en pied de page l'attribution des sources conformément aux exigences PI.

---

## 5. Mesures Techniques de Sécurité

### 5.1 Authentification & Autorisation
```
┌─────────────────────────────────────────┐
│  API Clients (Dashboard, Scripts)       │
├─────────────────────────────────────────┤
│  Token Supabase (JWT signé)             │ ← Clé API unique
├─────────────────────────────────────────┤
│  Row-Level Security (RLS) - Supabase   │ ← Qui peut voir quoi
├─────────────────────────────────────────┤
│  PostgreSQL (table fact_measures)      │ ← Connexion sécurisée
└─────────────────────────────────────────┘
```

**Configuration:**
- ✅ Authentification API par token (pas d'accès anonyme en écriture)
- ✅ Row-Level Security activé : utilisateurs voient données publiques seulement
- ✅ Logs d'accès : Supabase enregistre chaque requête

### 5.2 Chiffrement
| Étape | Méthode | Implémentation |
|-------|---------|---|
| **En transit** | HTTPS/TLS 1.3 | Toutes API externes + Supabase |
| **Au repos** | AES-256 | Supabase (default) |
| **Secrets** | Supabase Vault | Clés API dans Secret Manager |

### 5.3 Gestion des Secrets
```python
# ✅ BON
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  # Depuis env/Secret Manager

# ❌ MAUVAIS
OPENWEATHER_API_KEY = "sk_live_123456"  # Hard-coded
```

**Processus:**
1. Secrets stockés dans `.env` en local (git-ignored)
2. En production (Scaleway) : Secrets injectés au runtime
3. Rotation annuelle obligatoire des clés

---

## 6. Audit & Logging

### 6.1 Logs d'Accès
```sql
-- Table : audit_log (optionnel, peut être activée)
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_ip VARCHAR(45),          -- IP utilisateur
    resource_accessed VARCHAR(255), -- Table/endpoint accédée
    action VARCHAR(10),           -- SELECT, INSERT, etc.
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN
);
```

### 6.2 Logs d'ETL
Chaque exécution ETL enregistre :
- ✅ Nombre de lignes extraites/transformées
- ✅ Erreurs/anomalies détectées
- ✅ Durée d'exécution
- ✅ Anomalies en table `anomalies`

**Rétention :** 90 jours en base, puis archive

---

## 7. Plan de Retrait / Suppression

### 7.1 Politique de Rétention
```
Données ACTIVES (temps réel)
├─ Data Lake (raw) : 7 jours
├─ Data Warehouse (fact tables) : 1-2 ans selon source
└─ Archives (S3) : 7 ans (légalement requis pour certaines données publiques)

Métadonnées (dim_city, dim_date) : Ilimitée (référentiel stable)
Logs d'erreur : 90 jours
Logs d'audit : 1 an
```

### 7.2 Suppression Automatisée
```python
# scripts/cleanup_data_lake.py
DELETE FROM raw_data_lake 
WHERE collected_at < NOW() - INTERVAL '7 days' 
AND processed = true;  -- Garder données non-traitées
```

### 7.3 Droit à l'Oubli (Requête Manuelle)
Si un citoyen demande suppression de ses données (applicable seulement si données perso présentes - cas très rare ici) :

```bash
# Processus :
1. Signaler via support@goodair.fr
2. Vérifier absence données perso (confirmation technique)
3. Documenter refus si inapplicable avec justifications RGPD
4. Répondre dans 30 jours
```

---

## 8. Responsabilités Organisationnelles

| Rôle | Responsabilité |
|-----|---|
| **Data Owner (GoodAir)** | Définir besoins, valider conformité |
| **DPO (Data Protection Officer)** | Contrôle RGPD, réponse droits utilisateurs |
| **Responsable Sécurité (RSSI)** | Mesures techniques, audit annuel |
| **ETL Manager** | Logs, nettoyage données, tracabilité |

---

## 9. Évaluation d'Impact (DPIA)

### 9.1 Risques Identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|---|---|---|
| Fuite données environnementales | Basse | Moyen | Chiffrement + authentification |
| Indisponibilité service | Moyen | Moyen | Backup quotidien S3 |
| Erreurs de nettoyage | Moyen | Bas | Validation avant suppression |
| Accès non autorisé | Basse | Moyen | RLS + logging |

### 9.2 Conclusion DPIA
✅ **Projet conforme RGPD** (risques résiduels acceptables avec mitigations)

---

## 10. Déclarations de Conformité

### 10.1 Hébergement et Localisation
- ✅ **Supabase (PostgreSQL)** : EU data center (Ireland / Netherlands)
- ✅ **Scaleway S3** : France (fr-par-1 region)
- ✅ **DNS/CDN** : Cloudflare (edge nodes Europe)
- ✅ Pas de transferts de données hors UE

### 10.2 Certifications Fournisseurs
- ✅ Supabase : SOC 2 Type II, GDPR compliant
- ✅ Scaleway : ISO 27001, GDPR compliant
- ✅ OpenWeather : GDPR + Standard Contractual Clauses

### 10.3 Politique de Modification
Toute évolution du traitement (nouvelle source, ajout données) nécessite :
1. Revue DPIA
2. Approbation DPO
3. Mise à jour de ce document
4. Communication utilisateurs (si pertinent)

---

## 11. Contact et Escalade

| Question | Contact |
|----------|---------|
| **Questions métier** | research@goodair.fr |
| **Questions données** | data-owner@totalgreen.fr |
| **Questions sécurité/RGPD** | dpo@totalgreen.fr |
| **Incidents sécurité** | security@totalgreen.fr (48h de notification) |

---

**Dernière mise à jour :** 15 Juin 2026  
**Statut :** En vigueur  
**Prochaine révision :** Juin 2027
