import asyncio
import pytest
from app import Window

COLOR_NOT_FOUND = "#e85a5a"
COLOR_FOUND = "#82c2f0"
COLOR_CONNECT = "#54ba32"
COLOR_BUTTON_FOCUS = '#f0982e'

class TestWindow:
    def setup_method(self, method):
        self.window = Window(asyncio.get_event_loop())

    def teardown_method(self, method):
        self.window.destroy()

    @pytest.mark.asyncio
    async def test_discover_devices(self):

        # Comprobar que no se han encontrado dispositivos
        assert self.window.txt_chest.cget('fg_color') == COLOR_NOT_FOUND
        assert self.window.txt_leg.cget('fg_color') == COLOR_NOT_FOUND

        # Llamar al SUT
        await self.window.discover_devices()

        # Comprobar que se han encontrado los dispositivos de Tipo 1 y 3
        devices_names = [self.window.radiobuttons[i].cget('text') for i in range(len(self.window.radiobuttons))]
        assert 'ChestMonitor 4C:11:AE:91:17:FA' in devices_names
        assert 'LegMonitor 4C:11:AE:8C:81:FA' in devices_names

        # Comprobar que los tipos están correctos
        assert self.window.type3.address == '4C:11:AE:91:17:FA'
        assert self.window.type3.name == 'ChestMonitor'
        assert self.window.type1.address == '4C:11:AE:8C:81:FA'
        assert self.window.type1.name == 'LegMonitor'

        # Comprobar que los labels están actualizados
        assert self.window.txt_chest.cget('fg_color') == COLOR_FOUND
        assert self.window.txt_leg.cget('fg_color') == COLOR_FOUND

    @pytest.mark.asyncio
    async def test_connect_and_disconnect_device(self):
        # Comprobar que no se han conectado los dispositivos
        assert self.window.txt_chest.cget('fg_color') == COLOR_NOT_FOUND
        assert self.window.txt_leg.cget('fg_color') == COLOR_NOT_FOUND

        # Llamar al SUT
        await self.window.discover_devices()
        legMonitor = self.window.type1.name + ' ' + self.window.type1.address
        chestMonitor = self.window.type3.name + ' ' + self.window.type3.address
        self.window.radio_var.set(legMonitor)
        
        await self.window.connect_device()
        self.window.radio_var.set(chestMonitor)
        await self.window.connect_device()

        # Comprobar que los dispositivos están conectados
        assert self.window.txt_chest.cget('fg_color') == COLOR_CONNECT
        assert self.window.txt_leg.cget('fg_color') == COLOR_CONNECT

        #Llamar al SUT
        self.window.radio_var.set(legMonitor)
        await self.window.disconnect_device()
        self.window.radio_var.set(chestMonitor)
        await self.window.disconnect_device()

        # Comprobar que los dispositivos están desconectados
        assert self.window.txt_chest.cget('fg_color') == COLOR_FOUND
        assert self.window.txt_leg.cget('fg_color') == COLOR_FOUND

if __name__ == '__main__':
    pytest.main()
