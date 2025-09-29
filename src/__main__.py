import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow
from ui_contato import Ui_MainWindow
from bleak import BleakClient, BleakScanner # biblioteca de BLE
from bleak.backends.characteristic import BleakGATTCharacteristic
from qasync import QEventLoop, asyncClose, asyncSlot
from contato_cli.player import Player # Classe de interação MIDI com o loopMIDI

# Consultar no código embarcado
TOUCH_CHARACTERISTIC_UUID = '62c84a29-95d6-44e4-a13d-a9372147ce21'
GYRO_CHARACTERISTIC_UUID = '9b7580ed-9fc2-41e7-b7c2-f63de01f0692'
ACCEL_CHARACTERISTIC_UUID = 'f62094cf-21a7-4f71-bb3f-5a5b17bb134e' 

player = Player("descontato_d")

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.connect_ble()

    @asyncSlot()
    async def connect_ble(self):
        print('Scan')
        def bleak_gyro_callback(characteristic: BleakGATTCharacteristic, data: bytearray): 
            gyro = int.from_bytes(data, 'little', signed=True)
            self.ui.lcdNumber.display(gyro)
            player.gyro = gyro
            player.update()
        def bleak_accel_callback(characteristic: BleakGATTCharacteristic, data: bytearray): 
            player.accel = int.from_bytes(data, 'little', signed=True)
        def bleak_touch_callback(characteristic: BleakGATTCharacteristic, data: bytearray):
            touch = int.from_bytes(data, 'little', signed=False)
            player.touch = touch

        while True:
            device = await BleakScanner.find_device_by_name("Contato")
            if device is None:
                print("Nenhum dispositivo encontrado, aguarde a procura novamente")
                await asyncio.sleep(30)
                continue

            disconnect_event = asyncio.Event()
                
            print("Conectando...")
            async with BleakClient(
                device, disconnected_callback=lambda c: disconnect_event.set()) as client:
                print("Conectado")
                await client.start_notify(GYRO_CHARACTERISTIC_UUID, bleak_gyro_callback)
                await client.start_notify(ACCEL_CHARACTERISTIC_UUID, bleak_accel_callback)
                await client.start_notify(TOUCH_CHARACTERISTIC_UUID, bleak_touch_callback)
                await disconnect_event.wait()
                print("Desconectado")


async def main(app):
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    main_window = MainWindow()
    main_window.show()
    await app_close_event.wait()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    asyncio.run(main(app), loop_factory=QEventLoop)