# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
cd contato_gui
pip install -r requirements.txt
python -m src
```

## Building an Executable

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile --icon=src/assets/icon.ico --name=Contato --add-data "src/assets;assets" src/__main__.py
```

Output: `dist/Contato.exe`. Build artifacts are gitignored (`build/`, `dist/`, `*.spec`).

There are no automated tests in this project.

## Client / Server

This project is the **BLE client**. The server is the ESP32 firmware at `../contato_hardware/platformio/`.

The hardware advertises a single BLE service (`03B80E5A-EDE8-4B33-A751-6CE34EC4C700`) and the GUI connects to it as a central device. All UUIDs used here must match exactly what is defined in `../contato_hardware/platformio/include/config.h`.

### GATT contract

| Characteristic | Direction | Description |
|---|---|---|
| `MIDI_CHAR` | hardware → GUI (notify) | BLE MIDI packets (5-byte, standard Apple spec) |
| `STATUS_CHAR` | hardware → GUI (notify) | 6-byte struct `<BBhhh`: state (uint8), touch (uint8), gyro_x (int16), accel_x (int16), tilt (int16) |
| `SECTIONS_CHAR` | GUI → hardware (write) / hardware → GUI (read) | Array of MIDI note bytes, one per gyro section (1–8) |
| `ACCEL_SENS_CHAR` | GUI → hardware (write) / hardware → GUI (read) | int16 percussion sensitivity threshold |
| `DIR_CHAR` | GUI → hardware (write) / hardware → GUI (read) | uint8 gyro direction inversion flag (0 or 1) |
| `TILT_CHAR` | GUI → hardware (write) / hardware → GUI (read) | uint8 pitch bend enable flag (0 or 1) |
| `LEGATO_CHAR` | GUI → hardware (write) / hardware → GUI (read) | uint8 legato mode enable flag (0 or 1) |
| `CALIBRATE_CHAR` | GUI → hardware (write-only) | Any byte triggers MPU6050 calibration |

### Hardware behaviour (relevant to the GUI)

- Roll angle is clamped to ±90° (`GYRO_MAX_DEG` in `constants.py`), mapped to a note section index, and included in every `STATUS_CHAR` notify (~333 Hz).
- Touch on GPIO T3 triggers Note-On; release triggers Note-Off on the current section's note.
- Linear acceleration on X above the threshold triggers a percussion note on MIDI channel 8 (note 36, Bass Drum).
- All configuration (sections, sensitivity, direction, tilt, legato) is persisted in ESP32 NVS and read back on startup — which is why the GUI reads initial state immediately after connecting.

## Architecture Overview

**Contato GUI** is a BLE → MIDI bridge: it receives sensor data and MIDI events from the hardware and routes them to a local MIDI output port, while letting the user configure the hardware's note mapping. Multiple devices can be connected simultaneously, each managed in its own tab.

### Async event loop

`src/__main__.py` sets up `qasync` to merge Qt's event loop with Python's `asyncio`. All BLE operations are `async`, and Qt signals/slots connect the two worlds. Slots that trigger BLE writes are decorated with `@asyncSlot` from `qasync`.

**Critical**: never call `dlg.exec()` or `app.processEvents()` after `asyncio.create_task()` has been called, as this runs the event loop re-entrantly and triggers `RuntimeError: Cannot enter into task`. Use `dlg.open()` + `await future` for dialogs, and `await asyncio.sleep(0)` to yield when layout needs to settle.

### Data flow

```
Hardware (BLE) --notify--> BleConnection --pyqtSignal--> MainWindow --> MidiManager --> MIDI port
                                                               ^
                                                          UI controls
                                                       (SeletorCircular, combos)
```

- `BleConnection` (`ble_client.py`) wraps a `BleakClient` as a `QObject`, emitting `status_received(gyro_x, touch, state, tilt)` and calling `midi.send()` directly from the BLE callback thread (bypassing the Qt signal queue for lower latency).
- `MainWindow` connects BLE signals and updates the UI.
- User configuration changes are sent back via `write_gatt_char` on the corresponding UUIDs.

### Startup sequence

1. `SplashScreen` shown while `scan_devices()` runs a 3s BLE scan filtered by `BLE_MIDI_SERVICE_UUID`.
2. `DevicePickerDialog` (modal) lets the user pick a device using `dlg.exec()` (safe here — no tasks running yet).
3. `AppWindow` is created; `add_device()` creates a `MainWindow` tab and starts `BleConnection.connect()` as an `asyncio.create_task`.
4. On connection, initial state (sections, sensitivity, direction, tilt, legato) is read inline inside `connect()` and emitted as `initial_state`. `MainWindow._apply_initial_state()` populates the controls, then re-enables them (they start disabled).
5. The "+" tab in `AppWindow` opens `DevicePickerDialog` via `dlg.open()` + `await future` (non-blocking, avoids re-entrancy) to add more devices.

### UI structure

`AppWindow` (`app.py`) is the top-level window. It contains a `QTabWidget` where each tab is a `MainWindow` instance. The last tab is always a permanent "+" for adding new devices. The window is fixed-size and opens centered at the top of the primary screen.

`SeletorCircular` (`notes_selector.py`) is the central custom widget per tab: a semicircular arc that visualises the gyro position and lets the user assign notes to each section.

`LoadingOverlay` (defined in `main_window.py`) is a full-window semi-transparent overlay. It shows "Conectando..." on startup, "Reconectando..." on disconnect, and "Calibrando..." while calibration is in progress.

### BLE reconnection

`BleConnection.connect()` runs a `while self._running` loop: on disconnect or failed connection attempt, it waits 3 seconds and retries. `MainWindow` shows the reconnecting overlay on `disconnected` and hides it on `initial_state`. Calling `BleConnection.stop()` sets `_running = False` and disconnects immediately, breaking the loop — used when a tab is closed.

### Multi-device

Multiple `BleConnection` + `MidiManager` + `MainWindow` instances run concurrently on the same asyncio event loop. This is required on Windows: running two separate processes each subscribing to BLE characteristics with the same UUIDs causes WinRT to stop delivering notifications to the second process.

### Coding conventions

- No exception handling, no defensive fallbacks (except the bare `except` in `BleConnection.connect` required for reconnect loop)
- Slots doing BLE writes must be decorated with `@asyncSlot`
- `signalNotes` is connected to `_on_notes_changed` **after** building the controls card to prevent spurious BLE writes during widget init
- MIDI bytes are sent directly from the BLE callback thread (not via Qt signal) to avoid event-loop dispatch latency
- `dlg.open()` + `await future` pattern must be used for any dialog shown while BLE tasks are running

### Accessibility

The app targets full screen reader support (Narrator / NVDA on Windows):

- Every interactive widget has `setAccessibleName(...)` set with a descriptive Portuguese string.
- Note combo boxes use dynamic names via `currentIndexChanged`: `"Nota {n}: {note}"` with `#` replaced by ` Sustenido` (e.g. `"Nota 1: Dó Sustenido 3"`).
- The instrument button name updates on every `setInstrument` call: `"Instrumento: {name}"`.
- `QTabBar.setTabAccessibleName` labels each device tab and the "+" tab (`"Adicionar dispositivo"`). The "+" tab name is refreshed after every `insertTab` since its index shifts.
- Close buttons on tabs carry `"Fechar {device_name}"`.
- A startup `QAccessible.Event.Alert` on `AppWindow` announces a full app description when the window first appears.
- `_rebuild_tab_order()` in `MainWindow` sets an explicit `QWidget.setTabOrder` chain: instrument button → note combos → number-of-notes spin → direction → sensitivity → pitch bend → legato → MIDI port → MIDI channel. Rebuilt whenever `notas_spin` changes or `_apply_initial_state` runs.

### Configuration persistence

`config.py` provides `save_setup` / `load_setup` — plain JSON files containing notes, instrument index, MIDI port, and channel. These are user-managed files, not auto-saved.

### References

`references/repertorio/` contains JSON files representing musical pieces for the Contato repertoire. They are reference data, not loaded by the application at runtime.
