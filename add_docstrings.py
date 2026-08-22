#!/usr/bin/env python3
"""
Add docstrings to key functions in SolarNode.
"""
import re
import os

# Define docstrings for common patterns
DOCSTRINGS = {
    'run_scenario': """
        Run a Monte Carlo simulation for Packet Delivery Ratio (PDR).

        Args:
            n_nodes (int): Number of nodes in the simulation.
            failure_rate (float): Fraction of nodes that fail (0.0 to 1.0).
            runs (int): Number of Monte Carlo runs.

        Returns:
            dict: Contains 'pdr_mean' and 'pdr_std' as percentages.
    """,
    'compare_lifetime': """
        Compare network lifetime with and without solar harvesting.

        Args:
            n_nodes (int): Number of nodes.
            hours (int): Maximum simulation hours.
            seed (int, optional): Random seed for reproducibility.

        Returns:
            dict: Contains 'time_hours', 'solarnode', 'random' lists.
    """,
    'simulate_with_energy': """
        Simulate network with energy model and AODV routing.

        Args:
            n_nodes (int): Number of nodes.
            failure_rate (float): Node failure rate.
            hours (int): Simulation hours.
            has_solar (bool): Whether nodes have solar harvesting.
            seed (int, optional): Random seed.

        Returns:
            list: Number of alive nodes per hour.
    """,
    'train_anomaly_model': """
        Train Isolation Forest anomaly detection model.

        Args:
            telemetry_data (list): List of Telemetry objects.
            contamination (float): Expected proportion of outliers.

        Returns:
            dict: Training status, samples, features.
    """,
    'detect_anomalies': """
        Detect anomalies in telemetry data.

        Args:
            telemetry_data (list): List of Telemetry objects.
            threshold (float): Anomaly score threshold.

        Returns:
            dict: List of anomalies with scores.
    """,
    'predict_failures': """
        Predict node failures based on battery trends.

        Args:
            current_telemetry (list): Latest telemetry per node.

        Returns:
            dict: List of predictions with risk levels.
    """,
    'get_recommendations': """
        Generate AI recommendations for network optimization.

        Args:
            network_stats (dict): Current network statistics.

        Returns:
            dict: List of recommendations with actions.
    """,
    'generate_nodes': """
        Generate random node positions in the area.

        Args:
            n (int): Number of nodes.
            seed (int, optional): Random seed.

        Returns:
            numpy.ndarray: (n, 2) array of coordinates.
    """,
    'create_mesh': """
        Create a mesh graph from node coordinates.

        Args:
            coords (numpy.ndarray): Node coordinates.

        Returns:
            networkx.Graph: Graph with edges based on range.
    """,
    'simulate_packets': """
        Simulate packet delivery using AODV routing.

        Args:
            G (networkx.Graph): Network graph.
            packets_per_node (int): Packets each node sends.

        Returns:
            float: Packet delivery ratio.
    """,
    'inject_failures': """
        Remove a fraction of nodes from the graph.

        Args:
            G (networkx.Graph): Original graph.
            failure_rate (float): Fraction to remove.

        Returns:
            networkx.Graph: Graph with failures applied.
    """,
    'compare_baseline': """
        Compare SolarNode performance against random baseline.

        Returns:
            dict: Failure rates and PDR values for both.
    """,
    'run_advanced_simulation': """
        Run simulation with AODV and energy model.

        Args:
            nodes (int): Number of nodes.
            hours (int): Simulation hours.
            has_solar (bool): Enable solar.

        Returns:
            dict: Alive nodes over time.
    """,
    'get_ntn_status': """
        Simulate NTN satellite connection status.

        Returns:
            dict: Status, latency, throughput.
    """,
    'simulate_isac': """
        Simulate ISAC survivor detection.

        Args:
            nodes_active (int): Active nodes.

        Returns:
            list: Detected survivors with confidence.
    """,
    'simulate_d2d': """
        Simulate D2D communication links.

        Args:
            nodes (int): Total nodes.
            failure_rate (float): Node failure rate.

        Returns:
            int: Number of active D2D links.
    """,
    'connect': """
        Connect to ESP32 via serial.

        Args:
            port (str, optional): Serial port. If None, auto-detect.

        Returns:
            bool: True if connected.
    """,
    'start': """
        Start reading serial data.

        Returns:
            bool: True if started successfully.
    """,
    'stop': """
        Stop reading serial data.
    """,
    '_process_packet': """
        Process incoming serial packet and store in database.

        Args:
            node_id (int): Node identifier.
            packet_type (int): Type code.
            payload (dict): Parsed JSON payload.
    """,
    'add_callback': """
        Add callback for incoming packets.

        Args:
            callback (callable): Function(node_id, type, payload).
    """,
    'send_command': """
        Send command to ESP32.

        Args:
            command (str): Command string.

        Returns:
            bool: True if sent.
    """,
}

# List of files and functions to update
FILES = {
    'app/services/simulation.py': [
        ('run_scenario', 'def run_scenario'),
        ('compare_baseline', 'def compare_baseline'),
        ('generate_nodes', 'def generate_nodes'),
        ('create_mesh', 'def create_mesh'),
        ('simulate_packets', 'def simulate_packets'),
        ('inject_failures', 'def inject_failures'),
    ],
    'app/services/simulation_v2.py': [
        ('generate_nodes', 'def generate_nodes'),
        ('create_mesh', 'def create_mesh'),
        ('simulate_with_energy', 'def simulate_with_energy'),
        ('compare_lifetime', 'def compare_lifetime'),
        ('run_advanced_simulation', 'def run_advanced_simulation'),
    ],
    'app/services/ml_service.py': [
        ('train_anomaly_model', 'def train_anomaly_model'),
        ('detect_anomalies', 'def detect_anomalies'),
        ('predict_failures', 'def predict_failures'),
        ('get_recommendations', 'def get_recommendations'),
    ],
    'app/services/fiveg.py': [
        ('get_ntn_status', 'def get_ntn_status'),
        ('simulate_isac', 'def simulate_isac'),
        ('simulate_d2d', 'def simulate_d2d'),
    ],
    'app/services/serial_bridge.py': [
        ('connect', 'def connect'),
        ('start', 'def start'),
        ('stop', 'def stop'),
        ('_process_packet', 'def _process_packet'),
        ('add_callback', 'def add_callback'),
        ('send_command', 'def send_command'),
    ],
}

def add_docstring_to_file(filepath, func_name, docstring):
    """Insert docstring after function definition if missing."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the function definition
    pattern = re.compile(rf'^\s*def\s+{func_name}\s*\(.*\)\s*:')
    new_lines = []
    inserted = False
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        if pattern.match(line):
            # Check if there's already a docstring (next line starts with """)
            if i+1 < len(lines) and lines[i+1].strip().startswith('"""'):
                # Already has docstring, skip
                pass
            else:
                # Insert docstring
                indent = ' ' * (len(line) - len(line.lstrip()))
                doc_lines = docstring.strip().split('\n')
                new_lines.append(indent + '"""' + doc_lines[0] + '\n')
                for doc_line in doc_lines[1:]:
                    new_lines.append(indent + doc_line + '\n')
                new_lines.append(indent + '"""\n')
            inserted = True
        i += 1

    if inserted:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        print(f'✅ Added docstring to {filepath}::{func_name}')
    else:
        print(f'⚠️ Could not find function {func_name} in {filepath}')

# Apply docstrings
for filepath, funcs in FILES.items():
    if not os.path.exists(filepath):
        print(f'❌ File not found: {filepath}')
        continue
    for func_name, pattern in funcs:
        if func_name in DOCSTRINGS:
            add_docstring_to_file(filepath, func_name, DOCSTRINGS[func_name])
        else:
            print(f'⚠️ No docstring defined for {func_name}')

print('🎉 Docstring addition complete.')
