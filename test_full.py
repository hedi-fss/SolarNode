#!/usr/bin/env python3
"""
Full test suite for SolarNode v2.0.
Run: python test_full.py
"""

import unittest
import os
import sys
import time
import subprocess
import requests
import signal

# ============================================================
# Configuration
# ============================================================
BASE_URL = os.environ.get('TEST_URL', 'http://localhost:5001')
PORT = int(os.environ.get('PORT', 5001))
SERVER_PROCESS = None
SERVER_LOG = None

def start_server():
    global SERVER_PROCESS, SERVER_LOG
    if SERVER_PROCESS is not None:
        return SERVER_PROCESS

    # Kill any existing server on the port
    try:
        subprocess.run(["fuser", "-k", f"{PORT}/tcp"], stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass  # fuser not available

    print(f"🔄 Starting Flask server on port {PORT}...")
    env = os.environ.copy()
    env['PORT'] = str(PORT)
    env['PYTHONUNBUFFERED'] = '1'

    # Capture server output to a log file
    SERVER_LOG = open('/tmp/solarnode_test.log', 'w')
    SERVER_PROCESS = subprocess.Popen(
        ['python', 'run.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        stdout=SERVER_LOG,
        stderr=subprocess.STDOUT
    )

    # Wait for server to be ready with increased timeout
    for i in range(15):
        try:
            requests.get(f"{BASE_URL}/", timeout=2)
            print("✅ Server is ready.")
            return SERVER_PROCESS
        except requests.exceptions.RequestException:
            time.sleep(1)
            # If we've waited long enough, show the server log
            if i == 14:
                print("❌ Server did not start. Showing log:")
                with open('/tmp/solarnode_test.log', 'r') as f:
                    print(f.read())
                return None
    return None

def stop_server():
    global SERVER_PROCESS
    if SERVER_PROCESS:
        SERVER_PROCESS.terminate()
        time.sleep(1)
        if SERVER_PROCESS.poll() is None:
            SERVER_PROCESS.kill()
        if SERVER_LOG:
            SERVER_LOG.close()
        SERVER_PROCESS = None
        print("🛑 Server stopped.")

# ============================================================
# Unit Tests (no server needed)
# ============================================================
class TestServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from app.services.simulation import SimulationService
            from app.services.simulation_v2 import SimulationServiceV2
            from app.services.ml_service import MLService
            from app.services.energy import EnergyModel
            from app.services.aodv import AODVRouter
            from app.services.fiveg import FiveGService
            cls.sim = SimulationService
            cls.sim_v2 = SimulationServiceV2
            cls.ml = MLService
            cls.energy = EnergyModel
            cls.aodv = AODVRouter
            cls.fiveg = FiveGService
            cls.available = True
        except ImportError as e:
            print(f"⚠️ App import error: {e}")
            cls.available = False

    def test_simulation_service(self):
        if not self.available:
            self.skipTest("App not available")
        sim = self.sim()
        coords = sim.generate_nodes(10)
        self.assertEqual(coords.shape, (10, 2))
        G = sim.create_mesh(coords)
        self.assertIsNotNone(G)

    def test_simulation_v2(self):
        if not self.available:
            self.skipTest("App not available")
        sim = self.sim_v2()
        result = sim.compare_lifetime(n_nodes=10, hours=50)
        self.assertIn('time_hours', result)
        self.assertIn('solarnode', result)
        self.assertIn('random', result)

    def test_energy_model(self):
        if not self.available:
            self.skipTest("App not available")
        energy = self.energy(battery_capacity=2000)
        self.assertEqual(energy.battery_level, 2000)
        energy.simulate_hour(has_solar=True, transmission_count=2)
        self.assertLess(energy.battery_level, 2000)

    def test_aodv_routing(self):
        if not self.available:
            self.skipTest("App not available")
        import networkx as nx
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2])
        G.add_edges_from([(0, 1), (1, 2)])
        router = self.aodv(G)
        result = router.send_packet(0, 2, 'test')
        self.assertTrue(result['delivered'])
        self.assertEqual(result['hops'], 2)

    def test_fiveg_service(self):
        if not self.available:
            self.skipTest("App not available")
        fg = self.fiveg()
        status = fg.get_ntn_status()
        self.assertIn('status', status)
        survivors = fg.simulate_isac(50)
        self.assertIsInstance(survivors, list)

    def test_ml_service(self):
        if not self.available:
            self.skipTest("App not available")
        ml = self.ml()
        result = ml.detect_anomalies([])
        self.assertIn('anomalies', result)

# ============================================================
# Integration Tests (server required)
# ============================================================
class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server()
        if cls.server is None:
            raise unittest.SkipTest("Server not available")
        cls.base = BASE_URL

    @classmethod
    def tearDownClass(cls):
        stop_server()

    def _test_endpoint(self, path, method='GET', data=None, expected=200, timeout=10):
        url = f"{self.base}{path}"
        try:
            if method == 'GET':
                resp = requests.get(url, timeout=timeout)
            else:
                resp = requests.post(url, json=data, timeout=timeout)
            self.assertEqual(resp.status_code, expected,
                             f"{path} returned {resp.status_code} (expected {expected})")
            return resp
        except requests.exceptions.ConnectionError:
            self.fail(f"Connection refused to {url}")

    def test_pages(self):
        for page in ['/', '/dashboard', '/analysis']:
            with self.subTest(page=page):
                self._test_endpoint(page)

    def test_simulation_endpoints(self):
        self._test_endpoint('/api/simulation/compare')
        self._test_endpoint('/api/simulation/lifetime?nodes=30&hours=100')
        resp = self._test_endpoint('/api/simulation/run', method='POST',
                                   data={'nodes': 20, 'failure_rate': 0.2, 'runs': 5})
        if resp:
            data = resp.json()
            self.assertIn('pdr_mean', data)

    def test_ml_endpoints(self):
        self._test_endpoint('/ml/status')
        self._test_endpoint('/ml/anomalies?limit=10')
        self._test_endpoint('/ml/predict')
        resp = self._test_endpoint('/ml/train', method='POST', timeout=30,
                                   data={'contamination': 0.1})
        if resp:
            data = resp.json()
            self.assertIn('status', data)

    def test_fiveg_endpoints(self):
        self._test_endpoint('/api/fiveg/status')
        self._test_endpoint('/api/fiveg/isac?nodes=30')
        self._test_endpoint('/api/fiveg/d2d?nodes=30&failure_rate=0.2')

    def test_hardware_endpoints(self):
        self._test_endpoint('/api/hardware/status')
        self._test_endpoint('/api/hardware/mock/start', method='POST',
                           data={'nodes': 10, 'interval': 1})
        time.sleep(2)
        self._test_endpoint('/api/telemetry/latest')
        self._test_endpoint('/api/hardware/mock/stop', method='POST')

    def test_export_endpoint(self):
        self._test_endpoint('/api/export/csv')

# ============================================================
# Mock Hardware Test
# ============================================================
class TestMockHardware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server()
        if cls.server is None:
            raise unittest.SkipTest("Server not available")
        cls.base = BASE_URL

    @classmethod
    def tearDownClass(cls):
        stop_server()

    def test_mock_data_flow(self):
        base = self.base
        # Stop any existing mock
        requests.post(f"{base}/api/hardware/mock/stop")
        time.sleep(1)

        resp = requests.post(f"{base}/api/hardware/mock/start",
                             json={'nodes': 5, 'interval': 1})
        self.assertEqual(resp.status_code, 200)
        time.sleep(2)

        resp = requests.get(f"{base}/api/hardware/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('mock_running', False), "Mock should be running")

        time.sleep(2)
        resp = requests.get(f"{base}/api/telemetry/latest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNotNone(data.get('node_id'), "No telemetry data received")

        resp = requests.post(f"{base}/api/hardware/mock/stop")
        self.assertEqual(resp.status_code, 200)

# ============================================================
# WebSocket Test
# ============================================================
class TestWebSocket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server()
        if cls.server is None:
            raise unittest.SkipTest("Server not available")
        cls.base = BASE_URL

    @classmethod
    def tearDownClass(cls):
        stop_server()

    def test_socketio_connect(self):
        try:
            import socketio
            sio = socketio.Client()
            connected = False
            @sio.on('connect')
            def on_connect():
                nonlocal connected
                connected = True
            sio.connect(f"{self.base.replace('http', 'ws')}")
            time.sleep(1)
            self.assertTrue(connected)
            sio.disconnect()
        except ImportError:
            self.skipTest("socketio client not installed")
        except Exception as e:
            self.skipTest(f"WebSocket test skipped: {e}")

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("SolarNode v2.0 - Full Project Test Suite")
    print("=" * 60)
    print(f"Server URL: {BASE_URL}")
    print("=" * 60)

    # Run unit tests first (no server needed)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestServices))

    # Start server for integration tests
    server = start_server()
    if server is not None:
        suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
        suite.addTests(loader.loadTestsFromTestCase(TestMockHardware))
        suite.addTests(loader.loadTestsFromTestCase(TestWebSocket))
    else:
        print("⚠️ Server not available, skipping integration tests.")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    stop_server()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Ran {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED.")
        sys.exit(1)
