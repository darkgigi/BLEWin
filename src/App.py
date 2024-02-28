import tkinter as tk
from tkinter import messagebox
from bleak import *
import asyncio
import threading
import subprocess

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
        self.loop = loop
        self.type1 = None
        self.type2 = None
        self.type3 = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
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

        lf_connection = tk.LabelFrame(self, text="Conexiones:")
        lf_connection.grid(column=1, row=0, padx=5, pady=10)

        b_connect = tk.Button(lf_connection,
                                text="Conectar todos",
                                command=None,
                                state="disabled")  # ,

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

    async def show(self):
        while True:
            self.update()
            await asyncio.sleep(.1)

    def on_close(self):
        self.loop.stop()
        super().destroy()

    async def discover_devices(self):
        self.restart_txt()
        discovered = await BleakScanner.discover()
        devices = [(d.name, d.address) for d in discovered]
        self.devices_list.delete(0, tk.END)
        for device in devices:
            if device[0] == 'ChestMonitor':
                self.type3 = device[1]
                self.txt_chest.config(background=COLOR_FOUND)
            if device[0] == 'WristMonitor':
                self.type2 = device[1]
                self.txt_wrist.config(background=COLOR_FOUND)
            if device[0] == 'LegMonitor':
                self.type1 = device[1]
                self.txt_leg.config(background=COLOR_FOUND)
            self.devices_list.insert(tk.END, f"{device[0]} {device[1]}")
        if connections:
            for name,address in connections:
                if address == self.type3:
                    self.txt_chest.config(background=COLOR_CONNECT)
                if address == self.type2:
                    self.txt_wrist.config(background=COLOR_CONNECT)
                if address == self.type1:
                    self.txt_leg.config(background=COLOR_CONNECT)
                self.devices_list.insert(tk.END, f"{name} {address}")

    async def connect_device(self):
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
            messagebox.showinfo("Conexión", "Dispositivo conectado exitosamente.")
        except Exception as e:
            messagebox.showerror("Error de conexión", "Dispositivo no disponible")


    def check_type(self, address, connection: BleakClient):
        if address == self.type1 and connection.is_connected:
            self.txt_leg.config(background=COLOR_CONNECT)
        elif address == self.type1 and not connection.is_connected:
            self.txt_leg.config(background=COLOR_FOUND)
        if address == self.type2 and connection.is_connected:
            self.txt_wrist.config(background=COLOR_CONNECT)
        elif address == self.type2 and not connection.is_connected:
            self.txt_wrist.config(background=COLOR_FOUND)
        if address == self.type3 and connection.is_connected:
            self.txt_chest.config(background=COLOR_CONNECT)
        elif address == self.type3 and not connection.is_connected:
            self.txt_chest.config(background=COLOR_FOUND)
    
    def restart_txt(self):
        self.txt_leg.config(background=COLOR_NOT_FOUND)
        self.txt_wrist.config(background=COLOR_NOT_FOUND)
        self.txt_chest.config(background=COLOR_NOT_FOUND)

    async def disconnect_device(self):
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
            connections.pop((name,address))
            messagebox.showinfo("Desconexión", "Dispositivo desconectado correctamente.")
        except Exception as e:
            messagebox.showerror("Error de desconexión", "Dispositivo no disponible")

    async def disconnect_all(self):
        global connections
        connections_copy = connections.copy()
        for name,address in connections.keys():
            connection = connections[(name,address)]
            await connection.disconnect()
            self.check_type(address, connection)
            connections_copy.pop((name,address))
        connections = connections_copy
        messagebox.showinfo("Desconexión", "Todos los dispositivos desconectados correctamente.")
        return
    
if __name__ == "__main__":
    install_dependencies()
    try:
        asyncio.run(App().exec())
    except RuntimeError as e:
        if str(e) == 'Event loop stopped before Future completed.':
            pass
        else:
            raise e