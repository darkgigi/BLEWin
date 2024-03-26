import customtkinter as ctk
from PIL import Image, ImageTk
from bleak import *
import asyncio
import subprocess
from utils import *
from CTkMessagebox import *
import random
from pylsl import StreamInfo, StreamOutlet
import pylsl as lsl
import numpy as np
import webbrowser

def install_dependencies():
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'])

COLOR_NOT_FOUND = "#e85a5a"
COLOR_FOUND = "#82c2f0"
COLOR_CONNECT = "#54ba32"
COLOR_BUTTON_FOCUS = '#f0982e'

SRV_FRAME = "0000acc0-0000-1000-8000-00805f9b34fb"  # Service propio
CH_FRAME = "0000acc5-0000-1000-8000-00805f9b34fb"
CH_CEDA_SEL = "0000acc6-0000-1000-8000-00805f9b34fb"

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

connections: dict[tuple() : BleakClient] = dict()
list_RR = [0, 0, 0, 0, 0, 0, 0]
#manuDetector = RTQRS(sizeBuffer=250, overlap=50)
lastRR = 0
rr_aux = 0
list_RR = [0, 0, 0, 0, 0, 0, 0]
paso = 200
datos = []

class App:
    async def exec(self):
        self.window = Window(asyncio.get_event_loop())
        await self.window.show()


class Window(ctk.CTk):
    def __init__(self,loop):
        super().__init__()
        self.title("BLEWin")
        self.loop = loop
        self.type3 = blemanager()
        self.type2 = blemanager()
        self.type1 = blemanager()
        self.is_closed = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.subscribed_connections = []
        self.is_closed = False
        self.radiobuttons = []
        self.radio_var = ctk.StringVar()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Imágenes
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        self.bluetooth_image = ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "bluetooth_light.png")), 
                                            dark_image=Image.open(os.path.join(image_path, "bluetooth_dark.png")),
                                            size=(30, 30))
        self.github_image = ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "github_light.png")),
                                         dark_image=Image.open(os.path.join(image_path, "github_dark.png")),
                                         size=(30, 30))

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="BLEWin",image=self.bluetooth_image, compound="left", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.github_logo_button = ctk.CTkButton(self.sidebar_frame, image=self.github_image, 
                                                text="V3.0.0", fg_color="transparent", text_color=("gray10", "gray90"), 
                                                hover_color=("gray70", "gray30"), command=lambda: webbrowser.open("https://github.com/darkgigi/BLEWin"),
                                                corner_radius=0, height=40, border_spacing=10)
        self.github_logo_button.grid(row=5, column=0, sticky="ew", pady=(0, 0))
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Modo:")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Claro", "Oscuro", "Sistema"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="Escalado IU:", anchor="w")
        self.scaling_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))

        self.appearance_mode_optionemenu.set("Claro")
        self.scaling_optionemenu.set("100%")

        # Primer frame
        lf_buttons_frame = ctk.CTkFrame(self)
        lf_buttons_frame.grid(column=1, row=0, sticky="nsew", padx=(20, 20), pady=(20, 0))
        # Configurar para que los elementos se expandan y contraigan
        lf_buttons_frame.grid_rowconfigure(0, weight=1) 
        lf_buttons_frame.grid_rowconfigure(1, weight=1)  
        lf_buttons_frame.grid_columnconfigure(0, weight=1)  

        lf_buttons= ctk.CTkLabel(lf_buttons_frame, text="Dispositivos: ")
        lf_buttons.grid(column=0, row=0, padx=5, pady=10, sticky="nsew")

        self.scrollable_frame = ctk.CTkScrollableFrame(lf_buttons_frame, label_text="Escáner", width=450)
        self.scrollable_frame.grid(column=0, row=1, padx=10, pady=5, sticky="nsew")

        button_discover = ctk.CTkButton(lf_buttons_frame, text="Escanear", command= lambda: asyncio.create_task(self.discover_devices()))
        button_discover.grid(column=0, row=2, padx=20, pady=10)

        button_connect = ctk.CTkButton(lf_buttons_frame, text="Conectar", command= lambda: asyncio.create_task(self.connect_device()))
        button_connect.grid(column=0, row=3, padx=20, pady=10)

        button_disconnect = ctk.CTkButton(lf_buttons_frame, text="Desconectar", command= lambda: asyncio.create_task(self.disconnect_device()))
        button_disconnect.grid(column=0, row=4, padx=20, pady=10)

        # Segundo frame
        lf_connection_frame = ctk.CTkFrame(self, width=250)
        lf_connection_frame.grid(column=2, row=0, padx=(20, 20), pady=(20, 0), sticky="nsew")        
        lf_connection = ctk.CTkLabel(lf_connection_frame, text="Estado:")
        lf_connection.grid(column=2, row=0, padx=5, pady=10)

        b_connect = ctk.CTkButton(lf_connection_frame,
                                text="Conectar todos",
                                command= lambda: asyncio.create_task(self.connect_all()))

        b_connect.grid(column=2, row=4, padx=20, pady=10)
        b_close = ctk.CTkButton(lf_connection_frame,
                            text="Desconectar todos",
                            command= lambda: asyncio.create_task(self.disconnect_all()))
        b_close.grid(column=2, row=5, padx=20, pady=10)
        
        self.txt_chest = ctk.CTkLabel(lf_connection_frame,
                                fg_color=COLOR_NOT_FOUND,
                                text="  Tipo 3  ",
                                width=100)
        self.txt_chest.grid(column=2, row=3, padx=5, pady=5)
        self.txt_leg = ctk.CTkLabel(lf_connection_frame,
                                fg_color=COLOR_NOT_FOUND,
                                text="  Tipo 1  ",
                                width=100)
        self.txt_leg.grid(column=2, row=1, padx=5, pady=5)
        self.txt_wrist = ctk.CTkLabel(lf_connection_frame,
                                fg_color=COLOR_NOT_FOUND,
                                text="  Tipo 2  ",
                                width=100)
        self.txt_wrist.grid(column=2, row=2, padx=5, pady=5)

        # Tercer frame
        lf_measurement_frame = ctk.CTkFrame(self, width=250)
        lf_measurement_frame.grid(column=2, row=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        lf_measurement = ctk.CTkLabel(lf_measurement_frame, text="Medición:")
        lf_measurement.grid(column=0, row=0, padx=5, pady=10)
        b_start = ctk.CTkButton(lf_measurement_frame,
                            text="Iniciar",
                            command= lambda: asyncio.create_task(self.start_measurement()))
        b_start.grid(column=0, row=1, padx=20, pady=10)
        b_stop = ctk.CTkButton(lf_measurement_frame, 
                           text="Detener", 
                           command = lambda: asyncio.create_task(self.stop_measurement()))
        b_stop.grid(column=0, row=2, padx=20, pady=10)
       
    async def show(self):
        """Muestra la ventana y comienza el bucle de eventos."""

        while not self.is_closed:
            self.update()
            await asyncio.sleep(.1)
            

    def on_close(self):
        """Detiene el bucle de eventos y cierra la ventana."""
        self.is_closed = True
        self.loop.stop()
        super().destroy()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        mode = ctk.get_appearance_mode()
        if new_appearance_mode == "Claro":
            mode = "Light"
        elif new_appearance_mode == "Oscuro":
            mode = "Dark"
        else:
            mode = "System"
        ctk.set_appearance_mode(mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)    

    async def discover_devices(self):
        """Busca dispositivos BLE disponibles y los muestra en la lista de dispositivos."""

        self.restart_txt()
        discovered = await BleakScanner.discover()
        devices = [(d.name, d.address) for d in discovered]

        for radiobutton in self.radiobuttons:
            radiobutton.destroy()
        self.radiobuttons = []

        for device in devices:
            if device[0] == 'ChestMonitor':
                self.type3.address = device[1]
                self.type3.name = device[0]
                self.txt_chest.configure(fg_color=COLOR_FOUND)
            if device[0] == 'WristMonitor':
                self.type2.address = device[1]
                self.type2.name = device[0]
                self.txt_wrist.configure(fg_color=COLOR_FOUND)
            if device[0] == 'LegMonitor':
                self.type1.address = device[1]
                self.type1.name = device[0]
                self.txt_leg.configure(fg_color=COLOR_FOUND)
            
            radiobutton = ctk.CTkRadioButton(self.scrollable_frame, text=f"{device[0]} {device[1]}", variable=self.radio_var, value=f"{device[0]} {device[1]}")
            radiobutton.grid(sticky="w", padx=5, pady=5)
            self.radiobuttons.append(radiobutton)

        if connections:
            for name,address in connections:
                if address == self.type3.address:
                    self.txt_chest.configure(fg_color=COLOR_CONNECT)
                if address == self.type2.address:
                    self.txt_wrist.configure(fg_color=COLOR_CONNECT)
                if address == self.type1.address:
                    self.txt_leg.configure(fg_color=COLOR_CONNECT)
                
                radiobutton = ctk.CTkRadioButton(self.scrollable_frame, text=f"{name} {address}", variable=self.radio_var, value=f"{name} {address}")
                radiobutton.grid(sticky="w", padx=5, pady=5)
                self.radiobuttons.append(radiobutton)

    async def connect_device(self):
        """Conecta el dispositivo seleccionado de la lista de dispositivos."""

        selected = self.radio_var
        if not selected.get():
            CTkMessagebox(title="Error de conexión", message="Dispositivo no seleccionado.", icon="cancel")
            return
        address = selected.get().split(" ")[1]
        name = selected.get().split(" ")[0]
        if (name,address) in connections and connections[(name,address)].is_connected:
            CTkMessagebox(title="Error de conexión", message="Dispositivo ya conectado.", icon="cancel")
            return
        try:
            connection = BleakClient(address)
            await connection.connect()
            self.check_type(address, connection)
            connections[(name,address)] = connection
            
            self.initialite_blemanager(address)
            CTkMessagebox(title="Conexión", message="Dispositivo conectado exitosamente.", icon="check")
        except Exception as e:
            CTkMessagebox(title="Error de conexión", message="Dispositivo no disponible", icon="cancel")


    def check_type(self, address, connection: BleakClient):
        """Actualiza el color de los labels de estado de los dispositivos encontrados y conectados."""

        subscribed_addresses = [device.address for device in self.subscribed_connections]
        if address == self.type1.address and connection.is_connected and address in subscribed_addresses:
            self.txt_leg.configure(fg_color=COLOR_BUTTON_FOCUS)
        elif address == self.type1.address and connection.is_connected:
            self.txt_leg.configure(fg_color=COLOR_CONNECT)
        elif address == self.type1.address and not connection.is_connected:
            self.txt_leg.configure(fg_color=COLOR_FOUND)
        if  address == self.type2.address and connection.is_connected and address in subscribed_addresses:
            self.txt_wrist.configure(fg_color=COLOR_BUTTON_FOCUS)
        elif  address == self.type2.address and connection.is_connected:
            self.txt_wrist.configure(fg_color=COLOR_CONNECT)
        elif  address == self.type2.address and not connection.is_connected:
            self.txt_wrist.configure(fg_color=COLOR_FOUND)
        if  address == self.type3.address and connection.is_connected and address in subscribed_addresses:
            self.txt_chest.configure(fg_color=COLOR_BUTTON_FOCUS)
        elif address == self.type3.address and connection.is_connected:
            self.txt_chest.configure(fg_color=COLOR_CONNECT)
        elif  address == self.type3.address and not connection.is_connected:
            self.txt_chest.configure(fg_color=COLOR_FOUND)

    def restart_txt(self):
        """Reinicia el color de los labels de estado de los dispositivos."""

        self.txt_leg.configure(fg_color=COLOR_NOT_FOUND)
        self.txt_wrist.configure(fg_color=COLOR_NOT_FOUND)
        self.txt_chest.configure(fg_color=COLOR_NOT_FOUND)

    def initialite_blemanager(self, address):
        """Inicializa los valores de los dispositivos BLE que se conectan"""

        if not self.type1 and not self.type2 and not self.type3:
            CTkMessagebox(title="Error de conexión", message="No se ha encontrado ningún dispositivo", icon="cancel")
            return
        if not connections:
            CTkMessagebox(title="Error de conexión", message="No se ha conectado ningún dispositivo", icon="cancel")
            return
        if self.type1.address == address and (name:=("LegMonitor",self.type1.address)) in connections:
            connection = connections[name]
            self.type1.id = 1
            self.type1.lsl_ta = StreamOutlet(
                StreamInfo('Nano33IoT_Leg_TA', 'TA', 1, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type1.lsl_acc = StreamOutlet(
                StreamInfo('Nano33IoT_Leg_ACC', 'ACC', 3, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type1.lsl_gyr = StreamOutlet(
                StreamInfo('Nano33IoT_Leg_GYR', 'GYR', 3, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type1.lsl_bat = StreamOutlet(
                StreamInfo('Nano33IoT_Leg_BAT', 'BAT', 1, lsl.IRREGULAR_RATE, 'float32', 'OWN'))
        if self.type2.address == address and (name:=("WristMonitor",self.type2.address)) in connections:
            connection = connections[name]
            self.type2.eda_config = connection.read_gatt_char(CH_CEDA_SEL)[0]
            self.type2.id = 2

            self.type2.lsl_eda = StreamOutlet(
                StreamInfo('Nano33IoT_Wrist_EDA', 'EDA', 1, lsl.IRREGULAR_RATE, 'int16', 'OWN'))
            self.type2.lsl_eda_config = StreamOutlet(
                StreamInfo('Nano33IoT_Wrist_EDA_CONFIG', 'EDA_CONFIG', 1, lsl.IRREGULAR_RATE, 'int16', 'OWN'))
            self.type2.lsl_ta = StreamOutlet(
                StreamInfo('Nano33IoT_Wrist_TA', 'TA', 1, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type2.lsl_st = StreamOutlet(
                StreamInfo('Nano33IoT_Wrist_ST', 'ST', 1, lsl.IRREGULAR_RATE, 'float32', 'OWN'))
            self.type2.lsl_acc = StreamOutlet(
                StreamInfo('Nano33IoT_Wrist_ACC', 'ACC', 3, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type2.lsl_gyr = StreamOutlet(
                StreamInfo('Nano33IoT_Wrist_GYR', 'GYR', 3, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type2.lsl_bat = StreamOutlet(
                StreamInfo('Nano33IoT_Wrist_BAT', 'BAT', 1, lsl.IRREGULAR_RATE, 'float32', 'OWN'))
        if self.type3.address == address and (name:=("ChestMonitor",self.type3.address)) in connections:
            connection = connections[name]
            self.type3.id = 3
            self.type3.lsl_ecg = StreamOutlet(
                StreamInfo('Nano33IoT_Chest_ECG', 'ECG', 1, lsl.IRREGULAR_RATE, 'int16', 'OWN'))
            self.type3.lsl_hr = StreamOutlet(
                StreamInfo('Nano33IoT_Chest_HR', 'HR', 1, lsl.IRREGULAR_RATE, 'float32', 'OWN'))
            self.type3.lsl_br = StreamOutlet(
                StreamInfo('Nano33IoT_Chest_BR', 'BR', 1, lsl.IRREGULAR_RATE, 'int16', 'OWN'))
            self.type3.lsl_ta = StreamOutlet(
                StreamInfo('Nano33IoT_Chest_TA', 'TA', 1, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type3.lsl_acc = StreamOutlet(
                StreamInfo('Nano33IoT_Chest_ACC', 'ACC', 3, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type3.lsl_gyr = StreamOutlet(
                StreamInfo('Nano33IoT_Chest_GYR', 'GYR', 3, lsl.IRREGULAR_RATE, 'float32', 'LSM6DS3'))
            self.type3.lsl_bat = StreamOutlet(
                StreamInfo('Nano33IoT_Chest_BAT', 'BAT', 1, lsl.IRREGULAR_RATE, 'float32', 'OWN'))

    async def disconnect_device(self):
        """Desconecta el dispositivo seleccionado."""

        selected = self.radio_var
        if not selected.get():
            CTkMessagebox(title="Error de desconexión", message="Dispositivo no seleccionado.", icon="cancel")
            return
        if self.subscribed_connections != []:
            await self.stop_measurement()
        address = selected.get().split(" ")[1]
        name = selected.get().split(" ")[0]
        if (name,address) not in connections:
            CTkMessagebox(title="Error de desconexión", message="Dispositivo no conectado.", icon="cancel")
            return
        try:
            connection = connections[(name,address)]
            await connection.disconnect()
            self.check_type(address, connection)
            self.restart_blemanager(address)
            connections.pop((name,address))
            CTkMessagebox(title="Desconexión", message="Dispositivo desconectado correctamente.", icon="check")
        except Exception as e:
            CTkMessagebox(title="Error de desconexión", message="Dispositivo no disponible", icon="cancel")

    def restart_blemanager(self, address):
        """Reinicia los valores de los dispositivos BLE que se desconectan"""

        connected_addresses = [address for _,address in connections.keys()]
        if self.type1.address == address and self.type1.address in connected_addresses:
            self.type1.lsl_ta = None
            self.type1.lsl_acc = None
            self.type1.lsl_gyr = None
            self.type1.lsl_bat = None
        if self.type2.address == address and self.type2.address in connected_addresses:
            self.type2.eda_config = None
            self.type2.lsl_eda = None
            self.type2.lsl_eda_config = None
            self.type2.lsl_ta = None
            self.type2.lsl_st = None
            self.type2.lsl_acc = None
            self.type2.lsl_gyr = None
            self.type2.lsl_bat = None
        if self.type3.address == address and self.type3.address in connected_addresses:
            self.type3.lsl_ecg = None
            self.type3.lsl_hr = None
            self.type3.lsl_br = None
            self.type3.lsl_ta = None
            self.type3.lsl_acc = None
            self.type3.lsl_gyr = None
            self.type3.lsl_bat = None

    async def connect_all(self):
        """Conecta todos los dispositivos encontrados en la lista de dispositivos."""

        if not self.type1 and not self.type2 and not self.type3:
            CTkMessagebox(title="Error de conexión", message="No se ha encontrado ningún dispositivo", icon="cancel")
            return
        addresses_connected = [address for _,address in connections.keys()]
        if self.type1.address and self.type1.address not in addresses_connected:
            connection = BleakClient(self.type1.address)
            await connection.connect()
            self.check_type(self.type1.address, connection)
            connections[("LegMonitor",self.type1.address)] = connection
            self.initialite_blemanager(self.type1.address)
        if self.type2.address and self.type2.address not in addresses_connected:
            connection = BleakClient(self.type2.address)
            await connection.connect()
            self.check_type(self.type2.address, connection)
            connections[("WristMonitor",self.type2.address)] = connection
            self.initialite_blemanager(self.type2.address)
        if self.type3.address and self.type3.address not in addresses_connected:
            connection = BleakClient(self.type3.address)
            await connection.connect()
            self.check_type(self.type3.address, connection)
            connections[("ChestMonitor",self.type3.address)] = connection
            self.initialite_blemanager(self.type3.address)
        CTkMessagebox(title="Conexión", message="Todos los dispositivos conectados correctamente.", icon="check")
        return
    
    async def disconnect_all(self):
        """Desconecta todos los dispositivos conectados."""

        if self.subscribed_connections != []:
            await self.stop_measurement()

        global connections
        connections_copy = connections.copy()
        for name,address in connections.keys():
            connection = connections[(name,address)]
            await connection.disconnect()
            self.check_type(address, connection)
            self.restart_blemanager(address)
            connections_copy.pop((name,address))
        connections = connections_copy
        CTkMessagebox(title="Desconexión", message="Todos los dispositivos desconectados correctamente.", icon="check")
        return
    
     # TODO: procesar los datos recibidos de los dispositivos
    async def start_measurement(self):
        """Inicia la medición de los dispositivos conectados."""
        if not connections:
            CTkMessagebox(title="Error de medición", message="No se ha conectado ningún dispositivo", icon="cancel")
            return
        connected_addresses = [address for _,address in connections.keys()]
        if self.type1.address in connected_addresses and not self.type1 in self.subscribed_connections:
            manager = self.MeasurementManager(self.type1, self)
            self.subscribed_connections.append(self.type1)
            connection = connections[("LegMonitor",self.type1.address)]
            await connection.start_notify(CH_FRAME, manager.handle_notification)
            self.check_type(self.type1.address, connection)
        if self.type2.address in connected_addresses and not self.type2 in self.subscribed_connections:
            manager = self.MeasurementManager(self.type2, self)
            self.subscribed_connections.append(self.type2)
            connection = connections[("WristMonitor",self.type2.address)]
            await connection.start_notify(CH_FRAME, manager.handle_notification)
            self.check_type(self.type2.address, connection)
        if self.type3.address in connected_addresses and not self.type3 in self.subscribed_connections:
            manager = self.MeasurementManager(self.type3, self)
            self.subscribed_connections.append(self.type3)
            connection = connections[("ChestMonitor",self.type3.address)]
            await connection.start_notify(CH_FRAME, manager.handle_notification)
            self.check_type(self.type3.address, connection)
        CTkMessagebox(title="Medición", message="Medición iniciada.")
    
    async def stop_measurement(self):
        """Detiene la medición de los dispositivos conectados."""
        if not self.subscribed_connections:
            CTkMessagebox(title="Error de medición", message="No se ha iniciado la medición", icon="cancel")
            return
        
        for tuple in connections:
            connection = connections[tuple]
            subscribed_addresses = [device.address for device in self.subscribed_connections]
            if connection.address in subscribed_addresses:
                await connection.stop_notify(CH_FRAME)
                if connection.address == self.type1.address:
                    self.subscribed_connections.remove(self.type1)
                if connection.address == self.type2.address:
                    self.subscribed_connections.remove(self.type2)
                if connection.address == self.type3.address:
                    self.subscribed_connections.remove(self.type3)
                self.check_type(connection.address, connection)
        CTkMessagebox(title="Medición", message="Medición detenida.")

    class MeasurementManager:
        def __init__(self, blemanager: blemanager, window):
            if isinstance(window, Window):
                self.mblemanager = blemanager
                self.window = window
            
        def handle_notification(self, sender: str, data: bytearray):
            """Procesa las notificaciones de las características."""
            if self.mblemanager.name == "LegMonitor":
                r_acc, r_gyr, r_bat, r_ta = self.getLegData(data)
                for e in range(0, len(r_acc), 3):
                    self.mblemanager.lsl_acc.push_sample(r_acc[e:e + 3])
                for e in range(0, len(r_gyr), 3):
                    self.mblemanager.lsl_gyr.push_sample(r_gyr[e:e + 3])
                for e in r_bat:
                    self.mblemanager.lsl_bat.push_sample([e])
                for e in r_ta:
                    self.mblemanager.lsl_ta.push_sample([e])
            elif self.mblemanager.name == "WristMonitor":
                r_eda, r_acc, r_gyr, r_bat, r_ta, r_st, r_eda_config = self.getWristData(data)
                # TODO: procesar los datos recibidos de la muñeca
            elif self.mblemanager.name == "ChestMonitor":
                r_ecg, r_acc, r_gyr, r_br, r_bat, r_ta = self.getChestData(data)
                for e in r_ecg:
                    self.mblemanager.lsl_ecg.push_sample([e])
                    # TODO: procesar los datos de la frecuencia cardíaca
                    '''
                    datos.append(e)
                    if len(datos) == 250:
                        res = manuDetector.realTimeQRSDetection(np.array(datos))
                        if len(res) > 0:
                            for element in res:
                                rr_aux = list_RR.pop(0)
                                rr_aux = 12480/(element - lastRR)
                                list_RR.append(rr_aux)
                                self.mblemanager.lsl_hr.push_sample([np.median(list_RR)])
                                lastRR = element
                            if lastRR > 210:
                                datos = []
                                lastRR = lastRR - 250
                            else:
                                datos = datos[200:250]
                                lastRR = lastRR -200
                    '''
                    #Valores aleatorios entre 60 y 180 para asegurar que se capturen los datos
                    self.mblemanager.lsl_hr.push_sample([random.randint(60, 180)])
                for e in range(0, len(r_acc), 3):
                    self.mblemanager.lsl_acc.push_sample(r_acc[e:e + 3])
                for e in range(0, len(r_gyr), 3):
                    self.mblemanager.lsl_gyr.push_sample(r_gyr[e:e + 3])
                for e in r_br:
                    self.mblemanager.lsl_br.push_sample([e])
                for e in r_bat:
                    self.mblemanager.lsl_bat.push_sample([e])
                for e in r_ta:
                    self.mblemanager.lsl_ta.push_sample([e])

        def getLegData(self, data):
            """Obtiene los datos de la pierna"""

            if len(data) != 28:
                CTkMessagebox(title="Error de datos", message="Longitud incorrecta", icon="cancel")
                return None, None, None, None
            else:
                acc = bytearray(data[0:12])
                gyr = bytearray(data[12:24])
                bat = bytearray(data[24:26])
                ta = bytearray(data[26:28])
                r_acc = accRead(acc)
                r_gyr = gyrRead(gyr)
                r_bat = batRead(bat)
                r_ta = taRead(ta)
                return r_acc, r_gyr, r_bat, r_ta
    
        def getWristData(self,data):
            """Obtiene los datos de la muñeca"""

            # TODO: probar si se reciben bien los datos de la muñeca
            if len(data) != 36:
                CTkMessagebox(title="Error de datos", message="Longitud incorrecta", icon="cancel")
                return None, None, None, None, None, None, None
            else:
                eda = bytearray(data[0:4])
                acc = bytearray(data[4:16])
                gyr = bytearray(data[16:28])
                bat = bytearray(data[28:30])
                ta = bytearray(data[30:32])
                st = bytearray(data[32:34])
                eda_config = bytearray(data[34:36])
                r_eda = bytearray2uint16list(eda)
                r_acc = accRead(acc)
                r_gyr = gyrRead(gyr)
                r_bat = batRead(bat)
                r_ta = taRead(ta)
                r_st = stRead(st)
                r_eda_config = bytearray2uint16list(eda_config)
                return r_eda, r_acc, r_gyr, r_bat, r_ta, r_st, r_eda_config
        
        def getChestData(self,data):
            """Obtiene los datos del pecho"""

            # TODO: corregir el error de longitud, el tamaño que recibe es de 72 bytes
            if len(data) != 64:
                CTkMessagebox(title="Error de datos", message="Longitud incorrecta", icon="cancel")
                return None, None, None, None, None, None
            else:
                ecg = bytearray(data[0:32])
                acc = bytearray(data[32:44])
                gyr = bytearray(data[44:56])
                br = bytearray(data[56:60])
                bat = bytearray(data[60:62])
                ta = bytearray(data[62:64])
                r_ecg = bytearray2uint16list(ecg)
                r_acc = accRead(acc)
                r_gyr = gyrRead(gyr)
                r_br = bytearray2uint16list(br)
                r_bat = batRead(bat)
                r_ta = taRead(ta)
                return r_ecg, r_acc, r_gyr, r_br, r_bat, r_ta


if __name__ == "__main__":
    
    try:
        asyncio.run(App().exec())
    except RuntimeError as e:
        if str(e) == 'Event loop stopped before Future completed.':
            pass
        else:
            raise e