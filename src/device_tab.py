import asyncio

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from about_dialog import AboutDialog
from ble_client import BleConnection
from config import load_setup, save_setup
from midi_manager import MidiManager
from notes_selector import SeletorCircular
from protocol import AccelLevel, GYRO_MAX_DEG, STATUS_CALIBRATING, name_to_midi


class DeviceTab(QWidget):
    def __init__(self, ble: BleConnection, midi: MidiManager, device):
        super().__init__()
        self.ble = ble
        self.midi = midi
        self.device = device

        self._last_touch = False
        self._last_touch_note = ""
        self._calibrating = False
        self._about_dialog = None

        style = QApplication.style()

        self.selector = SeletorCircular(sections=6, ticks=60)
        self.selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.save_btn = QPushButton(" Salvar")
        self.load_btn = QPushButton(" Abrir")
        self.cal_btn = QPushButton(" Calibrar")
        self.about_btn = QPushButton(" Sobre")
        for button, icon, accessible_name in (
            (self.save_btn, QStyle.StandardPixmap.SP_DialogSaveButton, "Salvar configuração em arquivo"),
            (self.load_btn, QStyle.StandardPixmap.SP_DialogOpenButton, "Abrir configuração de arquivo"),
            (self.cal_btn, QStyle.StandardPixmap.SP_BrowserReload, "Calibrar giroscópio"),
            (self.about_btn, QStyle.StandardPixmap.SP_MessageBoxInformation, "Sobre o Contato GUI"),
        ):
            button.setIcon(style.standardIcon(icon))
            button.setIconSize(QSize(16, 16))
            button.setFixedHeight(24)
            button.setAccessibleName(accessible_name)

        self.notas_spin = QSpinBox()
        self.notas_spin.setRange(1, 8)
        self.notas_spin.setValue(6)
        self.notas_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.notas_spin.setAccessibleName("Número de notas")

        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["Direita", "Esquerda"])
        self.dir_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dir_combo.setAccessibleName("Direção do giroscópio")

        self.accel_combo = QComboBox()
        for level in AccelLevel:
            self.accel_combo.addItem(level.name.title(), level)
        self.accel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.accel_combo.setAccessibleName("Sensibilidade da percussão")

        self.midi_output_combo = QComboBox()
        self.midi_output_combo.addItems(self.midi.ports)
        self.midi_output_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.midi_output_combo.setAccessibleName("Porta de saída MIDI")

        self.channel_combo = QComboBox()
        self.channel_combo.addItems([str(i) for i in range(1, 17)])
        self.channel_combo.setFixedWidth(64)
        self.channel_combo.setAccessibleName("Canal MIDI de saída")

        self.tilt_check = QCheckBox()
        self.tilt_check.setAccessibleName("Pitch bend por inclinação do antebraço")

        self.legato_check = QCheckBox()
        self.legato_check.setAccessibleName("Modo legato: a nota sustenta até tocar outra")

        self.status_label = QLabel("—")

        self.overlay = QLabel(self)
        self.overlay.setVisible(False)
        self.overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay.setStyleSheet("background-color: rgba(234, 244, 251, 210); font-size: 14pt;")

        topbar = QFrame()
        topbar.setFixedHeight(40)
        topbar.setStyleSheet("QFrame { border-bottom: 1px solid #555; }")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(10, 0, 10, 0)
        topbar_layout.setSpacing(5)
        topbar_layout.addWidget(self.save_btn)
        topbar_layout.addWidget(self.load_btn)
        topbar_layout.addStretch()
        topbar_layout.addWidget(self.cal_btn)
        topbar_layout.addWidget(self.about_btn)

        midi_row = QWidget()
        midi_row_layout = QHBoxLayout(midi_row)
        midi_row_layout.setContentsMargins(0, 0, 0, 0)
        midi_row_layout.setSpacing(8)
        midi_row_layout.addWidget(self.midi_output_combo, stretch=1)
        midi_row_layout.addWidget(QLabel("Canal"))
        midi_row_layout.addWidget(self.channel_combo)

        controls_grid = QGridLayout()
        controls_grid.setHorizontalSpacing(14)
        controls_grid.setVerticalSpacing(8)
        controls_grid.setColumnMinimumWidth(0, 110)
        controls_grid.setColumnStretch(1, 1)
        controls_grid.addWidget(QLabel("Notas"), 0, 0)
        controls_grid.addWidget(self.notas_spin, 0, 1)
        controls_grid.addWidget(QLabel("Direção"), 1, 0)
        controls_grid.addWidget(self.dir_combo, 1, 1)
        controls_grid.addWidget(QLabel("Sensibilidade"), 2, 0)
        controls_grid.addWidget(self.accel_combo, 2, 1)
        controls_grid.addWidget(QLabel("Pitch bend"), 3, 0)
        controls_grid.addWidget(self.tilt_check, 3, 1, Qt.AlignmentFlag.AlignRight)
        controls_grid.addWidget(QLabel("Legato"), 4, 0)
        controls_grid.addWidget(self.legato_check, 4, 1, Qt.AlignmentFlag.AlignRight)
        controls_grid.addWidget(QLabel("Saída MIDI"), 5, 0)
        controls_grid.addWidget(midi_row, 5, 1)

        controls_card = QFrame()
        controls_card.setObjectName("ControlsCard")
        controls_card_layout = QVBoxLayout(controls_card)
        controls_card_layout.setContentsMargins(20, 14, 20, 16)
        controls_card_layout.setSpacing(0)
        controls_card_layout.addLayout(controls_grid)

        footer = QFrame()
        footer.setFixedHeight(22)
        footer.setStyleSheet("QFrame { background-color: #dde8ee; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 0, 10, 0)
        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(topbar)
        layout.addWidget(self.selector, stretch=1)
        layout.addWidget(controls_card)
        layout.addWidget(footer)

        self.save_btn.clicked.connect(lambda: save_setup(self, self))
        self.load_btn.clicked.connect(lambda: load_setup(self, self))
        self.cal_btn.clicked.connect(self._on_calibrate)
        self.about_btn.clicked.connect(self._show_about)

        self.notas_spin.valueChanged.connect(self.selector.setSections)
        self.notas_spin.valueChanged.connect(lambda _: self.rebuild_tab_order())
        self.dir_combo.currentIndexChanged.connect(self._on_direction_changed)
        self.accel_combo.currentIndexChanged.connect(self._on_accel_changed)
        self.midi_output_combo.currentIndexChanged.connect(self.midi.open_port)
        self.tilt_check.stateChanged.connect(self._on_tilt_changed)
        self.legato_check.stateChanged.connect(self._on_legato_changed)

        self.selector.signalInstrumentChanged.connect(self._on_instrument_changed)
        self.selector.signalNotePreview.connect(self._on_note_preview)
        self.selector.signalNotes.connect(self._on_notes_changed)

        self.ble.midi = self.midi
        self.ble.status_received.connect(self._on_ble_status)
        self.ble.initial_state.connect(self._apply_initial_state)
        self.ble.disconnected.connect(self._on_ble_disconnected)

        self.set_overlay("Conectando...")
        self.set_controls_enabled(False)
        self.rebuild_tab_order()
        asyncio.create_task(self.ble.connect(device))

    def resizeEvent(self, event):
        self.overlay.resize(self.size())
        super().resizeEvent(event)

    def set_overlay(self, message):
        self.overlay.setText(message)
        self.overlay.resize(self.size())
        self.overlay.raise_()
        self.overlay.setVisible(True)

    def clear_overlay(self):
        self.overlay.setVisible(False)

    def set_status(self, message):
        self.status_label.setText(message)

    def set_controls_enabled(self, enabled):
        self.selector.setEnabled(enabled)
        self.notas_spin.setEnabled(enabled)
        self.dir_combo.setEnabled(enabled)
        self.accel_combo.setEnabled(enabled)
        self.tilt_check.setEnabled(enabled)
        self.legato_check.setEnabled(enabled)
        self.midi_output_combo.setEnabled(enabled)
        self.channel_combo.setEnabled(enabled)
        self.cal_btn.setEnabled(enabled)

    def rebuild_tab_order(self):
        chain = [
            self.selector.center_button,
            *self.selector.combos,
            self.notas_spin,
            self.dir_combo,
            self.accel_combo,
            self.tilt_check,
            self.legato_check,
            self.midi_output_combo,
            self.channel_combo,
        ]
        for current, nxt in zip(chain, chain[1:]):
            QWidget.setTabOrder(current, nxt)

    def _on_ble_status(self, gyro, touch, state, tilt):
        if state == STATUS_CALIBRATING:
            if not self._calibrating:
                self._calibrating = True
                self.set_overlay("Calibrando...")
            return

        if self._calibrating:
            self._calibrating = False
            self.clear_overlay()

        if touch and not self._last_touch:
            notes = [combo.currentText() for combo in self.selector.combos]
            section = min(int((-gyro + GYRO_MAX_DEG) / (2 * GYRO_MAX_DEG) * len(notes)), len(notes) - 1)
            self._last_touch_note = notes[section]
            self.set_status(f"Nota {self._last_touch_note} ativada")
        elif not touch and self._last_touch:
            self.set_status(f"Nota {self._last_touch_note} desativada")

        self._last_touch = touch
        self.selector.gyro = gyro
        self.selector.touch = touch
        self.selector.tilt = tilt
        self.selector.update()

    def _on_ble_disconnected(self):
        self._calibrating = False
        self.set_controls_enabled(False)
        self.set_overlay("Reconectando...")

    def _apply_initial_state(self, state):
        notes = state["notes"]
        accel_level = state["accel_level"]
        direction = state["direction"]
        tilt_enabled = state["tilt_enabled"]
        legato_enabled = state["legato_enabled"]

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

        self.accel_combo.blockSignals(True)
        self.accel_combo.setCurrentIndex(self.accel_combo.findText(accel_level.name.title()))
        self.accel_combo.blockSignals(False)

        self.dir_combo.blockSignals(True)
        self.dir_combo.setCurrentIndex(direction)
        self.dir_combo.blockSignals(False)

        self.tilt_check.blockSignals(True)
        self.tilt_check.setChecked(tilt_enabled)
        self.tilt_check.blockSignals(False)
        self.selector.tilt_enabled = tilt_enabled

        self.legato_check.blockSignals(True)
        self.legato_check.setChecked(legato_enabled)
        self.legato_check.blockSignals(False)

        self.set_controls_enabled(True)
        self.rebuild_tab_order()
        self.clear_overlay()

    @asyncSlot(int, str)
    async def _on_instrument_changed(self, program, name):
        channel = int(self.channel_combo.currentText()) - 1
        self.midi.program_change(channel, program)

    def _on_note_preview(self, note_name):
        channel = int(self.channel_combo.currentText()) - 1
        self.midi.all_notes_off(channel)
        self.midi.preview_note(channel, name_to_midi(note_name))
        self.set_status(f"Pré-visualização: {note_name}")

    @asyncSlot(list)
    async def _on_notes_changed(self, notes_list):
        await self.ble.write_sections(notes_list)

    @asyncSlot(int)
    async def _on_accel_changed(self, idx):
        await self.ble.write_accel(self.accel_combo.itemData(idx))

    @asyncSlot(int)
    async def _on_tilt_changed(self, state):
        enabled = bool(state)
        self.selector.tilt_enabled = enabled
        await self.ble.write_tilt_enabled(enabled)

    @asyncSlot(int)
    async def _on_legato_changed(self, state):
        await self.ble.write_legato_enabled(bool(state))

    @asyncSlot(int)
    async def _on_direction_changed(self, idx):
        await self.ble.write_direction(idx)

    @asyncSlot()
    async def _on_calibrate(self):
        await self.ble.calibrate()

    def _show_about(self):
        dlg = AboutDialog(self)
        self._about_dialog = dlg
        dlg.finished.connect(lambda _: setattr(self, "_about_dialog", None))
        dlg.open()
