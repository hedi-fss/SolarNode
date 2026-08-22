"""AODV Routing Protocol Simulation"""
import networkx as nx


class AODVRouter:
    def __init__(self, graph):
        self.graph = graph
        self.routing_tables = {node: {} for node in graph.nodes()}
        self.seq_numbers = {node: 0 for node in graph.nodes()}

    def route_discovery(self, src, dst):
        """Find path using AODV-like discovery"""
        if src == dst:
            return [src]

        try:
            # Use shortest path as AODV approximation
            path = nx.shortest_path(self.graph, src, dst, weight='weight')
            return path
        except nx.NetworkXNoPath:
            return None

    def send_packet(self, src, dst, payload):
        """Send packet using AODV routing"""
        path = self.route_discovery(src, dst)
        if path:
            # Simulate packet forwarding
            for node in path:
                self.seq_numbers[node] += 1
            return {'path': path, 'hops': len(path) - 1, 'delivered': True}
        return {'delivered': False, 'hops': None}
