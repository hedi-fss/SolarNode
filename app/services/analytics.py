"""Analytics Service - AI/ML Anomaly Detection"""
import numpy as np
from sklearn.ensemble import IsolationForest
from app.models import Telemetry


class AnalyticsService:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False

    def train(self):
        """Train anomaly detection model on historical data"""
        data = Telemetry.query.all()
        if len(data) < 10:
            return {'status': 'insufficient_data'}

        features = np.array(
            [[d.battery, d.temperature, d.hop_count] for d in data])
        self.model.fit(features)
        self.is_trained = True
        return {'status': 'trained', 'samples': len(data)}

    def detect_anomalies(self, limit=50):
        """Detect anomalies in recent telemetry"""
        data = Telemetry.query.order_by(
            Telemetry.timestamp.desc()).limit(limit).all()
        if not data or not self.is_trained:
            return []

        features = np.array(
            [[d.battery, d.temperature, d.hop_count] for d in data])
        predictions = self.model.predict(features)

        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:
                anomalies.append({
                    'node_id': data[i].node_id,
                    'timestamp': data[i].timestamp.isoformat(),
                    'battery': data[i].battery,
                    'temperature': data[i].temperature,
                    'anomaly_score': float(self.model.score_samples([features[i]])[0])
                })
        return anomalies

    def predict_failures(self):
        """Predict nodes at risk of failure"""
        # Simplified: nodes with battery < 20% are at risk
        nodes = Telemetry.query.filter(Telemetry.battery < 20).all()
        return [{'node_id': n.node_id, 'battery': n.battery} for n in nodes]
