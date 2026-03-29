import asyncio

from PyQt6.QtWidgets import QWidget
from qasync import asyncSlot

from about_dialog import AboutDialog
from ble_client import BleConnection
from config import load_setup, save_setup
from device_controls import DeviceControls
from loading_overlay import LoadingOverlay
from midi_manager import MidiManager
from protocol import GYRO_MAX_DEG, STATUS_CALIBRATING, name_to_midi


class DeviceTab(QWidget):
    def __init__(self, ble: BleConnection, midi: MidiManager, device=None):
        super().__init__()
        self.ble = ble
        self.midi = midi
        self.device = device

        self.controls = DeviceControls(self, midi)
        self.controls.build()
        self.overlay = LoadingOverlay(self)

        self.selector = self.controls.selector
        self.notas_spin = self.controls.notas_spin
        self.dir_combo = self.controls.dir_combo
        self.accel_combo = self.controls.accel_combo
        self.midi_output_combo = self.controls.midi_output_combo
        self.channel_combo = self.controls.channel_combo
        self.tilt_check = self.controls.tilt_check
        self.legato_check = self.controls.legato_check
        self.cal_btn = self.controls.cal_btn

        self._last_touch = False
        self._last_touch_note = ""
        self._calibrating = False
        self._about_dialog = None

        self._connect_ui()
        self._connect_ble()

        self.overlay.show_overlay("Conectando...")
        self.controls.set_controls_enabled(False)
        self.controls.rebuild_tab_order()

        if device:
            asyncio.create_task(self.ble.connect(device))

    def _connect_ui(self):
        self.controls.save_btn.clicked.connect(lambda: save_setup(self, self))
        self.controls.load_btn.clicked.connect(lambda: load_setup(self, self))
        self.controls.cal_btn.clicked.connect(self._on_calibrate)
        self.controls.about_btn.clicked.connect(self._show_about)

        self.notas_spin.valueChanged.connect(self.selector.setSections)
        self.notas_spin.valueChanged.connect(lambda _: self.controls.rebuild_tab_order())
        self.dir_combo.currentIndexChanged.connect(self._on_direction_changed)
        self.accel_combo.currentIndexChanged.connect(self._on_accel_changed)
        self.midi_output_combo.currentIndexChanged.connect(self.midi.open_port)
        self.tilt_check.stateChanged.connect(self._on_tilt_changed)
        self.legato_check.stateChanged.connect(self._on_legato_changed)

        self.selector.signalInstrumentChanged.connect(self._on_instrument_changed)
        self.selector.signalNotePreview.connect(self._on_note_preview)
        self.selector.signalNotes.connect(self._on_notes_changed)

    def _connect_ble(self):
        self.ble.midi = self.midi
        self.ble.status_received.connect(self._on_ble_status)
        self.ble.initial_state.connect(self._apply_initial_state)
        self.ble.disconnected.connect(self._on_ble_disconnected)

    def _set_status(self, message):
        self.controls.set_status(message)

    def _on_ble_status(self, gyro, touch, state, tilt):
        if state == STATUS_CALIBRATING:
            if not self._calibrating:
                self._calibrating = True
                self.overlay.show_overlay("Calibrando...")
            return

        if self._calibrating:
            self._calibrating = False
            self.overlay.hide_overlay()

        if touch and not self._last_touch:
            notes = [combo.currentText() for combo in self.selector.combos]
            section = min(int((-gyro + GYRO_MAX_DEG) / (2 * GYRO_MAX_DEG) * len(notes)), len(notes) - 1)
            self._last_touch_note = notes[section]
            self._set_status(f"Nota {self._last_touch_note} ativada")
        elif not touch and self._last_touch:
            self._set_status(f"Nota {self._last_touch_note} desativada")

        self._last_touch = touch
        self.selector.gyro = gyro
        self.selector.touch = touch
        self.selector.tilt = tilt
        self.selector.update()

    def _on_ble_disconnected(self):
        self._calibrating = False
        self.controls.set_controls_enabled(False)
        self.overlay.show_overlay("Reconectando...")

    def _apply_initial_state(self, state):
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

        if "tilt_enabled" in state:
            self.tilt_check.blockSignals(True)
            self.tilt_check.setChecked(state["tilt_enabled"])
            self.tilt_check.blockSignals(False)
            self.selector.tilt_enabled = state["tilt_enabled"]

        if "legato_enabled" in state:
            self.legato_check.blockSignals(True)
            self.legato_check.setChecked(state["legato_enabled"])
            self.legato_check.blockSignals(False)

        self.controls.set_controls_enabled(True)
        self.controls.rebuild_tab_order()
        self.overlay.hide_overlay()

    @asyncSlot(int, str)
    async def _on_instrument_changed(self, program, name):
        channel = int(self.channel_combo.currentText()) - 1
        self.midi.program_change(channel, program)

    def _on_note_preview(self, note_name):
        channel = int(self.channel_combo.currentText()) - 1
        self.midi.all_notes_off(channel)
        self.midi.preview_note(channel, name_to_midi(note_name))
        self._set_status(f"Pré-visualização: {note_name}")

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
