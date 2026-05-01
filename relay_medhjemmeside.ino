#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

#define RELAY_PIN 33

const char* ssid = "moto g62 5G_5930";
const char* password = "fjk4h43rwrpd344";

// Din server
String server = "https://ramsen0004.pythonanywhere.com/status";

WiFiClientSecure client;

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  WiFi.begin(ssid, password);

  Serial.print("Forbinder til WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi forbundet!");
  Serial.println(WiFi.localIP());

  client.setInsecure();
}

void loop() {

  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;

    http.begin(client, server);

    int code = http.GET();

    if (code == 200) {

      String payload = http.getString();
      Serial.println("Server svar: " + payload);

      if (payload.indexOf("\"pump\":true") != -1) {
        digitalWrite(RELAY_PIN, HIGH);
        Serial.println("RELAY ON");
      } else {
        digitalWrite(RELAY_PIN, LOW);
        Serial.println("RELAY OFF");
      }

    } else {
      Serial.println("HTTP fejl: " + String(code));
    }

    http.end();

  } else {
    Serial.println("WiFi mistet!");
  }

  delay(5000); // lidt mere stabil
}