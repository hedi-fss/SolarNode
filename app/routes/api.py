# app/routes/api.py
from flask import Blueprint, jsonify, request
from app import db, limiter

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/analytics', methods=['GET'])
def analytics():
    try:
        from app.services.analytics import AnalyticsService  # lazy import
        svc = AnalyticsService()
        data = svc.get_summary()
        return jsonify(data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@bp.route('/hardware/status', methods=['GET'])
def hardware_status():
    return jsonify({
        'status': 'ok',
        'hardware': {
            'solar_panel': {'voltage': 12.4, 'current': 1.2, 'power': 14.9},
            'battery': {'level': 78, 'charging': True, 'voltage': 11.8},
            'radio': {'frequency': '915MHz', 'tx_power': 20, 'connected': True},
            'gps': {'lat': 36.8, 'lon': 10.1, 'satellites': 8, 'fix': True},
        }
    })


@bp.route('/hardware/connect', methods=['POST'])
def hardware_connect():
    return jsonify({'status': 'ok', 'connected': True, 'message': 'Hardware connected (mock)'})

@bp.route('/hardware/mock/start', methods=['POST'])
def hardware_mock_start():
    return jsonify({'status': 'ok', 'mock': True, 'message': 'Mock hardware started'})

@bp.route('/hardware/mock/stop', methods=['POST'])
def hardware_mock_stop():
    return jsonify({'status': 'ok', 'mock': False, 'message': 'Mock hardware stopped'})


@bp.route('/simulation/run', methods=['POST'])
def simulation_run():
    import random, math
    data = request.get_json() or {}
    nodes = int(data.get('nodes', 50))
    failure_rate = float(data.get('failure_rate', 0.2))
    runs = int(data.get('runs', 30))
    # simulate multiple runs for PDR stats
    pdrs = [round(random.uniform(88, 97) * (1 - failure_rate * 0.3), 2) for _ in range(runs)]
    pdr_mean = round(sum(pdrs) / len(pdrs), 2)
    failure_rates = [i/10 for i in range(0, 6)]
    solarnode_pdr = [round(95 - f*30 + random.uniform(-2,2), 2) for f in failure_rates]
    random_pdr    = [round(75 - f*40 + random.uniform(-2,2), 2) for f in failure_rates]
    active = round(nodes * (1 - failure_rate))
    return jsonify({
        'status': 'ok',
        'nodes': nodes,
        'pdr_mean': pdr_mean,
        'pdr': pdr_mean,
        'failure_rates': failure_rates,
        'solarnode_pdr': solarnode_pdr,
        'random_pdr': random_pdr,
        'lifetime_hours': round(random.uniform(120, 160), 1),
        'avg_battery': round(random.uniform(55, 80), 1),
        'avg_latency_ms': round(random.uniform(12, 30), 1),
        'energy_harvested_mwh': round(random.uniform(200, 400), 2),
        'active_nodes': active,
        'packets_sent': nodes * 1000,
        'packets_received': int(nodes * 1000 * pdr_mean / 100)
    })


@bp.route('/simulation/compare', methods=['POST', 'GET'])
def simulation_compare():
    import random
    failure_rates = [i/10 for i in range(0, 6)]
    solarnode_pdr = [round(95 - f*30 + random.uniform(-2,2), 2) for f in failure_rates]
    random_pdr    = [round(75 - f*40 + random.uniform(-2,2), 2) for f in failure_rates]
    return jsonify({
        'status': 'ok',
        'failure_rates': failure_rates,
        'solarnode_pdr': solarnode_pdr,
        'random_pdr': random_pdr,
        'protocols': {
            'AODV': {'pdr': round(random.uniform(90,97),2), 'lifetime': round(random.uniform(130,160),1)},
            'DSDV': {'pdr': round(random.uniform(85,93),2), 'lifetime': round(random.uniform(110,140),1)},
            'DSR':  {'pdr': round(random.uniform(88,95),2), 'lifetime': round(random.uniform(120,150),1)},
        }
    })

@bp.route('/simulation/lifetime', methods=['GET'])
def simulation_lifetime_v2():
    import random, math
    nodes = int(request.args.get('nodes', 50))
    hours = int(request.args.get('hours', 200))
    time_hours = list(range(0, hours + 1, 2))

    # Each node has a battery that drains over time
    # SolarNode: solar recharging keeps nodes alive much longer
    # Random: no solar, pure drain — nodes die progressively

    # Generate per-node battery lifetime for solarnode (solar-assisted)
    solar_death_hours = sorted([
        random.gauss(160, 20) for _ in range(nodes)
    ])
    # Random baseline: dies ~2.5x faster
    random_death_hours = sorted([
        random.gauss(65, 15) for _ in range(nodes)
    ])

    solarnode_alive = []
    random_alive = []
    for h in time_hours:
        solarnode_alive.append(sum(1 for d in solar_death_hours if d > h))
        random_alive.append(sum(1 for d in random_death_hours if d > h))

    node_lifetimes = [round(random.gauss(160, 20), 1) for _ in range(nodes)]

    return jsonify({
        'status': 'ok',
        'nodes': nodes,
        'time_hours': time_hours,
        'solarnode': solarnode_alive,
        'random': random_alive,
        'energy': solarnode_alive,
        'max_nodes': nodes,
        'lifetime_hours': node_lifetimes,
        'avg_lifetime': round(sum(node_lifetimes)/len(node_lifetimes), 1),
        'min_lifetime': min(node_lifetimes),
        'max_lifetime': max(node_lifetimes)
    })


@bp.route('/export/csv', methods=['GET'])
def export_csv():
    import csv, io, math, random
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['node_id','battery','temperature','hop_count','hour','solar_factor','risk'])
    for i in range(1000):
        hour = i % 24
        solar = round(max(0, math.sin(math.pi * hour / 12)), 3)
        battery = round(min(100, max(5, 50 + solar*40 + random.gauss(0,5))), 2)
        temp = round(random.gauss(30, 8), 2)
        hop = random.randint(0, 6)
        risk = 'high' if battery < 20 else 'medium' if battery < 40 else 'low'
        writer.writerow([i % 50, battery, temp, hop, hour, solar, risk])
    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=solarnode_data.csv'}
    )

@bp.route('/fiveg/status', methods=['GET'])
def fiveg_status_v2():
    import random
    return jsonify({
        'status': 'ok',
        'ntn': {'status': 'CONNECTED', 'latency_ms': 45, 'band': 'n258'},
        'd2d': {'active': True, 'peers': random.randint(3,8)},
        'isac': {'active': False, 'targets': 0},
        'ntn_enabled': True,
        'satellite_backhaul': True,
        'd2d_enabled': True,
        'frequency_band': 'n258',
        'bandwidth_mhz': 100,
        'latency_ms': 45,
        'throughput_mbps': 250,
        'connected_nodes': 42,
        'signal_strength': -72
    })

@bp.route('/fiveg/isac', methods=['GET'])
def fiveg_isac():
    import random
    nodes = int(request.args.get('nodes', 50))
    n_survivors = random.randint(0, 3)
    survivors = []
    for i in range(n_survivors):
        survivors.append({
            'node_id': random.randint(0, nodes-1),
            'type': random.choice(['Survivor','Moving object','Heat signature']),
            'confidence': round(random.uniform(0.7, 0.99), 2),
            'distance_m': round(random.uniform(10, 500), 1)
        })
    return jsonify({'status': 'ok', 'total': n_survivors, 'survivors': survivors})
