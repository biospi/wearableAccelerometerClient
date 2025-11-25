# coding:utf-8

import asyncio
from dataclasses import dataclass
from functools import cached_property

import bleak
from PyQt5.QtCore import QObject, pyqtSignal
from bleak import BleakClient
from bleak.backends.device import BLEDevice

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

UART_SAFE_SIZE = 20


@dataclass
class QBleakClient(QObject):
    device: BLEDevice

    messageChanged = pyqtSignal(bytearray)
    messageDiconnect = pyqtSignal(int)

    def __post_init__(self):
        super().__init__()

    @cached_property
    def client(self) -> BleakClient:
        return BleakClient(self.device, disconnected_callback=self._handle_disconnect)

    async def start(self):
        print("Starting bleak client")
        await self.client.connect()
        await self.client.start_notify(UART_TX_CHAR_UUID, self._handle_read)

    async def stop(self):
        print(f"stopping bleak client")
        try:
            await self.client.disconnect()
        except asyncio.exceptions.CancelledError as e:
            print(e)

    async def write(self, data):
        try:
            await self.client.write_gatt_char(UART_RX_CHAR_UUID, data)
            print(f"sent:{data}")
        except bleak.exc.BleakError as e:
            print(e)
            print(f"self.client={self.client}")

    def _handle_disconnect(self, arg) -> None:
        print(f"Device was disconnected, goodbye. {arg}")
        data = -9
        self.messageDiconnect.emit(data)

    def _handle_read(self, _: int, data: bytearray) -> None:
        print(f"received:{data}")
        self.messageChanged.emit(data)
