#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <WiFi.h>
#include <PubSubClient.h>

// Nombre y dirección MAC
const char* nombreDispositivo = "S5-5bc02";
const char* macDispositivo = "41:05:07:6A:BC:02";

// Wi-Fi
const char* ssid = "AulaNautica";
const char* password = "XicxetS4";

// MQTT
const char* mqtt_broker = "mqtt.eclipseprojects.io";
const int mqtt_port = 1883;
const char* mqtt_device_id = "A0001";  // Valor fijo de A0001

// Cliente WiFi y cliente MQTT
WiFiClient espClient;
PubSubClient client(espClient);

// Variable para controlar el escaneo BLE
BLEScan* pBLEScan;

// Función para convertir manufacturerData a una cadena hexadecimal
String dataToHexString(std::string data) {
  String hexString = "";
  for (size_t i = 0; i < data.length(); i++) {
    char hex[3];
    sprintf(hex, "%02X", (unsigned char)data[i]);
    hexString += hex;
  }
  return hexString;
}

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    // Verificar si el dispositivo encontrado coincide con el nombre o la dirección MAC
    if (advertisedDevice.getName() == nombreDispositivo || advertisedDevice.getAddress().toString() == macDispositivo) {
      Serial.println("¡Device found!");
      Serial.print("Name: ");
      Serial.println(advertisedDevice.getName().c_str());
      Serial.print("MAC Address: ");
      Serial.println(advertisedDevice.getAddress().toString().c_str());

      // Obtener manufacturer data si existe
      std::string manufacturerData = advertisedDevice.getManufacturerData();
      if (manufacturerData.empty()) {
        manufacturerData = "Manufacturer data not found";
      }

      // Convertir manufacturerData a una cadena hexadecimal
      String manufacturerDataHex = dataToHexString(manufacturerData);

      // Imprimir el manufacturer data en el monitor serial
      Serial.print("Manufacturer Data (Hex): ");
      Serial.println(manufacturerDataHex);

      // Verificar si manufacturerDataHex comienza con "0002AAEE"
      if (manufacturerDataHex.startsWith("0002AAEE")) {
        // Preparar el topic para el mensaje MQTT en formato pulsus/{A0001}/{Nombre}/metrics
        char mqtt_topic[256];
        snprintf(mqtt_topic, sizeof(mqtt_topic), "pulsus/%s/%s/metrics", mqtt_device_id, advertisedDevice.getName().c_str());

        // Publicar el manufacturerDataHex como mensaje en el topic MQTT
        Serial.print("Publishing to topic: ");
        Serial.println(mqtt_topic);
        if (client.publish(mqtt_topic, manufacturerDataHex.c_str())) {
          Serial.println("Publish success!");
        } else {
          Serial.println("Publish failed!");
        }
      } else {
        Serial.println("Manufacturer Data does not start with '0002AAEE', skipping...");
      }

      // Imprimir todos los detalles del dispositivo
      Serial.println("Device details:");
      Serial.println(advertisedDevice.toString().c_str());

      // Detener el escaneo una vez que se encuentra el dispositivo
      pBLEScan->stop();
    }
  }
};

// Conectar a Wi-Fi
void connectWiFi() {
  Serial.println("Connecting to Wi-Fi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting...");
  }
  Serial.println("Wi-Fi connected.");
}

// Conectar a MQTT Broker
void connectMQTT() {
  client.setServer(mqtt_broker, mqtt_port);
  Serial.println("Connecting to MQTT broker...");
  while (!client.connected()) {
    if (client.connect("ArduinoNanoESP32")) {
      Serial.println("Connected to MQTT broker.");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE SCAN...");

  // Conectar a Wi-Fi
  connectWiFi();

  // Conectar a MQTT
  connectMQTT();

  // Inicializar el dispositivo BLE
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();  // Crear objeto de escaneo
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setInterval(1000);  // Intervalo de escaneo
  pBLEScan->setWindow(999);     // Tiempo de ventana de escaneo
  pBLEScan->setActiveScan(true); // Escaneo activo, busca respuestas
}

void loop() {
  // Mantener la conexión MQTT
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();

  // Inicia un escaneo de 5 segundos
  BLEScanResults foundDevices = pBLEScan->start(5, false);
  Serial.print("Devices found: ");
  Serial.println(foundDevices.getCount());
  Serial.println("SCAN ENDED.");
  delay(2000); // Esperar 2 segundos antes de escanear de nuevo
}
