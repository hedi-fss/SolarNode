# SolarNode Hardware Test Plan

## Pre-Test Checklist
- [ ] ESP32 board connected via USB
- [ ] LoRa module connected (CS=5, RST=14, DIO0=2)
- [ ] GPS module connected (RX=4, TX=15)
- [ ] Solar panel connected (5V)
- [ ] Battery connected (3.7V Li-ion)
- [ ] Serial monitor open (115200 baud)
- [ ] Flask server running on port 5001

## Test 1: Serial Communication
**Objective:** Verify ESP32 ↔ Flask communication.
**Procedure:**
1. Connect ESP32 via USB.
2. Run `python run.py` (server).
3. Click "Connect" on the dashboard.
4. Verify telemetry appears in the database.

**Expected:** Serial connection established, telemetry data visible in dashboard.

## Test 2: LoRa Range
**Objective:** Measure effective communication range.
**Procedure:**
1. Deploy 2 nodes at increasing distances (100m, 500m, 1km, 2km).
2. Send test packets and record RSSI and PDR.

**Expected:** RSSI > -100 dBm at 500m, PDR > 90%.

## Test 3: GPS Accuracy
**Objective:** Verify GPS positioning.
**Procedure:**
1. Place node outdoors with clear sky.
2. Record GPS coordinates for 5 minutes.
3. Compare with known location.

**Expected:** Accuracy < 5m, fix time < 60s.

## Test 4: Solar/Battery Performance
**Objective:** Validate energy harvesting and battery life.
**Procedure:**
1. Place node in sunlight.
2. Monitor battery voltage over 12 hours.
3. Calculate charging efficiency.

**Expected:** Battery >80%, solar charging >100mA.

## Test 5: End-to-End Integration
**Objective:** Verify complete system.
**Procedure:**
1. Deploy 10 nodes.
2. Send alerts from multiple nodes.
3. Verify dashboard updates, alerts, and survivor detection.

**Expected:** All nodes visible, alerts within 2 seconds, ISAC detects survivors.

## Troubleshooting
- If serial fails: check USB cable, port permissions (`sudo chmod 666 /dev/ttyUSB0`).
- If LoRa fails: verify antenna connection, frequency settings.
- If GPS fails: ensure clear sky, wait for fix.
