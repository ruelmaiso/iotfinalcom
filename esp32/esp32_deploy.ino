#include <WiFi.h>
#include <WiFiUdp.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASS = "YOUR_PASSWORD";
const char* TEACHER_IP = "192.168.1.100";
const uint16_t TEACHER_PORT = 9202;

#define ONE_WIRE_PIN 4
#define FAN_PC01 14
#define FAN_PC02 27

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);
WiFiUDP udp;

DeviceAddress foundSensors[8];
uint8_t sensorCount = 0;

volatile uint32_t pulses1 = 0;
volatile uint32_t pulses2 = 0;

unsigned long lastTelemetryMs = 0;
const unsigned long TELEMETRY_INTERVAL_MS = 2000;

void IRAM_ATTR isr1() { pulses1++; }
void IRAM_ATTR isr2() { pulses2++; }

int rpmFromPulses(uint32_t pulses, float intervalSec) {
  float rev = pulses / 2.0f;
  return (int)((rev / intervalSec) * 60.0f);
}

void ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 5000) {
    delay(100);
  }
}

void discoverSensors() {
  sensorCount = 0;
  oneWire.reset_search();
  DeviceAddress addr;
  while (oneWire.search(addr) && sensorCount < 8) {
    memcpy(foundSensors[sensorCount], addr, sizeof(DeviceAddress));
    sensorCount++;
  }
}

float readTempByIndex(uint8_t idx) {
  if (idx >= sensorCount) return NAN;
  return sensors.getTempC(foundSensors[idx]);
}

void sendPayload(const char* pc, float temp, int rpm) {
  bool fan_ok = rpm > 0;
  char packet[200];
  if (isnan(temp)) {
    snprintf(packet, sizeof(packet),
             "{\"pc_id\":\"%s\",\"temperature\":null,\"fan_ok\":%s,\"fan_rpm\":%d}",
             pc, fan_ok ? "true" : "false", rpm);
  } else {
    snprintf(packet, sizeof(packet),
             "{\"pc_id\":\"%s\",\"temperature\":%.2f,\"fan_ok\":%s,\"fan_rpm\":%d}",
             pc, temp, fan_ok ? "true" : "false", rpm);
  }
  udp.beginPacket(TEACHER_IP, TEACHER_PORT);
  udp.write((const uint8_t*)packet, strlen(packet));
  udp.endPacket();
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  sensors.begin();
  discoverSensors();

  pinMode(FAN_PC01, INPUT_PULLUP);
  pinMode(FAN_PC02, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FAN_PC01), isr1, RISING);
  attachInterrupt(digitalPinToInterrupt(FAN_PC02), isr2, RISING);

  lastTelemetryMs = millis();
}

void loop() {
  ensureWiFi();

  unsigned long now = millis();
  if (now - lastTelemetryMs < TELEMETRY_INTERVAL_MS) {
    delay(5);
    return;
  }

  float intervalSec = (now - lastTelemetryMs) / 1000.0f;
  lastTelemetryMs = now;

  sensors.requestTemperatures();
  float t1 = readTempByIndex(0); // sensor[0] -> PC01
  float t2 = readTempByIndex(1); // sensor[1] -> PC02

  uint32_t p1 = pulses1;
  uint32_t p2 = pulses2;
  pulses1 = 0;
  pulses2 = 0;

  sendPayload("PC01", t1, rpmFromPulses(p1, intervalSec));
  sendPayload("PC02", t2, rpmFromPulses(p2, intervalSec));
}
