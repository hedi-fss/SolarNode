"""API Routes"""
from flask import Blueprint, jsonify, request, current_app
from app import db, limiter, socketio
from app.models import Telemetry, Node, NetworkStats
from app.services.simulation import SimulationService
from app.services.analytics import AnalyticsService
from datetime import datetime

bp = Blueprint('api', __name__)
sim_service = SimulationService()
analytics = AnalyticsService()

# === Telemetry Endpoints ===
@bp.route('/telemetry/latest')
def get_latest_telemetry():
    latest = Telemetry.query.order_by(Telemetry.timestamp.desc()).first()
    if latest:
        return jsonify(latest.to_dict())
    return jsonify({'error': 'No data'}), 404

@bp.route('/telemetry/history')
def get_telemetry_history():
    limit = request.args.get('limit', 100, type=int)
    history = Telemetry.query.order_by(Telemetry.timestamp.desc()).limit(limit).all()
    return jsonify([h.to_dict() for h in history])

@bp.route('/network/stats')
def get_network_stats():
    stats = NetworkStats.query.order_by(NetworkStats.timestamp.desc()).first()
    if stats:
        return jsonify(stats.to_dict())
    return jsonify({'error': 'No stats'}), 404

@bp.route('/simulation/run', methods=['POST'])
def run_simulation():
    data = request.get_json() or {}
    nodes = data.get('nodes', 50)
    failure_rate = data.get('failure_rate', 0.0)
    runs = data.get('runs', 50)
    result = sim_service.run_scenario(nodes, failure_rate, runs)
    return jsonify(result)

@bp.route('/simulation/compare')
def compare_scenarios():
    result = sim_service.compare_baseline()
    return jsonify(result)

@bp.route('/simulation/lifetime')
def get_lifetime():
    """Get network lifetime comparison"""
    n_nodes = request.args.get('nodes', 50, type=int)
    hours = request.args.get('hours', 200, type=int)
    seed = request.args.get('seed', None, type=int)
    try:
        from app.services.simulation_v2 import SimulationServiceV2
        sim_v2 = SimulationServiceV2()
        result = sim_v2.compare_lifetime(n_nodes=n_nodes, hours=hours, seed=seed)
        result["max_nodes"] = n_nodes
        return jsonify(result)
    except ImportError:
        # Fallback if SimulationServiceV2 doesn't exist
        time_hours = list(range(hours))
        random_lifetime = [max(0, n_nodes - i/1.5) for i in range(hours)]
        solarnode_lifetime = [max(0, n_nodes - i/3.5) for i in range(hours)]
        return jsonify({
            'time_hours': time_hours,
            'random': random_lifetime,
            'solarnode': solarnode_lifetime,
            'max_nodes': n_nodes
        })

@bp.route('/simulation/advanced', methods=['POST'])
def run_advanced_simulation():
    """Run advanced simulation with energy modeling"""
    data = request.get_json() or {}
    nodes = data.get('nodes', 50)
    hours = data.get('hours', 200)
    has_solar = data.get('has_solar', True)
    try:
        from app.services.simulation_v2 import SimulationServiceV2
        sim_v2 = SimulationServiceV2()
        alive_over_time = sim_v2.simulate_with_energy(nodes, hours=hours, has_solar=has_solar)
        return jsonify({
            'time_hours': list(range(len(alive_over_time))),
            'alive_nodes': alive_over_time
        })
    except ImportError:
        # Fallback simulation
        lifetime = [max(0, nodes - i/(3.5 if has_solar else 1.5)) for i in range(hours)]
        return jsonify({
            'time_hours': list(range(len(lifetime))),
            'alive_nodes': lifetime
        })

# === 5G/6G Endpoints ===
@bp.route('/fiveg/status')
def get_fiveg_status():
    from app.services.fiveg import FiveGService
    fg = FiveGService()
    return jsonify({
        'ntn': fg.get_ntn_status(),
        'd2d': {'active': fg.d2d_active},
        'isac': {'active': fg.isac_active}
    })

@bp.route('/fiveg/isac')
def get_isac_detections():
    from app.services.fiveg import FiveGService
    fg = FiveGService()
    nodes_active = request.args.get('nodes', 50, type=int)
    survivors = fg.simulate_isac(nodes_active)
    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'survivors': survivors,
        'total': len(survivors)
    })

@bp.route('/fiveg/d2d')
def get_d2d_stats():
    from app.services.fiveg import FiveGService
    fg = FiveGService()
    nodes = request.args.get('nodes', 50, type=int)
    failure_rate = request.args.get('failure_rate', 0.0, type=float)
    links = fg.simulate_d2d(nodes, failure_rate)
    return jsonify({
        'd2d_links': links,
        'max_possible': nodes * (nodes - 1) // 2
    })

# === Export Endpoint ===
@bp.route('/export/csv')
def export_csv():
    import csv
    from io import StringIO
    stats = NetworkStats.query.order_by(NetworkStats.timestamp.desc()).limit(20).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['timestamp', 'total_nodes', 'active_nodes', 'pdr', 'avg_latency', 'network_lifetime'])
    for stat in stats:
        writer.writerow([
            stat.timestamp.isoformat(),
            stat.total_nodes,
            stat.active_nodes,
            stat.pdr,
            stat.avg_latency,
            stat.network_lifetime
        ])
    output = si.getvalue()
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=solarnode_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    }

# === ML Endpoints ===
@bp.route('/ml/anomalies')
def get_anomalies():
    return jsonify({'anomalies': [], 'status': 'normal'})

@bp.route('/ml/predict')
def predict_failures():
    return jsonify({'predictions': [], 'status': 'normal'})

@bp.route('/ml/train', methods=['POST'])
def train_model():
    result = analytics.train()
    return jsonify(result)

# === Nodes Endpoints ===
@bp.route('/nodes')
def get_nodes():
    nodes = Node.query.all()
    return jsonify([n.to_dict() for n in nodes])

@bp.route('/nodes/active')
def get_active_nodes():
    active = Node.query.filter_by(is_active=True).count()
    return jsonify({'active_nodes': active})

# === Hardware Integration Endpoints ===
@bp.route('/hardware/status')
def hardware_status():
    try:
        from app.services.serial_bridge import serial_bridge
        from app.services.mock_hardware import mock_hardware
        return jsonify({
            'serial_connected': serial_bridge.serial_conn is not None,
            'serial_port': serial_bridge.port,
            'mock_running': mock_hardware.running,
            'mock_nodes': mock_hardware.nodes,
            'mock_interval': mock_hardware.interval
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'serial_connected': False,
            'mock_running': False,
            'serial_port': None,
            'mock_nodes': 0,
            'mock_interval': 0
        }), 200

@bp.route('/hardware/connect', methods=['POST'])
def hardware_connect():
    from app.services.serial_bridge import serial_bridge
    data = request.get_json() or {}
    port = data.get('port')
    result = serial_bridge.connect(port)
    if result:
        serial_bridge.start()
        return jsonify({'status': 'connected', 'port': serial_bridge.port})
    return jsonify({'status': 'error', 'message': 'Failed to connect'}), 400

@bp.route('/hardware/mock/start', methods=['POST'])
def mock_start():
    from app.services.mock_hardware import mock_hardware
    data = request.get_json() or {}
    if data.get('nodes'):
        mock_hardware.set_nodes(data['nodes'])
    if data.get('interval'):
        mock_hardware.set_interval(data['interval'])
    mock_hardware.start()
    return jsonify({
        'status': 'started',
        'nodes': mock_hardware.nodes,
        'interval': mock_hardware.interval
    })

@bp.route('/hardware/mock/stop', methods=['POST'])
def mock_stop():
    from app.services.mock_hardware import mock_hardware
    mock_hardware.stop()
    return jsonify({'status': 'stopped'})

@bp.route('/hardware/ingest', methods=['POST'])
def ingest_hardware_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    node_id = data.get('node_id', 0)
    packet_type = data.get('type', 'telemetry')
    payload = data.get('data', {})
    telemetry = Telemetry(
        node_id=node_id,
        timestamp=datetime.utcnow(),
        battery=payload.get('battery', 0),
        temperature=payload.get('temp', 0),
        humidity=payload.get('humidity', 0),
        latitude=payload.get('lat', 0),
        longitude=payload.get('lon', 0),
        altitude=payload.get('alt', 0),
        packet_type=packet_type,
        hop_count=payload.get('hop_count', 0)
    )
    db.session.add(telemetry)
    db.session.commit()
    socketio.emit('telemetry_update', {
        'node_id': node_id,
        'type': packet_type,
        'data': payload,
        'timestamp': datetime.utcnow().isoformat()
    })
    return jsonify({'status': 'ingested', 'node_id': node_id})

@bp.route('/simulation/scenarios')
def get_scenario_comparison():
    """Run and return comparison across multiple scenarios."""
    from app.services.simulation import SimulationService
    sim = SimulationService()
    results = sim.compare_all_scenarios()
    return jsonify(results)
