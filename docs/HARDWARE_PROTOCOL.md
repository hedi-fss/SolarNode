# SolarNode Hardware-Software Interface Protocol

## Communication Overview

ESP32 nodes communicate with the Flask backend via **serial (USB)** for local testing and **WiFi/MQTT** for production.

### Serial Protocol (USB)

| Field | Bytes | Description |
|-------|-------|-------------|
| START | 1 | 0xAA (header) |
| NODE_ID | 2 | Node identifier (0-65535) |
| TYPE | 1 | 0x01=telemetry, 0x02=GPS, 0x03=alert, 0x04=status |
| LENGTH | 2 | Payload length (big-endian) |
| PAYLOAD | Variable | JSON or binary data |
| CHECKSUM | 2 | CRC16 |
| END | 1 | 0xBB (footer) |

### Packet Types

| Type | Value | Payload Format |
|------|-------|----------------|
| Telemetry | 0x01 | `{"battery":85,"temp":32,"humidity":60}` |
| GPS | 0x02 | `{"lat":36.8,"lon":10.2,"alt":50}` |
| Alert | 0x03 | `{"type":"panic","gps":{"lat":36.8,"lon":10.2}}` |
| Status | 0x04 | `{"status":"active","uptime":3600}` |

### Example Serial Packet
AA 00 01 01 00 1C {"battery":85,"temp":32} 12 34 BB
│ │ │ │ │ │ │ │ │
│ │ │ │ │ │ │ │ └─ END
│ │ │ │ │ │ │ └─ CRC16
│ │ │ │ │ │ └─ Payload
│ │ │ │ │ └─ LENGTH (28 bytes)
│ │ │ │ └─ TYPE (Telemetry)
│ │ │ └─ NODE_ID (1)
│ │ └─ START
│ └─ NODE_ID
└─ START
## WiFi/MQTT Protocol

| Topic | Format | Description |
|-------|--------|-------------|
| `solarnode/{node_id}/telemetry` | JSON | Battery, temp, humidity |
| `solarnode/{node_id}/gps` | JSON | GPS coordinates |
| `solarnode/{node_id}/alert` | JSON | Panic alerts |
| `solarnode/{node_id}/config` | JSON | Configuration updates |
| `solarnode/gateway` | JSON | Gateway aggregated data |

## Endpoint Mapping

| Source | Backend Endpoint |
|--------|------------------|
| Serial | `/api/hardware/serial` |
| MQTT | `/api/hardware/mqtt` |
| HTTP | `/api/hardware/ingest` |
