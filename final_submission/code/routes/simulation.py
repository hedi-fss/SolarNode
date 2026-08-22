"""Simulation Routes"""
from flask import Blueprint, jsonify, request
from app.services.simulation import SimulationService

bp = Blueprint('simulation', __name__)
sim_service = SimulationService()


@bp.route('/run', methods=['POST'])
def run_simulation():
    """Run a simulation scenario"""
    data = request.get_json() or {}
    nodes = data.get('nodes', 50)
    failure_rate = data.get('failure_rate', 0.0)
    runs = data.get('runs', 50)

    result = sim_service.run_scenario(nodes, failure_rate, runs)
    return jsonify(result)


@bp.route('/compare')
def compare_scenarios():
    """Compare SolarNode vs Random baseline"""
    result = sim_service.compare_baseline()
    return jsonify(result)


@bp.route('/lifetime')
def get_lifetime():
    """Get network lifetime simulation results"""
    # Simple canned response for now
    return jsonify({
        'time_hours': list(range(200)),
        'no_solar': [50 - i / 4 for i in range(200) if i < 200],
        'with_solar': [50 - i / 10 for i in range(200) if i < 200]
    })
