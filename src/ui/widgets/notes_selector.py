import math

from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QPushButton
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPixmap, QPainterPath,
    QTransform, QRadialGradient, QBrush,
)

from constants import NOTE_NAMES, INSTRUMENTS, PRIMARY_COLOR
from ui.widgets.combo_box import ToggleEnterComboBox
from ui.dialogs.instrument import InstrumentSelectorDialog
from ui.theme import BG, SURFACE, RAISED, BORDER, ACCENT, ACCENT2


# Pre-parsed colors used in paintEvent (derive accent from theme so a single
# change in theme.py propagates everywhere)
_C_BG      = QColor(BG)
_C_TRACK   = QColor(71, 85, 105, 80)   # dim arc track
_C_TICK    = QColor(100, 120, 140)     # idle tick
_C_ACCENT  = QColor(ACCENT)           # matches theme accent
_C_DIVIDER = QColor(_C_ACCENT.red(), _C_ACCENT.green(), _C_ACCENT.blue(), 45)


class WNotesSelector(QFrame):
    signalInstrumentChanged = pyqtSignal(int, str)
    signalNotes             = pyqtSignal(list)

    def __init__(self, sections: int = 6, ticks: int = 30, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 480)

        self.margin     = 15
        self.offset     = 80
        self.sections   = sections
        self.ticks      = ticks
        self.tick_long  = 14
        self.tick_short = 7
        self.combos: list[ToggleEnterComboBox] = []

        self.gyro  = 0
        self.touch = True

        self.pulse_phase = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.start(30)

        self._all_notes = [
            f"{note}{octave}"
            for octave in range(1, 6)
            for note in NOTE_NAMES
        ]

        self.instruments = INSTRUMENTS
        self.current_instrument_index = 0

        icon, _ = self.instruments[0]
        self.center_button = QPushButton(icon, self)
        self.center_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.center_button.setFixedSize(90, 90)
        self.center_button.setStyleSheet(f"""
            QPushButton {{
                border-radius: 45px;
                font-size: 32px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {RAISED}, stop:1 {SURFACE});
                border: 2px solid {BORDER};
                color: #fff;
            }}
            QPushButton:hover  {{ border: 2px solid {ACCENT}; background: {RAISED}; }}
            QPushButton:focus  {{ border: 2px solid {ACCENT}; }}
            QPushButton:pressed {{ background: {SURFACE}; }}
        """)
        self.center_button.clicked.connect(self._show_instrument_selector)

        self._hand_icon = self._make_hand_icon()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _make_hand_icon() -> QPixmap:
        pix = QPixmap(22, 22)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.moveTo(11, 2);  path.lineTo(20, 11); path.lineTo(11, 20)
        path.lineTo(10, 15); path.lineTo(15, 11); path.lineTo(10, 7)
        path.closeSubpath()
        p.setPen(QPen(_C_ACCENT, 2))
        p.setBrush(QColor(_C_ACCENT.red(), _C_ACCENT.green(), _C_ACCENT.blue(), 60))
        p.drawPath(path)
        p.end()
        return pix

    def _update_pulse(self):
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)
        self.update()

    # ── Public API ────────────────────────────────────────────────────────────

    def setSections(self, count: int) -> None:
        count = int(count)
        old_notes = [c.currentText() for c in self.combos]

        self.sections = count
        new_notes = (
            old_notes[:count] if count <= len(old_notes)
            else old_notes + ["C3"] * (count - len(old_notes))
        )

        for c in self.combos:
            c.deleteLater()
        self.combos = []

        for note in new_notes:
            combo = ToggleEnterComboBox(self)
            combo.addItems(self._all_notes)
            combo.setCurrentText(note)
            combo.currentIndexChanged.connect(
                lambda _: self.signalNotes.emit([c.currentText() for c in self.combos])
            )
            combo.show()
            self.combos.append(combo)

        self.signalNotes.emit([c.currentText() for c in self.combos])
        self._reposition_widgets()
        self.update()

    def setInstrument(self, index: int, dialog=None) -> None:
        self.current_instrument_index = index
        icon, name = self.instruments[index]
        self.center_button.setText(icon)
        self.signalInstrumentChanged.emit(index, name)
        if dialog:
            dialog.accept()

    # ── Internal layout ───────────────────────────────────────────────────────

    def _reposition_widgets(self) -> None:
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            return

        cx, cy = w / 2 - self.offset, h / 2
        r = min((h / 2) - self.margin, (w - cx) - self.margin)
        section_angle = math.pi / max(1, self.sections)
        start_ang = -math.pi / 2

        bw, bh = self.center_button.width(), self.center_button.height()
        self.center_button.move(int(cx - bw / 2), int(cy - bh / 2))

        for i, combo in enumerate(self.combos):
            mid = start_ang + section_angle * (i + 0.5)
            rr  = r * 0.6
            x   = cx + rr * math.cos(mid) - combo.width()  / 2
            y   = cy + rr * math.sin(mid) - combo.height() / 2
            combo.move(int(x), int(y))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_widgets()

    # ── Instrument selector ───────────────────────────────────────────────────

    def _show_instrument_selector(self) -> None:
        dlg = InstrumentSelectorDialog(
            self.instruments, self.current_instrument_index, self
        )
        dlg.instrumentSelected.connect(lambda idx: self.setInstrument(idx, None))
        dlg.exec()

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2 - self.offset, h / 2
        r = min((h / 2) - self.margin, (w - cx) - self.margin)

        # ── Background ───────────────────────────────────────────────────────
        painter.fillRect(self.rect(), _C_BG)

        # Soft radial glow centred on the arc pivot
        grad = QRadialGradient(cx, cy, r * 1.1)
        grad.setColorAt(0.0, QColor(_C_ACCENT.red() // 4, _C_ACCENT.green() // 3, _C_ACCENT.blue() // 3, 40))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), QBrush(grad))

        section_angle    = math.pi / max(1, self.sections)
        selected_tick    = int(
            ((self.gyro * math.pi / -180) + math.pi / 2) / (math.pi / self.ticks)
        )
        selected_section = int(
            ((self.gyro * math.pi / -180) + math.pi / 2) / (math.pi / self.sections)
        )
        start_ang, end_ang = -math.pi / 2, math.pi / 2

        # ── Outer arc track ──────────────────────────────────────────────────
        arc_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        painter.setPen(QPen(_C_TRACK, 1.5))
        painter.drawArc(arc_rect, 90 * 16, -180 * 16)

        # Thin inner ring (section boundary reference)
        inner_r = r * 0.3
        inner_rect = QRectF(cx - inner_r, cy - inner_r, 2 * inner_r, 2 * inner_r)
        painter.setPen(QPen(_C_TRACK, 1))
        painter.drawArc(inner_rect, 90 * 16, -180 * 16)

        pulse = 0.5 + 0.5 * math.sin(self.pulse_phase)

        # ── Ticks ────────────────────────────────────────────────────────────
        for i in range(self.ticks + 1):
            t  = start_ang + (end_ang - start_ang) * (i / self.ticks)
            ox, oy = cx + r * math.cos(t), cy + r * math.sin(t)
            tl = self.tick_long if i % 5 == 0 else self.tick_short
            ix, iy = cx + (r - tl) * math.cos(t), cy + (r - tl) * math.sin(t)

            if i == selected_tick:
                ang_deg = math.degrees(t)
                rotated = self._hand_icon.transformed(
                    QTransform().rotate(ang_deg),
                    Qt.TransformationMode.SmoothTransformation,
                )
                icon_r = r + 12
                px = cx + icon_r * math.cos(t) - rotated.width()  / 2
                py = cy + icon_r * math.sin(t) - rotated.height() / 2
                painter.drawPixmap(int(px), int(py), rotated)
                continue

            in_section = (
                0 <= selected_section < self.sections
                and selected_section * section_angle
                    <= t + math.pi / 2
                    <= (selected_section + 1) * section_angle
            )
            highlight = in_section and self.touch

            if highlight:
                r_val = int(_C_ACCENT.red()   * (0.8 + 0.2 * pulse))
                g_val = int(_C_ACCENT.green() * (0.8 + 0.2 * pulse))
                b_val = int(_C_ACCENT.blue()  * (0.8 + 0.2 * pulse))
                pen = QPen(QColor(r_val, g_val, b_val), 2.5)
            elif i % 5 == 0:
                pen = QPen(QColor(148, 163, 184), 1.5)  # brighter on major ticks
            else:
                pen = QPen(_C_TICK, 1)

            painter.setPen(pen)
            painter.drawLine(QPointF(ix, iy), QPointF(ox, oy))

        # ── "0°" label ───────────────────────────────────────────────────────
        painter.setPen(QColor(100, 116, 139, 180))
        f = painter.font()
        f.setPointSize(8)
        painter.setFont(f)
        painter.drawText(int(cx + r + 16), int(cy + 4), "0°")

        # ── Section dividers ─────────────────────────────────────────────────
        for i in range(self.sections + 1):
            t  = start_ang + section_angle * i
            x1, y1 = cx + r * 0.3 * math.cos(t), cy + r * 0.3 * math.sin(t)
            x2, y2 = cx + r * 0.8 * math.cos(t), cy + r * 0.8 * math.sin(t)

            if i in (selected_section, selected_section + 1) and self.touch:
                alpha = int(160 + 60 * pulse)
                r_val = int(_C_ACCENT.red()   * (0.7 + 0.3 * pulse))
                g_val = int(_C_ACCENT.green() * (0.7 + 0.3 * pulse))
                b_val = int(_C_ACCENT.blue()  * (0.7 + 0.3 * pulse))
                pen = QPen(QColor(r_val, g_val, b_val, alpha), 2)
            else:
                pen = QPen(_C_DIVIDER, 1.5)

            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
