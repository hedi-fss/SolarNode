#!/usr/bin/env python3
"""Verify mock hardware data generation and ingestion."""
import requests
import time
import json

BASE_URL = "http://localhost:5001"

def test_mock_start():
    print("Starting mock hardware...")
    resp = requests.post(f"{BASE_URL}/api/hardware/mock/start",
                         json={"nodes": 20, "interval": 2})
    if resp.status_code == 200:
        print("✅ Mock started")
    else:
        print(f"❌ Mock start failed: {resp.status_code}")

def test_mock_status():
    print("Checking mock status...")
    resp = requests.get(f"{BASE_URL}/api/hardware/status")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Mock running: {data.get('mock_running')}")
        print(f"   Nodes: {data.get('mock_nodes')}")
        print(f"   Interval: {data.get('mock_interval')}")
    else:
        print(f"❌ Status failed: {resp.status_code}")

def test_telemetry():
    print("Fetching latest telemetry...")
    resp = requests.get(f"{BASE_URL}/api/telemetry/latest")
    if resp.status_code == 200:
        data = resp.json()
        if data.get('node_id') is not None:
            print(f"✅ Telemetry received: Node {data['node_id']}, Battery {data.get('battery')}")
        else:
            print("❌ No telemetry data")
    else:
        print(f"❌ Telemetry failed: {resp.status_code}")

def test_anomalies():
    print("Fetching anomalies...")
    resp = requests.get(f"{BASE_URL}/ml/anomalies?limit=10")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Anomalies: {len(data.get('anomalies', []))} detected")
    else:
        print(f"❌ Anomalies failed: {resp.status_code}")

def test_stop_mock():
    print("Stopping mock...")
    resp = requests.post(f"{BASE_URL}/api/hardware/mock/stop")
    if resp.status_code == 200:
        print("✅ Mock stopped")
    else:
        print(f"❌ Stop failed: {resp.status_code}")

if __name__ == "__main__":
    test_mock_start()
    time.sleep(3)
    test_mock_status()
    test_telemetry()
    test_anomalies()
    test_stop_mock()
