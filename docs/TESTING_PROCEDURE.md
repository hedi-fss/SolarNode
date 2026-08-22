# SolarNode Hardware Testing Procedure

## Pre-Test Checklist

- [ ] ESP32 board connected via USB
- [ ] LoRa module connected (CS=5, RST=14, DIO0=2)
- [ ] GPS module connected (RX=4, TX=15)
- [ ] Solar panel connected (5V)
- [ ] Battery connected (3.7V Li-ion)
- [ ] Serial monitor open (115200 baud)

## Test 1: Serial Communication

**Objective:** Verify ESP32 → Flask serial communication

**Procedure:**
1. Connect ESP32 via USB
2. Start Flask server
3. Call `/api/hardware/connect`
4. Verify telemetry appears in dashboard

**Expected Results:**
- Serial connection established
- Telemetry data appears in database
- Dashboard updates in real-time

## Test 2: LoRa Communication

**Objective:** Verify LoRa range and reliability

**Procedure:**
1. Deploy 2 nodes 100m apart
2. Send test packets
3. Record RSSI and packet delivery

**Expected Results:**
- RSSI > -100 dBm at 100m
- PDR > 95%

## Test 3: GPS Accuracy

**Objective:** Verify GPS positioning accuracy

**Procedure:**
1. Place node outside with clear sky view
2. Record GPS coordinates
3. Compare with known location

**Expected Results:**
- Accuracy < 5m
- Fix time < 60s

## Test 4: Solar/Battery

**Objective:** Verify solar charging and battery life

**Procedure:**
1. Place node in sunlight
2. Monitor battery voltage over 24 hours
3. Calculate charging efficiency

**Expected Results:**
- Battery maintains > 80%
- Solar charging > 100mA

## Test 5: End-to-End Integration

**Objective:** Verify complete system

**Procedure:**
1. Deploy 10 nodes
2. Send alerts from multiple nodes
3. Verify dashboard shows all data
4. Verify alert notifications

**Expected Results:**
- All nodes visible on dashboard
- Alerts appear within 2 seconds
- Survivor detection works
