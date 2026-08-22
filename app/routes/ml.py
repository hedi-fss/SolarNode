"""ML Routes - fast synthetic data for HTTP, large dataset for training only"""
from flask import Blueprint, jsonify, request

bp = Blueprint('ml', __name__, url_prefix='/api/ml')


def _synthetic_telemetry(n=500):
    """Generate n synthetic telemetry records. Keep n small for HTTP routes."""
    import random, math
    records = []
    for i in range(n):
        hour = i % 24
        solar_factor = max(0, math.sin(math.pi * hour / 12))
        battery = min(100, max(5, 50 + solar_factor * 40 + random.gauss(0, 5)))
        records.append({
            'node_id': i % 50,
            'battery': round(battery, 2),
            'temperature': round(random.gauss(30, 8), 2),
            'hop_count': random.randint(0, 6),
        })
    return records


def _synthetic_telemetry_large(n=200000):
    """Large dataset for training only."""
    import random, math
    records = []
    for i in range(n):
        hour = i % 24
        solar_factor = max(0, math.sin(math.pi * hour / 12))
        battery = min(100, max(5, 50 + solar_factor * 40 + random.gauss(0, 5)))
        records.append({
            'node_id': i % 50,
            'battery': round(battery, 2),
            'temperature': round(random.gauss(30, 8), 2),
            'hop_count': random.randint(0, 6),
        })
    return records


@bp.route('/train', methods=['POST'])
def train():
    try:
        from app.services.ml_service import MLService
        svc = MLService()
        data = _synthetic_telemetry_large(200000)
        result = svc.train_anomaly_model(data)
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'message': str(e), 'trace': traceback.format_exc()}), 500


@bp.route('/predict', methods=['GET', 'POST'])
def predict():
    try:
        from app.services.ml_service import MLService
        svc = MLService()
        data = _synthetic_telemetry(500)
        result = svc.predict_failures(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/evaluate', methods=['GET', 'POST'])
def evaluate():
    try:
        from app.services.ml_service import MLService
        svc = MLService()
        data = _synthetic_telemetry(500)
        result = svc.evaluate_model(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/anomalies', methods=['GET'])
def anomalies():
    try:
        from app.services.ml_service import MLService
        svc = MLService()
        limit = min(int(request.args.get('limit', 100)), 500)
        data = _synthetic_telemetry(limit)
        result = svc.detect_anomalies(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/detect', methods=['POST'])
def detect():
    try:
        from app.services.ml_service import MLService
        svc = MLService()
        data = _synthetic_telemetry(500)
        result = svc.detect_anomalies(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/recommendations', methods=['GET'])
def recommendations():
    try:
        from app.services.ml_service import MLService
        svc = MLService()
        stats = {}
        for k, v in request.args.items():
            try:
                stats[k] = float(v)
            except ValueError:
                pass
        result = svc.get_recommendations(stats)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/status', methods=['GET'])
def status():
    try:
        from app.services.ml_service import MLService
        svc = MLService()
        return jsonify({
            'is_trained': svc.is_trained,
            'training_samples': svc.training_samples or 200000,
            'contamination': svc.contamination_used,
            'threshold': float(svc.anomaly_threshold),
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
