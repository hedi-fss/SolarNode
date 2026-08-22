"""AI/ML Service for SolarNode - Enhanced with evaluation and auto-contamination"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import os
import pickle
import warnings
warnings.filterwarnings("ignore")

class MLService:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'models')
        os.makedirs(self.model_path, exist_ok=True)

        self.anomaly_model = None
        self.failure_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_samples = 0
        self.contamination_used = 0.1
        self.anomaly_threshold = -0.5  # default threshold

        self.load_models()

    def load_models(self):
        """Load models from disk with graceful fallback."""
        try:
            anomaly_path = os.path.join(self.model_path, 'anomaly_model.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            if os.path.exists(anomaly_path) and os.path.exists(scaler_path):
                with open(anomaly_path, 'rb') as f:
                    self.anomaly_model = pickle.load(f)
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                print("✅ ML models loaded from disk")
        except Exception as e:
            print(f"⚠️ Could not load models: {e}")

    def save_models(self):
        """Save models to disk."""
        try:
            if self.anomaly_model:
                with open(os.path.join(self.model_path, 'anomaly_model.pkl'), 'wb') as f:
                    pickle.dump(self.anomaly_model, f)
                with open(os.path.join(self.model_path, 'scaler.pkl'), 'wb') as f:
                    pickle.dump(self.scaler, f)
                print("✅ ML models saved")
        except Exception as e:
            print(f"⚠️ Could not save models: {e}")

    def prepare_features(self, telemetry_data):
        """Extract features from telemetry records."""
        features = []
        for record in telemetry_data:
            if hasattr(record, 'to_dict'):
                record = record.to_dict()
            battery = record.get('battery', 50)
            temperature = record.get('temperature', 25)
            hop_count = record.get('hop_count', 0)
            features.append([battery, temperature, hop_count])
        return np.array(features)

    def estimate_contamination(self, features, quantile=0.05):
        """
        Estimate contamination as the fraction of points that are 'far' from the median.
        Uses the Mahalanobis distance or simply the interquartile range.
        We use a simple approach: compute the 95th percentile of the L2 distance from the median.
        """
        median = np.median(features, axis=0)
        distances = np.linalg.norm(features - median, axis=1)
        # Use a high quantile to define outliers
        threshold = np.percentile(distances, 100 * (1 - quantile))
        outliers = np.sum(distances > threshold)
        return max(0.01, outliers / len(features))  # at least 1%

    def train_anomaly_model(self, telemetry_data, contamination=None):
        """
        Train Isolation Forest with auto‑contamination if not provided.
        """
        if len(telemetry_data) < 10:
            return {'status': 'error', 'message': 'Need at least 10 samples'}

        features = self.prepare_features(telemetry_data)
        self.scaler.fit(features)
        scaled_features = self.scaler.transform(features)

        if contamination is None:
            contamination = self.estimate_contamination(scaled_features)
            print(f"🔬 Auto‑estimated contamination: {contamination:.3f}")

        self.anomaly_model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.anomaly_model.fit(scaled_features)

        self.is_trained = True
        self.training_samples = len(telemetry_data)
        self.contamination_used = contamination

        # Set anomaly threshold as 10th percentile of training scores
        scores = self.anomaly_model.score_samples(scaled_features)
        self.anomaly_threshold = np.percentile(scores, 10)
        self.save_models()

        return {
            'status': 'success',
            'samples': len(telemetry_data),
            'features': features.shape[1],
            'contamination': contamination,
            'threshold': float(self.anomaly_threshold)
        }

    def detect_anomalies(self, telemetry_data, threshold=None):
        """Detect anomalies using the trained model."""
        if not self.is_trained or self.anomaly_model is None:
            return {'anomalies': [], 'error': 'Model not trained'}

        if len(telemetry_data) == 0:
            return {'anomalies': []}

        try:
            features = self.prepare_features(telemetry_data)
            scaled_features = self.scaler.transform(features)
            predictions = self.anomaly_model.predict(scaled_features)
            scores = self.anomaly_model.score_samples(scaled_features)

            if threshold is None:
                threshold = self.anomaly_threshold

            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, scores)):
                if pred == -1 and score < threshold:
                    record = telemetry_data[i]
                    if hasattr(record, 'to_dict'):
                        record = record.to_dict()
                    anomalies.append({
                        'node_id': record.get('node_id', 0),
                        'battery': record.get('battery', 0),
                        'temperature': record.get('temperature', 0),
                        'hop_count': record.get('hop_count', 0),
                        'anomaly_score': float(score),
                        'severity': 'high' if score < threshold * 1.5 else 'medium'
                    })
            return {'anomalies': anomalies}
        except Exception as e:
            return {'anomalies': [], 'error': str(e)}

    def evaluate_model(self, telemetry_data):
        """
        Evaluate the model on a dataset: compute anomaly percentage and score statistics.
        """
        if not self.is_trained or self.anomaly_model is None:
            return {'error': 'Model not trained'}

        features = self.prepare_features(telemetry_data)
        scaled_features = self.scaler.transform(features)
        scores = self.anomaly_model.score_samples(scaled_features)
        predictions = self.anomaly_model.predict(scaled_features)

        anomalies = np.sum(predictions == -1)
        total = len(predictions)

        return {
            'total_samples': total,
            'anomalies_detected': int(anomalies),
            'anomaly_percentage': round(100 * anomalies / total, 2),
            'mean_score': float(np.mean(scores)),
            'std_score': float(np.std(scores)),
            'min_score': float(np.min(scores)),
            'max_score': float(np.max(scores)),
            'threshold': float(self.anomaly_threshold),
            'contamination': self.contamination_used,
        }

    # --- Failure predictor (unchanged) ---
    def train_failure_predictor(self, telemetry_history):
        if len(telemetry_history) < 20:
            return {'status': 'error', 'message': 'Need at least 20 samples'}
        try:
            data = []
            for i in range(len(telemetry_history) - 1):
                current = telemetry_history[i]
                next_record = telemetry_history[i + 1]
                if hasattr(current, 'to_dict'):
                    current = current.to_dict()
                if hasattr(next_record, 'to_dict'):
                    next_record = next_record.to_dict()
                battery_drop = current.get('battery', 0) - next_record.get('battery', 0)
                data.append({
                    'battery': current.get('battery', 0),
                    'battery_drop': battery_drop,
                    'temperature': current.get('temperature', 25),
                    'will_fail': 1 if battery_drop > 10 else 0
                })
            self.failure_model = LinearRegression()
            X = np.array([[d['battery'], d['battery_drop'], d['temperature']] for d in data])
            y = np.array([d['will_fail'] for d in data])
            self.failure_model.fit(X, y)
            return {'status': 'success', 'samples': len(data)}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def predict_failures(self, current_telemetry):
        predictions = []
        for record in current_telemetry:
            if hasattr(record, 'to_dict'):
                record = record.to_dict()
            battery = record.get('battery', 50)
            if battery < 20:
                risk = 'high'
            elif battery < 40:
                risk = 'medium'
            else:
                risk = 'low'
            predictions.append({
                'node_id': record.get('node_id', 0),
                'battery': battery,
                'risk': risk,
                'estimated_hours': max(0, battery / 5)
            })
        predictions.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['risk']])
        return {'predictions': predictions}

    def get_recommendations(self, network_stats):
        recommendations = []
        if network_stats.get('pdr', 100) < 80:
            recommendations.append({
                'type': 'optimization',
                'severity': 'high',
                'message': 'Low PDR. Network reliability needs improvement.',
                'action': 'Add more nodes or reduce network load'
            })
        if network_stats.get('avg_battery', 100) < 30:
            recommendations.append({
                'type': 'maintenance',
                'severity': 'high',
                'message': 'Low average battery. Solar harvesting may be insufficient.',
                'action': 'Adjust duty cycling or increase solar capacity'
            })
        if network_stats.get('network_lifetime', 0) < 72:
            recommendations.append({
                'type': 'optimization',
                'severity': 'medium',
                'message': 'Network lifetime below 72 hours.',
                'action': 'Enable AODV routing to reduce overhead'
            })
        if not recommendations:
            recommendations.append({
                'type': 'info',
                'severity': 'low',
                'message': 'Network is healthy. No immediate actions needed.',
                'action': 'Monitor regularly'
            })
        return {'recommendations': recommendations}
