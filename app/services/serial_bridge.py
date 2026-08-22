"""Serial Bridge for ESP32 Communication"""
import json
import threading
import time
from datetime import datetime
from app import db, socketio
from app.models import Telemetry, Node

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("⚠️ pyserial not installed. Serial bridge will be disabled.")

class SerialBridge:
    def __init__(self, port=None, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.thread = None
        self.callbacks = []

    def find_port(self):
        """Auto-detect ESP32 serial port."""
        if not SERIAL_AVAILABLE:
            return None
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB" in port.description or "CP210" in port.description or "CH340" in port.description:
                return port.device
        return None

    def connect(self, port=None):
        """Connect to ESP32 via serial."""
        if not SERIAL_AVAILABLE:
            print("❌ pyserial not installed")
            return False
        if port is None:
            port = self.find_port()
        if port is None:
            print("❌ No ESP32 serial port found")
            return False

        try:
            self.serial_conn = serial.Serial(port, self.baudrate, timeout=1)
            print(f"✅ Connected to ESP32 on {port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def start(self):
        """Start reading serial data."""
        if not SERIAL_AVAILABLE:
            print("❌ Cannot start serial bridge: pyserial not installed")
            return False
        if self.serial_conn is None:
            if not self.connect():
                return False

        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        print("✅ Serial bridge started")
        return True

    def stop(self):
        """Stop reading serial data."""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
        print("✅ Serial bridge stopped")

    def _read_loop(self):
        """Read and parse serial data."""
        buffer = bytearray()

        while self.running:
            if self.serial_conn and self.serial_conn.in_waiting:
                data = self.serial_conn.read(self.serial_conn.in_waiting)
                buffer.extend(data)

                while len(buffer) >= 8:
                    if buffer[0] != 0xAA:
                        buffer.pop(0)
                        continue

                    if len(buffer) < 8:
                        break

                    length = (buffer[5] << 8) | buffer[6]

                    if len(buffer) < 8 + length + 3:
                        break

                    node_id = (buffer[1] << 8) | buffer[2]
                    packet_type = buffer[3]
                    payload_bytes = buffer[7:7 + length]

                    try:
                        payload = json.loads(payload_bytes.decode('utf-8'))
                        self._process_packet(node_id, packet_type, payload)
                    except Exception as e:
                        print(f"❌ Parse error: {e}")

                    buffer = buffer[7 + length + 3:]

            time.sleep(0.01)

    def _process_packet(self, node_id, packet_type, payload):
        """Process incoming serial packet and store in database."""
        type_map = {
            0x01: 'telemetry',
            0x02: 'gps',
            0x03: 'alert',
            0x04: 'status'
        }
        packet_type_str = type_map.get(packet_type, 'unknown')

        print(f"📡 Node {node_id}: {packet_type_str} - {payload}")

        with db.app.app_context():
            telemetry = Telemetry(
                node_id=node_id,
                timestamp=datetime.utcnow(),
                battery=payload.get('battery', 0),
                temperature=payload.get('temp', 0),
                humidity=payload.get('humidity', 0),
                latitude=payload.get('lat', 0),
                longitude=payload.get('lon', 0),
                altitude=payload.get('alt', 0),
                packet_type=packet_type_str,
                hop_count=payload.get('hop_count', 0)
            )
            db.session.add(telemetry)
            db.session.commit()

        socketio.emit('telemetry_update', {
            'node_id': node_id,
            'type': packet_type_str,
            'data': payload,
            'timestamp': datetime.utcnow().isoformat()
        })

        if packet_type_str == 'alert':
            socketio.emit('alert', {
                'node_id': node_id,
                'message': f"🚨 PANIC BUTTON from Node {node_id}",
                'gps': {'lat': payload.get('lat', 0), 'lon': payload.get('lon', 0)}
            })

        with db.app.app_context():
            node = Node.query.filter_by(node_id=node_id).first()
            if node:
                node.last_seen = datetime.utcnow()
                node.battery_level = payload.get('battery', 100)
                db.session.commit()
            else:
                new_node = Node(
                    node_id=node_id,
                    is_active=True,
                    battery_level=payload.get('battery', 100),
                    last_seen=datetime.utcnow()
                )
                db.session.add(new_node)
                db.session.commit()

        for callback in self.callbacks:
            try:
                callback(node_id, packet_type_str, payload)
            except Exception as e:
                print(f"❌ Callback error: {e}")

    def add_callback(self, callback):
        """Add callback for incoming packets."""
        self.callbacks.append(callback)
        print(f"✅ Callback added (total: {len(self.callbacks)})")

    def send_command(self, command):
        """Send command to ESP32."""
        if self.serial_conn:
            self.serial_conn.write((command + '\n').encode())
            print(f"📤 Sent command: {command}")
            return True
        return False

# Global instance
serial_bridge = SerialBridge()
