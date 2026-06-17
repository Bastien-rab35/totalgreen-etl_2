"""
Service de détection d'anomalies pour les données environnementales.
Utilise une approche hybride : règles métier + statistiques + ML (Isolation Forest).
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """
    Détecte les anomalies dans les mesures environnementales.
    Approche multi-niveaux :
    1. Règles métier (limites physiques)
    2. Analyse statistique (Z-score, IQR)
    3. ML - Isolation Forest (anomalies multivariées)
    """
    
    # Règles métier : limites physiques pour chaque métrique
    BUSINESS_RULES = {
        'temperature': {'min': -50, 'max': 60, 'unit': '°C'},
        'feels_like': {'min': -60, 'max': 70, 'unit': '°C'},
        'pressure': {'min': 800, 'max': 1100, 'unit': 'hPa'},
        'humidity': {'min': 0, 'max': 100, 'unit': '%'},
        'wind_speed': {'min': 0, 'max': 200, 'unit': 'km/h'},
        'wind_gust': {'min': 0, 'max': 300, 'unit': 'km/h'},
        'clouds': {'min': 0, 'max': 100, 'unit': '%'},
        'visibility': {'min': 0, 'max': 50000, 'unit': 'm'},
        'uvi': {'min': 0, 'max': 15, 'unit': 'index'},
        'aqi': {'min': 0, 'max': 500, 'unit': 'index'},
        'pm2_5': {'min': 0, 'max': 1000, 'unit': 'µg/m³'},
        'pm10': {'min': 0, 'max': 2000, 'unit': 'µg/m³'},
        'no2': {'min': 0, 'max': 500, 'unit': 'µg/m³'},
        'o3': {'min': 0, 'max': 800, 'unit': 'µg/m³'},
        'so2': {'min': 0, 'max': 500, 'unit': 'µg/m³'},
        'co': {'min': 0, 'max': 50000, 'unit': 'µg/m³'}
    }
    
    # Seuils pour Z-score (nombre d'écarts-types)
    Z_SCORE_THRESHOLD = {
        'low': 2.0,      # 2 sigma = 95% des valeurs
        'medium': 2.5,   # 2.5 sigma = 98.8%
        'high': 3.0,     # 3 sigma = 99.7%
        'critical': 4.0  # 4 sigma = très rare
    }
    
    def __init__(self, contamination: float = 0.05):
        """
        Initialise le service de détection d'anomalies.
        
        Args:
            contamination: Proportion estimée d'anomalies (0.01 à 0.1)
                          0.05 = 5% des données sont potentiellement anormales
        """
        self.contamination = contamination
        self.isolation_forest = None
        self.scaler = StandardScaler()
        # Imputer pour remplacer les NaN avant normalisation/prédiction
        self.imputer = SimpleImputer(strategy='mean')
        self.is_trained = False
        
    def check_business_rules(self, measure: Dict) -> List[Dict]:
        """
        Vérifie les règles métier (limites physiques).
        
        Args:
            measure: Dictionnaire avec les mesures
            
        Returns:
            Liste des anomalies détectées
        """
        anomalies = []
        
        for field, limits in self.BUSINESS_RULES.items():
            value = measure.get(field)
            
            if value is None:
                continue
                
            # Vérifier si hors limites
            if value < limits['min'] or value > limits['max']:
                anomalies.append({
                    'anomaly_type': 'business_rule',
                    'severity': 'critical',
                    'field_name': field,
                    'actual_value': value,
                    'expected_range_min': limits['min'],
                    'expected_range_max': limits['max'],
                    'description': f"{field} = {value} {limits['unit']} est hors limites physiques [{limits['min']}, {limits['max']}]",
                    'action_taken': 'rejected'
                })
                
        return anomalies
    
    def check_statistical_anomalies(self, measure: Dict, city_stats: Dict) -> List[Dict]:
        """
        Détecte les anomalies statistiques via Z-score.
        Compare la mesure aux statistiques historiques de la ville.
        
        Args:
            measure: Mesure actuelle
            city_stats: Statistiques de la ville (mean, std par champ)
            
        Returns:
            Liste des anomalies détectées
        """
        anomalies = []
        
        if not city_stats:
            logger.warning("Pas de statistiques disponibles pour l'analyse Z-score")
            return anomalies
        
        for field in ['temperature', 'humidity', 'pressure', 'aqi']:
            value = measure.get(field)
            stats = city_stats.get(field)
            
            if value is None or stats is None:
                continue
                
            mean = stats.get('mean')
            std = stats.get('std')
            
            if mean is None or std is None or std == 0:
                continue
            
            # Calculer le Z-score
            z_score = abs((value - mean) / std)
            
            # Déterminer la sévérité
            severity = None
            if z_score >= self.Z_SCORE_THRESHOLD['critical']:
                severity = 'critical'
            elif z_score >= self.Z_SCORE_THRESHOLD['high']:
                severity = 'high'
            elif z_score >= self.Z_SCORE_THRESHOLD['medium']:
                severity = 'medium'
            elif z_score >= self.Z_SCORE_THRESHOLD['low']:
                severity = 'low'
            
            if severity:
                anomalies.append({
                    'anomaly_type': 'statistical',
                    'severity': severity,
                    'field_name': field,
                    'actual_value': value,
                    'expected_range_min': mean - 3*std,
                    'expected_range_max': mean + 3*std,
                    'anomaly_score': float(z_score),
                    'description': f"{field} = {value:.1f} s'écarte de {z_score:.2f} écarts-types (μ={mean:.1f}, σ={std:.1f})",
                    'action_taken': 'flagged' if severity in ['low', 'medium'] else 'rejected'
                })
        
        return anomalies
    
    def train_isolation_forest(self, historical_data: np.ndarray):
        """
        Entraîne le modèle Isolation Forest sur les données historiques.
        
        Args:
            historical_data: Array numpy (n_samples, n_features)
                            Features: [temperature, humidity, pressure, aqi, pm2_5, pm10]
        """
        if historical_data is None or len(historical_data) < 100:
            logger.warning("Pas assez de données historiques pour entraîner Isolation Forest (min: 100)")
            return
        
        try:
            # Fit l'imputer sur les données historiques. Certaines colonnes
            # peuvent être entièrement NaN => SimpleImputer.statistics_ contiendra des NaN.
            # On corrige ces statistiques en remplaçant les NaN par la moyenne
            # colonne (ou 0.0 si la colonne est complètement vide) avant de transformer.
            self.imputer.fit(historical_data)

            # S'assurer que les valeurs statistiques ne contiennent pas de NaN
            stats = np.array(self.imputer.statistics_, dtype=float)
            if np.isnan(stats).any():
                col_means = np.nanmean(historical_data, axis=0)
                col_means = np.where(np.isnan(col_means), 0.0, col_means)
                stats[np.isnan(stats)] = col_means[np.isnan(stats)]
                self.imputer.statistics_ = stats

            # Transformer puis normaliser
            X_imputed = self.imputer.transform(historical_data)

            # Si des NaN persistent (cas extrême), remplacer par 0
            if np.isnan(X_imputed).any():
                X_imputed = np.nan_to_num(X_imputed, nan=0.0)

            X_scaled = self.scaler.fit_transform(X_imputed)

            # Entraînement du modèle
            self.isolation_forest = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                n_jobs=-1
            )

            self.isolation_forest.fit(X_scaled)
            self.is_trained = True

            logger.info(f"✓ Isolation Forest entraîné sur {len(historical_data)} mesures (imputation appliquée)")

        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement Isolation Forest: {e}")
            self.is_trained = False
    
    def check_ml_anomalies(self, measure: Dict) -> Optional[Dict]:
        """
        Détecte les anomalies multivariées avec Isolation Forest.
        
        Args:
            measure: Mesure actuelle
            
        Returns:
            Dictionnaire d'anomalie si détectée, None sinon
        """
        if not self.is_trained:
            logger.debug("ML skip: modèle non entraîné")
            return None

        # Construire un array avec NaN pour les valeurs manquantes
        features = [
            np.nan if measure.get('temperature') is None else measure.get('temperature'),
            np.nan if measure.get('humidity') is None else measure.get('humidity'),
            np.nan if measure.get('pressure') is None else measure.get('pressure'),
            np.nan if measure.get('aqi') is None else measure.get('aqi'),
            np.nan if measure.get('pm2_5') is None else measure.get('pm2_5'),
            np.nan if measure.get('pm10') is None else measure.get('pm10')
        ]

        # Appliquer imputer (fallback si non-fitté)
        try:
            if not hasattr(self.imputer, 'statistics_'):
                logger.debug("Imputer non fitté — fit rapide sur l'échantillon")
                # fit sur l'échantillon pour éviter l'erreur; pas idéal mais empêche la levée
                try:
                    self.imputer.fit(np.array([features], dtype=float))
                except Exception:
                    # si impossible (ex: toutes les valeurs NaN), on remplace par 0
                    logger.warning('Imputer.fit failed on sample — remplissage NaN par 0')
                    features = [0 if (v is None or (isinstance(v, float) and np.isnan(v))) else v for v in features]

            X_imputed = self.imputer.transform([features])

            # Si l'imputer a des statistiques NaN (colonne vide lors du fit),
            # transform peut produire des NaN. On s'en protège ici.
            if np.isnan(X_imputed).any():
                logger.warning('Imputer.transform a produit des NaN — application de nan_to_num')
                X_imputed = np.nan_to_num(X_imputed, nan=0.0)

            logger.debug(f'X_imputed: {X_imputed}')

        except Exception as e:
            logger.warning(f"Imputer transform fallback: {e} — remplacement NaN par 0")
            features = [0 if (v is None or (isinstance(v, float) and np.isnan(v))) else v for v in features]
            X_imputed = np.array([features], dtype=float)

        # Appliquer scaler (fallback si non-fitté)
        try:
            if not hasattr(self.scaler, 'scale_'):
                logger.debug("Scaler non fitté — fit rapide sur l'échantillon imputed")
                try:
                    self.scaler.fit(X_imputed)
                except Exception:
                    logger.warning('Scaler.fit failed on sample — utilisation directe des valeurs')

            X = self.scaler.transform(X_imputed)

        except Exception as e:
            logger.error(f"Scaler transform failed: {e}")
            return None

        # Vérifier que le modèle existe
        if self.isolation_forest is None:
            logger.warning('IsolationForest non initialisé')
            return None

        try:
            # Prédiction (-1 = anomalie, 1 = normal)
            prediction = self.isolation_forest.predict(X)[0]
            # Score d'anomalie
            anomaly_score = self.isolation_forest.score_samples(X)[0]

        except Exception as e:
            logger.error(f"Erreur lors de la prédiction IsolationForest: {e}")
            return None

        if prediction == -1:
            # Déterminer la sévérité basée sur le score
            if anomaly_score < -0.8:
                severity = 'critical'
            elif anomaly_score < -0.6:
                severity = 'high'
            elif anomaly_score < -0.4:
                severity = 'medium'
            else:
                severity = 'low'

            return {
                'anomaly_type': 'ml_isolation_forest',
                'severity': severity,
                'field_name': 'multivariate',
                'actual_value': None,
                'expected_range_min': None,
                'expected_range_max': None,
                'anomaly_score': float(anomaly_score),
                'description': f"Anomalie multivariée détectée (score={anomaly_score:.3f})",
                'action_taken': 'flagged' if severity in ['low', 'medium'] else 'rejected'
            }

        return None
    
    def detect_anomalies(
        self, 
        measure: Dict, 
        city_stats: Optional[Dict] = None
    ) -> Tuple[bool, List[Dict], float]:
        """
        Détection complète des anomalies (règles + stats + ML).
        
        Args:
            measure: Mesure à analyser
            city_stats: Statistiques historiques de la ville (optionnel)
            
        Returns:
            Tuple (is_anomaly, anomalies_list, max_score)
            - is_anomaly: True si au moins une anomalie est détectée
            - anomalies_list: Liste de toutes les anomalies
            - max_score: Score d'anomalie le plus élevé
        """
        all_anomalies = []
        
        # 1. Règles métier (priorité max)
        business_anomalies = self.check_business_rules(measure)
        all_anomalies.extend(business_anomalies)
        
        # 2. Analyse statistique
        if city_stats:
            stat_anomalies = self.check_statistical_anomalies(measure, city_stats)
            all_anomalies.extend(stat_anomalies)
        
        # 3. ML Isolation Forest
        ml_anomaly = self.check_ml_anomalies(measure)
        if ml_anomaly:
            all_anomalies.append(ml_anomaly)
        
        # Déterminer si c'est une anomalie globale
        is_anomaly = len(all_anomalies) > 0
        
        # Score max (pour stocker dans fact_measures)
        max_score = 0.0
        if all_anomalies:
            scores = [a.get('anomaly_score', 0) for a in all_anomalies if a.get('anomaly_score')]
            max_score = max(scores) if scores else 0.0
        
        return is_anomaly, all_anomalies, max_score


def format_anomaly_for_db(anomaly: Dict, city_id: int, city_name: str, captured_at: datetime) -> Dict:
    """
    Formate une anomalie pour insertion dans la table anomalies.
    
    Args:
        anomaly: Dictionnaire d'anomalie détectée
        city_id: ID de la ville
        city_name: Nom de la ville
        captured_at: Timestamp de la mesure
        
    Returns:
        Dictionnaire formaté pour insertion
    """
    return {
        'city_id': city_id,
        'city_name': city_name,
        'captured_at': captured_at,
        'anomaly_type': anomaly.get('anomaly_type'),
        'severity': anomaly.get('severity'),
        'field_name': anomaly.get('field_name'),
        'actual_value': anomaly.get('actual_value'),
        'expected_range_min': anomaly.get('expected_range_min'),
        'expected_range_max': anomaly.get('expected_range_max'),
        'anomaly_score': anomaly.get('anomaly_score'),
        'description': f"{anomaly.get('description')} (Action: {anomaly.get('action_taken')})" if anomaly.get('action_taken') else anomaly.get('description')
    }
