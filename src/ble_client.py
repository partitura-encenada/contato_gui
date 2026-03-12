import asyncio
import struct

from PyQt6.QtCore import QObject, pyqtSignal
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from constants import (
    SECTIONS_CHAR_UUID,
    STATUS_CHARACTERISTIC_UUID,
    ACCEL_SENS_CHARACTERISTIC_UUID,
    CALIBRATE_CHAR_UUID,
    BLE_MIDI_CHAR_UUID,
    DIR_CHAR_UUID,
    TILT_CHAR_UUID,
    LEGATO_CHAR_UUID,
    AccelLevel,
    NOTE_NAMES,
    name_to_midi,
)


class BleConnection(QObject):
    status_received = pyqtSignal(int, bool, int, int)
    initial_state   = pyqtSignal(dict)
    connected       = pyqtSignal()
    disconnected    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client: BleakClient | None = None
        self.midi = None
        self._running = True

    def _on_status(self, _: BleakGATTCharacteristic, data: bytearray):
        state, touch, gyro_x, accel_x, tilt = struct.unpack("<BBhhh", data)
        self.status_received.emit(gyro_x, bool(touch), state, tilt)

    def _on_midi(self, _: BleakGATTCharacteristic, data: bytearray):
        raw = bytes(data)
        if len(raw) < 3:
            return
        # Chamada direta evita o despacho pelo event loop do Qt
        self.midi.send(list(raw[-3:]))

    async def connect(self, device) -> None:
        while self._running:
            async with BleakClient(device) as client:
                self._client = client
                print(f"Conectado a {device.name} / {device.address}")
                self.connected.emit()

                # Lê estado inicial antes de ativar notificações
                state: dict = {}

                section_bytes = await client.read_gatt_char(SECTIONS_CHAR_UUID)
                notes = []
                for b in section_bytes:
                    note   = NOTE_NAMES[b % 12]
                    octave = max(1, min(5, (b // 12) - 1))
                    notes.append(f"{note} {octave}")
                state["notes"] = notes

                sens_bytes = await client.read_gatt_char(ACCEL_SENS_CHARACTERISTIC_UUID)
                raw = int.from_bytes(sens_bytes[:4], "little", signed=True)
                state["accel_level"] = min(AccelLevel, key=lambda lvl: abs(lvl.value - raw))

                dir_bytes = await client.read_gatt_char(DIR_CHAR_UUID)
                state["direction"] = 1 if dir_bytes[0] != 0 else 0

                tilt_bytes = await client.read_gatt_char(TILT_CHAR_UUID)
                state["tilt_enabled"] = tilt_bytes[0] != 0

                legato_bytes = await client.read_gatt_char(LEGATO_CHAR_UUID)
                state["legato_enabled"] = legato_bytes[0] != 0

                self.initial_state.emit(state)

                await client.start_notify(BLE_MIDI_CHAR_UUID, self._on_midi)
                await client.start_notify(STATUS_CHARACTERISTIC_UUID, self._on_status)

                while self._running and client.is_connected:
                    await asyncio.sleep(0.5)

            self._client = None
            if not self._running:
                break
            self.disconnected.emit()
            print("Desconectado. Tentando reconectar em 3s...")
            await asyncio.sleep(3)

    async def stop(self) -> None:
        self._running = False
        if self._client is not None and self._client.is_connected:
            await self._client.disconnect()

    async def write_sections(self, notes_list: list) -> None:
        midi_bytes = bytes([name_to_midi(n) for n in notes_list])
        await self._client.write_gatt_char(SECTIONS_CHAR_UUID, midi_bytes, response=True)
        print("Sections →", list(midi_bytes))

    async def write_accel(self, level: AccelLevel) -> None:
        payload = level.value.to_bytes(2, "little", signed=True)
        await self._client.write_gatt_char(ACCEL_SENS_CHARACTERISTIC_UUID, payload, response=True)
        print(f"Accel → {level.name} ({level.value})")

    async def write_direction(self, idx: int) -> None:
        val = bytes([1 if idx == 1 else 0])
        await self._client.write_gatt_char(DIR_CHAR_UUID, val, response=True)
        print(f"Direção → {'Esquerda' if idx == 1 else 'Direita'}")

    async def write_tilt_enabled(self, enabled: bool) -> None:
        await self._client.write_gatt_char(TILT_CHAR_UUID, bytes([1 if enabled else 0]), response=True)
        print(f"Pitch bend → {'on' if enabled else 'off'}")

    async def write_legato_enabled(self, enabled: bool) -> None:
        await self._client.write_gatt_char(LEGATO_CHAR_UUID, bytes([1 if enabled else 0]), response=True)
        print(f"Legato → {'on' if enabled else 'off'}")

    async def calibrate(self) -> None:
        await self._client.write_gatt_char(CALIBRATE_CHAR_UUID, bytes([0x01]), response=True)
        print("Calibração enviada.")
