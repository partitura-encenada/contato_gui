"""Gerenciamento da conexão BLE com o dispositivo Contato.

Mantém o cliente Bleak ativo com reconexão automática, despacha notificações
de status e MIDI como sinais PyQt, e expõe métodos assíncronos para escrever
configurações no hardware via GATT.
"""

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
    AccelLevel,
    NOTE_NAMES,
    name_to_midi,
)


class BleConnection(QObject):
    status_received = pyqtSignal(int, bool, int)   # (gyro_x, touch, state)
    initial_state   = pyqtSignal(dict)         # estado inicial lido do hardware
    connected       = pyqtSignal()
    disconnected    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client: BleakClient | None = None
        self.midi = None

    # ── Callbacks de notificação BLE ──────────────────────────────────────────

    def _on_status(self, _: BleakGATTCharacteristic, data: bytearray):
        state, touch, gyro_x, accel_x = struct.unpack("<BBhh", data)
        self.status_received.emit(gyro_x, bool(touch), state)

    def _on_midi(self, _: BleakGATTCharacteristic, data: bytearray):
        raw = bytes(data)
        if len(raw) < 3:
            return
        self.midi.send(list(raw[-3:]))

    # ── Loop de conexão com reconexão automática ───────────────────────────────

    async def connect(self, device) -> None:
        """Conecta ao dispositivo e reconecta automaticamente após desconexão."""
        while True:
            async with BleakClient(device) as client:
                self._client = client
                print(f"Conectado a {device.name} / {device.address}")
                self.connected.emit()

                state = await self._read_initial_state(client)
                self.initial_state.emit(state)

                await client.start_notify(BLE_MIDI_CHAR_UUID, self._on_midi)
                await client.start_notify(STATUS_CHARACTERISTIC_UUID, self._on_status)

                while client.is_connected:
                    await asyncio.sleep(0.5)

            self._client = None
            self.disconnected.emit()
            print("Desconectado. Tentando reconectar em 3s...")
            await asyncio.sleep(3)

    async def _read_initial_state(self, client: BleakClient) -> dict:
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

        return state

    # ── Escrita no hardware ───────────────────────────────────────────────────

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

    async def calibrate(self) -> None:
        await self._client.write_gatt_char(CALIBRATE_CHAR_UUID, bytes([0x01]), response=True)
        print("Calibração enviada.")
