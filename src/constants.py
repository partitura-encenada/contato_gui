from enum import Enum

from PyQt6.QtGui import QColor

# ── UUIDs BLE ─────────────────────────────────────────────────────────────────
# Identificadores das características GATT do dispositivo Contato.
# Devem coincidir exatamente com os UUIDs definidos no firmware (platformio/include/config.h).

SECTIONS_CHAR_UUID            = '251beea3-1c81-454f-a9dd-8561ec692ded'  # array de notas MIDI
STATUS_CHARACTERISTIC_UUID    = 'f8d968fe-99d7-46c4-a61c-f38093af6ec8'  # giroscópio + toque (notify)
ACCEL_SENS_CHARACTERISTIC_UUID = 'c7f2b2e2-1a2b-4c3d-9f0a-123456abcdef' # limiar do acelerômetro
CALIBRATE_CHAR_UUID           = 'b4d0c9f8-3b9a-4a4e-93f2-2a8c9f5ee7a2'  # dispara calibração
BLE_MIDI_CHAR_UUID            = '7772e5db-3868-4112-a1a9-f2669d106bf3'  # MIDI sobre BLE (padrão Apple)
DIR_CHAR_UUID                 = 'a1b2c3d4-0001-4b33-a751-6ce34ec4c701'  # direção do giro
BLE_MIDI_SERVICE_UUID         = '03b80e5a-ede8-4b33-a751-6ce34ec4c700'  # serviço BLE MIDI padrão

# ── Enums ─────────────────────────────────────────────────────────────────────

class AccelLevel(Enum):
    """Níveis de sensibilidade do acelerômetro enviados ao hardware."""
    SOFT   = 800    # baixa sensibilidade — requer movimento mais brusco
    MEDIUM = 1250   # sensibilidade intermediária
    HARD   = 1600   # alta sensibilidade — responde a movimentos suaves

# ── UI ────────────────────────────────────────────────────────────────────────

PRIMARY_COLOR = QColor(100, 180, 255)  # cor de destaque principal (azul claro)
PORT_INDEX    = 0                       # índice padrão da porta MIDI de saída

# ── Música ───────────────────────────────────────────────────────────────────

# Nomes das 12 notas cromáticas (notação inglesa, usada internamente)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Instrumentos disponíveis no seletor (emoji + nome GM)
INSTRUMENTS: list[tuple[str, str]] = [
    ("🎹", "Acoustic Grand Piano"),  ("🎼", "Bright Acoustic Piano"),
    ("🎵", "Electric Grand Piano"),  ("🎶", "Honky-tonk Piano"),
    ("🎧", "Electric Piano 1"),      ("🎛️", "Electric Piano 2"),
    ("🎻", "Harpsichord"),           ("🎸", "Clavinet"),
    ("✨", "Celesta"),               ("🔔", "Glockenspiel"),
    ("📦", "Music Box"),             ("🛎️", "Vibraphone"),
    ("🥁", "Marimba"),              ("🎺", "Xylophone"),
    ("⛓️", "Tubular Bells"),        ("🎶", "Dulcimer"),
]

def name_to_midi(name: str) -> int:
    """Converte nome de nota (ex.: 'C#3') para número MIDI (0–127)."""
    if '#' in name[:2]:
        note, octave = name[:2], int(name[2:])
    else:
        note, octave = name[0], int(name[1:])
    return max(0, min(127, (octave + 1) * 12 + NOTE_NAMES.index(note)))
