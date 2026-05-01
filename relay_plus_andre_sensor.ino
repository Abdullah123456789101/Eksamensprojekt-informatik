#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

#define RELAY_PIN 33
#define DHTPIN 22
#define DHTTYPE DHT11
#define SOIL_PIN 34

const char* ssid = "moto g62 5G_5930";
const char* password = "fjk4h43rwrpd344";

String sensorServer = "https://ramsen0004.pythonanywhere.com/api/sensor";
String statusServer = "https://ramsen0004.pythonanywhere.com/status";

WiFiClientSecure client;
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  dht.begin();

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi forbundet!");
  client.setInsecure();
}

void loop() {

  if (WiFi.status() == WL_CONNECTED) {

    // ----------------------------
    // 1. LÆS SENSORER
    // ----------------------------
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    int soilRaw = analogRead(SOIL_PIN);

    int soil = map(soilRaw, 4095, 1500, 0, 100);
    soil = constrain(soil, 0, 100);

    if (!isnan(humidity) && !isnan(temperature)) {

      HTTPClient http;

      http.begin(client, sensorServer);
      http.addHeader("Content-Type", "application/json");

      String json = "{";
      json += "\"temperature\":" + String(temperature) + ",";
      json += "\"humidity\":" + String(humidity) + ",";
      json += "\"soil_moisture\":" + String(soil);
      json += "}";

      http.POST(json);
      http.end();
    }

    // ----------------------------
    // 2. HENT RELAY STATUS
    // ----------------------------
    HTTPClient http2;

    http2.begin(client, statusServer);
    int code = http2.GET();

    if (code == 200) {

      String payload = http2.getString();
      Serial.println("Status: " + payload);

      bool pumpOn = payload.indexOf("\"pump\":true") != -1;

      if (pumpOn) {
        digitalWrite(RELAY_PIN, HIGH);
        Serial.println("RELAY ON");
      } else {
        digitalWrite(RELAY_PIN, LOW);
        Serial.println("RELAY OFF");
      }

    } else {
      Serial.println("Status fejl: " + String(code));
    }

    http2.end();
  }

  delay(5000);
}