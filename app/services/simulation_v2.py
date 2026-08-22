"""SolarNode Simulation v2 with AODV + Energy"""
import numpy as np
import networkx as nx
from app.services.aodv import AODVRouter
from app.services.energy import EnergyModel
import random

class SimulationServiceV2:
    def __init__(self):
        self.area_km = 5.0
        self.range_km = 0.8
        self.gateway_id = 0

    def generate_nodes(self, n=50, seed=None):
        """
        Generate random node positions in the area.

        Args:
            n (int): Number of nodes.
            seed (int, optional): Random seed.

        Returns:
            numpy.ndarray: (n, 2) array of coordinates.
        """
        if seed is not None:
            np.random.seed(seed)
        return np.random.uniform(0, self.area_km, (n, 2))

    def create_mesh(self, coords):
        """
        Create a mesh graph from node coordinates.

        Args:
            coords (numpy.ndarray): Node coordinates.

        Returns:
            networkx.Graph: Graph with edges based on range.
        """
        G = nx.Graph()
        n = len(coords)
        for i, (x, y) in enumerate(coords):
            G.add_node(i, pos=(x, y))
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist <= self.range_km:
                    G.add_edge(i, j, weight=dist)
        return G

    def simulate_with_energy(self, n_nodes=50, failure_rate=0.0, hours=200, has_solar=True, seed=None):
        """
        Simulate network with energy model and AODV routing.

        Args:
            n_nodes (int): Number of nodes.
            failure_rate (float): Node failure rate.
            hours (int): Simulation hours.
            has_solar (bool): Whether nodes have solar harvesting.
            seed (int, optional): Random seed.

        Returns:
            list: Number of alive nodes per hour.
        """
        coords = self.generate_nodes(n_nodes, seed=seed)
        G = self.create_mesh(coords)

        energies = {}
        for i in range(n_nodes):
            base_capacity = 2000
            variation = np.random.uniform(0.8, 1.2)
            energies[i] = EnergyModel(battery_capacity=base_capacity * variation)

        alive_over_time = []
        for hour in range(hours):
            alive_nodes = []
            for node in range(n_nodes):
                if node != self.gateway_id:
                    tx_count = 0
                    if node in G.nodes and self.gateway_id in G.nodes:
                        router = AODVRouter(G)
                        result = router.send_packet(node, self.gateway_id, 'test')
                        tx_count = 1 if result['delivered'] else 0
                    if random.random() < 0.2:
                        tx_count += 1
                    energies[node].simulate_hour(has_solar=has_solar, transmission_count=tx_count)

                if energies[node].is_dead():
                    if node in G.nodes:
                        G.remove_node(node)
                else:
                    alive_nodes.append(node)

            alive_over_time.append(len(alive_nodes))
            if len(alive_nodes) < n_nodes * 0.1:
                break

        return alive_over_time

    def compare_lifetime(self, n_nodes=50, hours=200, seed=None):
        """
        Compare network lifetime with and without solar harvesting.

        Args:
            n_nodes (int): Number of nodes.
            hours (int): Maximum simulation hours.
            seed (int, optional): Random seed for reproducibility.

        Returns:
            dict: Contains 'time_hours', 'solarnode', 'random' lists.
        """
        solarnode_lifetime = self.simulate_with_energy(n_nodes, has_solar=True, hours=hours, seed=seed)
        random_lifetime = self.simulate_with_energy(n_nodes, has_solar=False, hours=hours, seed=None if seed is None else seed + 1)

        max_len = max(len(solarnode_lifetime), len(random_lifetime))
        solarnode_lifetime += [0] * (max_len - len(solarnode_lifetime))
        random_lifetime += [0] * (max_len - len(random_lifetime))

        return {
            'time_hours': list(range(max_len)),
            'solarnode': solarnode_lifetime,
            'random': random_lifetime
        }
