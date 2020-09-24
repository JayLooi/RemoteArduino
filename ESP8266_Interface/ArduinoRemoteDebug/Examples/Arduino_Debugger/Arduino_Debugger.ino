#define DEVICEID    Arduino-1         // Change to a custom id for your deivce, if not define, DEVICEID will be defaulted as Unknown
#include "ArduinoRemoteDebug.h"

#define ssid              "<WiFi-SSID>"
#define password          "<WiFi-Password>"
#define mqtt_server       "<MQTT-Server>"
#define mqtt_username     "<MQTT-Username>"
#define mqtt_password     "<MQTT-Password>"
#define TX                tx
#define RX                rx
#define tx_topic          CREATE_TOPIC(DEVICEID, TX)       // Output: "<DEVICEID>/<TX>"
#define rx_topic          CREATE_TOPIC(DEVICEID, RX)       // Output: "<DEVICEID>/<RX>"

#define IND_LED       <Digital-Pin-Num-For-Indicator-LED>
#define RESET_PIN     <Digital-Pin-Num-For-Reset>

WiFiClient espClient;
ArduinoRemoteDebug ArduinoDebugger(&espClient, RESET_PIN, IND_LED);

void wifiSetup() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while(WiFi.status() != WL_CONNECTED) {
    digitalWrite(IND_LED, HIGH);
    delay(200);
    digitalWrite(IND_LED, LOW);
    delay(200);
  }
}

void setup() {
  wifiSetup();
  ArduinoDebugger.setServer(mqtt_server, 1883);
  ArduinoDebugger.setMQTTCallback();
  ArduinoDebugger.setUsername(mqtt_username);
  ArduinoDebugger.setPassword(mqtt_password);
  ArduinoDebugger.setTxTopic(tx_topic);
  ArduinoDebugger.setRxTopic(rx_topic);
  ArduinoDebugger.setReadTimeout(500);
}

void loop() {
  ArduinoDebugger.clientLoop();
}
