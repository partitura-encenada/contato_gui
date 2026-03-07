import asyncio
import os

from PyQt6.QtCore import Qt, QPointF, QRectF, QSize
from PyQt6.QtWidgets import (
    QWidget, QFrame, QPushButton, QComboBox,
    QLabel, QSpinBox, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSizePolicy,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from qasync import asyncSlot

from constants import AccelLevel
from config import save_setup, load_setup
from ble.client import BleConnection
from midi.manager import MidiManager
from ui.widgets.notes_selector import WNotesSelector
from ui.dialogs.about import AboutDialog
from ui.theme import SURFACE, RAISED, BORDER, ACCENT, ACCENT2, TEXT, MUTED


def _btn_icon(kind: str, size: int = 13) -> QIcon:
    """Draw a minimal line icon for toolbar buttons."""
    color = QColor("#c8d4de")
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color, 1.3)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    s = float(size)

    if kind == "save":
        # Down-arrow with base line (save-to-disk)
        p.drawLine(QPointF(s / 2, 1.5),       QPointF(s / 2, s - 3.5))
        p.drawLine(QPointF(s / 2 - 2.5, s - 6), QPointF(s / 2, s - 3.5))
        p.drawLine(QPointF(s / 2 + 2.5, s - 6), QPointF(s / 2, s - 3.5))
        p.drawLine(QPointF(2.0, s - 1.5),     QPointF(s - 2.0, s - 1.5))

    elif kind == "open":
        # Simplified folder shape
        p.drawLine(QPointF(1.5, 4.5),          QPointF(1.5, s - 1.5))
        p.drawLine(QPointF(1.5, s - 1.5),      QPointF(s - 1.5, s - 1.5))
        p.drawLine(QPointF(s - 1.5, s - 1.5),  QPointF(s - 1.5, 4.5))
        p.drawLine(QPointF(s - 1.5, 4.5),      QPointF(s / 2 + 1.0, 4.5))
        p.drawLine(QPointF(s / 2 + 1.0, 4.5),  QPointF(s / 2 - 0.5, 2.5))
        p.drawLine(QPointF(s / 2 - 0.5, 2.5),  QPointF(1.5, 2.5))
        p.drawLine(QPointF(1.5, 2.5),           QPointF(1.5, 4.5))

    elif kind == "info":
        # Circle with "i"
        p.drawEllipse(QRectF(1.5, 1.5, s - 3.0, s - 3.0))
        fat = QPen(color, 1.8)
        fat.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(fat)
        p.drawPoint(QPointF(s / 2, s * 0.33))
        p.drawLine(QPointF(s / 2, s * 0.47), QPointF(s / 2, s * 0.73))

    p.end()
    return QIcon(pix)


class MainWindow(QWidget):
    def __init__(self, ble: BleConnection, midi: MidiManager, device=None):
        super().__init__()
        self.ble  = ble
        self.midi = midi

        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Contato GUI")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_topbar())

        self.selector = WNotesSelector(sections=6, ticks=60)
        self.selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.selector, stretch=1)

        # Wire selector signals before building controls (setValue triggers setSections)
        self.selector.signalInstrumentChanged.connect(self._on_instrument_changed)
        self.selector.signalNotes.connect(self._on_notes_changed)

        layout.addWidget(self._build_controls_card())

        # Wire BLE signals
        self.ble.status_received.connect(self._on_ble_status)
        self.ble.midi_received.connect(self._on_ble_midi)
        self.ble.initial_state.connect(self._apply_initial_state)

        if device:
            asyncio.create_task(self.ble.connect(device))

    # ── Layout builders ───────────────────────────────────────────────────────

    def _build_topbar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(40)
        frame.setStyleSheet(
            f"QFrame {{ background-color: {SURFACE}; border-bottom: 1px solid {BORDER}; }}"
        )

        topbar = QHBoxLayout(frame)
        topbar.setContentsMargins(10, 0, 10, 0)
        topbar.setSpacing(5)

        save_btn  = QPushButton(" Salvar")
        load_btn  = QPushButton(" Abrir")
        about_btn = QPushButton(" Sobre")

        save_btn.setIcon(_btn_icon("save"))
        load_btn.setIcon(_btn_icon("open"))
        about_btn.setIcon(_btn_icon("info"))

        icon_sz = QSize(13, 13)
        for b in (save_btn, load_btn, about_btn):
            b.setIconSize(icon_sz)
            b.setFixedHeight(24)

        save_btn.clicked.connect(lambda: save_setup(self, self))
        load_btn.clicked.connect(lambda: load_setup(self, self))
        about_btn.clicked.connect(lambda: AboutDialog(self).exec())

        topbar.addWidget(save_btn)
        topbar.addWidget(load_btn)
        topbar.addStretch()
        topbar.addWidget(about_btn)

        return frame

    def _build_controls_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("ControlsCard")
        card.setStyleSheet(
            f"#ControlsCard {{ background-color: {SURFACE}; border-top: 1px solid {BORDER}; }}"
        )

        outer = QVBoxLayout(card)
        outer.setContentsMargins(20, 14, 20, 16)
        outer.setSpacing(0)

        def muted(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
            return lbl

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)

        # ── Row 0: Notes ──────────────────────────────────────────────────────
        self.notas_spin = QSpinBox()
        self.notas_spin.setRange(1, 8)
        self.notas_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.notas_spin.valueChanged.connect(self.selector.setSections)
        self.notas_spin.setValue(6)
        grid.addWidget(muted("Notas"), 0, 0)
        grid.addWidget(self.notas_spin, 0, 1)

        # ── Row 1: Direction ─────────────────────────────────────────────────
        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["Esquerda", "Direita"])
        self.dir_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dir_combo.currentIndexChanged.connect(self._on_direction_changed)
        grid.addWidget(muted("Direção"), 1, 0)
        grid.addWidget(self.dir_combo, 1, 1)

        # ── Row 2: Sensitivity ───────────────────────────────────────────────
        self.accel_combo = QComboBox()
        for level in AccelLevel:
            self.accel_combo.addItem(level.name.title(), level)
        self.accel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.accel_combo.currentIndexChanged.connect(self._on_accel_changed)
        grid.addWidget(muted("Sensibilidade"), 2, 0)
        grid.addWidget(self.accel_combo, 2, 1)

        # ── Row 3: MIDI output + channel (shared row) ────────────────────────
        self.midi_output_combo = QComboBox()
        self.midi_output_combo.addItems(self.midi.ports)
        self.midi_output_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.midi_output_combo.currentIndexChanged.connect(self._on_midi_port_changed)

        self.channel_combo = QComboBox()
        self.channel_combo.addItems([str(i) for i in range(1, 17)])
        self.channel_combo.setFixedWidth(64)

        midi_row = QHBoxLayout()
        midi_row.setContentsMargins(0, 0, 0, 0)
        midi_row.setSpacing(8)
        midi_row.addWidget(self.midi_output_combo, stretch=1)
        midi_row.addWidget(muted("Canal"))
        midi_row.addWidget(self.channel_combo)

        midi_container = QWidget()
        midi_container.setLayout(midi_row)

        grid.addWidget(muted("Saída MIDI"), 3, 0)
        grid.addWidget(midi_container, 3, 1)

        outer.addLayout(grid)
        return card

    # ── BLE signal handlers ───────────────────────────────────────────────────

    def _on_ble_status(self, gyro: int, touch: bool) -> None:
        self.selector.gyro  = gyro
        self.selector.touch = touch
        self.selector.update()

    def _on_ble_midi(self, msg: list) -> None:
        self.midi.send(msg)

    def _apply_initial_state(self, state: dict) -> None:
        notes = state.get("notes", [])
        self.notas_spin.setValue(len(notes))
        for combo, note in zip(self.selector.combos, notes):
            combo.setCurrentText(note)

        if "accel_level" in state:
            level = state["accel_level"]
            self.accel_combo.blockSignals(True)
            idx = self.accel_combo.findText(level.name.title())
            if idx >= 0:
                self.accel_combo.setCurrentIndex(idx)
            self.accel_combo.blockSignals(False)

        if "direction" in state:
            self.dir_combo.blockSignals(True)
            self.dir_combo.setCurrentIndex(state["direction"])
            self.dir_combo.blockSignals(False)

    # ── UI event handlers ─────────────────────────────────────────────────────

    def _on_midi_port_changed(self, idx: int) -> None:
        self.midi.open_port(idx)

    @asyncSlot(int, str)
    async def _on_instrument_changed(self, index: int, name: str) -> None:
        ch = max(0, min(15, int(self.channel_combo.currentText()) - 1))
        self.midi.program_change(ch, max(0, min(127, index)))

    @asyncSlot(list)
    async def _on_notes_changed(self, notes_list: list) -> None:
        await self.ble.write_sections(notes_list)

    @asyncSlot(int)
    async def _on_accel_changed(self, idx: int) -> None:
        level = self.accel_combo.itemData(idx)
        await self.ble.write_accel(level)

    @asyncSlot(int)
    async def _on_direction_changed(self, idx: int) -> None:
        await self.ble.write_direction(idx)

    @asyncSlot()
    async def _on_calibrate(self) -> None:
        await self.ble.calibrate()
