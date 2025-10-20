import sys
import math
import json
import math 
from pathlib import Path
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import asyncio
from qasync import QApplication, QEventLoop, asyncSlot
from Player import Player # Classe de interação MIDI com o loopMIDI
from bleak import BleakClient, BleakScanner # biblioteca de BLE
from bleak.backends.characteristic import BleakGATTCharacteristic

TOUCH_CHARACTERISTIC_UUID = '62c84a29-95d6-44e4-a13d-a9372147ce21'
GYRO_CHARACTERISTIC_UUID = '9b7580ed-9fc2-41e7-b7c2-f63de01f0692'
ACCEL_CHARACTERISTIC_UUID = 'f62094cf-21a7-4f71-bb3f-5a5b17bb134e' 

NOTES = [f"{n}{o}" for o in range(1, 5) for n in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]]
CONFIG_FILE = Path.home() / 'Documents' / 'notes_config.json'

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

class GyroDisplay(QWidget):
    def __init__(self, sections = 3, parent = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.player = Player()
        self._sections = max(1, int(sections))
        self._notes = [NOTES[36]] * self._sections
        self._gyro_value = 30
        self._touch = False
        self._selected_section = 1
        self._accel_note = "C2"
        self.combos = []

        self.ble_update() 
        self._setup_combos()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # so widget can receive Tab events
        self.setTabOrderChain()   
    
    def sizeHint(self):
        return QSize(150, 300)
    # ---------------------------------------------------------------------
    #  Atributos
    # ---------------------------------------------------------------------
    @property
    def sections(self):
        """Número de seções do gráfico de configuração de notas"""
        return self._sections

    @sections.setter
    def sections(self, n):
        n = max(1, int(n))
        if n != self._sections:
            old_notes = self._notes.copy()
            self._sections = n
            self._notes = (old_notes[:n] + [NOTES[0]] * (n - len(old_notes)))[:n]
            self._setup_combos()
            self.update()

    @property
    def notes(self):
        """Lista de notas do setup (ordem no sentido horário do gráfico semicirculo)"""
        return self._notes

    @notes.setter
    def notes(self, notes_list):
        for i in range(min(len(notes_list), self._sections)):
            if notes_list[i] in NOTES:
                self._notes[i] = notes_list[i]
        self.update()

    @property
    def gyro_value(self):
        """Valor atual da leitura de inclinação do giroscópio"""
        return self._gyro_value
    
    @gyro_value.setter
    def gyro_value(self, n):
        self._gyro_value = min(90, int(n))
        self._gyro_value = max(-90, int(n))

    @property
    def touch(self):
        """Valor atual da leitura do toque do dispositivo"""
        return self._touch
    
    @touch.setter
    def touch(self, bool):
        if bool == True:
            self._touch = bool
        else:
            self._touch = False

    @property
    def selected_section(self):
        """Seção indicada pelo ponteiro"""
        return self._selected_section
    
    @selected_section.setter
    def selected_section(self, n):
        self._selected_section = max(0, min(self._sections - 1, n))

    # ---------------------------------------------------------------------
    #  Combo box 
    # ---------------------------------------------------------------------
    def _setup_combos(self):
        for combo in self.combos:
            combo.deleteLater()
        self.combos.clear()

        for i in range(self._sections):
            combo = QComboBox(self)
            combo.addItems(NOTES)
            combo.setCurrentText(self._notes[i])
            combo.hide()
            combo.currentIndexChanged.connect(lambda idx, s=i: self._combo_changed(s, idx))
            combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            combo.installEventFilter(self)
            self.combos.append(combo)

    def _show_combo(self, idx):
        """Show one combo and focus it, hide all others."""
        for i, combo in enumerate(self.combos):
            if i == idx:
                cx, cy = self._combo_position(i)
                combo.move(int(cx), int(cy))
                combo.raise_()            # bring it above the semicircle
                combo.show()
                combo.setFocus()
            else:
                combo.hide()

    def _combo_changed(self, section_idx, note_idx):
        self._notes[section_idx] = NOTES[note_idx]
        self.update()

    def setTabOrderChain(self):
        if not self.combos:
            return
        for i in range(len(self.combos) - 1):
            self.setTabOrder(self.combos[i], self.combos[i + 1])

    # ---------------------------------------------------------------------
    #  Renderização do painter 
    # ---------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = 10
        cy = h / 2.0
        r = min(h / 2.0 - 10, w - 20)
        delta = math.pi / self._sections

        self.selected_section = int(((self.gyro_value * math.pi / -180) + math.pi / 2) / delta)

        # Draw sections and labels
        for i in range(self._sections):
            start_angle = -math.pi / 2 + i * delta
            end_angle = -math.pi / 2 + (i + 1) * delta

            poly = QPolygonF()
            poly.append(QPointF(cx, cy))
            steps = max(2, int(10 * (delta / (math.pi / 8))))
            for s in range(steps + 1):
                t = start_angle + (end_angle - start_angle) * (s / steps)
                x = cx + r * math.cos(t)
                y = cy + r * math.sin(t)
                poly.append(QPointF(x, y))
            poly.append(QPointF(cx, cy))

            # alternating gray colors
            if i % 2 == 0:
                base = QColor(230, 230, 230) # gray
            else:
                base = QColor(200, 200, 200) # dark gray
            
            selected_color = QColor(220, 220, 0)

            if self.selected_section == i and self.touch:
                brush = QBrush(selected_color)
                painter.setBrush(brush)
            else:
                painter.setBrush(QBrush(base))

            painter.drawPolygon(poly)

            mid_angle = (start_angle + end_angle) / 2
            label_x = cx + (r / 2) * math.cos(mid_angle)
            label_y = cy + (r / 2) * math.sin(mid_angle)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QPointF(label_x - 10, label_y + 5), self._notes[i])
        
        # Draw dial
        painter.translate(QPointF(cx, cy))
        painter.rotate(-self.gyro_value + 270)
        painter.setPen(QPen(QColor("red"), 2))
        painter.drawLine(0, 0, 0, int(r - 10))

        # TODO: ISSO NÃO DEVERIA ESTAR AQUI MAS COMO É CHAMADA NO UPDATE SERVE
        # if touch

    # ---------------------------------------------------------------------
    #  Lógica de interação
    # ---------------------------------------------------------------------
    def mousePressEvent(self, event):
        """"""
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.position()
        idx = self._index_at_point(pos.x(), pos.y())
        if idx is None:
            # Clicked outside: hide all combos
            for combo in self.combos:
                combo.hide()
            self._selected = None
            self.update()
            return

        self._selected = idx
        self._show_combo(idx)
        self.update()

    def focusNextPrevChild(self, next: bool):
        """"""
        current = self.focusWidget()
        if current in self.combos:
            idx = self.combos.index(current)
            next_idx = idx + (1 if next else -1)

            if next_idx < 0 or next_idx >= len(self.combos):
                return False

            self._show_combo(next_idx)
            return True
        elif current == self:
            self._show_combo(0 if next else len(self.combos) - 1)
            return True

        return super().focusNextPrevChild(next)
    
    def eventFilter(self, obj, event):
        """Esconde combo box ao perder foco"""
        if isinstance(obj, QComboBox):
            if event.type() == QEvent.Type.FocusOut:
                if not obj.view().isVisible():
                    obj.hide()
        return super().eventFilter(obj, event)
    
    # ---------------------------------------------------------------------
    #  Auxiliares de geometria
    # ---------------------------------------------------------------------
    def _index_at_point(self, x, y):
        w = self.width()
        h = self.height()
        cx = 10
        cy = h / 2.0
        r = min(h / 2.0 - 10, w - 20)

        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        if dist > r or dx < 0:
            return None

        angle = math.atan2(dy, dx)
        if angle < -math.pi / 2 or angle > math.pi / 2:
            return None

        delta = math.pi / self._sections
        idx = int((angle + math.pi / 2) / delta)
        idx = max(0, min(self._sections - 1, idx))
        return idx


    def _combo_position(self, i):
        # Mais ou menos no centro da seção
        w = self.width()
        h = self.height()
        cx = 10
        cy = h / 2.0
        r = min(h / 2.0 - 10, w - 20)
        delta = math.pi / self._sections
        start_angle = -math.pi / 2 + i * delta
        end_angle = -math.pi / 2 + (i + 1) * delta
        mid_angle = (start_angle + end_angle) / 2
        x = cx + (r / 2) * math.cos(mid_angle)
        y = cy + (r / 2) * math.sin(mid_angle)
        return x, y

    @asyncSlot()
    async def ble_update(self):
        print('Scan')
        def bleak_gyro_callback(characteristic: BleakGATTCharacteristic, data: bytearray): 
            gyro = int.from_bytes(data, 'little', signed=True)
            self.player.gyro = gyro
            self.gyro_value = gyro
            self.player.update(self.notes, self.selected_section)
            self.update()
            # print(f'roll: {player.gyro} acc_x: {player.accel} t: {player.touch}')
        def bleak_accel_callback(characteristic: BleakGATTCharacteristic, data: bytearray):  
            self.player.accel = int.from_bytes(data, 'little', signed=True)
        def bleak_touch_callback(characteristic: BleakGATTCharacteristic, data: bytearray):
            touch = int.from_bytes(data, 'little', signed=False)
            self.touch = touch
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

class GyroDisplayControls(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.gyro_display = GyroDisplay()
        
        file_controls = QHBoxLayout()
        controls = QVBoxLayout()

        self.save_btn = QPushButton("Salvar")
        self.save_btn.clicked.connect(self.save_config)
        file_controls.addWidget(self.save_btn)
        self.load_btn = QPushButton("Abrir")
        self.load_btn.clicked.connect(self.load_config)
        file_controls.addWidget(self.load_btn)

        # --- Horizontal row: label + spinbox ---
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(QLabel("Notas:"))
        self.spin = QSpinBox()
        self.spin.setRange(1, 24)
        self.spin.setValue(3)
        self.spin.valueChanged.connect(self._on_spin)
        row.addWidget(self.spin)
        row.addStretch()
        controls.addLayout(row)

        # --- Horizontal row: label + spinbox ---
        row = QHBoxLayout()
        row.addWidget(QLabel("Notas:"))
        self.spin = QSpinBox()
        self.spin.setRange(1, 24)
        self.spin.setValue(3)
        self.spin.valueChanged.connect(self._on_spin)
        row.addStretch()
        row.addWidget(self.spin)
        controls.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Acelerômetro:"))
        self.accel_note_combo = QComboBox()
        self.accel_note_combo.currentIndexChanged.connect(self._accel_note_combo_changed)   
        self.accel_note_combo.addItems(NOTES)
        row.addStretch()
        row.addWidget(self.accel_note_combo)
        controls.addLayout(row)
        
        layout.addLayout(file_controls)
        layout.addWidget(self.gyro_display, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(controls)


    def _on_spin(self, val):
        self.gyro_display.sections = val

    def _accel_note_combo_changed(self, i):
        pass

    def save_config(self):
        data = {'sections': self.gyro_display.sections, 'notes': self.gyro_display.notes}
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                print(f"List saved to {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")

    def load_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                sections = data.get("sections")
                self.spin.setValue(sections)
                self.gyro_display.notes = data.get('notes')

async def main(app):
    splash.close()
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    win = GyroDisplayControls()
    win.setWindowTitle('Contato GUI')
    win.setFixedSize(400, 500)
    win.show()
    await app_close_event.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    asyncio.run(main(app), loop_factory=QEventLoop)