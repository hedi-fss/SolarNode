"""5G/6G NTN and D2D Simulation Service"""
import random


class FiveGService:
    def __init__(self):
        self.ntn_active = True
        self.d2d_active = True
        self.isac_active = True
        self.satellites = [
            {"id": "LEO-1", "latency": 50, "throughput": 100},
            {"id": "LEO-2", "latency": 45, "throughput": 120},
            {"id": "GEO-1", "latency": 600, "throughput": 50}
        ]
        self.current_satellite = self.satellites[0]

    def get_ntn_status(self):
        """Simulate NTN (satellite) connection status"""
        # Simulate occasional outages (5% chance)
        if random.random() < 0.05:
            return {
                "status": "DEGRADED",
                "latency": self.current_satellite["latency"] * 3,
                "throughput": self.current_satellite["throughput"] * 0.3,
                "message": "Signal interference detected"
            }
        return {
            "status": "CONNECTED",
            "latency": self.current_satellite["latency"] + random.randint(-10, 10),
            "throughput": self.current_satellite["throughput"] + random.randint(-20, 20),
            "message": "Normal operation"
        }

    def simulate_isac(self, nodes_active):
        """
        Integrated Sensing and Communication:
        Detect survivors based on node activity and sensor simulation.
        """
        survivors = []
        for node_id in range(nodes_active):
            # Simulate sensor detection: random chance a survivor is near a
            # node
            if random.random() < 0.15:  # 15% chance per node
                survivors.append({
                    "node_id": node_id,
                    "confidence": round(random.uniform(0.6, 0.99), 2),
                    "type": random.choice(["person", "group", "animal"]),
                    "location": {
                        "lat": random.uniform(-90, 90),
                        "lon": random.uniform(-180, 180)
                    }
                })
        return survivors

    def simulate_d2d(self, nodes, failure_rate):
        """
        Device-to-Device communication: nodes can relay messages directly.
        Returns: number of direct D2D links established.
        """
        d2d_links = 0
        for i in range(nodes):
            for j in range(i + 1, nodes):
                # D2D link probability: depends on distance (simulated)
                if random.random() < 0.3:  # 30% chance
                    d2d_links += 1
        # Failure rate reduces D2D links
        d2d_links = int(d2d_links * (1 - failure_rate))
        return max(0, d2d_links)
