import math

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtWidgets import QFrame, QPushButton
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPainterPath,
)

from constants import NOTE_NAMES, INSTRUMENTS
from combo_box import ToggleEnterComboBox
from instrument_dialog import InstrumentSelectorDialog


_C_TRACK   = QColor(71,  85,  105, 80)
_C_TICK    = QColor(100, 120, 140)
_C_ACCENT  = QColor(50,  150, 210)
_C_DIVIDER = QColor(50,  150, 210, 45)


class SeletorCircular(QFrame):
    signalInstrumentChanged = pyqtSignal(int, str)
    signalNotes             = pyqtSignal(list)
    signalNotePreview       = pyqtSignal(str)

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

        self.gyro         = 0
        self.touch        = False
        self.tilt         = 0
        self.tilt_enabled = False

        self._all_notes = [
            f"{note} {octave}"
            for octave in range(1, 6)
            for note in NOTE_NAMES
        ]

        self.instruments = INSTRUMENTS
        self.current_instrument_index = 0

        icon, _ = self.instruments[0]
        self.center_button = QPushButton(icon, self)
        self.center_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.center_button.setFixedSize(90, 90)
        self.center_button.setStyleSheet("QPushButton { border-radius: 45px; font-size: 32px; }")
        self.center_button.setAccessibleName("Instrumento")
        self.center_button.clicked.connect(self._show_instrument_selector)

    def setSections(self, count: int) -> None:
        count     = int(count)
        old_notes = [c.currentText() for c in self.combos]

        self.sections = count
        new_notes = (
            old_notes[:count] if count <= len(old_notes)
            else old_notes + [f"{NOTE_NAMES[0]} 3"] * (count - len(old_notes))
        )

        for c in self.combos:
            c.deleteLater()
        self.combos = []

        for i, note in enumerate(new_notes):
            combo = ToggleEnterComboBox(self)
            combo.addItems(self._all_notes)
            combo.blockSignals(True)
            combo.setCurrentText(note)
            combo.blockSignals(False)
            combo.setAccessibleName(f"Nota {i + 1}: {note.replace('#', ' Sustenido')}")
            combo.currentIndexChanged.connect(
                lambda _: self.signalNotes.emit([c.currentText() for c in self.combos])
            )
            combo.currentIndexChanged.connect(
                lambda _, c=combo: self.signalNotePreview.emit(c.currentText())
            )
            combo.currentIndexChanged.connect(
                lambda _, c=combo, n=i + 1: c.setAccessibleName(
                    f"Nota {n}: {c.currentText().replace('#', ' Sustenido')}"
                )
            )
            combo.show()
            self.combos.append(combo)

        self.signalNotes.emit([c.currentText() for c in self.combos])

        w, h   = self.width(), self.height()
        cx, cy = w / 2 - self.offset, h / 2
        r      = min((h / 2) - self.margin, (w - cx) - self.margin)
        section_angle = math.pi / max(1, self.sections)

        bw, bh = self.center_button.width(), self.center_button.height()
        self.center_button.move(int(cx - bw / 2), int(cy - bh / 2))

        for i, combo in enumerate(self.combos):
            mid = -math.pi / 2 + section_angle * (i + 0.5)
            rr  = r * 0.6
            x   = cx + rr * math.cos(mid) - combo.width()  / 2
            y   = cy + rr * math.sin(mid) - combo.height() / 2
            combo.move(int(x), int(y))

        self.update()

    def setInstrument(self, index: int) -> None:
        self.current_instrument_index = index
        icon, name = self.instruments[index]
        self.center_button.setText(icon)
        self.signalInstrumentChanged.emit(index, name)

    def _show_instrument_selector(self) -> None:
        dlg = InstrumentSelectorDialog(
            self.instruments, self.current_instrument_index, self
        )
        dlg.instrumentSelected.connect(self.setInstrument)
        dlg.exec()

    def _draw_arrow(self, painter, px, py, angle, opacity=1.0) -> None:
        path = QPainterPath()
        path.moveTo( 0, -9); path.lineTo(9,  0); path.lineTo(0,  9)
        path.lineTo(-1,  4); path.lineTo(4,  0); path.lineTo(-1, -4)
        path.closeSubpath()
        painter.save()
        painter.setOpacity(opacity)
        painter.translate(px, py)
        painter.rotate(math.degrees(angle))
        painter.setPen(QPen(_C_ACCENT, 2))
        painter.setBrush(_C_ACCENT)
        painter.drawPath(path)
        painter.restore()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h   = self.width(), self.height()
        cx, cy = w / 2 - self.offset, h / 2
        r      = min((h / 2) - self.margin, (w - cx) - self.margin)

        section_angle    = math.pi / max(1, self.sections)
        selected_tick    = int(((self.gyro * math.pi / -180) + math.pi / 2) / (math.pi / self.ticks))
        selected_section = int(((self.gyro * math.pi / -180) + math.pi / 2) / (math.pi / self.sections))
        start_ang, end_ang = -math.pi / 2, math.pi / 2

        arc_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        painter.setPen(QPen(_C_TRACK, 1.5))
        painter.drawArc(arc_rect, 90 * 16, -180 * 16)

        inner_r    = r * 0.3
        inner_rect = QRectF(cx - inner_r, cy - inner_r, 2 * inner_r, 2 * inner_r)
        painter.setPen(QPen(_C_TRACK, 1))
        painter.drawArc(inner_rect, 90 * 16, -180 * 16)

        for i in range(self.ticks + 1):
            t      = start_ang + (end_ang - start_ang) * (i / self.ticks)
            ox, oy = cx + r * math.cos(t), cy + r * math.sin(t)
            tl     = self.tick_long if i % 5 == 0 else self.tick_short
            ix, iy = cx + (r - tl) * math.cos(t), cy + (r - tl) * math.sin(t)

            if i == selected_tick:
                self._draw_arrow(painter, cx + (r + 12) * math.cos(t),
                                           cy + (r + 12) * math.sin(t), t)
                continue

            in_section = (
                0 <= selected_section < self.sections
                and selected_section * section_angle
                    <= t + math.pi / 2
                    <= (selected_section + 1) * section_angle
            )
            highlight = in_section and self.touch

            if highlight:
                pen = QPen(_C_ACCENT, 2.5)
            elif i % 5 == 0:
                pen = QPen(QColor(148, 163, 184), 1.5)
            else:
                pen = QPen(_C_TICK, 1)

            painter.setPen(pen)
            painter.drawLine(QPointF(ix, iy), QPointF(ox, oy))

        painter.setPen(QColor(100, 116, 139, 180))
        f = painter.font()
        f.setPointSize(8)
        painter.setFont(f)
        painter.drawText(int(cx + r + 30), int(cy + 4), "0°")

        for i in range(self.sections + 1):
            t      = start_ang + section_angle * i
            x1, y1 = cx + r * 0.3 * math.cos(t), cy + r * 0.3 * math.sin(t)
            x2, y2 = cx + r * 0.8 * math.cos(t), cy + r * 0.8 * math.sin(t)

            if i in (selected_section, selected_section + 1) and self.touch:
                pen = QPen(_C_ACCENT, 2)
            else:
                pen = QPen(_C_DIVIDER, 1.5)

            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        if self.tilt_enabled:
            gyro_angle  = self.gyro * math.pi / -180
            tilt_offset = -(self.tilt / 90.0) * (30 * math.pi / 180)
            ghost_angle = max(-math.pi / 2, min(math.pi / 2, gyro_angle + tilt_offset))
            self._draw_arrow(painter, cx + (r + 12) * math.cos(ghost_angle),
                                      cy + (r + 12) * math.sin(ghost_angle),
                                      ghost_angle, opacity=0.3)
