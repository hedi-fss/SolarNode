"""API Documentation - Lists all available endpoints"""
from flask import Blueprint, jsonify, current_app

bp = Blueprint('docs', __name__, url_prefix='/api')

@bp.route('/docs')
def api_docs():
    """List all available API endpoints."""
    rules = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != 'static' and not rule.endpoint.startswith('docs'):
            rules.append({
                'endpoint': rule.endpoint,
                'methods': sorted(list(rule.methods - {'HEAD', 'OPTIONS'})),
                'path': str(rule)
            })
    return jsonify({'endpoints': rules})
