import tkinter as tk
from tkinter import ttk
import requests
import threading
import time

# --- CONFIGURACIÓN DEL SERVIDOR ---
ESP32_IP = "192.168.100.83" 
BASE_URL = f"http://{ESP32_IP}"

# --- PALETA DE COLORES ---
COLOR_FONDO = "#2E2E2E"
COLOR_FRAME = "#3B3B3B"
COLOR_TEXTO = "#FFFFFF"
COLOR_TEXTO_SEC = "#B0B0B0"
COLOR_VERDE_ON = "#4CAF50"
COLOR_ROJO_OFF = "#F44336"
COLOR_INDICADOR_ON = "#76FF03"
COLOR_INDICADOR_OFF = "#FF5252"
COLOR_CONTROL_ACTIVO = "#76FF03"
COLOR_CONTROL_INACTIVO = "#FF9800" # Naranja

# --- CLASE PRINCIPAL DE LA APLICACIÓN ---
class InvernaderoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mi Invernadero 🌿")
        self.geometry("600x420") 
        self.configure(background=COLOR_FONDO) # Fondo de la ventana principal

        # --- Variables de instancia ---
        self.temperatura_actual = tk.StringVar(value="--.- °C")
        self.estado_ventilador = tk.BooleanVar(value=False)
        self.estado_foco = tk.BooleanVar(value=False)
        self.setpoint = tk.DoubleVar(value=25.0)
        self.control_lazo_cerrado_activo = tk.BooleanVar(value=False)
        
        self.open_loop_frame = None
        self.closed_loop_frame = None
        self.toggle_button = None
        
        # --- DEFINICIÓN DE ESTILOS ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # Usamos 'clam' como base para poder personalizar colores

        # Estilo principal de la ventana y frames
        self.style.configure('.', background=COLOR_FONDO, foreground=COLOR_TEXTO, font=('Helvetica', 11))
        
        # Estilo para los LabelFrames (los marcos)
        self.style.configure('TLabelframe', background=COLOR_FRAME, bordercolor=COLOR_TEXTO_SEC)
        self.style.configure('TLabelframe.Label', background=COLOR_FRAME, foreground=COLOR_TEXTO, font=('Helvetica', 13, 'bold'))

        # Estilo para Labels
        self.style.configure('TLabel', background=COLOR_FRAME, foreground=COLOR_TEXTO)
        
        # Estilo para la temperatura 
        self.style.configure('Temp.TLabel', font=('Helvetica', 22, 'bold'), foreground=COLOR_VERDE_ON, background=COLOR_FRAME)
        
        # Estilo para Labels de estado (APAGADO / ENCENDIDO)
        self.style.configure('Indicator.TLabel', font=('Helvetica', 10, 'bold'), background=COLOR_FRAME)

        # Estilo para Botones
        self.style.configure('TButton', font=('Helvetica', 10, 'bold'), borderwidth=0)
        self.style.map('TButton',
            background=[('active', '#555555')],
            foreground=[('active', COLOR_TEXTO)])

        # Estilo Botón ON (Verde)
        self.style.configure('On.TButton', background=COLOR_VERDE_ON, foreground=COLOR_FONDO)
        self.style.map('On.TButton', background=[('active', '#388E3C')])

        # Estilo Botón OFF (Rojo)
        self.style.configure('Off.TButton', background=COLOR_ROJO_OFF, foreground=COLOR_TEXTO)
        self.style.map('Off.TButton', background=[('active', '#D32F2F')])

        # Estilo Botón de Control (Naranja/Verde)
        self.style.configure('Toggle.TButton', background=COLOR_CONTROL_INACTIVO, foreground=COLOR_FONDO)
        self.style.map('Toggle.TButton', 
            background=[('active', '#E65100'),
                        ('selected', COLOR_VERDE_ON)]) 

        # Estilo para la entrada de texto (Setpoint)
        self.style.configure('TEntry', fieldbackground="#DCDCDC", foreground="#000000", borderwidth=0)
        
        # --- Creación de Widgets ---
        self.create_open_loop_frame()
        self.create_closed_loop_frame()
        
        # Estado inicial
        self.set_frame_state(self.closed_loop_frame, tk.DISABLED, exclude_widget=self.toggle_button)

    def set_frame_state(self, frame, state, exclude_widget=None):
        """Habilita o deshabilita todos los widgets hijos de un frame."""
        for widget in frame.winfo_children():
            if widget != exclude_widget:
                try:
                    widget.configure(state=state)
                except tk.TclError:
                    pass

    def send_command(self, actuador, estado):
        """Envía un comando al ESP32 mediante una petición HTTP."""
        try:
            url = f"{BASE_URL}/control?actuador={actuador}&estado={estado}"
            requests.get(url, timeout=2)
            print(f"Comando enviado: {actuador} -> {'ON' if estado else 'OFF'}")
        except requests.RequestException as e:
            print(f"Error al enviar comando: {e}")

    def create_open_loop_frame(self):
        self.open_loop_frame = ttk.LabelFrame(self, text="Control Manual (Lazo Abierto)", padding=20)
        self.open_loop_frame.pack(fill="x", padx=10, pady=10)
        frame = self.open_loop_frame
        
        # Configura las columnas para que los botones se expandan
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        
        ttk.Label(frame, text="Temperatura Actual 🌡️", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(frame, textvariable=self.temperatura_actual, style='Temp.TLabel').grid(row=0, column=1, columnspan=2, sticky="w")
        
        # --- Widgets Ventilador ---
        ttk.Label(frame, text="Ventilador 💨").grid(row=1, column=0, sticky="w", pady=(10,5))
        ttk.Button(frame, text="ON", style='On.TButton', command=lambda: self.send_command('ventilador', 1)).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="OFF", style='Off.TButton', command=lambda: self.send_command('ventilador', 0)).grid(row=1, column=2, sticky="ew", padx=5)
        
        ventilador_indicator = ttk.Label(frame, text="APAGADO", foreground=COLOR_INDICADOR_OFF, style='Indicator.TLabel')
        ventilador_indicator.grid(row=1, column=3, padx=10)
        
        # --- Widgets Foco ---
        ttk.Label(frame, text="Foco/Calefactor 🔥").grid(row=2, column=0, sticky="w", pady=(15,5))
        ttk.Button(frame, text="ON", style='On.TButton', command=lambda: self.send_command('foco', 1)).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="OFF", style='Off.TButton', command=lambda: self.send_command('foco', 0)).grid(row=2, column=2, sticky="ew", padx=5)
        
        foco_indicator = ttk.Label(frame, text="APAGADO", foreground=COLOR_INDICADOR_OFF, style='Indicator.TLabel')
        foco_indicator.grid(row=2, column=3, padx=10)

        # Lógica de indicadores
        self.estado_ventilador.trace_add('write', lambda *args: ventilador_indicator.config(text="ENCENDIDO" if self.estado_ventilador.get() else "APAGADO", foreground=COLOR_INDICADOR_ON if self.estado_ventilador.get() else COLOR_INDICADOR_OFF))
        self.estado_foco.trace_add('write', lambda *args: foco_indicator.config(text="ENCENDIDO" if self.estado_foco.get() else "APAGADO", foreground=COLOR_INDICADOR_ON if self.estado_foco.get() else COLOR_INDICADOR_OFF))

    def create_closed_loop_frame(self):
        self.closed_loop_frame = ttk.LabelFrame(self, text="Control Automático (Lazo Cerrado)", padding=20)
        self.closed_loop_frame.pack(fill="x", padx=10, pady=10)
        frame = self.closed_loop_frame
        
        ttk.Label(frame, text="Temperatura Deseada (°C):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.setpoint, width=10, font=('Helvetica', 12)).grid(row=1, column=1, sticky="w")
        
        self.toggle_button = ttk.Button(frame, text="Activar Control Automático", style='Toggle.TButton', command=self.toggle_closed_loop)
        self.toggle_button.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        self.control_status_label = ttk.Label(frame, text="INACTIVO", foreground=COLOR_CONTROL_INACTIVO, font=('Helvetica', 12, 'bold'), background=COLOR_FRAME)
        self.control_status_label.grid(row=2, column=2, padx=10)

    def toggle_closed_loop(self):
        self.control_lazo_cerrado_activo.set(not self.control_lazo_cerrado_activo.get())
        
        if self.control_lazo_cerrado_activo.get():
            self.control_status_label.config(text="ACTIVO", foreground=COLOR_CONTROL_ACTIVO)
            self.toggle_button.config(text="Desactivar Control Automático", style='Off.TButton')
            
            self.set_frame_state(self.open_loop_frame, tk.DISABLED)
            self.set_frame_state(self.closed_loop_frame, tk.NORMAL, exclude_widget=self.toggle_button)
            print("Control en lazo cerrado ACTIVADO")
        else:
            self.control_status_label.config(text="INACTIVO", foreground=COLOR_CONTROL_INACTIVO)
            self.toggle_button.config(text="Activar Control Automático", style='Toggle.TButton')

            self.set_frame_state(self.open_loop_frame, tk.NORMAL)
            self.set_frame_state(self.closed_loop_frame, tk.DISABLED, exclude_widget=self.toggle_button)
            
            print("Control en lazo cerrado DESACTIVADO. Apagando actuadores.")
            self.send_command('ventilador', 0)
            self.send_command('foco', 0)

# --- HILO DE ACTUALIZACIÓN ---
def update_data_from_server(app):
    """Hilo que pide datos al ESP32 cada 2 segundos."""
    while True:
        try:
            response = requests.get(f"{BASE_URL}/data", timeout=2)
            if response.status_code == 200:
                data = response.json()
                
                temp = data['temperatura']
                if isinstance(temp, (int, float)):
                    app.temperatura_actual.set(f"{temp:.2f} °C")
                    
                    if app.control_lazo_cerrado_activo.get():
                        setpoint_val = app.setpoint.get()
                        if temp > setpoint_val:
                            app.send_command('ventilador', 1)
                            app.send_command('foco', 0)
                        elif temp < setpoint_val - 1: # Histéresis de 1 grado
                            app.send_command('foco', 1)
                            app.send_command('ventilador', 0)
                        else:
                            if app.estado_ventilador.get():
                                app.send_command('ventilador', 0)
                            if app.estado_foco.get():
                                app.send_command('foco', 0)
                else:
                    app.temperatura_actual.set("Error Sensor")
                
                app.estado_ventilador.set(data['ventilador'] == 1)
                app.estado_foco.set(data['foco'] == 1)
                
        except requests.RequestException as e:
            app.temperatura_actual.set("Sin Conexión")
            app.temperatura_actual.set("N/C °C") # N/C = No Conectado
            print(f"No se pudo conectar al ESP32: {e}")
        
        time.sleep(2)

# --- FUNCIÓN PRINCIPAL ---
if __name__ == "__main__":
    app = InvernaderoApp()
    
    update_thread = threading.Thread(target=update_data_from_server, args=(app,), daemon=True)
    update_thread.start()
    
    app.mainloop()