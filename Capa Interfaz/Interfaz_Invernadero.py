import tkinter as tk
from tkinter import ttk
import requests
import threading
import time

# --- CONFIGURACIÓN DEL SERVIDOR ---
# CAMBIA ESTA IP POR LA DE TU ESP32
ESP32_IP = "192.168.1.100"
BASE_URL = f"http://{ESP32_IP}"

# Variables globales para los datos
temperatura_actual = tk.StringVar(value="--.- °C")
estado_ventilador = tk.BooleanVar(value=False)
estado_foco = tk.BooleanVar(value=False)
setpoint = tk.DoubleVar(value=25.0)
control_lazo_cerrado_activo = tk.BooleanVar(value=False)

# --- CLASE PRINCIPAL DE LA APLICACIÓN ---
class InvernaderoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Control de Invernadero (Web)")
        self.geometry("600x450")
        
        # Estilos
        self.style = ttk.Style(self)
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 12))
        self.style.configure('Indicator.TLabel', font=('Helvetica', 10, 'bold'))
        
        self.create_open_loop_frame()
        self.create_closed_loop_frame()

    def send_command(self, actuador, estado):
        """Envía un comando al ESP32 mediante una petición HTTP."""
        try:
            url = f"{BASE_URL}/control?actuador={actuador}&estado={estado}"
            requests.get(url, timeout=2) # Timeout de 2 segundos
            print(f"Comando enviado: {actuador} -> {'ON' if estado else 'OFF'}")
        except requests.RequestException as e:
            print(f"Error al enviar comando: {e}")

    def create_open_loop_frame(self):
        frame = ttk.LabelFrame(self, text="Control en Lazo Abierto", padding=20)
        frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(frame, text="Temperatura Actual:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(frame, textvariable=temperatura_actual, font=('Helvetica', 14, 'bold')).grid(row=0, column=1, sticky="w")
        
        ttk.Label(frame, text="Ventilador:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Button(frame, text="ON", command=lambda: self.send_command('ventilador', 1)).grid(row=1, column=1, sticky="ew")
        ttk.Button(frame, text="OFF", command=lambda: self.send_command('ventilador', 0)).grid(row=1, column=2, sticky="ew")
        ventilador_indicator = ttk.Label(frame, text="APAGADO", foreground="red", style='Indicator.TLabel')
        ventilador_indicator.grid(row=1, column=3, padx=10)
        
        ttk.Label(frame, text="Foco/Bombilla:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Button(frame, text="ON", command=lambda: self.send_command('foco', 1)).grid(row=2, column=1, sticky="ew")
        ttk.Button(frame, text="OFF", command=lambda: self.send_command('foco', 0)).grid(row=2, column=2, sticky="ew")
        foco_indicator = ttk.Label(frame, text="APAGADO", foreground="red", style='Indicator.TLabel')
        foco_indicator.grid(row=2, column=3, padx=10)

        estado_ventilador.trace_add('write', lambda *args: ventilador_indicator.config(text="ENCENDIDO" if estado_ventilador.get() else "APAGADO", foreground="green" if estado_ventilador.get() else "red"))
        estado_foco.trace_add('write', lambda *args: foco_indicator.config(text="ENCENDIDO" if estado_foco.get() else "APAGADO", foreground="green" if estado_foco.get() else "red"))

    def create_closed_loop_frame(self):
        # ... (Esta función es idéntica a la versión anterior)
        frame = ttk.LabelFrame(self, text="Control en Lazo Cerrado", padding=20)
        frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(frame, text="Temperatura Actual:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(frame, textvariable=temperatura_actual, font=('Helvetica', 14, 'bold')).grid(row=0, column=1, sticky="w")
        ttk.Label(frame, text="Temperatura Deseada (°C):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=setpoint, width=10).grid(row=1, column=1)
        toggle_button = ttk.Button(frame, text="Activar Control Automático", command=self.toggle_closed_loop)
        toggle_button.grid(row=2, column=0, columnspan=2, pady=10)
        self.control_status_label = ttk.Label(frame, text="INACTIVO", foreground="orange", style='Indicator.TLabel')
        self.control_status_label.grid(row=2, column=2)

    def toggle_closed_loop(self):
        # ... (Esta función es idéntica a la versión anterior, pero llama a la nueva `send_command`)
        control_lazo_cerrado_activo.set(not control_lazo_cerrado_activo.get())
        if control_lazo_cerrado_activo.get():
            self.control_status_label.config(text="ACTIVO", foreground="green")
        else:
            self.control_status_label.config(text="INACTIVO", foreground="orange")
            self.send_command('ventilador', 0)
            self.send_command('foco', 0)

def update_data_from_server(app):
    """Hilo que pide datos al ESP32 cada 2 segundos."""
    while True:
        try:
            response = requests.get(f"{BASE_URL}/data", timeout=2)
            if response.status_code == 200:
                data = response.json()
                temp = data['temperatura']
                if isinstance(temp, (int, float)):
                    temperatura_actual.set(f"{temp:.2f} °C")
                    if control_lazo_cerrado_activo.get():
                        if temp > setpoint.get():
                            app.send_command('ventilador', 1)
                            app.send_command('foco', 0)
                        elif temp < setpoint.get() - 1:
                            app.send_command('foco', 1)
                            app.send_command('ventilador', 0)
                else:
                    temperatura_actual.set("Error Sensor")
                
                estado_ventilador.set(data['ventilador'] == 1)
                estado_foco.set(data['foco'] == 1)
        except requests.RequestException as e:
            temperatura_actual.set("Sin Conexión")
            print(f"No se pudo conectar al ESP32: {e}")
        
        time.sleep(2) # Esperar 2 segundos para la siguiente actualización

# --- FUNCIÓN PRINCIPAL ---
if __name__ == "__main__":
    app = InvernaderoApp()
    
    update_thread = threading.Thread(target=update_data_from_server, args=(app,), daemon=True)
    update_thread.start()
    
    app.mainloop()