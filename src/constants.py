from enum import Enum

from PyQt6.QtGui import QColor

# -- UUIDs BLE
# Devem coincidir exatamente com os UUIDs definidos no firmware (platformio/include/config.h).

SECTIONS_CHAR_UUID             = '251beea3-1c81-454f-a9dd-8561ec692ded'  # array de notas MIDI
STATUS_CHARACTERISTIC_UUID     = 'f8d968fe-99d7-46c4-a61c-f38093af6ec8'  # giroscópio + toque (notify)
ACCEL_SENS_CHARACTERISTIC_UUID = 'c7f2b2e2-1a2b-4c3d-9f0a-123456abcdef' # limiar do acelerômetro
CALIBRATE_CHAR_UUID            = 'b4d0c9f8-3b9a-4a4e-93f2-2a8c9f5ee7a2'  # dispara calibração
BLE_MIDI_CHAR_UUID             = '7772e5db-3868-4112-a1a9-f2669d106bf3'  # MIDI sobre BLE (padrão Apple)
DIR_CHAR_UUID                  = 'a1b2c3d4-0001-4b33-a751-6ce34ec4c701'  # direção do giro
BLE_MIDI_SERVICE_UUID          = '03b80e5a-ede8-4b33-a751-6ce34ec4c700'  # serviço BLE MIDI padrão

# -- Enums

class AccelLevel(Enum):
    """Níveis de sensibilidade do acelerômetro enviados ao hardware."""
    SUAVE = 800    # limiar baixo — responde a movimentos suaves
    MÉDIO = 1250   # limiar intermediário
    FORTE = 1600   # limiar alto — requer movimentos mais intensos

# -- UI

PRIMARY_COLOR = QColor(100, 180, 255)  # cor de destaque principal (azul claro)
PORT_INDEX    = 0                       # índice padrão da porta MIDI de saída
GYRO_MAX_DEG  = 90                      # deve coincidir com GYRO_MAX_DEG no firmware

# -- Música

NOTE_NAMES = ["Dó", "Dó#", "Ré", "Ré#", "Mi", "Fá", "Fá#", "Sol", "Sol#", "Lá", "Lá#", "Si"]

INSTRUMENTS: list[tuple[str, str]] = [
    ("🎹", "Piano de Cauda"),        ("🎼", "Piano Acústico"),
    ("🎵", "Piano Elétrico de Cauda"), ("🎶", "Piano Honky-tonk"),
    ("🎧", "Piano Elétrico 1"),      ("🎛️", "Piano Elétrico 2"),
    ("🎻", "Cravo"),                 ("🎸", "Clavinet"),
    ("✨", "Celesta"),               ("🔔", "Glockenspiel"),
    ("📦", "Caixinha de Música"),    ("🛎️", "Vibrafone"),
    ("🥁", "Marimba"),              ("🎺", "Xilofone"),
    ("⛓️", "Sinos Tubulares"),      ("🎶", "Dulcimer"),
]

def name_to_midi(name: str) -> int:
    """Converte nome de nota (ex.: 'Dó# 3') para número MIDI (0-127)."""
    for note in sorted(NOTE_NAMES, key=len, reverse=True):
        if name.startswith(note):
            octave = int(name[len(note):].strip())
            return (octave + 1) * 12 + NOTE_NAMES.index(note)
    return 0
