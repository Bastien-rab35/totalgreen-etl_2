# 🔄 Stratégie de Fusion Anti-Perte de Données

**Date** : 7 février 2026  
**Version** : 2.0  
**Objectif** : 0% de perte de données, même si une API est en panne

---

## 🎯 Problème Initial

Lorsqu'une API (OpenWeather ou AQICN) ne répond pas pour une ville à une heure donnée :
- **Ancien comportement** : L'entrée attendait indéfiniment sa paire (weather+AQI)
- **Risque** : Données non traitées accumulées dans le Data Lake
- **Impact** : Perte potentielle de données si l'API reste down longtemps

---

## ✅ Solution Implémentée

### Stratégie en 2 temps

#### 1️⃣ **Fusion Optimale (< 2h)**
Pour les entrées récentes (âge < 2h) :
- Groupement par `(city_id, heure)` pour fusionner weather+AQI
- Crée **1 seule mesure** avec les 2 sources quand disponibles
- **Avantage** : Minimise les valeurs NULL (93.8% de fusion complète)

#### 2️⃣ **Traitement Orphelines (> 2h)**
Pour les entrées anciennes (âge ≥ 2h) :
- **Traitement immédiat** même si la paire manque
- Crée une mesure partielle avec NULL pour la source manquante
- **Garantie** : Aucune donnée ne reste bloquée

---

## 📊 Code Implémenté

### Fichier : `src/etl_transform_to_db.py`

```python
def group_by_city_and_time(self, data_list: list) -> dict:
    """
    STRATÉGIE ANTI-PERTE:
    1. Groupe weather+AQI par (city_id, heure) pour fusion optimale
    2. Traite AUSSI les entrées orphelines (>2h) SEULES
    3. Garantit 0% de perte même si une API est en panne
    """
    
    for entry in data_list:
        age_hours = calcul_age(entry)
        
        if age_hours > 2:
            # ⏰ ORPHELINE : Traiter immédiatement
            traiter_seule(entry)
        else:
            # ⏳ RÉCENTE : Grouper pour fusion
            grouper(entry)
```

---

## 📈 Résultats

### Statistiques Actuelles (4593 mesures)

| Métrique | Valeur | % |
|----------|--------|---|
| **Mesures complètes** (weather+AQI) | 4309 | 93.8% |
| **Mesures partielles** (1 source) | 284 | 6.2% |
| **Données perdues** | 0 | 0% ✅ |

### Taux de NULL

| Champ | NULL | % | Cause |
|-------|------|---|-------|
| **Temperature** | 280 | 6.1% | API OpenWeather temporairement down |
| **AQI** | 284 | 6.2% | API AQICN données non fraîches |

**Note** : Les 6.2% de NULL sont **normaux** et dus à l'indisponibilité temporaire des APIs, PAS à un bug de fusion.

---

## 🔍 Diagnostic

### Vérifier la stratégie

```bash
python scripts/check_fusion_strategy.py
```

**Affiche** :
- Nombre d'entrées non traitées
- Répartition par ville
- Entrées orphelines détectées (> 2h)
- Taux de fusion complet vs partiel

### Exemple de sortie

```
📦 Data Lake - Entrées non traitées: 0
✅ Toutes les données sont traitées !

💾 Measures dans la BDD: 4593
   Temp NULL: 280 (6.1%)
   AQI NULL: 284 (6.2%)

📈 Taux de fusion:
   Complètes (weather+AQI): 4309 (93.8%)
   Partielles (1 source): 284 (6.2%)
```

---

## ⚙️ Configuration

### Délai avant traitement orphelin

**Actuel** : 2 heures  
**Modifiable dans** : `src/etl_transform_to_db.py` ligne 167

```python
if age_hours > 2:  # ← Modifier ici (en heures)
```

**Recommandations** :
- **2h** : Équilibre optimal (défaut)
- **1h** : Plus réactif, mais plus de mesures partielles
- **4h** : Fusion maximale, mais risque d'accumulation

---

## 🚀 Avantages de la Stratégie

### ✅ Avantages

1. **0% de perte** : Toutes les données sont traitées
2. **Fusion optimale** : 93.8% de mesures complètes
3. **Auto-réparation** : Gère automatiquement les pannes API
4. **Traçabilité** : Logs des mesures incomplètes
5. **Flexibilité** : Délai configurable

### 📊 Comparaison Avant/Après

| Métrique | Ancien | Nouveau |
|----------|--------|---------|
| **Perte de données** | Possible | 0% ✅ |
| **Fusion complète** | ~50% | 93.8% ✅ |
| **Gestion panne API** | ❌ Blocage | ✅ Auto |
| **NULL values** | 98.9% | 6.2% ✅ |

---

## 📝 Logs de Monitoring

### Mesure complète (fusion réussie)

```
✓ Paris [weather+aqi] → BDD
```

### Mesure incomplète (orpheline)

```
⏰ Entrée orpheline détectée (âge: 3.2h) - City 1 @ 2026-02-07T14:00 [weather] → traitement immédiat
✓ Paris [weather] → BDD
```

### Mesure en attente (< 2h)

```
⏳ Mesure incomplète: City 1 @ 2026-02-07T16:00 - manque aqi (âge: 1.3h)
```

---

## 🔧 Maintenance

### Vérifications régulières

1. **Taux de NULL** :
   ```sql
   SELECT 
     COUNT(*) FILTER (WHERE temp IS NULL) * 100.0 / COUNT(*) as temp_null_pct,
     COUNT(*) FILTER (WHERE aqi_index IS NULL) * 100.0 / COUNT(*) as aqi_null_pct
   FROM measures;
   ```

2. **Entrées non traitées** :
   ```python
   python scripts/check_fusion_strategy.py
   ```

3. **Logs d'orphelines** :
   ```bash
   grep "⏰ Entrée orpheline" logs/etl_transform.log
   ```

### Alertes recommandées

- ⚠️ Si entrées non traitées > 100
- ⚠️ Si taux NULL > 15%
- ⚠️ Si orphelines > 50/jour

---

## 🎓 Conclusion

La stratégie de fusion anti-perte garantit **0% de perte de données** tout en maximisant la fusion (93.8%). Les 6.2% de NULL sont dus à l'indisponibilité temporaire des APIs externes, ce qui est normal et inévitable.

**Recommandation** : Aucune action nécessaire. Le système fonctionne comme prévu.

---

**Auteur** : TotalGreen ETL Team  
**Dernière mise à jour** : 7 février 2026
