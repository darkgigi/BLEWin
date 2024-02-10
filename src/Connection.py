import asyncio
from bleak import BleakScanner
from bleak import BleakClient
from bleak import BleakError

async def discover():
    devices = await BleakScanner.discover()
    return devices

class Connection:
    def __init__(self, address):
        self.address = address

    async def connect(self):
        try:
            async with BleakClient(self.address) as client:
                return client.is_connected
        except BleakError:
            return False

    async def disconnect(self):
        async with BleakClient(self.address) as client:
            await client.disconnect()
