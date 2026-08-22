"""ML/AI Routes"""
from flask import Blueprint, jsonify, request
from app import db
from app.models import Telemetry, NetworkStats
from app.services.ml_service import MLService
from datetime import datetime

bp = Blueprint('ml', __name__)
ml_service = MLService()

@bp.route('/status')
def get_status():
    """Get ML service status."""
    return jsonify({
        'is_trained': ml_service.is_trained,
        'training_samples': ml_service.training_samples,
        'model_loaded': ml_service.anomaly_model is not None
    })

@bp.route('/train', methods=['POST'])
def train_model():
    """Train anomaly detection model on historical data."""
    data = request.get_json() or {}
    contamination = data.get('contamination', None)  # None = auto
    telemetry_data = Telemetry.query.order_by(Telemetry.timestamp.desc()).all()
    if len(telemetry_data) < 10:
        return jsonify({'error': 'Need at least 10 samples for training'}), 400
    result = ml_service.train_anomaly_model(telemetry_data, contamination=contamination)
    if len(telemetry_data) > 20:
        ml_service.train_failure_predictor(telemetry_data)
    return jsonify(result)

@bp.route('/anomalies')
def get_anomalies():
    """Detect anomalies in recent telemetry."""
    limit = request.args.get('limit', 100, type=int)
    telemetry_data = Telemetry.query.order_by(Telemetry.timestamp.desc()).limit(limit).all()
    if not telemetry_data:
        return jsonify({'anomalies': [], 'message': 'No telemetry data available'})
    if not ml_service.is_trained:
        return jsonify({
            'anomalies': [],
            'message': 'Model not trained. Click "Train AI" first.',
            'error': 'not_trained'
        })
    result = ml_service.detect_anomalies(telemetry_data)
    return jsonify(result)

@bp.route('/predict')
def predict_failures():
    """Predict which nodes are at risk of failure."""
    from sqlalchemy import func
    latest_per_node = db.session.query(
        Telemetry.node_id,
        func.max(Telemetry.timestamp).label('max_timestamp')
    ).group_by(Telemetry.node_id).subquery()
    latest_data = db.session.query(Telemetry).join(
        latest_per_node,
        (Telemetry.node_id == latest_per_node.c.node_id) &
        (Telemetry.timestamp == latest_per_node.c.max_timestamp)
    ).all()
    if not latest_data:
        return jsonify({'predictions': [], 'message': 'No telemetry data available'})
    result = ml_service.predict_failures(latest_data)
    return jsonify(result)

@bp.route('/recommendations')
def get_recommendations():
    """Get AI-generated recommendations."""
    recommendations = []
    try:
        stats = NetworkStats.query.order_by(NetworkStats.timestamp.desc()).first()
        if stats:
            stats_dict = stats.to_dict()
        else:
            stats_dict = {'total_nodes': 50, 'active_nodes': 50, 'pdr': 90.0, 'network_lifetime': 100}
        from sqlalchemy import func
        avg_battery = db.session.query(func.avg(Telemetry.battery)).scalar() or 50
        stats_dict['avg_battery'] = avg_battery
        if stats_dict.get('pdr', 100) < 80:
            recommendations.append({
                'type': 'optimization',
                'severity': 'high',
                'message': f'Low PDR ({stats_dict["pdr"]:.1f}%) detected.',
                'action': 'Add more nodes or reduce network load'
            })
        if stats_dict.get('avg_battery', 100) < 30:
            recommendations.append({
                'type': 'maintenance',
                'severity': 'high',
                'message': f'Low average battery ({stats_dict["avg_battery"]:.1f}%).',
                'action': 'Adjust duty cycling or increase solar capacity'
            })
        if stats_dict.get('network_lifetime', 0) < 72:
            recommendations.append({
                'type': 'optimization',
                'severity': 'medium',
                'message': f'Network lifetime ({stats_dict["network_lifetime"]:.0f}h) below 72h.',
                'action': 'Enable AODV routing'
            })
        anomaly_count = Telemetry.query.filter(Telemetry.battery < 20).count()
        if anomaly_count > 0:
            recommendations.append({
                'type': 'warning',
                'severity': 'medium',
                'message': f'{anomaly_count} nodes have critically low battery (<20%).',
                'action': 'Deploy replacement nodes or prioritize solar recharge'
            })
        if not recommendations:
            recommendations.append({
                'type': 'info',
                'severity': 'low',
                'message': 'Network is healthy. No immediate actions needed.',
                'action': 'Monitor regularly'
            })
    except Exception as e:
        recommendations.append({
            'type': 'info',
            'severity': 'low',
            'message': 'Network analysis complete. Run a simulation to get specific recommendations.',
            'action': 'Click "Run Simulation" to generate recommendations'
        })
    return jsonify({'recommendations': recommendations})

@bp.route('/evaluate')
def evaluate_model():
    """Evaluate the trained model on recent telemetry data."""
    data = Telemetry.query.order_by(Telemetry.timestamp.desc()).limit(1000).all()
    if not data:
        return jsonify({'error': 'No data for evaluation'}), 400
    result = ml_service.evaluate_model(data)
    return jsonify(result)

@bp.route('/info')
def model_info():
    """Get information about the current model."""
    return jsonify({
        'is_trained': ml_service.is_trained,
        'samples': ml_service.training_samples,
        'contamination': ml_service.contamination_used,
        'threshold': ml_service.anomaly_threshold
    })
