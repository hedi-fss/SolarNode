"""Database Models"""
from app import db
from datetime import datetime


class Telemetry(db.Model):
    __tablename__ = 'telemetry'
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    altitude = db.Column(db.Float)
    battery = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light = db.Column(db.Float)
    packet_type = db.Column(db.String(20))
    hop_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'battery': self.battery,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'light': self.light,
            'packet_type': self.packet_type,
            'hop_count': self.hop_count
        }


class Node(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, unique=True, nullable=False)
    is_gateway = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    battery_level = db.Column(db.Float, default=100.0)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    x_position = db.Column(db.Float)
    y_position = db.Column(db.Float)

    def to_dict(self):
        return {
            'id': self.id,
            'node_id': self.node_id,
            'is_gateway': self.is_gateway,
            'is_active': self.is_active,
            'battery_level': self.battery_level,
            'last_seen': self.last_seen.isoformat(),
            'x': self.x_position,
            'y': self.y_position
        }


class NetworkStats(db.Model):
    __tablename__ = 'network_stats'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total_nodes = db.Column(db.Integer)
    active_nodes = db.Column(db.Integer)
    total_edges = db.Column(db.Integer)
    pdr = db.Column(db.Float)
    avg_latency = db.Column(db.Float)
    network_lifetime = db.Column(db.Float)

    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_nodes': self.total_nodes,
            'active_nodes': self.active_nodes,
            'total_edges': self.total_edges,
            'pdr': self.pdr,
            'avg_latency': self.avg_latency,
            'network_lifetime': self.network_lifetime
        }
