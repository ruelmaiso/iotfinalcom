# ESP32 Deployment Mode Integration

## Pin Mapping
| Function | GPIO |
|---|---|
| DS18B20 OneWire data | GPIO4 |
| Fan pulse PC01 | GPIO14 |
| Fan pulse PC02 | GPIO27 |

## Wiring Instructions
- DS18B20 bus: VDD -> 3.3V, GND -> GND, DATA -> GPIO4.
- Use a 4.7k pull-up resistor between DATA and 3.3V.
- Hall pulse outputs:
  - PC01 fan sensor -> GPIO14
  - PC02 fan sensor -> GPIO27
- Common ground is mandatory between sensors and ESP32.

## WiFi Configuration Steps
1. Set `WIFI_SSID` and `WIFI_PASS` in `esp32/esp32_deploy.ino`.
2. Set `TEACHER_IP` to teacher deployment host LAN address.
3. Keep UDP port `9202` synchronized with deployment settings.
4. Upload firmware and monitor serial output for STA connectivity.

## Sensor Mapping Logic
- DS18B20 sensors are discovered dynamically at runtime.
- Sequential mapping is enforced:
  - `sensor[0] -> PC01`
  - `sensor[1] -> PC02`
- If a sensor index is missing, temperature is sent as `null`.
- Fan pulse counters are sampled every cycle and reset after send.

## JSON Format Specification
```json
{
  "pc_id": "PC01",
  "temperature": 36.2,
  "fan_ok": true,
  "fan_rpm": 1400
}
```

## Deployment Notes
- Works LAN-only and does not require internet.
- Runs in STA mode and attempts WiFi reconnect continuously.
- Uses non-blocking `millis()` scheduling with 2-second telemetry interval.
- Router restart recovery is automatic through reconnect logic.

## Troubleshooting Guide
- No packets at teacher:
  - verify teacher IP and UDP port 9202
  - verify same subnet and firewall rules
- Missing temperatures:
  - verify DS18B20 bus wiring and pull-up resistor
  - check sensor count and physical bus integrity
- RPM always zero:
  - verify hall sensor output voltage compatibility
  - verify pulse edge configuration and fan activity
