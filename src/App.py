import tkinter as tk
from tkinter import messagebox
from bleak import *
import asyncio
import threading
import subprocess
from pylsl import StreamInfo, StreamOutlet
from utils import *
import pylsl as lsl

def install_dependencies():
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'])

COLOR_NOT_FOUND = "#f26f68"
COLOR_FOUND = "#44dddd"
COLOR_CONNECT = "#33cc55"
COLOR_BUTTON_FOCUS = '#82c2f0'

SRV_FRAME = "0000acc0-0000-1000-8000-00805f9b34fb"  # Service propio
CH_FRAME = "0000acc5-0000-1000-8000-00805f9b34fb"
CH_CEDA_SEL = "0000acc6-0000-1000-8000-00805f9b34fb"

connections: dict[tuple() : BleakClient] = dict()

class App:
    async def exec(self):
        self.window = Window(asyncio.get_event_loop())
        await self.window.show()


class Window(tk.Tk):
    def __init__(self,loop):
        super().__init__()
        self.title("BLEWin")
        self.resizable(False, False)
        self.loop = loop
        self.type3 = blemanager()
        self.type2 = blemanager()
        self.type1 = blemanager()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.subscribed_connections = []

        lf_buttons= tk.LabelFrame(self, text="Dispositivos: ")
        lf_buttons.grid(column=0, row=0, padx=10, pady=10)
        self.devices_list = tk.Listbox(lf_buttons, selectmode=tk.SINGLE, width=100, height=20)
        self.devices_list.grid(column=0, row=1, padx=4, pady=4)
        
        button_discover = tk.Button(lf_buttons, text="Escanear", command=lambda: self.loop.create_task(self.discover_devices()))
        button_discover.grid(column=0, row=2, padx=4, pady=4)

        button_connect = tk.Button(lf_buttons, text="Conectar", command=lambda: self.loop.create_task(self.connect_device()))
        button_connect.grid(column=0, row=3, padx=4, pady=4)

        button_disconnect = tk.Button(lf_buttons, text="Desconectar", command=lambda: self.loop.create_task(self.disconnect_device()))
        button_disconnect.grid(column=0, row=4, padx=4, pady=4)

        lf_connection = tk.LabelFrame(self, text="Estado:")
        lf_connection.grid(column=1, row=0, padx=5, pady=10)

        b_connect = tk.Button(lf_connection,
                                text="Conectar todos",
                                command=lambda: self.loop.create_task(self.connect_all()))

        b_connect.grid(column=1, row=3, padx=4, pady=4)
        b_close = tk.Button(lf_connection,
                            text="Desconectar todos",
                            command= lambda: self.loop.create_task(self.disconnect_all()))
        b_close.grid(column=1, row=4, padx=4, pady=4)
        self.txt_chest = tk.Label(lf_connection,
                                background=COLOR_NOT_FOUND,
                                text="  Tipo 3  ")
        self.txt_chest.grid(column=1, row=2, padx=4, pady=4)
        self.txt_leg = tk.Label(lf_connection,
                            background=COLOR_NOT_FOUND,
                            text="  Tipo 1  ")
        self.txt_leg.grid(column=1, row=0, padx=4, pady=4)
        self.txt_wrist = tk.Label(lf_connection,
                                background=COLOR_NOT_FOUND,
                                text="  Tipo 2  ")
        self.txt_wrist.grid(column=1, row=1, padx=4, pady=4)

        lf_measurement = tk.LabelFrame(self, text="Medición:")
        lf_measurement.grid(column=2, row=0, padx=5, pady=10)
        b_start = tk.Button(lf_measurement,
                            text="Iniciar",
                            command=lambda: self.loop.create_task(self.start_measurement()))
        b_start.grid(column=2, row=0, padx=4, pady=4)
        b_stop = tk.Button(lf_measurement, 
                           text="Detener", 
                           command = lambda: self.loop.create_task(self.stop_measurement()))
        b_stop.grid(column=2, row=1, padx=4, pady=4)

    async def show(self):
        """Muestra la ventana y comienza el bucle de eventos."""

        while True:
            self.update()
            await asyncio.sleep(.1)

    def on_close(self):
        """Detiene el bucle de eventos y cierra la ventana."""

        self.loop.stop()
        super().destroy()

    async def discover_devices(self):
        """Busca dispositivos BLE disponibles y los muestra en la lista de dispositivos."""

        self.restart_txt()
        discovered = await BleakScanner.discover()
        devices = [(d.name, d.address) for d in discovered]
        self.devices_list.delete(0, tk.END)
        for device in devices:
            if device[0] == 'ChestMonitor':
                self.type3.address = device[1]
                self.type3.name = device[0]
                self.txt_chest.config(background=COLOR_FOUND)
            if device[0] == 'WristMonitor':
                self.type2.address = device[1]
                self.type2.name = device[0]
                self.txt_wrist.config(background=COLOR_FOUND)
            if device[0] == 'LegMonitor':
                self.type1.address = device[1]
                self.type1.name = device[0]
                self.txt_leg.config(background=COLOR_FOUND)
            self.devices_list.insert(tk.END, f"{device[0]} {device[1]}")
        if connections:
            for name,address in connections:
                if address == self.type3.address:
                    self.txt_chest.config(background=COLOR_CONNECT)
                if address == self.type2.address:
                    self.txt_wrist.config(background=COLOR_CONNECT)
                if address == self.type1.address:
                    self.txt_leg.config(background=COLOR_CONNECT)
                self.devices_list.insert(tk.END, f"{name} {address}")

    async def connect_device(self):
        """Conecta el dispositivo seleccionado de la lista de dispositivos."""

        selected = self.devices_list.curselection()
        if not selected:
            messagebox.showerror("Error de conexión", "Dispositivo no seleccionado.")
            return
        address = self.devices_list.get(selected[0]).split(" ")[1]
        name = self.devices_list.get(selected[0]).split(" ")[0]
        if (name,address) in connections and connections[(name,address)].is_connected:
            messagebox.showerror("Error de conexión", "Dispositivo ya conectado.")
            return
        try:
            connection = BleakClient(address)
            await connection.connect()
            self.check_type(address, connection)
            connections[(name,address)] = connection
            self.initialite_blemanager(address)
            messagebox.showinfo("Conexión", "Dispositivo conectado exitosamente.")
        except Exception as e:
            messagebox.showerror("Error de conexión", "Dispositivo no disponible")


    def check_type(self, address, connection: BleakClient):
        """Actualiza el color de los labels de estado de los dispositivos encontrados y conectados."""

        if address == self.type1.address and connection.is_connected:
            self.txt_leg.config(background=COLOR_CONNECT)
        elif address == self.type1.address and not connection.is_connected:
            self.txt_leg.config(background=COLOR_FOUND)
        if  address == self.type2.address and connection.is_connected:
            self.txt_wrist.config(background=COLOR_CONNECT)
        elif  address == self.type2.address and not connection.is_connected:
            self.txt_wrist.config(background=COLOR_FOUND)
        if address == self.type3.address and connection.is_connected:
            self.txt_chest.config(background=COLOR_CONNECT)
        elif  address == self.type3.address and not connection.is_connected:
            self.txt_chest.config(background=COLOR_FOUND)
    
    def restart_txt(self):
        """Reinicia el color de los labels de estado de los dispositivos."""

        self.txt_leg.config(background=COLOR_NOT_FOUND)
        self.txt_wrist.config(background=COLOR_NOT_FOUND)
        self.txt_chest.config(background=COLOR_NOT_FOUND)

    async def disconnect_device(self):
        """Desconecta el dispositivo seleccionado."""

        selected = self.devices_list.curselection()
        if not selected:
            messagebox.showerror("Error de desconexión", "Dispositivo no seleccionado.")
            return
        address = self.devices_list.get(selected[0]).split(" ")[1]
        name = self.devices_list.get(selected[0]).split(" ")[0]
        if (name,address) not in connections:
            messagebox.showerror("Error de desconexión", "Dispositivo no conectado.")
            return
        try:
            connection = connections[(name,address)]
            await connection.disconnect()
            self.check_type(address, connection)
            self.restart_blemanager(address)
            connections.pop((name,address))
            messagebox.showinfo("Desconexión", "Dispositivo desconectado correctamente.")
        except Exception as e:
            messagebox.showerror("Error de desconexión", "Dispositivo no disponible")

    async def disconnect_all(self):
        """Desconecta todos los dispositivos conectados."""

        global connections
        connections_copy = connections.copy()
        for name,address in connections.keys():
            connection = connections[(name,address)]
            await connection.disconnect()
            self.check_type(address, connection)
            self.restart_blemanager(address)
            connections_copy.pop((name,address))
        connections = connections_copy
        messagebox.showinfo("Desconexión", "Todos los dispositivos desconectados correctamente.")
        return
    
    async def connect_all(self):
        """Conecta todos los dispositivos encontrados en la lista de dispositivos."""

        if not self.type1 and not self.type2 and not self.type3:
            messagebox.showerror("Error de conexión", "No se ha encontrado ningún dispositivo")
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
        messagebox.showinfo("Conexión", "Todos los dispositivos conectados correctamente.")
        return
    
    def initialite_blemanager(self, address):
        """Inicializa los valores de los dispositivos BLE que se conectan"""

        if not self.type1 and not self.type2 and not self.type3:
            messagebox.showerror("Error de conexión", "No se ha encontrado ningún dispositivo")
            return
        if not connections:
            messagebox.showerror("Error de conexión", "No se ha conectado ningún dispositivo")
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

    # TODO: procesar los datos recibidos de los dispositivos
    async def start_measurement(self):
        """Inicia la medición de los dispositivos conectados."""
        if not connections:
            messagebox.showerror("Error de medición", "No se ha conectado ningún dispositivo")
            return
        connected_addresses = [address for _,address in connections.keys()]
        if self.type1.address in connected_addresses and not self.type1 in self.subscribed_connections:
            manager = self.MeasurementManager(self.type1, self)
            self.subscribed_connections.append(self.type1)
            await connections[("LegMonitor",self.type1.address)].start_notify(CH_FRAME, manager.handle_notification)
        if self.type2.address in connected_addresses and not self.type2 in self.subscribed_connections:
            manager = self.MeasurementManager(self.type2, self)
            self.subscribed_connections.append(self.type2)
            await connections[("WristMonitor",self.type2.address)].start_notify(CH_FRAME, manager.handle_notification)
        if self.type3.address in connected_addresses and not self.type3 in self.subscribed_connections:
            manager = self.MeasurementManager(self.type3, self)
            self.subscribed_connections.append(self.type3)
            await connections[("ChestMonitor",self.type3.address)].start_notify(CH_FRAME, manager.handle_notification)
    
    async def stop_measurement(self):
        """Detiene la medición de los dispositivos conectados."""

        for tuple in connections:
            connection = connections[tuple]
            await connection.stop_notify(CH_FRAME)
        self.subscribed_connections = []

    class MeasurementManager:
        def __init__(self, blemanager: blemanager, window):
            if isinstance(window, Window):
                self.mblemanager = blemanager
                self.window = window
            
        def handle_notification(self, sender: str, data: bytearray):
            """Procesa las notificaciones de las características."""
            if self.mblemanager.name == "LegMonitor":
                r_acc, r_gyr, r_bat, r_ta = self.getLegData(data)
                print(r_acc, r_gyr, r_bat, r_ta)
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
                # TODO: procesar los datos recibidos del pecho

        def getLegData(self, data):
            """Obtiene los datos de la pierna"""

            if len(data) != 28:
                messagebox.showerror("Error de datos", "Longitud incorrecta")
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
                messagebox.showerror("Error de datos", "Longitud incorrecta")
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
                messagebox.showerror("Error de datos", "Longitud incorrecta")
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