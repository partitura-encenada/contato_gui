# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
cd contato_gui
pip install -r requirements.txt
python -m src
```

There are no automated tests in this project.

## Architecture Overview

**Contato GUI** is a BLE → MIDI bridge: it connects to the Contato hardware device (which has a gyroscope and capacitive touch sensor) over Bluetooth Low Energy and routes MIDI events to a local MIDI output port.

### Async event loop

The entry point (`src/__main__.py`) sets up `qasync` to merge Qt's event loop with Python's `asyncio`. This is the foundation of the whole app — all BLE operations are `async`, and Qt signals/slots connect the two worlds. Slots that trigger BLE writes are decorated with `@asyncSlot` from `qasync`.

### Data flow

```
Hardware (BLE) ──notify──► BleConnection ──pyqtSignal──► MainWindow ──► MidiManager ──► MIDI port
                                                                   ▲
                                                            UI controls
                                                         (WNotesSelector, combos)
```

- `BleConnection` (`ble/client.py`) is a `QObject` that wraps a `BleakClient`. It emits `status_received(gyro_x, touch)` and `midi_received(msg)` as Qt signals from BLE notification callbacks.
- `MainWindow` connects those signals and forwards MIDI bytes directly to `MidiManager.send()`.
- Configuration written by the user (notes, accel level, direction) is sent back to the hardware via `write_gatt_char` on the corresponding UUIDs defined in `constants.py`.

### Startup sequence

1. `SplashScreen` is shown while `scan_devices()` runs (3 s BLE scan filtered by `BLE_MIDI_SERVICE_UUID`).
2. `pick_device()` shows a modal dialog to choose a device.
3. `MainWindow` is created; `BleConnection.connect()` is started as an `asyncio.create_task`.
4. On connection, `_read_initial_state()` reads current hardware config (notes, accel threshold, direction) and emits `initial_state`. `MainWindow._apply_initial_state()` populates the controls, then re-enables them (they start disabled).

### BLE GATT characteristics

All UUIDs are in `constants.py`. Key ones:
- `SECTIONS_CHAR_UUID` — array of MIDI note bytes (one per gyro section, 1–8 sections)
- `STATUS_CHARACTERISTIC_UUID` — notify: 5-byte packet `<hhB` (gyro_x, accel_x, touch)
- `BLE_MIDI_CHAR_UUID` — standard Apple BLE MIDI service; notify delivers raw MIDI messages

### UI structure

`WNotesSelector` (`ui/widgets/notes_selector.py`) is the central custom widget: a circular dial that visualises gyro position and lets the user assign notes to each section. It emits `signalNotes(list)` when notes change and `signalNotePreview(str)` on hover.

Theme colors and the global QSS stylesheet are in `ui/theme.py`. The dark palette is applied via both `QPalette` (for native subcontrols) and QSS.

### Configuration persistence

`config.py` provides `save_setup` / `load_setup` — plain JSON files containing notes, instrument index, MIDI port, and channel. These are user-managed files, not auto-saved.

### References

`references/repertorio/` contains JSON files representing musical pieces for the Contato repertoire. They are reference data, not loaded by the application at runtime.
