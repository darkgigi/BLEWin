import asyncio
import unittest
from unittest.mock import patch
from app import Window

COLOR_NOT_FOUND = "#f26f68"
COLOR_FOUND = "#44dddd"
COLOR_CONNECT = "#33cc55"
COLOR_BUTTON_FOCUS = '#82c2f0'

class TestWindow(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.window = Window(asyncio.get_event_loop())


    async def test_discover_devices(self):

        # Comprobar que no se han encontrado dispositivos
        self.assertEqual(self.window.txt_chest.cget('background'), COLOR_NOT_FOUND)
        self.assertEqual(self.window.txt_leg.cget('background'), COLOR_NOT_FOUND)

        # Llamar al SUT
        await self.window.discover_devices()

        # Comprobar que se han encontrado los dispositivos de Tipo 1 y 3
        devices_names = [self.window.devices_list.get(i) for i in range(self.window.devices_list.size())]
        self.assertTrue('ChestMonitor 4C:11:AE:91:17:FA' in devices_names)
        self.assertTrue('LegMonitor 4C:11:AE:8C:81:FA' in devices_names)

        # Comprobar que los tipos están correctos
        self.assertEqual(self.window.type3.address, '4C:11:AE:91:17:FA')
        self.assertEqual(self.window.type3.name, 'ChestMonitor')
        self.assertEqual(self.window.type1.address, '4C:11:AE:8C:81:FA')
        self.assertEqual(self.window.type1.name, 'LegMonitor')

        # Comprobar que los labels están actualizados
        self.assertEqual(self.window.txt_chest.cget('background'), COLOR_FOUND)
        self.assertEqual(self.window.txt_leg.cget('background'), COLOR_FOUND)

if __name__ == '__main__':
    unittest.main()
