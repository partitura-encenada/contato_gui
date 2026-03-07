from enum import Enum

from PyQt6.QtGui import QColor

# ── BLE UUIDs ────────────────────────────────────────────────────────────────

SECTIONS_CHAR_UUID            = '251beea3-1c81-454f-a9dd-8561ec692ded'
STATUS_CHARACTERISTIC_UUID    = 'f8d968fe-99d7-46c4-a61c-f38093af6ec8'
ACCEL_SENS_CHARACTERISTIC_UUID = 'c7f2b2e2-1a2b-4c3d-9f0a-123456abcdef'
CALIBRATE_CHAR_UUID           = 'b4d0c9f8-3b9a-4a4e-93f2-2a8c9f5ee7a2'
BLE_MIDI_CHAR_UUID            = '7772e5db-3868-4112-a1a9-f2669d106bf3'
DIR_CHAR_UUID                 = 'a1b2c3d4-0001-4b33-a751-6ce34ec4c701'
BLE_MIDI_SERVICE_UUID         = '03b80e5a-ede8-4b33-a751-6ce34ec4c700'

# ── Enums ────────────────────────────────────────────────────────────────────

class AccelLevel(Enum):
    SOFT   = 800
    MEDIUM = 1250
    HARD   = 1600

# ── UI ───────────────────────────────────────────────────────────────────────

PRIMARY_COLOR = QColor(100, 180, 255)
PORT_INDEX    = 0

# ── Music ────────────────────────────────────────────────────────────────────

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

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
    if '#' in name[:2]:
        note, octave = name[:2], int(name[2:])
    else:
        note, octave = name[0], int(name[1:])
    return max(0, min(127, (octave + 1) * 12 + NOTE_NAMES.index(note)))
