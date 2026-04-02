import struct
from enum import Enum


BLE_MIDI_SERVICE_UUID          = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
BLE_MIDI_CHAR_UUID             = "7772e5db-3868-4112-a1a9-f2669d106bf3"
SECTIONS_CHAR_UUID             = "251beea3-1c81-454f-a9dd-8561ec692ded"
ACCEL_SENS_CHARACTERISTIC_UUID = "c7f2b2e2-1a2b-4c3d-9f0a-123456abcdef"
STATUS_CHARACTERISTIC_UUID     = "f8d968fe-99d7-46c4-a61c-f38093af6ec8"
DIR_CHAR_UUID                  = "a1b2c3d4-0001-4b33-a751-6ce34ec4c701"
CALIBRATE_CHAR_UUID            = "b4d0c9f8-3b9a-4a4e-93f2-2a8c9f5ee7a2"
TILT_CHAR_UUID                 = "d2e3f4a5-0002-4b33-a751-6ce34ec4c702"
LEGATO_CHAR_UUID               = "e3f4a5b6-0003-4b33-a751-6ce34ec4c703"

STATUS_IDLE        = 0
STATUS_CALIBRATING = 1

GYRO_MAX_DEG = 89

NOTE_NAMES = ["Dó", "Dó#", "Ré", "Ré#", "Mi", "Fá", "Fá#", "Sol", "Sol#", "Lá", "Lá#", "Si"]


class AccelLevel(Enum):
    SUAVE = 14000
    MÉDIO = 10000
    FORTE = 6000


def decode_status(data):
    state, touch, gyro_x, accel_x, tilt = struct.unpack("<BBhhh", data)
    return {
        "state": state,
        "touch": bool(touch),
        "gyro": gyro_x,
        "accel": accel_x,
        "tilt": tilt,
    }


def midi_to_name(value):
    note = NOTE_NAMES[value % 12]
    octave = max(1, min(5, (value // 12) - 1))
    return f"{note} {octave}"


def name_to_midi(name):
    for note in sorted(NOTE_NAMES, key=len, reverse=True):
        if name.startswith(note):
            octave = int(name[len(note):].strip())
            return (octave + 1) * 12 + NOTE_NAMES.index(note)
