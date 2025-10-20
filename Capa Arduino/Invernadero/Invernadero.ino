#include <WiFi.h>
#include <WebServer.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// --- CONFIGURACIÓN DE TU RED WIFI ---
const char* ssid = "TU_WIFI_SSID";
const char* password = "TU_WIFI_PASSWORD";

// --- CONFIGURACIÓN DE PINES ---
#define ONE_WIRE_BUS 21 // Pin D21 para el sensor DS18B20
const int pinVentilador = 22;
const int pinFoco = 23;

// --- INICIALIZACIÓN DE DISPOSITIVOS Y SERVIDOR ---
WebServer server(80); // El servidor web se ejecuta en el puerto 80
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Variables para guardar el estado de los actuadores
bool estadoVentilador = false; // false = OFF, true = ON
bool estadoFoco = false;

// --- FUNCIÓN PARA MANEJAR LA PETICIÓN DE DATOS ---
void handleData() {
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);
  tempC -= 300;
  
  // Crear una respuesta en formato JSON (fácil de leer para Python)
  String json = "{";
  json += "\"temperatura\": ";
  json += (tempC == DEVICE_DISCONNECTED_C) ? "\"Error\"" : String(tempC);
  json += ", ";
  json += "\"ventilador\": ";
  json += estadoVentilador ? "1" : "0";
  json += ", ";
  json += "\"foco\": ";
  json += estadoFoco ? "1" : "0";
  json += "}";

  server.send(200, "application/json", json);
}

// --- FUNCIÓN PARA MANEJAR LOS COMANDOS DE CONTROL ---
void handleControl() {
  // Recibir los parámetros de la URL, ej: /control?actuador=ventilador&estado=1
  String actuador = server.arg("actuador");
  int estado = server.arg("estado").toInt();

  if (actuador == "ventilador") {
    digitalWrite(pinVentilador, (estado == 1) ? LOW : HIGH); 
    estadoVentilador = (estado == 1);
  } else if (actuador == "foco") {
    digitalWrite(pinFoco, (estado == 1) ? LOW : HIGH);
    estadoFoco = (estado == 1);
  }
  
  server.send(200, "text/plain", "OK"); // Responder a Python que el comando fue recibido
}

// --- FUNCIÓN DE CONFIGURACIÓN ---
void setup() {
  Serial.begin(1152200);
  sensors.begin();
  pinMode(pinVentilador, OUTPUT);
  pinMode(pinFoco, OUTPUT);
  
  // Lógica invertida: HIGH es APAGADO
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
  Serial.println(WiFi.localIP()); // ¡ESTA IP ES LA QUE NECESITAS PARA PYTHON!

  // Definir las "páginas" o "endpoints" del servidor
  server.on("/data", HTTP_GET, handleData);
  server.on("/control", HTTP_GET, handleControl);
  
  server.begin(); // Iniciar el servidor
  Serial.println("Servidor HTTP iniciado");
}

// --- BUCLE PRINCIPAL ---
void loop() {
  server.handleClient(); // Escuchar peticiones de clientes (Python)
}