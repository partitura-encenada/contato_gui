"""Gerenciamento da conexão BLE com o dispositivo Contato.

Mantém o cliente Bleak ativo, despacha notificações de status e MIDI
como sinais PyQt, e expõe métodos assíncronos para escrever configurações
no hardware via GATT.
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
    # Emitido continuamente enquanto conectado: posição do giroscópio e estado do toque
    status_received = pyqtSignal(int, bool)   # (gyro_x, touch)
    midi_received   = pyqtSignal(list)         # mensagem MIDI bruta de 3 bytes

    # Emitido uma vez após a conexão, com o estado inicial lido do dispositivo
    initial_state   = pyqtSignal(dict)

    connected    = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client: BleakClient | None = None

    @property
    def is_connected(self) -> bool:
        """Retorna True se há um cliente BLE ativo e conectado."""
        return self._client is not None and self._client.is_connected

    # ── Callbacks de notificação BLE ──────────────────────────────────────────

    def _on_status(self, _: BleakGATTCharacteristic, data: bytearray):
        """Recebe pacote de status (5 bytes): gyro_x (int16), accel_x (int16), touch (uint8)."""
        gyro_x, _, touch = struct.unpack("<hhB", data)
        self.status_received.emit(gyro_x, bool(touch))

    def _on_midi(self, _: BleakGATTCharacteristic, data: bytearray):
        """Recebe mensagem BLE MIDI e repassa os 3 bytes de status+dados para o sinal."""
        raw = bytes(data)
        if len(raw) < 3:
            return
        # Os últimos 3 bytes do pacote BLE MIDI contêm a mensagem MIDI propriamente dita
        msg = list(raw[-3:])
        print("MIDI in:", msg)
        self.midi_received.emit(msg)

    # ── Ciclo de vida da conexão ──────────────────────────────────────────────

    async def connect(self, device) -> None:
        """Conecta ao dispositivo, lê o estado inicial e mantém a conexão aberta."""
        async with BleakClient(device) as client:
            self._client = client
            print(f"Conectado a {device.name} / {device.address}")
            self.connected.emit()

            # Lê configurações persistidas no hardware antes de ativar notificações
            state = await self._read_initial_state(client)
            self.initial_state.emit(state)

            await client.start_notify(BLE_MIDI_CHAR_UUID, self._on_midi)
            await client.start_notify(STATUS_CHARACTERISTIC_UUID, self._on_status)

            # Mantém a corrotina viva enquanto a conexão estiver ativa
            while True:
                await asyncio.sleep(1)

        self._client = None
        self.disconnected.emit()

    async def _read_initial_state(self, client: BleakClient) -> dict:
        """Lê seções de notas, nível de acelerômetro e direção do giroscópio do hardware."""
        state: dict = {}

        # Converte bytes MIDI de volta para nomes de nota legíveis (ex.: 60 → 'C4')
        section_bytes = await client.read_gatt_char(SECTIONS_CHAR_UUID)
        notes = []
        for b in section_bytes:
            note   = NOTE_NAMES[b % 12]
            octave = max(1, min(5, (b // 12) - 1))
            notes.append(f"{note}{octave}")
        state["notes"] = notes

        # Encontra o nível de AccelLevel mais próximo do valor salvo no hardware
        sens_bytes = await client.read_gatt_char(ACCEL_SENS_CHARACTERISTIC_UUID)
        if sens_bytes and len(sens_bytes) >= 4:
            raw = int.from_bytes(sens_bytes[:4], "little", signed=True)
            state["accel_level"] = min(AccelLevel, key=lambda lvl: abs(lvl.value - raw))

        # Direção do giro: 1 = esquerda, 0 = direita
        dir_bytes = await client.read_gatt_char(DIR_CHAR_UUID)
        if dir_bytes:
            state["direction"] = 1 if dir_bytes[0] != 0 else 0

        return state

    # ── Métodos de escrita no hardware ───────────────────────────────────────

    async def write_sections(self, notes_list: list) -> None:
        """Envia array de notas MIDI ao hardware para atualizar as seções do giroscópio."""
        if not self.is_connected:
            return
        midi_bytes = bytes([name_to_midi(n) for n in notes_list])
        await self._client.write_gatt_char(SECTIONS_CHAR_UUID, midi_bytes, response=True)
        print("Sections →", list(midi_bytes))

    async def write_accel(self, level: AccelLevel) -> None:
        """Envia o limiar de sensibilidade do acelerômetro ao hardware (int16 little-endian)."""
        if not self.is_connected:
            return
        payload = level.value.to_bytes(2, "little", signed=True)
        await self._client.write_gatt_char(ACCEL_SENS_CHARACTERISTIC_UUID, payload, response=True)
        print(f"Accel → {level.name} ({level.value})")

    async def write_direction(self, idx: int) -> None:
        """Envia o sentido do mapeamento do giroscópio (0 = direita, 1 = esquerda)."""
        if not self.is_connected:
            return
        val = bytes([1 if idx == 1 else 0])
        await self._client.write_gatt_char(DIR_CHAR_UUID, val, response=True)
        print(f"Direção → {'Esquerda' if idx == 1 else 'Direita'}")

    async def calibrate(self) -> None:
        """Dispara o processo de calibração do MPU6050 no hardware."""
        if not self.is_connected:
            print("Nenhum cliente BLE conectado — não é possível calibrar.")
            return
        await self._client.write_gatt_char(CALIBRATE_CHAR_UUID, bytes([0x01]), response=True)
        print("Calibração enviada.")
