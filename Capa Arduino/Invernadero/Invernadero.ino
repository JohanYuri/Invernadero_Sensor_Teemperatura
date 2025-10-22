#include <WiFi.h>
#include <WebServer.h>
#include <DHT.h>

// --- CONFIGURACIÓN DE LA RED WIFI ---
const char* ssid = "MEGACABLE-2.4G-E8AA_EXT";
const char* password = "pD9vzFKzK2";

// --- CONFIGURACIÓN DE PINES ---
#define DHTPIN 21       // Pin D21 para el sensor DHT22
#define DHTTYPE DHT22   // Define el tipo de sensor
const int pinVentilador = 22; // Pin D22 para el relevador del ventilador
const int pinFoco = 23;       // Pin D23 para el relevador del foco

// --- PINES DE LOS DISPLAYS  ---
// Segmentos: {a, b, c, d, e, f, g}
int display1Pins[7] = {25, 26, 27, 14, 12, 13, 33};
int display2Pins[7] = {17, 16, 4,  2,  15, 5,  18};

// --- MAPA DE SEGMENTOS PARA DISPLAY (Cátodo Común: 1=ON, 0=OFF) ---
// Dígitos:         {a, b, c, d, e, f, g}
byte segmentMap[11][7] = {
  { 1, 1, 1, 1, 1, 1, 0 }, // 0
  { 0, 1, 1, 0, 0, 0, 0 }, // 1
  { 1, 1, 0, 1, 1, 0, 1 }, // 2
  { 1, 1, 1, 1, 0, 0, 1 }, // 3
  { 0, 1, 1, 0, 0, 1, 1 }, // 4
  { 1, 0, 1, 1, 0, 1, 1 }, // 5
  { 1, 0, 1, 1, 1, 1, 1 }, // 6
  { 1, 1, 1, 0, 0, 0, 0 }, // 7
  { 1, 1, 1, 1, 1, 1, 1 }, // 8
  { 1, 1, 1, 1, 0, 1, 1 }, // 9
  { 0, 0, 0, 0, 0, 0, 1 }  // 10 (Guion "-")
};

// --- INICIALIZACIÓN DE DISPOSITIVOS Y SERVIDOR ---
WebServer server(80);
DHT dht(DHTPIN, DHTTYPE);
bool estadoVentilador = false;
bool estadoFoco = false;

// --- FUNCIÓN PARA MOSTRAR TEMPERATURA EN DISPLAYS ---
void showTemperatureOnDisplays(float tempC) {
  int digit1, digit2;

  if (isnan(tempC)) {
    // Si hay error, mostrar "--"
    digit1 = 10; // Índice 10 es el guion
    digit2 = 10;
  } else {
    // Convertir a entero y limitar a 99
    int tempInt = (int)tempC;
    if (tempInt > 99) tempInt = 99;
    if (tempInt < 0) tempInt = 0; // Mostrar 00 si es negativo

    digit1 = tempInt / 10; // Dígito de las decenas
    digit2 = tempInt % 10; // Dígito de las unidades
  }

  // Escribir en Display 1 (Decenas)
  for (int i = 0; i < 7; i++) {
    digitalWrite(display1Pins[i], segmentMap[digit1][i]);
  }

  // Escribir en Display 2 (Unidades)
  for (int i = 0; i < 7; i++) {
    digitalWrite(display2Pins[i], segmentMap[digit2][i]);
  }
}

// --- FUNCIÓN PARA MANEJAR LA PETICIÓN DE DATOS (MODIFICADA) ---
void handleData() {
  float tempC = dht.readTemperature();

  // --- Actualizar los displays ---
  showTemperatureOnDisplays(tempC);
  
  // Crear una respuesta en formato JSON
  String json = "{";
  if (isnan(tempC)) {
    json += "\"temperatura\": \"Error\"";
  } else {
    json += "\"temperatura\": ";
    json += String(tempC);
  }
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

// --- FUNCIÓN DE CONFIGURACIÓN ---
void setup() {
  Serial.begin(115200);
  dht.begin(); // Iniciar el sensor DHT
  
  // Configurar pines de actuadores
  pinMode(pinVentilador, OUTPUT);
  pinMode(pinFoco, OUTPUT);
  digitalWrite(pinVentilador, HIGH);
  digitalWrite(pinFoco, HIGH);
  
  // --- Configurar los 14 pines de los displays como SALIDA ---
  for (int i = 0; i < 7; i++) {
    pinMode(display1Pins[i], OUTPUT);
    pinMode(display2Pins[i], OUTPUT);
  }
  
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

// --- BUCLE PRINCIPAL ---
void loop() {
  server.handleClient();
}