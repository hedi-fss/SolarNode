import os
import sqlite3
import tempfile
import unittest

from app import create_app
from config import config


class TelemetrySchemaCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self._original_db_uri = config.SQLALCHEMY_DATABASE_URI
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._tmp_dir.name, "legacy.db")
        config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self._db_path}"

    def tearDown(self):
        config.SQLALCHEMY_DATABASE_URI = self._original_db_uri
        self._tmp_dir.cleanup()

    def test_latest_endpoint_works_with_legacy_telemetry_schema(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE telemetry (
                    node_id INTEGER,
                    timestamp DATETIME,
                    latitude FLOAT,
                    longitude FLOAT,
                    altitude FLOAT,
                    battery FLOAT,
                    temperature FLOAT,
                    humidity FLOAT,
                    packet_type VARCHAR(20),
                    hop_count INTEGER
                )
                """
            )
            conn.execute(
                """
                INSERT INTO telemetry (
                    node_id, timestamp, latitude, longitude, altitude, battery,
                    temperature, humidity, packet_type, hop_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (7, "2026-01-01 00:00:00", 36.8, 10.1, 12.0, 75.0, 29.0, 41.0, "telemetry", 1),
            )
            conn.commit()

        app = create_app()
        client = app.test_client()
        response = client.get("/telemetry/latest")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["node_id"], 7)
        self.assertIn("id", payload)

        with sqlite3.connect(self._db_path) as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(telemetry)").fetchall()]
        self.assertIn("id", columns)

    def test_latest_endpoint_on_fresh_database_returns_not_found(self):
        app = create_app()
        client = app.test_client()
        response = client.get("/telemetry/latest")

        self.assertEqual(response.status_code, 404)
        payload = response.get_json()
        self.assertEqual(payload.get("error"), "No telemetry data found")


if __name__ == "__main__":
    unittest.main()
