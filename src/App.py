# Contato GUI - cliente BLE-MIDI (pt-BR). Uses python-rtmidi (rtmidi) exclusively.

import os
import sys
import math
import json
import asyncio
from functools import partial

from PyQt6.QtCore import Qt, QPointF, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QComboBox,
    QLabel, QSpinBox, QVBoxLayout, QHBoxLayout, QDialog,
    QGridLayout, QFileDialog, QListWidget, QListWidgetItem, QSplashScreen
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPixmap, QPainterPath,
    QTransform, QIcon, QFont
)

from qasync import QApplication as QAsyncApplication, QEventLoop, asyncSlot

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# Use only python-rtmidi (rtmidi)
try:
    import rtmidi
except Exception as e:
    rtmidi = None
    print("Aviso: python-rtmidi (rtmidi) não disponível:", e)

SECTIONS_CHAR_UUID = '251beea3-1c81-454f-a9dd-8561ec692ded'
GYRO_CHARACTERISTIC_UUID = 'f8d968fe-99d7-46c4-a61c-f38093af6ec8'
TOUCH_CHARACTERISTIC_UUID = '55558523-eca8-4b78-ae20-97ed68c68c26'
CALIBRATE_CHAR_UUID = 'b4d0c9f8-3b9a-4a4e-93f2-2a8c9f5ee7a2'
BLE_MIDI_CHAR_UUID = '7772e5db-3868-4112-a1a9-f2669d106bf3'

PRIMARY_COLOR = QColor(100, 180, 255)
PORT_INDEX = 0

class SplashScreen(QSplashScreen):
    def __init__(self):
        max_size = 500
        image_path = os.path.join(os.path.dirname(__file__), "splash.png")
        if not os.path.exists(image_path):
            pm = QPixmap(400, 240)
            pm.fill(Qt.GlobalColor.white)
            p = QPainter(pm)
            p.setPen(QPen(QColor(100, 100, 120)))
            font = QFont()
            font.setPointSize(18)
            p.setFont(font)
            p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "Contato")
            p.end()
            super().__init__(pm)
            return

        pix = QPixmap(image_path)
        if pix.width() > max_size or pix.height() > max_size:
            pix = pix.scaled(
                max_size, max_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        super().__init__(pix)

_NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def midi_to_name(x):
    try: x=int(x)
    except: return "C3"
    if x<0: x=0
    note=_NOTE_NAMES[x%12]
    octave=(x//12)-1
    octave=max(1,min(5,octave))
    return f"{note}{octave}"

def name_to_midi(name):
    try:
        if '#' in name[:2]: note=name[:2]; octave=int(name[2:])
        else: note=name[0]; octave=int(name[1:])
        idx=_NOTE_NAMES.index(note)
        return max(0,min(127,(octave+1)*12+idx))
    except:
        return 60

class ToggleEnterComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedWidth(48)

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
            QComboBox QAbstractItemView {{
                background:#ffffff; border:1px solid #bbb;
                selection-background-color: {PRIMARY_COLOR.name()};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
            }}
        """
        self.setStyleSheet(style)

    def keyPressEvent(self, e):
        # Robust Enter/Return toggling fallback.
        if e is None or not hasattr(e, "key"):
            return super().keyPressEvent(e)

        key = e.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            try:
                view = self.view()
                if getattr(view, "isVisible", lambda: False)():
                    self.hidePopup()
                else:
                    self.showPopup()
            except Exception:
                # any unexpected error -> fallback to default behaviour
                super().keyPressEvent(e)
        else:
            super().keyPressEvent(e)

class SemicircleSectionWidget(QFrame):
    instrumentChanged = pyqtSignal(int, str)
    notesCached = pyqtSignal(list)

    def __init__(self, sections=6, ticks=30, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 450)
        self.margin = 30
        self.sections = sections
        self.ticks = ticks
        self.tick_long = 14
        self.tick_short = 8

        self.cached_notes = []
        self.suppress_emit = False   # <<-- add this line
        self.gyro_value = 0
        self.selected_tick = 0
        self.selected_section = 0
        self.touch_value = True
        self.pulse_phase = 0.0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.updatePulse)
        self.pulse_timer.start(30)

        self.notes = [f"{note}{octave}" for octave in range(1,6) for note in
                      ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]]

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

        self.combos = []
        self.createCombos()

        self.hand_icon = QPixmap(20,20)
        self.hand_icon.fill(Qt.GlobalColor.transparent)
        p = QPainter(self.hand_icon)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.moveTo(10,2); path.lineTo(18,10); path.lineTo(10,18)
        path.lineTo(9,14); path.lineTo(14,10); path.lineTo(9,6); path.closeSubpath()
        pen = QPen(QColor(100,180,255),2)
        p.setPen(pen); p.drawPath(path); p.end()

    def updateGyro(self, gyro):
        if int(gyro) != self.gyro_value:
            self.gyro_value = int(max(-89, min(89, gyro)))
            self.selected_tick = int(((self.gyro_value * math.pi / -180) + math.pi / 2) / (math.pi / self.ticks))
            self.selected_section = int(((self.gyro_value * math.pi / -180) + math.pi / 2) / (math.pi / self.sections))
            self.update()

    def updateTouch(self, touch):
        if touch != self.touch_value:
            self.touch_value = touch
            self.update()

    def updatePulse(self):
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)

    def createCombos(self):
        for c in getattr(self, "combos", []):
            c.deleteLater()
        self.combos = []
        for _ in range(self.sections):
            combo = ToggleEnterComboBox(self)
            combo.addItems(self.notes)
            combo.setCurrentText("C3")
            combo.setFixedWidth(60)
            # ensure instance stylesheet remains applied (some platforms override)
            combo.setStyleSheet(combo.styleSheet())
            combo.show()
            combo.currentTextChanged.connect(self.cacheCombos)
            self.combos.append(combo)
        self.updateComboboxPositions()
        self.cacheCombos()

    def cacheCombos(self, emit=True):
        """
        Cache current combo values. If emit is True and suppress_emit is False,
        emit notesCached. Use emit=False during bulk UI updates to avoid writing back.
        """
        self.cached_notes = [c.currentText() for c in self.combos]
        if emit and not getattr(self, "suppress_emit", False):
            self.notesCached.emit(self.cached_notes)

    def setSections(self, count):
        count = int(count)
        old_notes = [c.currentText() for c in getattr(self,"combos",[])]
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
            combo.setCurrentText(note)
            combo.setFixedWidth(60)
            combo.setStyleSheet(combo.styleSheet())
            combo.show()
            combo.currentTextChanged.connect(self.cacheCombos)
            self.combos.append(combo)
        self.updateComboboxPositions()
        self.cacheCombos()
        self.update()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.updateComboboxPositions()

    def updateComboboxPositions(self):
        if not self.combos: return
        w,h = self.width(), self.height()
        cx,cy = w/2 - 60, h/2
        r = min((h/2)-self.margin, (w-cx)-self.margin)
        section_angle = math.pi / self.sections
        start_ang = -math.pi/2
        bw,bh = self.center_button.width(), self.center_button.height()
        self.center_button.move(int(cx-bw/2), int(cy-bh/2))
        for i, combo in enumerate(self.combos):
            mid = start_ang + section_angle * (i + 0.5)
            rr = r * 0.8
            x = cx + rr * math.cos(mid) - combo.width()/2
            y = cy + rr * math.sin(mid) - combo.height()/2
            combo.move(int(x), int(y))

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
        self.instrumentChanged.emit(index, name)
        if dialog: dialog.accept()

    def paintEvent(self, _):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h = self.width(), self.height()
        cx,cy = w/2 - 60, h/2
        r = min((h/2)-self.margin, (w-cx)-self.margin)
        section_angle = math.pi / self.sections
        start_ang, end_ang = -math.pi/2, math.pi/2

        for i in range(self.ticks+1):
            t = start_ang + (end_ang-start_ang)*(i/self.ticks)
            ox,oy = cx + r*math.cos(t), cy + r*math.sin(t)
            tl = self.tick_long if i%5==0 else self.tick_short
            ix,iy = cx + (r-tl)*math.cos(t), cy + (r-tl)*math.sin(t)
            if i == self.selected_tick:
                ang_deg = math.degrees(t)
                rotated = self.hand_icon.transformed(QTransform().rotate(ang_deg), Qt.TransformationMode.SmoothTransformation)
                icon_r = r + 10
                ix = cx + icon_r*math.cos(t) - rotated.width()/2
                iy = cy + icon_r*math.sin(t) - rotated.height()/2
                painter.drawPixmap(int(ix), int(iy), rotated)
                continue
            highlight = (self.selected_section >=0 and self.selected_section*section_angle <= t + math.pi/2 <= (self.selected_section+1)*section_angle and self.touch_value)
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

        center_t = 0
        r_label = r + 16
        label_x = cx + r_label*math.cos(center_t)
        label_y = cy + r_label*math.sin(center_t)
        painter.setPen(QColor(100,100,120,150))
        f = painter.font(); f.setPointSize(9); painter.setFont(f)
        painter.drawText(int(label_x-8), int(label_y+4), "0º")

        for i in range(self.sections+1):
            t = start_ang + section_angle * i
            inner_r = r * 0.3
            outer_r = r * 0.8
            x1,y1 = cx + inner_r*math.cos(t), cy + inner_r*math.sin(t)
            x2,y2 = cx + outer_r*math.cos(t), cy + outer_r*math.sin(t)
            if i in (self.selected_section, self.selected_section+1) and self.touch_value:
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
    def __init__(self, selected_device=None):
        super().__init__()
        self.selected_device = selected_device
        self.ble_client = None
        self.midi_out = None
        self.midi_out_driver = None  # rtmidi.MidiOut object
        self.setWindowTitle("Contato GUI")
        self.setFixedSize(460, 640)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "icon.ico")))

        # Attempt to open a midi output port using rtmidi only
        try:
            if rtmidi is None:
                raise RuntimeError("rtmidi not available")
            self.midi_out_driver = rtmidi.MidiOut()
            ports = self.midi_out_driver.get_ports()
            if ports:
                idx = max(0, min(PORT_INDEX, len(ports)-1))
                self.midi_out_driver.open_port(idx)
                self.midi_out = True
                print(f"rtmidi: porta {idx} aberta: {ports[idx]}")
            else:
                print("rtmidi: nenhuma porta de saída disponível.")
                self.midi_out = None
        except Exception as e:
            print("rtmidi não disponível ou falha ao abrir porta:", e)
            self.midi_out = None
            self.midi_out_driver = None

        # Topbar
        save_btn = QPushButton("Salvar")
        load_btn = QPushButton("Abrir")
        calibrate_btn = QPushButton("Calibrar")
        for b in (save_btn, load_btn, calibrate_btn):
            b.setFixedSize(90, 26)
            b.setStyleSheet("QPushButton{border:1px solid #b0b0b0;border-radius:3px;background:#eaeaea;} QPushButton:hover{background:#dcdcdc}")

        save_btn.clicked.connect(self.saveSetup)
        load_btn.clicked.connect(self.loadSetup)
        calibrate_btn.clicked.connect(lambda: asyncio.create_task(self.send_calibrate_command()))

        topbar = QHBoxLayout()
        topbar.setContentsMargins(6,6,6,6)
        topbar.setSpacing(6)
        topbar.addWidget(save_btn)
        topbar.addWidget(load_btn)
        topbar.addStretch()
        topbar.addWidget(calibrate_btn)

        topbar_frame = QFrame()
        topbar_frame.setLayout(topbar)
        topbar_frame.setFixedHeight(40)
        topbar_frame.setStyleSheet("background:#f4f4f4;border-bottom:1px solid #bfbfbf;")

        # Semicircle widget
        self.selector = SemicircleSectionWidget(sections=6, ticks=60)
        self.selector.instrumentChanged.connect(self.onInstrumentChanged)
        self.selector.notesCached.connect(self.on_notes_cached)

        divider = QFrame(); divider.setFrameShape(QFrame.Shape.HLine); divider.setStyleSheet("color:#cfcfcf;")

        notas_label = QLabel("Notas")
        self.notas_spin = QSpinBox()
        self.notas_spin.setRange(1,24)
        self.notas_spin.setValue(self.selector.sections)
        self.notas_spin.valueChanged.connect(self.selector.setSections)

        controls = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(notas_label)
        row.addStretch()
        row.addWidget(self.notas_spin)
        controls.addLayout(row)
        row = QHBoxLayout()
        midi_label = QLabel("Saída MIDI:")
        self.midi_output_combo = QComboBox()
        self.channel_combo = QComboBox()
        self.channel_combo.addItems([str(i) for i in range(1,17)])
        try:
            if rtmidi is None:
                raise RuntimeError("rtmidi not available")
            ports = rtmidi.MidiOut().get_ports()
            if ports:
                self.midi_output_combo.addItems(ports)
            else:
                self.midi_output_combo.addItem("Nenhuma porta")
        except Exception:
            self.midi_output_combo.addItem("rtmidi indisponível")
            ports = []
        row.addWidget(midi_label)
        row.addWidget(self.midi_output_combo)
        row.addStretch()
        row.addWidget(QLabel("Canal:"))
        row.addWidget(self.channel_combo)
        controls.addLayout(row)

        layout = QVBoxLayout()
        layout.addWidget(topbar_frame)
        layout.addWidget(self.selector, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(divider)
        layout.addLayout(controls)

        # função para alterar porta selecionada
        def _on_midi_port_changed(idx):
            try:
                # close old port if any
                if getattr(self, "midi_out_driver", None):
                    try:
                        self.midi_out_driver.close_port()
                    except Exception:
                        pass
                    self.midi_out_driver = None
                    self.midi_out = None
                if rtmidi is None:
                    return
                midi_driver = rtmidi.MidiOut()
                ports_local = midi_driver.get_ports()
                if ports_local and 0 <= idx < len(ports_local):
                    midi_driver.open_port(idx)
                    self.midi_out_driver = midi_driver
                    self.midi_out = True
                    print(f"Porta MIDI alterada → {ports_local[idx]}")
            except Exception as e:
                print("Erro ao alterar porta MIDI:", e)

        self.midi_output_combo.currentIndexChanged.connect(_on_midi_port_changed)

        self.setLayout(layout)

        # ensure tab order: all selector combos in sequence, last combo -> notas_spin (controls)
        self._establish_tab_order()

        # Conecta automaticamente se foi passado dispositivo
        if self.selected_device:
            asyncio.create_task(self.ble_connect_to_selected(self.selected_device))

    def _establish_tab_order(self):
        try:
            combos = getattr(self.selector, "combos", [])
            if combos:
                prev = combos[0]
                for c in combos[1:]:
                    self.setTabOrder(prev, c)
                    prev = c
                # last combobox should be before controls (notas_spin)
                self.setTabOrder(prev, self.notas_spin)
        except Exception:
            pass

    async def ble_connect_to_selected(self, device):
        try:
            disconnect_event = asyncio.Event()
            async with BleakClient(device, disconnected_callback=lambda c: disconnect_event.set()) as client:
                self.ble_client = client
                print(f"Conectado a {device.name} / {device.address}")

                # Ler SECTIONS e aplicar no UI (bloqueia sinais do spinbox)
                try:
                    sec_bytes = await client.read_gatt_char(SECTIONS_CHAR_UUID)
                    if sec_bytes is not None:
                        n_sections = len(sec_bytes)
                        try:
                            # Prevent spinbox valueChanged handler and combo emits from firing
                            self.notas_spin.blockSignals(True)
                            self.selector.suppress_emit = True
                            # set spinbox value and sections (this recreates combos)
                            self.notas_spin.setValue(n_sections)
                            self.selector.setSections(n_sections)

                            # Now set each combo's text while blocking their signals
                            for i, b in enumerate(sec_bytes):
                                nm = midi_to_name(b)
                                if i < len(self.selector.combos):
                                    combo = self.selector.combos[i]
                                    combo.blockSignals(True)
                                    combo.setCurrentText(nm)
                                    combo.blockSignals(False)
                            # update cached_notes but do NOT write back
                            self.selector.cacheCombos(emit=False)
                        finally:
                            # re-enable emits/signals and optionally write once
                            self.selector.suppress_emit = False
                            self.notas_spin.blockSignals(False)
                except Exception as e:
                    print("Erro ao ler SECTIONS:", e)

                # notificações
                try:
                    await client.start_notify(BLE_MIDI_CHAR_UUID, self.ble_midi_callback)
                    print("Inscrito em notificações BLE-MIDI.")
                except Exception as e:
                    print("Não foi possível iniciar notificações BLE-MIDI:", e)

                try:
                    await client.start_notify(GYRO_CHARACTERISTIC_UUID, self.ble_gyro_callback)
                except Exception as e:
                    print("Não foi possível iniciar notificações do giroscópio:", e)

                try:
                    await client.start_notify(TOUCH_CHARACTERISTIC_UUID, self.ble_touch_callback)
                except Exception as e:
                    print("Não foi possível iniciar notificações de toque:", e)

                await disconnect_event.wait()
                print("Dispositivo desconectado")
                self.ble_client = None
        except Exception as e:
            print("Erro na conexão BLE:", e)
            self.ble_client = None

    def ble_gyro_callback(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        try:
            val = int.from_bytes(data, 'little', signed=True)
        except:
            val = 0
        self.selector.updateGyro(val)

    def ble_touch_callback(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        try:
            val = int.from_bytes(data, 'little', signed=False)
        except:
            val = 0
        self.selector.updateTouch(bool(val))

    def ble_midi_callback(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        payload = bytes(data)
        if not payload:
            return
        if self.midi_out_driver is None:
            print("MIDI não aberto — não é possível enviar MIDI.")
            return
        try:
            # send raw bytes via rtmidi
            # rtmidi expects a list of ints for send_message
            try:
                self.midi_out_driver.send_message(list(payload))
            except Exception as e:
                # best-effort: attempt to normalize to at most 3 bytes
                try:
                    msg = list(payload[-3:])
                    self.midi_out_driver.send_message(msg)
                except Exception as e2:
                    print("Erro ao enviar mensagem MIDI via rtmidi:", e2, "bytes:", list(payload))
        except Exception as e:
            print("Erro ao enviar MIDI (rtmidi):", e, "bytes:", list(payload))

    @asyncSlot(int, str)
    async def onInstrumentChanged(self, index: int, name: str):
        prog = max(0, min(127, int(index)))
        ch = 0
        try:
            if hasattr(self, "channel_combo") and self.channel_combo is not None:
                ch = max(0, min(15, int(self.channel_combo.currentText()) - 1))
        except Exception:
            ch = 0
        print(f"Instrumento alterado → {name} (programa {prog}) no canal {ch+1}")
        if getattr(self, "midi_out_driver", None) is None:
            print("MIDI não aberto — nada a enviar.")
            return
        try:
            status = 0xC0 | (ch & 0x0F)
            self.midi_out_driver.send_message([status, prog])
        except Exception as e:
            print("Erro ao enviar Program Change via rtmidi:", e)

    def on_notes_cached(self, notes_list):
        asyncio.create_task(self._async_write_sections(notes_list))

    async def _async_write_sections(self, notes_list):
        if not self.ble_client or not getattr(self.ble_client, "is_connected", False):
            return
        try:
            midi_bytes = bytes([name_to_midi(n) for n in notes_list])
            await self.ble_client.write_gatt_char(SECTIONS_CHAR_UUID, midi_bytes, response=True)
            print("Escreveu sections no servidor:", list(midi_bytes))
        except Exception as e:
            print("Erro ao escrever sections no servidor:", e)

    async def send_calibrate_command(self):
        if not self.ble_client or not getattr(self.ble_client, "is_connected", False):
            print("Nenhum cliente BLE conectado — não é possível calibrar.")
            return
        try:
            await self.ble_client.write_gatt_char(CALIBRATE_CHAR_UUID, bytes([0x01]), response=True)
            print("Comando de calibração enviado ao servidor.")
        except Exception as e:
            print("Falha ao enviar comando de calibração:", e)

    def saveSetup(self):
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

    def loadSetup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Configuração", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print("Erro ao abrir arquivo:", e)
            return
        self.selector.setSections(data.get("sections", 6))
        for combo, note in zip(self.selector.combos, data.get("notes", [])):
            combo.setCurrentText(note)
        self.selector.cacheCombos()
        instr = data.get("instrument", 0)
        self.selector.setInstrument(instr, None)
        # aplica porta MIDI se disponível
        try:
            idx = int(data.get("midi_port_index", 0))
            if 0 <= idx < self.midi_output_combo.count():
                self.midi_output_combo.setCurrentIndex(idx)
        except Exception:
            pass
        try:
            ch = int(data.get("midi_channel", 1))
            if 1 <= ch <= 16:
                self.channel_combo.setCurrentText(str(ch))
        except Exception:
            pass
        print("Configuração carregada de", path)

# Device selector
async def choose_device_before_opening(parent=None):
    devices = await BleakScanner.discover(timeout=1.0)
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

# App entrypoint
async def main(app):
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    splash = SplashScreen()
    splash.show()
    await asyncio.sleep(1.0)

    selected = await choose_device_before_opening(None)
    splash.close()
    if not selected:
        print("Nenhum dispositivo selecionado — encerrando.")
        app.quit()
        return

    win = MainWindow(selected_device=selected)
    win.setWindowTitle("Contato GUI")
    win.show()

    await app_close_event.wait()

if __name__ == "__main__":
    qapp = QAsyncApplication(sys.argv)
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main(qapp))
