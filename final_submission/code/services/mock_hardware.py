"""Mock Hardware Data Generator (For testing without ESP32)"""
import random
import threading
import time
from datetime import datetime
from flask import current_app
from app import db, socketio
from app.models import Telemetry, Node

class MockHardware:
    def __init__(self):
        self.running = False
        self.thread = None
        self.nodes = 50
        self.interval = 5  # seconds
        self.app = None

    def start(self, app=None):
        """Start generating mock data with app context."""
        if self.running:
            return
        if app is None:
            # Try to get the app from current_app if available
            self.app = current_app._get_current_object()
        else:
            self.app = app
        if self.app is None:
            print("❌ Cannot start mock hardware: no app context")
            return
        self.running = True
        self.thread = threading.Thread(target=self._generate_loop, daemon=True)
        self.thread.start()
        print(f"✅ Mock hardware started ({self.nodes} nodes, {self.interval}s interval)")

    def stop(self):
        """Stop generating mock data."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("✅ Mock hardware stopped")

    def _generate_loop(self):
        """Generate mock data in a loop."""
        while self.running:
            try:
                if self.app is None:
                    break
                with self.app.app_context():
                    node_id = random.randint(0, self.nodes - 1)

                    battery = random.uniform(20, 100)
                    temperature = random.uniform(15, 45)
                    humidity = random.uniform(30, 80)
                    lat = random.uniform(36.5, 37.5)
                    lon = random.uniform(9.5, 10.5)
                    is_alert = random.random() < 0.1

                    telemetry = Telemetry(
                        node_id=node_id,
                        timestamp=datetime.utcnow(),
                        battery=battery,
                        temperature=temperature,
                        humidity=humidity,
                        latitude=lat,
                        longitude=lon,
                        altitude=random.uniform(0, 100),
                        packet_type='alert' if is_alert else 'telemetry',
                        hop_count=random.randint(0, 5)
                    )
                    db.session.add(telemetry)
                    db.session.commit()

                    socketio.emit('telemetry_update', {
                        'node_id': node_id,
                        'type': 'alert' if is_alert else 'telemetry',
                        'data': {
                            'battery': battery,
                            'temp': temperature,
                            'humidity': humidity,
                            'lat': lat,
                            'lon': lon
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    })

                    node = Node.query.filter_by(node_id=node_id).first()
                    if node:
                        node.last_seen = datetime.utcnow()
                        node.battery_level = battery
                        db.session.commit()
                    else:
                        new_node = Node(
                            node_id=node_id,
                            is_active=True,
                            battery_level=battery,
                            last_seen=datetime.utcnow()
                        )
                        db.session.add(new_node)
                        db.session.commit()

                    if is_alert:
                        socketio.emit('alert', {
                            'node_id': node_id,
                            'message': f"🚨 MOCK ALERT from Node {node_id}",
                            'gps': {'lat': lat, 'lon': lon}
                        })
            except Exception as e:
                print(f"❌ Mock hardware error: {e}")
            time.sleep(self.interval)

    def set_nodes(self, count):
        self.nodes = count

    def set_interval(self, seconds):
        self.interval = seconds

# Global instance
mock_hardware = MockHardware()
