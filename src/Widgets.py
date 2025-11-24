import os

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

class SemicircleSectionWidget(QFrame):
    instrumentChanged = pyqtSignal(int, str)
    notesCached = pyqtSignal(list)

    def __init__(self, sections=6, ticks=30, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.margin = 15
        self.offset = 80
        self.sections = sections
        self.ticks = ticks
        self.tick_long = 14
        self.tick_short = 8

        self.cached_notes = []
        self.suppress_emit = False  
        self.gyro_value = 0
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
        cx,cy = w/2 - self.offset, h/2
        r = min((h/2)-self.margin, (w-cx)-self.margin)
        section_angle = math.pi / self.sections
        selected_tick = int(((self.gyro_value * math.pi / -180) + math.pi / 2) / (math.pi / self.ticks))
        selected_section = int(((self.gyro_value * math.pi / -180) + math.pi / 2) / (math.pi / self.sections))
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
            highlight = (selected_section >=0 and selected_section * section_angle <= t + math.pi/2 <= (selected_section + 1) * section_angle and self.touch_value)
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
            if i in (selected_section, selected_section + 1) and self.touch_value:
                pulse = 0.5 + 0.5*math.sin(self.pulse_phase)
                color = QColor(int(PRIMARY_COLOR.red()*(0.7+0.3*pulse)),
                               int(PRIMARY_COLOR.green()*(0.7+0.3*pulse)),
                               int(PRIMARY_COLOR.blue()*(0.7+0.3*pulse)), 220)
                pen = QPen(color,2)
            else:
                pen = QPen(QColor(PRIMARY_COLOR.red(), PRIMARY_COLOR.green(), PRIMARY_COLOR.blue(), 60),2)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1,y1), QPointF(x2,y2))