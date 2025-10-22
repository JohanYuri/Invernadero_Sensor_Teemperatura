#include <WiFi.h>
#include <WebServer.h>
// --- LIBRERÍAS PARA EL SENSOR DHT ---
#include <DHT.h>

// --- CONFIGURACIÓN DE LA RED WIFI ---
const char* ssid = "MEGACABLE-2.4G-E8AA_EXT";
const char* password = "pD9vzFKzK2";

// --- CONFIGURACIÓN DE PINES ---
#define DHTPIN 21       // Pin D21 para el sensor DHT22
#define DHTTYPE DHT22   // Define el tipo de sensor
const int pinVentilador = 22;
const int pinFoco = 23;

// --- INICIALIZACIÓN DE DISPOSITIVOS Y SERVIDOR ---
WebServer server(80);
// Inicializa el sensor DHT
DHT dht(DHTPIN, DHTTYPE);

// Variables para guardar el estado de los actuadores
bool estadoVentilador = false;
bool estadoFoco = false;

// --- FUNCIÓN PARA MANEJAR LA PETICIÓN DE DATOS (MODIFICADA) ---
void handleData() {
  // Leer solo la temperatura
  float tempC = dht.readTemperature();

  // Verificar si la lectura fue exitosa (isnan = "Is Not a Number")
  if (isnan(tempC)) {
    // Enviar error si falla la lectura
    String jsonError = "{";
    jsonError += "\"temperatura\": \"Error\"";
    jsonError += ", \"ventilador\": " + String(estadoVentilador ? "1" : "0");
    jsonError += ", \"foco\": " + String(estadoFoco ? "1" : "0");
    jsonError += "}";
    server.send(200, "application/json", jsonError);
    return;
  }
  
  // Crear una respuesta en formato JSON
  String json = "{";
  json += "\"temperatura\": ";
  json += String(tempC);
  json += ", ";
  json += "\"ventilador\": ";
  json += estadoVentilador ? "1" : "0";
  json += ", ";
  json += "\"foco\": ";
  json += estadoFoco ? "1" : "0";
  json += "}";

  server.send(200, "application/json", json);
}

// --- FUNCIÓN PARA MANEJAR LOS COMANDOS DE CONTROL (SIN CAMBIOS) ---
void handleControl() {
  String actuador = server.arg("actuador");
  int estado = server.arg("estado").toInt();

  if (actuador == "ventilador") {
    digitalWrite(pinVentilador, (estado == 1) ? LOW : HIGH);
    estadoVentilador = (estado == 1);
  } else if (actuador == "foco") {
    digitalWrite(pinFoco, (estado == 1) ? LOW : HIGH);
    estadoFoco = (estado == 1);
  }
  
  server.send(200, "text/plain", "OK");
}

// --- FUNCIÓN DE CONFIGURACIÓN (MODIFICADA) ---
void setup() {
  Serial.begin(115200);
  dht.begin(); // Iniciar el sensor DHT
  
  pinMode(pinVentilador, OUTPUT);
  pinMode(pinFoco, OUTPUT);
  
  digitalWrite(pinVentilador, HIGH);
  digitalWrite(pinFoco, HIGH);
  
  // Conexión a WiFi
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado!");
  Serial.print("Dirección IP: ");
  Serial.println(WiFi.localIP());
  
  // Definir los endpoints
  server.on("/data", HTTP_GET, handleData);
  server.on("/control", HTTP_GET, handleControl);
  
  server.begin();
  Serial.println("Servidor HTTP iniciado");
}

// --- BUCLE PRINCIPAL (SIN CAMBIOS) ---
void loop() {
  server.handleClient();
}