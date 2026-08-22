#!/usr/bin/env python3
import unittest
from datetime import datetime

from app import create_app, db
from app.models.telemetry import Telemetry
from config import config as app_config


class TestTelemetryLatestEndpoint(unittest.TestCase):
    def setUp(self):
        self.original_uri = app_config.SQLALCHEMY_DATABASE_URI
        app_config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        app_config.SQLALCHEMY_DATABASE_URI = self.original_uri

    def test_latest_endpoint_returns_json_when_no_data(self):
        resp = self.client.get("/telemetry/latest")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        self.assertEqual(resp.get_json().get("data"), None)

    def test_latest_endpoint_compat_api_prefix(self):
        resp = self.client.get("/api/telemetry/latest")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)

    def test_latest_endpoint_returns_latest_record(self):
        with self.app.app_context():
            db.create_all()
            older = Telemetry(node_id=1, timestamp=datetime(2024, 1, 1))
            latest = Telemetry(node_id=2, timestamp=datetime(2024, 1, 2))
            db.session.add_all([older, latest])
            db.session.commit()

        resp = self.client.get("/telemetry/latest")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload["node_id"], 2)


if __name__ == "__main__":
    unittest.main()
