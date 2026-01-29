import os
import sys
import math
import json
import asyncio
import struct
from enum import Enum

from PyQt6.QtCore import Qt, QPointF, QTimer, pyqtSignal, QEvent
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QComboBox,
    QLabel, QSpinBox, QVBoxLayout, QHBoxLayout, QDialog,
    QGridLayout, QFileDialog, QListWidget, QListWidgetItem, QSplashScreen, QDial
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPixmap, QPainterPath,
    QTransform, QIcon, QFont
)

from qasync import QApplication as QAsyncApplication, QEventLoop, asyncSlot
import rtmidi
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

SECTIONS_CHAR_UUID = '251beea3-1c81-454f-a9dd-8561ec692ded'
STATUS_CHARACTERISTIC_UUID = 'f8d968fe-99d7-46c4-a61c-f38093af6ec8'
ACCEL_SENS_CHARACTERISTIC_UUID = 'c7f2b2e2-1a2b-4c3d-9f0a-123456abcdef'
CALIBRATE_CHAR_UUID = 'b4d0c9f8-3b9a-4a4e-93f2-2a8c9f5ee7a2'
BLE_MIDI_CHAR_UUID = '7772e5db-3868-4112-a1a9-f2669d106bf3'
DIR_CHAR_UUID = "a1b2c3d4-0001-4b33-a751-6ce34ec4c701"
# LEGATO_CHAR_UUID = "a1b2c3d4-0002-4b33-a751-6ce34ec4c702"
BLE_MIDI_SERVICE_UUID = '03b80e5a-ede8-4b33-a751-6ce34ec4c700'

class AccelLevel(Enum):
    SOFT = 800
    MEDIUM = 1250
    HARD = 1600
PRIMARY_COLOR = QColor(100, 180, 255)
PORT_INDEX = 0

class SplashScreen(QSplashScreen):
    def __init__(self):
        max_size = 500
        image_path = os.path.join(os.path.dirname(__file__), "splash.png")
        pix = QPixmap(image_path)
        pix = pix.scaled(
            max_size, max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        super().__init__(pix)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About")
        self.setFixedSize(360, 240)

        layout = QVBoxLayout(self)

        # --- About text ---
        title = QLabel("BLE MIDI Client")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        desc = QLabel(
            "A BLE sensor → MIDI bridge.\n\n"
            "Built for low-latency experimentation."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()

        # --- Bottom logos (placeholder) ---
        logos_layout = QHBoxLayout()
        logos_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        splash = QPixmap(os.path.join(os.path.dirname(__file__), "splash.png"))  # reuse splash as placeholder
        splash = splash.scaled(
            64, 64,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        logo_label = QLabel()
        logo_label.setPixmap(splash)

        logos_layout.addWidget(logo_label)

        layout.addLayout(logos_layout)


NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def name_to_midi(name):
    if '#' in name[:2]: note=name[:2]; octave=int(name[2:])
    else: note=name[0]; octave=int(name[1:])
    idx=NOTE_NAMES.index(note)
    return max(0,min(127,(octave+1)*12+idx))

class ToggleEnterComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedWidth(60)

        # apply explicit instance stylesheet to ensure it's used across platforms
        style = f"""
            QComboBox {{
                background:#f8f8f8; border:1px solid #bbb;
                color:#333; font-size:11px; padding:1px 2px;
                border-radius:4px; min-height:18px;
            }}
            QComboBox:hover {{
                border:1px solid {PRIMARY_COLOR.name()};
                background:#f2f9ff;
            }}
            QComboBox:focus {{
                border:1px solid {PRIMARY_COLOR.name()};
                background:#e8f4ff; color:#222;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
            }}
        """
        self.setStyleSheet(style)

    def keyPressEvent(self, e):
        key = e.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if getattr(self.view, "isVisible", lambda: False)():
                self.hidePopup()
            else:
                self.showPopup()
        else:
            super().keyPressEvent(e)

class WNotesSelector(QFrame):
    signalInstrumentChanged = pyqtSignal(int, str)
    signalNotes = pyqtSignal(list)

    def __init__(self, sections = 6, ticks = 30, parent = None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.margin = 15
        self.offset = 80
        self.sections = sections
        self.combos = []
        self.ticks = ticks
        self.tick_long = 14
        self.tick_short = 8

        self.gyro = 0
        self.touch = True
        self.pulse_phase = 0.0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.updatePulse)
        self.pulse_timer.start(30)

        self.notes = [f"{note}{octave}" for octave in range(1,6) for note in
                      NOTE_NAMES]

        self.instruments = [
            ("🎹","Acoustic Grand Piano"), ("🎼","Bright Acoustic Piano"),
            ("🎵","Electric Grand Piano"), ("🎶","Honky-tonk Piano"),
            ("🎧","Electric Piano 1"), ("🎛️","Electric Piano 2"),
            ("🎻","Harpsichord"), ("🎸","Clavinet"),
            ("✨","Celesta"), ("🔔","Glockenspiel"),
            ("📦","Music Box"), ("🛎️","Vibraphone"),
            ("🥁","Marimba"), ("🎺","Xylophone"),
            ("⛓️","Tubular Bells"), ("🎶","Dulcimer")
        ]
        self.current_instrument_index = 0
        icon, _ = self.instruments[self.current_instrument_index]
        self.center_button = QPushButton(icon, self)
        self.center_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.center_button.setFixedSize(90, 90)
        self.center_button.setStyleSheet(f"""
            QPushButton {{ border-radius:45px; font-size:32px;
                background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fff, stop:1 #e6e6e6);
                border:2px solid #bfbfbf; }}
            QPushButton:focus {{ border:2px solid {PRIMARY_COLOR.name()}; }}
        """)
        self.center_button.clicked.connect(self.showInstrumentSelector)

        self.hand_icon = QPixmap(20,20)
        self.hand_icon.fill(Qt.GlobalColor.transparent)
        p = QPainter(self.hand_icon)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.moveTo(10,2); path.lineTo(18,10); path.lineTo(10,18)
        path.lineTo(9,14); path.lineTo(14,10); path.lineTo(9,6); path.closeSubpath()
        pen = QPen(QColor(100,180,255),2)
        p.setPen(pen); p.drawPath(path); p.end()

    def updatePulse(self):
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)

    def setSections(self, count):
        count = int(count)
        old_notes = [c.currentText() for c in self.combos]
        self.sections = count
        if count <= len(old_notes):
            new_notes = old_notes[:count]
        else:
            new_notes = old_notes + ["C3"] * (count - len(old_notes))
        for c in getattr(self,"combos",[]):
            c.deleteLater()
        self.combos = []
        for note in new_notes:
            combo = ToggleEnterComboBox(self)
            combo.addItems(self.notes)
            combo.blockSignals(True)
            combo.currentIndexChanged.connect(lambda i: self.signalNotes.emit([c.currentText() for c in self.combos]))
            combo.blockSignals(False)
            combo.setCurrentText(note)
            combo.show()
            self.combos.append(combo)
        self.signalNotes.emit([c.currentText() for c in self.combos])

        # Update position
        w,h = self.width(), self.height()
        cx,cy = w/2 - self.offset, h/2
        r = min((h/2)-self.margin, (w-cx)-self.margin)
        section_angle = math.pi / self.sections
        start_ang = -math.pi/2
        bw,bh = self.center_button.width(), self.center_button.height()
        self.center_button.move(int(cx-bw/2), int(cy-bh/2))
        for i, combo in enumerate(self.combos):
            mid = start_ang + section_angle * (i + 0.5)
            rr = r * 0.6
            x = cx + rr * math.cos(mid) - combo.width()/2
            y = cy + rr * math.sin(mid) - combo.height()/2
            combo.move(int(x), int(y))

        self.update()

    def showInstrumentSelector(self):
        dialog = QDialog(self); dialog.setWindowTitle("Select Instrument"); dialog.setModal(True)
        grid = QGridLayout(dialog); grid.setSpacing(12); grid.setContentsMargins(20,20,20,20)
        for i,(icon,name) in enumerate(self.instruments):
            btn = QPushButton(f"{icon}\n{name}")
            btn.setFixedSize(110,70)
            if i == self.current_instrument_index:
                btn.setStyleSheet("background-color:#d0e6ff;border:2px solid #2b72ff;border-radius:10px;font-size:13px;font-weight:bold;")
            else:
                btn.setStyleSheet("background-color:#e6e6e6;border:1px solid #ccc;border-radius:10px;font-size:13px;")
            btn.clicked.connect(lambda _, idx=i: self.setInstrument(idx, dialog))
            grid.addWidget(btn, i//4, i%4)
        dialog.exec()

    def setInstrument(self, index, dialog):
        self.current_instrument_index = index
        icon,name = self.instruments[index]
        self.center_button.setText(icon)
        self.signalInstrumentChanged.emit(index, name)
        if dialog: dialog.accept()

    def paintEvent(self, _):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h = self.width(), self.height()
        cx,cy = w/2 - self.offset, h/2
        r = min((h/2) - self.margin, (w-cx) - self.margin)
        section_angle = math.pi / self.sections
        selected_tick = int(((self.gyro * math.pi / -180) + math.pi / 2) / (math.pi / self.ticks))
        selected_section = int(((self.gyro * math.pi / -180) + math.pi / 2) / (math.pi / self.sections))
        start_ang, end_ang = -math.pi/2, math.pi/2

        for i in range(self.ticks+1):
            t = start_ang + (end_ang-start_ang)*(i/self.ticks)
            ox,oy = cx + r*math.cos(t), cy + r*math.sin(t)
            tl = self.tick_long if i%5==0 else self.tick_short
            ix,iy = cx + (r-tl)*math.cos(t), cy + (r-tl)*math.sin(t)
            if i == selected_tick:
                ang_deg = math.degrees(t)
                rotated = self.hand_icon.transformed(QTransform().rotate(ang_deg), Qt.TransformationMode.SmoothTransformation)
                icon_r = r + 10
                ix = cx + icon_r*math.cos(t) - rotated.width()/2
                iy = cy + icon_r*math.sin(t) - rotated.height()/2
                painter.drawPixmap(int(ix), int(iy), rotated)
                continue
            highlight = (selected_section >=0 and selected_section * section_angle <= t + math.pi/2 <= (selected_section + 1) * section_angle and self.touch)
            if highlight:
                pulse = 0.5 + 0.5*math.sin(self.pulse_phase)
                color = QColor(int(PRIMARY_COLOR.red()*(0.8+0.2*pulse)),
                               int(PRIMARY_COLOR.green()*(0.8+0.2*pulse)),
                               int(PRIMARY_COLOR.blue()*(0.8+0.2*pulse)))
                pen = QPen(color,3)
            else:
                pen = QPen(QColor(60,60,60),2)
            painter.setPen(pen)
            painter.drawLine(QPointF(ix,iy), QPointF(ox,oy))

        painter.setPen(QColor(100,100,120,150))
        f = painter.font(); 
        f.setPointSize(9); 
        painter.setFont(f)
        painter.drawText(int(cx + r + 30), int(cy + 4), "0º")

        for i in range(self.sections + 1):
            t = start_ang + section_angle * i
            inner_r = r * 0.3
            outer_r = r * 0.8
            x1,y1 = cx + inner_r*math.cos(t), cy + inner_r*math.sin(t)
            x2,y2 = cx + outer_r*math.cos(t), cy + outer_r*math.sin(t)
            if i in (selected_section, selected_section + 1) and self.touch:
                pulse = 0.5 + 0.5*math.sin(self.pulse_phase)
                color = QColor(int(PRIMARY_COLOR.red()*(0.7+0.3*pulse)),
                               int(PRIMARY_COLOR.green()*(0.7+0.3*pulse)),
                               int(PRIMARY_COLOR.blue()*(0.7+0.3*pulse)), 220)
                pen = QPen(color,2)
            else:
                pen = QPen(QColor(PRIMARY_COLOR.red(), PRIMARY_COLOR.green(), PRIMARY_COLOR.blue(), 60),2)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1,y1), QPointF(x2,y2))

class MainWindow(QWidget):
    def __init__(self, selected_device = None):
        super().__init__()
        self.selected_device = selected_device
        self.ble_client = None
        self.midi_out_driver = rtmidi.MidiOut()
        self.ports = self.midi_out_driver.get_ports()
        self.setWindowTitle("Contato GUI")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icon.ico")))
        if self.ports:
            idx = max(0, min(PORT_INDEX, len(self.ports)-1))
            self.midi_out_driver.open_port(idx)
            print(f"rtmidi: porta {idx} aberta: {self.ports[idx]}")
        else:
            print("rtmidi: nenhuma porta de saída disponível.")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --------------- TOPBAR ---------------
        topbar = QHBoxLayout()
        topbar.setContentsMargins(6,6,6,6)
        topbar.setSpacing(6)
        save_btn = QPushButton("Salvar")
        load_btn = QPushButton("Abrir")
        calibrate_btn = QPushButton("Calibrar")
        about_btn = QPushButton("Sobre")
        def show_about(self):
            dialog = AboutDialog(self)
            dialog.exec()

        about_btn.clicked.connect(lambda: show_about(self))

        for b in (save_btn, load_btn, calibrate_btn, about_btn):
            b.setFixedSize(90, 26)
            b.setStyleSheet("QPushButton{border-radius:3px;background:#eaeaea;} QPushButton:hover{background:#dcdcdc}")
        save_btn.clicked.connect(self.save_setup)
        load_btn.clicked.connect(self.load_setup)
        calibrate_btn.clicked.connect(self.send_calibrate_command)
        topbar.addWidget(save_btn)
        topbar.addWidget(load_btn)
        topbar.addWidget(calibrate_btn)
        topbar.addStretch()
        topbar.addWidget(about_btn)
        topbar_frame = QFrame()
        topbar_frame.setLayout(topbar)
        topbar_frame.setFixedHeight(40)
        topbar_frame.setStyleSheet("background:#f4f4f4;border-bottom:1px solid #bfbfbf;")
        layout.addWidget(topbar_frame)
        # --------------- ---------------

        # --------------- NOTES SELECTOR ---------------
        self.selector = WNotesSelector(sections=6, ticks=60)
        self.selector.signalInstrumentChanged.connect(self.async_on_instrument_changed)
        self.selector.signalNotes.connect(self.async_write_sections)
        layout.addWidget(self.selector, alignment=Qt.AlignmentFlag.AlignCenter)
        # --------------- ---------------

        # --------------- DIVIDER ---------------
        divider = QFrame(); 
        divider.setFrameShape(QFrame.Shape.HLine); 
        divider.setStyleSheet("color:#cfcfcf;")
        layout.addWidget(divider)
        # --------------- ---------------
        
        # --------------- CONTROLS ---------------
        controls = QVBoxLayout()

        row = QHBoxLayout()
        notas_label = QLabel("Notas:")
        row.addWidget(notas_label)
        row.addStretch()
        self.notas_spin = QSpinBox()
        self.notas_spin.setRange(1,8)
        self.notas_spin.setValue(self.selector.sections)
        self.notas_spin.valueChanged.connect(self.selector.setSections)
        row.addWidget(self.notas_spin)
        controls.addLayout(row)

        row = QHBoxLayout()
        midi_label = QLabel("Saída MIDI:")
        row.addWidget(midi_label)
        self.midi_output_combo = QComboBox()
        self.channel_combo = QComboBox()
        self.channel_combo.addItems([str(i) for i in range(1,17)])
        self.midi_output_combo.addItems(self.ports)
        row.addWidget(self.midi_output_combo)
        self.midi_output_combo.currentIndexChanged.connect(self.on_midi_port_changed)
        row.addStretch()
        row.addWidget(QLabel("Canal:"))
        row.addWidget(self.channel_combo)
        controls.addLayout(row)

        row = QHBoxLayout()
        midi_label = QLabel("Sensibilidade:")
        row.addWidget(midi_label)
        row.addStretch()
        self.accel_combo = QComboBox()
        for level in AccelLevel:
            self.accel_combo.addItem(level.name.title(), level)  # show Soft/Medium/Hard
        self.accel_combo.setFixedWidth(110)
        self.accel_combo.currentIndexChanged.connect(self.async_write_accel_threshold)
        row.addWidget(self.accel_combo)
        controls.addLayout(row)

        row = QHBoxLayout()
        dir_label = QLabel("Direção:")
        row.addWidget(dir_label)
        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["Esquerda", "Direita"])
        self.dir_combo.setFixedWidth(110)
        self.dir_combo.currentIndexChanged.connect(self.async_write_direction)
        row.addWidget(self.dir_combo)
        controls.addLayout(row)

        layout.addLayout(controls)
        # --------------- ---------------

        if self.selected_device:
            asyncio.create_task(self.ble_connect_to_selected(self.selected_device))

    def ble_status_callback(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        gyro_x, accel_x, touch = struct.unpack("<hhB", data)
        self.selector.gyro = gyro_x
        self.selector.touch = touch
        self.selector.update()
        
    def ble_midi_callback(
        self,
        _: BleakGATTCharacteristic,
        data: bytearray
    ):
        raw = bytes(data)
        if len(raw) < 3:
            return

        msg = list(raw[-3:])
        print(msg)
        self.midi_out_driver.send_message(msg)

    def on_midi_port_changed(self, idx):
        self.midi_out_driver.close_port()
        self.midi_out_driver.open_port(idx)
        print(f"Porta MIDI alterada: {self.ports[idx]}")

    @asyncSlot(int, str)
    async def async_on_instrument_changed(self, index: int, name: str):
        prog = max(0, min(127, int(index)))
        ch = max(0, min(15, int(self.channel_combo.currentText()) - 1))

        print(f"Instrumento alterado: {name} (programa {prog}) no canal {ch+1}")
        try:
            status = 0xC0 | (ch & 0x0F)
            self.midi_out_driver.send_message([status, prog])
        except Exception as e:
            print("Erro ao enviar Program Change via rtmidi:", e)

    @asyncSlot(int)
    async def async_write_accel_threshold(self, idx: int):
        if not self.ble_client:
            return
        
        # get the enum object stored as userData
        enum_obj = self.accel_combo.itemData(idx)

        payload = enum_obj.value.to_bytes(2, "little", signed=True)
        await self.ble_client.write_gatt_char(ACCEL_SENS_CHARACTERISTIC_UUID, payload, response=True)
        print(f"Escreveu accel sensitivity: {enum_obj.name} ({enum_obj.value})")

    @asyncSlot(list)
    async def async_write_sections(self, notes_list):
        """Escreve seções/ notas no servidor"""
        if not self.ble_client:
            return
      
        midi_bytes = bytes([name_to_midi(n) for n in notes_list])
        await self.ble_client.write_gatt_char(SECTIONS_CHAR_UUID, midi_bytes, response=True)
        print("Escreveu sections no servidor:", list(midi_bytes))

    @asyncSlot(int)
    async def async_write_direction(self, idx: int):
        """Escreve 0 para Direita, 1 para Esquerda no server."""
        if not self.ble_client:
            print("Nenhum cliente BLE conectado — não pode escrever direção.")
            return
        val = bytes([1 if idx == 1 else 0])
        try:
            await self.ble_client.write_gatt_char(DIR_CHAR_UUID, val, response=True)
            print(f"Escreveu direção → {'Esquerda' if idx==1 else 'Direita'} ({val[0]})")
        except Exception as e:
            print("Erro escrevendo direção:", e)

    @asyncSlot()
    async def send_calibrate_command(self):
        if not self.ble_client:
            print("Nenhum cliente BLE conectado — não é possível calibrar.")
            return
        await self.ble_client.write_gatt_char(CALIBRATE_CHAR_UUID, bytes([0x01]), response=True)
        print("Comando de calibração enviado ao servidor.")

    def save_setup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Configuração", "", "JSON Files (*.json)")
        if not path:
            return
        data = {
            "sections": self.selector.sections,
            "instrument": self.selector.current_instrument_index,
            "notes": [c.currentText() for c in self.selector.combos],
            "midi_port_index": self.midi_output_combo.currentIndex(),
            "midi_channel": int(self.channel_combo.currentText())
        }
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            print("Configuração salva em", path)
        except Exception as e:
            print("Erro ao salvar configuração:", e)

    def load_setup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Configuração", "", "JSON Files (*.json)")
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print("Erro ao abrir arquivo:", e)
            return
        self.selector.setSections(data.get("sections"))
        for combo, note in zip(self.selector.combos, data.get("notes", [])):
            combo.setCurrentText(note)
        # self.selector.signal_write_combos()
        self.selector.setInstrument(data.get("instrument"), None)
        # aplica porta MIDI se disponível
        self.midi_output_combo.setCurrentIndex(int(data.get("midi_port_index")))
        self.channel_combo.setCurrentText(str(data.get("midi_channel")))
        print("Configuração carregada de", path)

    async def ble_connect_to_selected(self, device):
        async with BleakClient(device) as client:
            self.ble_client = client
            print(f"Conectado a {device.name} / {device.address}")
            
            # Ler sections
            section_bytes = await client.read_gatt_char(SECTIONS_CHAR_UUID)
            self.notas_spin.setValue(len(section_bytes))
            for i, b in enumerate(section_bytes):
                note = NOTE_NAMES[b%12]
                octave = (b // 12) -1
                octave = max(1,min(5,octave))
                if i < len(self.selector.combos):
                    combo = self.selector.combos[i]
                    combo.setCurrentText(f"{note}{octave}")
            
            # Ler SENSITIVITY e aplicar no UI (bloqueia sinais do combobox)
            sens_bytes = await client.read_gatt_char(ACCEL_SENS_CHARACTERISTIC_UUID)
            if sens_bytes and len(sens_bytes) >= 4:
                raw = int.from_bytes(sens_bytes[:4], "little", signed=True)
                level = min(AccelLevel, key=lambda lvl: abs(lvl.value - raw))
                self.accel_combo.blockSignals(True)
                idx = self.accel_combo.findText(level.name.title())
                if idx >= 0:
                    self.accel_combo.setCurrentIndex(idx)
                self.accel_combo.blockSignals(False)

            dir_bytes = await client.read_gatt_char(DIR_CHAR_UUID)
            if dir_bytes and len(dir_bytes) >= 1:
                idx = 1 if dir_bytes[0] != 0 else 0
                self.dir_combo.blockSignals(True)
                self.dir_combo.setCurrentIndex(idx)
                self.dir_combo.blockSignals(False)

            # # Notify subscribing
            await client.start_notify(BLE_MIDI_CHAR_UUID, self.ble_midi_callback)
            await client.start_notify(STATUS_CHARACTERISTIC_UUID, self.ble_status_callback)
            # await client.start_notify(, self.ble_touch_callback)
            # await client.start_notify(ACCEL_CHARACTERISTIC_UUID, self.ble_accel_callback)
            while True:
                await asyncio.sleep(1)

async def choose_device_before_opening(parent = None):
    devices = await BleakScanner.discover(timeout = 3.0, service_uuids = [BLE_MIDI_SERVICE_UUID])
    dlg = QDialog(parent)
    dlg.setWindowTitle("Selecionar dispositivo BLE")
    dlg.setModal(True)
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("Selecione o dispositivo 'Contato' para conectar:"))
    listw = QListWidget(dlg)
    listw.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    listw.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    for d in devices:
        display = f"{d.name or 'Unknown'} — {d.address}"
        item = QListWidgetItem(display)
        item.setData(Qt.ItemDataRole.UserRole, d)
        listw.addItem(item)
    layout.addWidget(listw)
    hl = QHBoxLayout()
    btn_ok = QPushButton("Conectar")
    btn_cancel = QPushButton("Cancelar")
    hl.addStretch()
    hl.addWidget(btn_ok)
    hl.addWidget(btn_cancel)
    layout.addLayout(hl)

    result = {'device': None}
    def on_ok():
        sel = listw.currentItem()
        if sel:
            result['device'] = sel.data(Qt.ItemDataRole.UserRole)
            dlg.accept()
        else:
            dlg.reject()
    def on_cancel():
        dlg.reject()

    btn_ok.clicked.connect(on_ok)
    btn_cancel.clicked.connect(on_cancel)

    listw.setCurrentRow(0)
    listw.setFocus()

    if dlg.exec():
        return result['device']
    return None

async def main(app):
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    # splash = SplashScreen()
    # splash.show()
    # await asyncio.sleep(3.0)

    selected = await choose_device_before_opening(None)
    # splash.close()
    if not selected:
        print("Nenhum dispositivo selecionado — encerrando.")
        app.quit()
        return

    win = MainWindow(selected_device = selected)
    win.setWindowTitle("Contato GUI")
    win.show()

    await app_close_event.wait()

if __name__ == "__main__":
    qapp = QAsyncApplication(sys.argv)
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main(qapp))
