from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import asyncio
import math 
from qasync import asyncSlot
from contato_cli.player import Player # Classe de interação MIDI com o loopMIDI
from bleak import BleakClient, BleakScanner # biblioteca de BLE
from bleak.backends.characteristic import BleakGATTCharacteristic

TOUCH_CHARACTERISTIC_UUID = '62c84a29-95d6-44e4-a13d-a9372147ce21'
GYRO_CHARACTERISTIC_UUID = '9b7580ed-9fc2-41e7-b7c2-f63de01f0692'
ACCEL_CHARACTERISTIC_UUID = 'f62094cf-21a7-4f71-bb3f-5a5b17bb134e' 

class GyroDisplay(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        # Init UI
        self.setGeometry(300, 300, 300, 300)
        self.value = 0
        self.center = self.rect().center()
        self.radius = min(self.width(), self.height()) // 2 - 10
        self.markers = []
        self.ble_update()
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)        

        # Fill background with translucent color
        bg_color = QColor(256, 256, 256, 256)  # RGBA, alpha=128 for 50% translucency
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())
        border_color = QColor("gray")  # Semi-transparent border
        pen = QPen(border_color, 4)
        painter.setPen(pen)
        painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))

        # Draw dial
        painter.save()
        painter.translate(self.center)
        painter.rotate(-self.value + 270)
        painter.setPen(QPen(QColor("red"), 3))
        painter.drawLine(0, 0, 0, self.radius - 30)
        painter.restore()

        # Draw labels
        painter.setPen(QPen(QColor("dark-gray"), 2))
        font_metrics = painter.fontMetrics()
        for i_label in range(1, 13):
            angle = ((i_label * 30) % 360) - 90
            painter.save()
            painter.translate(self.center)
            painter.rotate(angle)
            painter.translate(0, -self.radius + 10)
            painter.rotate(-angle)
            text = f"{-angle + 90}º"
            text_width = font_metrics.horizontalAdvance(text)
            text_height = font_metrics.height()
            painter.drawText(-text_width // 2, text_height // 2, text)
            painter.restore()


        # Draw markers
        painter.setPen(QPen(QColor("red"), 10))
        for i_marker in self.markers:
            painter.save()
            painter.translate(self.center)
            painter.rotate(-i_marker + 90)
            painter.translate(0, -self.radius)
            painter.drawPoint(0, 0)
            painter.restore()

        painter.end()
    # Mouse events

    # def mouseMoveEvent(self, event):
    #     x, y = event.pos().x() - (self.width() / 2), event.pos().y() - (self.height() / 2)
    #     print(int(math.atan2(y, x) / math.pi * 180))

    def mouseDoubleClickEvent(self, event):
        x, y = event.pos().x() - (self.width() / 2), event.pos().y() - (self.height() / 2)
        self.markers.append(-int(math.atan2(y, x) / math.pi * 180))
        print(self.markers)
        self.update()

    @asyncSlot()
    async def ble_update(self):
        player = Player("descontato_d")
        print('Scan')
        def bleak_gyro_callback(characteristic: BleakGATTCharacteristic, data: bytearray): 
            gyro = int.from_bytes(data, 'little', signed=True)
            player.gyro = gyro
            self.value = gyro
            player.update()
            self.update()
            print(f'roll: {player.gyro} acc_x: {player.accel} t: {player.touch}')
        def bleak_accel_callback(characteristic: BleakGATTCharacteristic, data: bytearray):  
            player.accel = int.from_bytes(data, 'little', signed=True)
        def bleak_touch_callback(characteristic: BleakGATTCharacteristic, data: bytearray):
            player.touch = int.from_bytes(data, 'little', signed=False)
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