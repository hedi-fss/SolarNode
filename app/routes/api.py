from flask import Blueprint, jsonify, request
from app import db
from app.models.telemetry import Telemetry
from sqlalchemy.exc import OperationalError

bp = Blueprint('api', __name__)

# ==================== TELEMETRY ENDPOINTS ====================

@bp.route('/telemetry/latest', methods=['GET'])
@bp.route('/api/telemetry/latest', methods=['GET'])
def get_latest_telemetry():
    try:
        latest = Telemetry.query.order_by(Telemetry.timestamp.desc()).first()
        if latest:
            return jsonify(latest.to_dict())
        return jsonify({
            'status': 'ok',
            'data': None,
            'message': 'No telemetry data found'
        }), 200
    except OperationalError:
        return jsonify({
            'status': 'ok',
            'data': None,
            'message': 'No telemetry data found'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/telemetry/history', methods=['GET'])
def get_telemetry_history():
    try:
        limit = request.args.get('limit', 100, type=int)
        history = Telemetry.query.order_by(Telemetry.timestamp.desc()).limit(limit).all()
        return jsonify([record.to_dict() for record in history])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/telemetry/stats', methods=['GET'])
def get_telemetry_stats():
    try:
        from sqlalchemy import func
        count = Telemetry.query.count()
        latest = Telemetry.query.order_by(Telemetry.timestamp.desc()).first()
        nodes = Telemetry.query.with_entities(Telemetry.node_id).distinct().count()
        return jsonify({
            'total_records': count,
            'latest_timestamp': latest.timestamp.isoformat() if latest else None,
            'nodes': nodes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== OTHER EXISTING ENDPOINTS ====================
# (Add your other API routes below, if any)
