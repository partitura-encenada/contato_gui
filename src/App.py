import sys
import math
import json
from PyQt6.QtCore import Qt, QPointF, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QComboBox,
    QLabel, QSpinBox, QVBoxLayout, QHBoxLayout, QDialog,
    QGridLayout, QFileDialog, QToolTip, QDial, QSplashScreen
)
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QPainterPath, QTransform, QIcon, QFont
import asyncio
from qasync import QApplication, QEventLoop, asyncSlot
from Player import Player # Classe de interação MIDI com o loopMIDI
from bleak import BleakClient, BleakScanner # biblioteca de BLE
from bleak.backends.characteristic import BleakGATTCharacteristic

TOUCH_CHARACTERISTIC_UUID = '62c84a29-95d6-44e4-a13d-a9372147ce21'
GYRO_CHARACTERISTIC_UUID = '9b7580ed-9fc2-41e7-b7c2-f63de01f0692'
ACCEL_CHARACTERISTIC_UUID = 'f62094cf-21a7-4f71-bb3f-5a5b17bb134e' 

PRIMARY_COLOR = QColor(100, 180, 255)

class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.GlobalColor.white)
        super().__init__(pixmap)
        self.setFont(QFont("Arial", 18, QFont.Weight.Bold))

    def drawContents(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Contato\npartitura encenada")
# ---------------------------------------------------------
# Small logarithmic dial
# ---------------------------------------------------------
class LogDial(QDial):
    """Small QDial with logarithmic scaling (0.5–10) and tooltip feedback."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(50)
        self.setNotchesVisible(True)
        self.setFixedSize(30, 30)
        self.setToolTip(f"{self.get_log_value():.2f}")
        self.valueChanged.connect(self.show_value)

    def get_log_value(self):
        # Map 0–100 linearly to logarithmic 0.5–10 range
        return 0.5 * (10 ** (self.value() / 100 * math.log10(20)))

    def show_value(self):
        val = self.get_log_value()
        QToolTip.showText(self.mapToGlobal(self.rect().center()), f"{val:.2f}", self)
        self.setToolTip(f"{val:.2f}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.setValue(min(self.value() + 1, self.maximum()))
        elif event.key() == Qt.Key.Key_Down:
            self.setValue(max(self.value() - 1, self.minimum()))
        else:
            super().keyPressEvent(event)


class ToggleEnterComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedWidth(48)
        self.setStyleSheet(f"""
            QComboBox {{
                background: #f8f8f8;
                border: 1px solid #bbbbbb;
                color: #333;
                font-size: 11px;
                padding: 1px 2px;
                border-radius: 4px;
                min-height: 18px;
            }}
            QComboBox:hover {{
                border: 1px solid {PRIMARY_COLOR.name()};
                background: #f2f9ff;
            }}
            QComboBox:focus, QComboBox:editable, QComboBox:on {{
                border: 1px solid {PRIMARY_COLOR.name()};
                background: #e8f4ff;
                color: #222;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 10px;
            }}
        """)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.view().isVisible():
                self.hidePopup()
            else:
                self.showPopup()
        else:
            super().keyPressEvent(event)


# ---------------------------------------------------------
# Simple toggle button (Left/Right)
# ---------------------------------------------------------
class ToggleButton(QPushButton):
    def __init__(self, text_left="Esquerda", text_right="Direita", parent=None):
        super().__init__(text_left, parent)
        self.text_left = text_left
        self.text_right = text_right
        self.checked = False
        self.updateStyle()
        self.clicked.connect(self.toggleState)

    def toggleState(self):
        self.checked = not self.checked
        self.updateStyle()

    def updateStyle(self):
        if self.checked:
            text, bg, border = self.text_right, "#cce4ff", "#3388ff"
        else:
            text, bg, border = self.text_left, "#f0f0f0", "#cccccc"
        self.setText(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 4px 12px;
                min-width: 80px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """)


# ---------------------------------------------------------
# Semicircle Widget
# ---------------------------------------------------------
class SemicircleSectionWidget(QFrame):
    instrumentChanged = pyqtSignal(int, str)  # index, name
    notesCached = pyqtSignal(list)
    def __init__(self, sections=6, ticks=30, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 450)

        self.margin = 30
        self.sections = sections
        self.ticks = ticks
        self.tick_long = 14
        self.tick_short = 8

        self.tick_positions = []
        self.cached_notes = []
        self.gyro_value = 0
        self.selected_tick = 0
        self.selected_section = 0
        self.touch_value = True
        # Pulse animation
        self.pulse_phase = 0.0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.updatePulse)
        self.pulse_timer.start(30)

        # Notes
        self.notes = [
            f"{note}{octave}"
            for octave in range(1, 6)
            for note in ["C", "C#", "D", "D#", "E", "F", "F#",
                         "G", "G#", "A", "A#", "B"]
        ]

        # Instruments
        self.instruments = [
            ("🎹", "Acoustic Grand Piano"), ("🎼", "Bright Acoustic Piano"),
            ("🎵", "Electric Grand Piano"), ("🎶", "Honky-tonk Piano"),
            ("🎧", "Electric Piano 1"), ("🎛️", "Electric Piano 2"),
            ("🎻", "Harpsichord"), ("🎸", "Clavinet"),
            ("✨", "Celesta"), ("🔔", "Glockenspiel"),
            ("📦", "Music Box"), ("🛎️", "Vibraphone"),
            ("🥁", "Marimba"), ("🎺", "Xylophone"),
            ("⛓️", "Tubular Bells"), ("🎶", "Dulcimer")
        ]
        self.current_instrument_index = 0

        # Center instrument button
        icon, _ = self.instruments[self.current_instrument_index]
        self.center_button = QPushButton(icon, self)
        self.center_button.setFixedSize(90, 90)
        self.center_button.setStyleSheet("""
            QPushButton {
                border-radius: 45px;
                font-size: 32px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                            stop:0 #ffffff, stop:1 #e6e6e6);
                border: 2px solid #bfbfbf;
            }
            QPushButton:hover { background: #f2f2f2; }
            QPushButton:pressed { background: #dcdcdc; }
        """)
        self.center_button.clicked.connect(self.showInstrumentSelector)

        # Combos
        self.combos = []
        self.createCombos()

        # Hand icon
        self.hand_icon = QPixmap(20, 20)
        self.hand_icon.fill(Qt.GlobalColor.transparent)
        p = QPainter(self.hand_icon)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.moveTo(10, 2)
        path.lineTo(18, 10)
        path.lineTo(10, 18)
        path.lineTo(9, 14)
        path.lineTo(14, 10)
        path.lineTo(9, 6)
        path.closeSubpath()
        pen = QPen(QColor(100, 180, 255), 2)
        p.setPen(pen)
        p.drawPath(path)
        p.end()

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
        for combo in getattr(self, "combos", []):
            combo.deleteLater()
        self.combos = []
        for _ in range(self.sections):
            combo = ToggleEnterComboBox(self)
            combo.addItems(self.notes)
            combo.setCurrentText("C3")
            combo.setFixedWidth(60)
            combo.show()
            combo.currentTextChanged.connect(self.cacheCombos)
            self.combos.append(combo)
        self.updateComboboxPositions()
        self.cacheCombos()

    def cacheCombos(self):
        """Cache current ComboBox states into a list and emit update."""
        self.cached_notes = [combo.currentText() for combo in self.combos]
        print('emit')
        self.notesCached.emit(self.cached_notes)

    def setSections(self, count):
        self.sections = count
        self.createCombos()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateComboboxPositions()

    def updateComboboxPositions(self):
        if not self.combos:
            return
        w, h = self.width(), self.height()
        cx, cy = w / 2 - 60, h / 2
        r = min((h / 2) - self.margin, (w - cx) - self.margin)
        section_angle = math.pi / self.sections
        start_ang = -math.pi / 2

        bw, bh = self.center_button.width(), self.center_button.height()
        self.center_button.move(int(cx - bw / 2), int(cy - bh / 2))

        for i, combo in enumerate(self.combos):
            mid = start_ang + section_angle * (i + 0.5)
            rr = r * 0.8
            x = cx + rr * math.cos(mid) - combo.width() / 2
            y = cy + rr * math.sin(mid) - combo.height() / 2
            combo.move(int(x), int(y))

    # def mousePressEvent(self, event):
    #     if event.button() != Qt.MouseButton.LeftButton:
    #         return super().mousePressEvent(event)

    #     x, y = event.position().x(), event.position().y()
    #     cx, cy = self.width() / 2 - 60, self.height() / 2
    #     r = min((self.height() / 2) - self.margin, (self.width() - cx) - self.margin)
    #     dx, dy = x - cx, y - cy
    #     angle = math.atan2(dy, dx)

    #     # Tick selection
    #     for i, t in self.tick_positions:
    #         tx = cx + r * math.cos(t)
    #         ty = cy + r * math.sin(t)
    #         if math.hypot(x - tx, y - ty) < 10:
    #             self.selected_tick = i
    #             self.update()
    #             return

    #     # Section selection
    #     if -math.pi / 2 <= angle <= math.pi / 2 and dx > 0:
    #         section_angle = math.pi / self.sections
    #         idx = int((angle + math.pi / 2) / section_angle)
    #         if 0 <= idx < self.sections:
    #             self.selected_section = idx
    #             self.update()

    def showInstrumentSelector(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Instrument")
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #f8f8f8;")
        grid = QGridLayout(dialog)
        grid.setSpacing(12)
        grid.setContentsMargins(20, 20, 20, 20)
        for i, (icon, name) in enumerate(self.instruments):
            btn = QPushButton(f"{icon}\n{name}")
            btn.setFixedSize(110, 70)
            if i == self.current_instrument_index:
                btn.setStyleSheet("background-color:#d0e6ff;border:2px solid #2b72ff;"
                                  "border-radius:10px;font-size:13px;font-weight:bold;")
            else:
                btn.setStyleSheet("background-color:#e6e6e6;border:1px solid #cccccc;"
                                  "border-radius:10px;font-size:13px;")
            btn.clicked.connect(lambda _, idx=i: self.setInstrument(idx, dialog))
            grid.addWidget(btn, i // 4, i % 4)
        dialog.exec()

    def setInstrument(self, index, dialog):
        self.current_instrument_index = index
        icon, name = self.instruments[index]
        self.center_button.setText(icon)
        self.instrumentChanged.emit(index, name)  # 🔔 Notify MainWindow
        if dialog:
            dialog.accept()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2 - 60, h / 2
        r = min((h / 2) - self.margin, (w - cx) - self.margin)
        section_angle = math.pi / self.sections
        start_ang, end_ang = -math.pi / 2, math.pi / 2
        self.tick_positions = []

        # Draw ticks
        for i in range(self.ticks + 1):
            t = start_ang + (end_ang - start_ang) * (i / self.ticks)
            self.tick_positions.append((i, t))
            ox, oy = cx + r * math.cos(t), cy + r * math.sin(t)
            tl = self.tick_long if i % 5 == 0 else self.tick_short
            ix, iy = cx + (r - tl) * math.cos(t), cy + (r - tl) * math.sin(t)

            # --- Selected tick -> draw hand icon ---
            if i == self.selected_tick:
                ang_deg = math.degrees(t)
                rotated = self.hand_icon.transformed(
                    QTransform().rotate(ang_deg),
                    Qt.TransformationMode.SmoothTransformation
                )

                # Draw the pointing hand at the tick location
                icon_r = r + 10
                ix = cx + icon_r * math.cos(t) - rotated.width() / 2
                iy = cy + icon_r * math.sin(t) - rotated.height() / 2
                painter.drawPixmap(int(ix), int(iy), rotated)
                continue  # Skip normal tick drawing for this one

            # --- Normal tick drawing ---
            highlight = (
                self.selected_section >= 0 and
                self.selected_section * section_angle <= t + math.pi / 2 <=
                (self.selected_section + 1) * section_angle and self.touch_value
            )

            if highlight:
                pulse = 0.5 + 0.5 * math.sin(self.pulse_phase)
                color = QColor(
                    int(PRIMARY_COLOR.red() * (0.8 + 0.2 * pulse)),
                    int(PRIMARY_COLOR.green() * (0.8 + 0.2 * pulse)),
                    int(PRIMARY_COLOR.blue() * (0.8 + 0.2 * pulse))
                )
                pen = QPen(color, 3)
            else:
                pen = QPen(QColor(60, 60, 60), 2)

            painter.setPen(pen)
            painter.drawLine(QPointF(ix, iy), QPointF(ox, oy))

        # --- Draw "0º" label beside the center tick ---
        center_t = 0  # center tick angle (vertical)
        cx, cy = w / 2 - 60, h / 2
        r_label = r + 16  # position label slightly outside radius
        label_x = cx + r_label * math.cos(center_t)
        label_y = cy + r_label * math.sin(center_t)

        painter.setPen(QColor(100, 100, 120, 150))  # faded gray-blue tone
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(int(label_x - 8), int(label_y + 4), "0º")
        
        # Dividers
        for i in range(self.sections + 1):
            t = start_ang + section_angle * i
            inner_r = r * 0.3
            outer_r = r * 0.8
            x1, y1 = cx + inner_r * math.cos(t), cy + inner_r * math.sin(t)
            x2, y2 = cx + outer_r * math.cos(t), cy + outer_r * math.sin(t)
            if i in (self.selected_section, self.selected_section + 1) and self.touch_value:
                pulse = 0.5 + 0.5 * math.sin(self.pulse_phase)
                color = QColor(
                    int(PRIMARY_COLOR.red() * (0.7 + 0.3 * pulse)),
                    int(PRIMARY_COLOR.green() * (0.7 + 0.3 * pulse)),
                    int(PRIMARY_COLOR.blue() * (0.7 + 0.3 * pulse)),
                    220
                )
                pen = QPen(color, 2)
            else:
                pen = QPen(QColor(PRIMARY_COLOR.red(), PRIMARY_COLOR.green(), PRIMARY_COLOR.blue(), 60), 2)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


# ---------------------------------------------------------
# Main Window
# ---------------------------------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gyro Display")
        self.player = Player()
        self.ble_init()

        self.resize(460, 640)

        # Topbar
        save_btn = QPushButton()
        save_btn.setIcon(QIcon.fromTheme("document-save"))
        save_btn.setToolTip("Save Setup")

        load_btn = QPushButton()
        load_btn.setIcon(QIcon.fromTheme("document-open"))
        load_btn.setToolTip("Load Setup")

        for b in (save_btn, load_btn):
            b.setFixedSize(22, 22)
            b.setIconSize(b.size() * 0.8)
            b.setStyleSheet("""
                QPushButton {
                    border: 1px solid #b0b0b0;
                    border-radius: 3px;
                    background-color: #eaeaea;
                }
                QPushButton:hover { background-color: #dcdcdc; }
            """)
        save_btn.clicked.connect(self.saveSetup)
        load_btn.clicked.connect(self.loadSetup)

        topbar = QHBoxLayout()
        topbar.setContentsMargins(0, 4, 6, 4)  # ⬅️ Reduced left padding from 6 → 4
        topbar.setSpacing(4)                   # ⬅️ Slightly closer buttons
        topbar.addWidget(save_btn)
        topbar.addWidget(load_btn)
        topbar.addStretch()

        topbar_frame = QFrame()
        topbar_frame.setLayout(topbar)
        topbar_frame.setFixedHeight(34)  # ⬅️ Slightly slimmer bar
        topbar_frame.setStyleSheet("background:#f4f4f4;border-bottom:1px solid #bfbfbf;")

        # Semicircle
        self.selector = SemicircleSectionWidget(sections=6, ticks=60)
        self.selector.instrumentChanged.connect(self.updateInstrumentLabel)
        self.selector.notesCached.connect(self.updateNotesLabel)
        self.player.cached_notes = self.selector.cached_notes

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color:#cfcfcf;")

        # Controls
        notas_label = QLabel("Notas")
        self.notas_spin = QSpinBox()
        self.notas_spin.setRange(1, 24)
        self.notas_spin.setValue(self.selector.sections)
        self.notas_spin.valueChanged.connect(self.selector.setSections)

        sens_label = QLabel("Sensibilidade (Acelerômetro)")
        self.sens_dial = LogDial()

        side_label = QLabel("Esquerda / Direita")
        self.side_toggle = ToggleButton()

        def make_row(label, widget):
            row = QHBoxLayout()
            row.setContentsMargins(5, 4, 5, 4)
            row.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
            row.addStretch()
            row.addWidget(widget, alignment=Qt.AlignmentFlag.AlignRight)
            return row

        controls = QVBoxLayout()
        controls.addLayout(make_row(notas_label, self.notas_spin))
        controls.addLayout(make_row(sens_label, self.sens_dial))
        controls.addLayout(make_row(side_label, self.side_toggle))
        controls.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(topbar_frame)
        layout.addWidget(self.selector, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(divider)
        layout.addLayout(controls)
        self.setLayout(layout)

    @asyncSlot()
    async def ble_init(self):
        print('Scan')
        def bleak_gyro_callback(characteristic: BleakGATTCharacteristic, data: bytearray): 
            self.selector.updateGyro(int.from_bytes(data, 'little', signed=True))
            self.player.update(self.selector.selected_section)
        def bleak_accel_callback(characteristic: BleakGATTCharacteristic, data: bytearray):  
            self.player.accel = int.from_bytes(data, 'little', signed=True)
        def bleak_touch_callback(characteristic: BleakGATTCharacteristic, data: bytearray):
            touch = int.from_bytes(data, 'little', signed=False)
            self.selector.updateTouch(touch)
            self.player.touch = touch
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

    def saveSetup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Configuração", "", "JSON Files (*.json)")
        if not path:
            return

        data = {
            "sections": self.selector.sections,
            "instrument": self.selector.current_instrument_index,
            "notes": [combo.currentText() for combo in self.selector.combos],
            "sensitivity": self.sens_dial.get_log_value(),
            "side": "right" if self.side_toggle.checked else "left"
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)


    def loadSetup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Configuração", "", "JSON Files (*.json)")
        if not path:
            return

        with open(path, "r") as f:
            data = json.load(f)

        # --- Update section count ---
        self.selector.setSections(data.get("sections", 6))

        # --- Update comboboxes ---
        for combo, note in zip(self.selector.combos, data.get("notes", [])):
            combo.setCurrentText(note)
        self.selector.cacheCombos()  # refresh cache

        # --- Update instrument ---
        self.selector.setInstrument(data.get("instrument", 0), None)

        # --- Update sensitivity dial ---
        sens_value = data.get("sensitivity", 1.0)
        # Find approximate dial position for the saved log value
        import math
        linear_value = min(max(int(math.log10(sens_value / 0.5) / math.log10(20) * 100), 0), 100)
        self.sens_dial.setValue(linear_value)

        # --- Update toggle ---
        if data.get("side", "left") == "right":
            if not self.side_toggle.checked:
                self.side_toggle.toggleState()
        else:
            if self.side_toggle.checked:
                self.side_toggle.toggleState()

    def updateInstrumentLabel(self, index, name):
        """Update label when the instrument changes."""
        self.player.change_program(index)

    def updateNotesLabel(self, notes_list):
        print('c')
        self.player.cached_notes = notes_list
# ---------------------------------------------------------
# Run
# ---------------------------------------------------------
async def main(app):
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    def after_splash():
        splash.close()
        win.show()

    splash = SplashScreen()
    splash.show()
    win = MainWindow()
    win.setWindowTitle('Contato GUI')
    QTimer.singleShot(2000, after_splash)
    await app_close_event.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    asyncio.run(main(app), loop_factory=QEventLoop)