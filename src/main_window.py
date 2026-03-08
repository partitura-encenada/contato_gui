"""Janela principal da aplicação Contato GUI.

Contém a barra superior com ações (salvar/abrir/calibrar/sobre), o widget seletor
de notas e o painel de controles (notas, direção, sensibilidade, MIDI).
"""

import asyncio
import os

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QComboBox,
    QLabel, QSpinBox, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSizePolicy, QStyle,
)
from PyQt6.QtGui import QIcon, QPainter, QColor
from qasync import asyncSlot

from constants import AccelLevel, GYRO_MAX_DEG, name_to_midi
from config import save_setup, load_setup
from ble_client import BleConnection
from midi_manager import MidiManager
from notes_selector import SeletorCircular
from about_dialog import AboutDialog


class LoadingOverlay(QWidget):
    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, parent):
        super().__init__(parent)
        self.setVisible(False)

        self._label = QLabel(self)
        font = self._label.font()
        font.setPointSize(14)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self._label)
        layout.addStretch()

        self._message = ""
        self._frame   = 0
        self._timer   = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)

    def show_overlay(self, message: str) -> None:
        self._message = message
        self._frame   = 0
        self._tick()
        self._timer.start()
        self.resize(self.parent().size())
        self.raise_()
        self.setVisible(True)

    def hide_overlay(self) -> None:
        self._timer.stop()
        self.setVisible(False)

    def _tick(self) -> None:
        f = self._FRAMES[self._frame % len(self._FRAMES)]
        self._label.setText(f"{f}  {self._message}")
        self._frame += 1

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(234, 244, 251, 210))


class MainWindow(QWidget):
    def __init__(self, ble: BleConnection, midi: MidiManager, device=None):
        super().__init__()
        self.ble  = ble
        self.midi = midi

        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Contato GUI")
        self.setFixedWidth(640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_topbar())

        self.selector = SeletorCircular(sections=6, ticks=60)
        self.selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.selector, stretch=1)

        self.selector.signalInstrumentChanged.connect(self._on_instrument_changed)
        self.selector.signalNotePreview.connect(self._on_note_preview)

        layout.addWidget(self._build_controls_card())
        layout.addWidget(self._build_footer())

        # signalNotes conectado após _build_controls_card para que o setValue
        # inicial do notas_spin não dispare uma escrita BLE antes da conexão
        self.selector.signalNotes.connect(self._on_notes_changed)

        # Overlay de carregamento (cobre a janela inteira)
        self.overlay = LoadingOverlay(self)
        self.overlay.show_overlay("Conectando...")

        # Sinais BLE
        self.ble.status_received.connect(self._on_ble_status)
        self.ble.midi_received.connect(self._on_ble_midi)
        self.ble.initial_state.connect(self._apply_initial_state)
        self.ble.disconnected.connect(self._on_ble_disconnected)

        self._last_touch      = False
        self._last_touch_note = ""
        self._calibrating     = False

        self._set_controls_enabled(False)

        if device:
            asyncio.create_task(self.ble.connect(device))

    # ── Construtores de layout ────────────────────────────────────────────────

    def _build_topbar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(40)
        frame.setStyleSheet("QFrame { border-bottom: 1px solid #555; }")

        topbar = QHBoxLayout(frame)
        topbar.setContentsMargins(10, 0, 10, 0)
        topbar.setSpacing(5)

        save_btn     = QPushButton(" Salvar")
        load_btn     = QPushButton(" Abrir")
        self.cal_btn = QPushButton(" Calibrar")
        about_btn    = QPushButton(" Sobre")

        style = QApplication.style()
        save_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        load_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.cal_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        about_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))

        icon_sz = QSize(16, 16)
        for b in (save_btn, load_btn, self.cal_btn, about_btn):
            b.setIconSize(icon_sz)
            b.setFixedHeight(24)

        save_btn.clicked.connect(lambda: save_setup(self, self))
        load_btn.clicked.connect(lambda: load_setup(self, self))
        self.cal_btn.clicked.connect(self._on_calibrate)
        about_btn.clicked.connect(lambda: AboutDialog(self).exec())

        topbar.addWidget(save_btn)
        topbar.addWidget(load_btn)
        topbar.addStretch()
        topbar.addWidget(self.cal_btn)
        topbar.addWidget(about_btn)

        return frame

    def _build_footer(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(22)
        frame.setStyleSheet("QFrame { background-color: #dde8ee; }")
        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 0, 10, 0)
        self._status_label = QLabel("—")
        row.addWidget(self._status_label)
        row.addStretch()
        return frame

    def _build_controls_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("ControlsCard")

        outer = QVBoxLayout(card)
        outer.setContentsMargins(20, 14, 20, 16)
        outer.setSpacing(0)

        def muted(text: str) -> QLabel:
            return QLabel(text)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)

        self.notas_spin = QSpinBox()
        self.notas_spin.setRange(1, 8)
        self.notas_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.notas_spin.valueChanged.connect(self.selector.setSections)
        self.notas_spin.setValue(6)
        grid.addWidget(muted("Notas"), 0, 0)
        grid.addWidget(self.notas_spin, 0, 1)

        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["Esquerda", "Direita"])
        self.dir_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dir_combo.currentIndexChanged.connect(self._on_direction_changed)
        grid.addWidget(muted("Direção"), 1, 0)
        grid.addWidget(self.dir_combo, 1, 1)

        self.accel_combo = QComboBox()
        for level in AccelLevel:
            self.accel_combo.addItem(level.name.title(), level)
        self.accel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.accel_combo.currentIndexChanged.connect(self._on_accel_changed)
        grid.addWidget(muted("Sensibilidade"), 2, 0)
        grid.addWidget(self.accel_combo, 2, 1)

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

    # ── Eventos ───────────────────────────────────────────────────────────────

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self.overlay.resize(self.size())

    # ── Manipuladores de sinais BLE ───────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        self._status_label.setText(msg)

    def _current_note_name(self, gyro: int) -> str:
        notes = [c.currentText() for c in self.selector.combos]
        if not notes:
            return "?"
        section = int((-gyro + GYRO_MAX_DEG) / (2 * GYRO_MAX_DEG) * len(notes))
        section = max(0, min(len(notes) - 1, section))
        return notes[section]

    def _on_ble_status(self, gyro: int, touch: bool) -> None:
        if self._calibrating:
            self._calibrating = False
            self.overlay.hide_overlay()

        if touch and not self._last_touch:
            self._last_touch_note = self._current_note_name(gyro)
            self._set_status(f"Nota {self._last_touch_note} ativada")
        elif not touch and self._last_touch:
            self._set_status(f"Nota {self._last_touch_note} desativada")

        self._last_touch    = touch
        self.selector.gyro  = gyro
        self.selector.touch = touch
        self.selector.update()

    def _on_ble_midi(self, msg: list) -> None:
        self.midi.send(msg)

    def _on_ble_disconnected(self) -> None:
        self._calibrating = False
        self._set_controls_enabled(False)
        self.overlay.show_overlay("Reconectando...")

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.selector.setEnabled(enabled)
        self.notas_spin.setEnabled(enabled)
        self.dir_combo.setEnabled(enabled)
        self.accel_combo.setEnabled(enabled)
        self.midi_output_combo.setEnabled(enabled)
        self.channel_combo.setEnabled(enabled)
        self.cal_btn.setEnabled(enabled)

    def _apply_initial_state(self, state: dict) -> None:
        notes = state.get("notes", [])

        self.notas_spin.blockSignals(True)
        self.notas_spin.setValue(len(notes))
        self.notas_spin.blockSignals(False)

        self.selector.blockSignals(True)
        self.selector.setSections(len(notes))
        self.selector.blockSignals(False)

        for combo, note in zip(self.selector.combos, notes):
            combo.blockSignals(True)
            combo.setCurrentText(note)
            combo.blockSignals(False)

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

        self._set_controls_enabled(True)
        self.overlay.hide_overlay()

    # ── Manipuladores de eventos da UI ────────────────────────────────────────

    def _on_midi_port_changed(self, idx: int) -> None:
        self.midi.open_port(idx)

    @asyncSlot(int, str)
    async def _on_instrument_changed(self, index: int, name: str) -> None:
        ch = max(0, min(15, int(self.channel_combo.currentText()) - 1))
        self.midi.program_change(ch, max(0, min(127, index)))

    def _on_note_preview(self, note_name: str) -> None:
        ch = max(0, min(15, int(self.channel_combo.currentText()) - 1))
        self.midi.all_notes_off(ch)
        self.midi.preview_note(ch, name_to_midi(note_name))
        self._set_status(f"Pré-visualização: {note_name}")

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
        self._calibrating = True
        self.overlay.show_overlay("Calibrando...")
        await self.ble.calibrate()
