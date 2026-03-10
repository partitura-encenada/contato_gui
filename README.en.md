# Contato GUI

Desktop application for gestural MIDI instrument control via Bluetooth Low Energy.

## About

**Contato GUI** is a BLE → MIDI bridge developed as a university research project by the GruPPEn group (UFRJ), with support from UFRJ's Technology Park. It connects the Contato hardware to any MIDI-compatible synthesizer or DAW. The device uses a gyroscope and capacitive touch sensor to select and trigger notes in real time with low latency.

## Features

- Automatic BLE connection to the Contato device
- Interactive circular note selector with real-time gyroscope position visualization
- Support for 1–8 individually configurable note sections
- Instrument selection via MIDI Program Change (16 GM instruments)
- Accelerometer sensitivity configuration (Soft / Medium / Hard)
- Configurable gyroscope mapping direction (Left / Right)
- MIDI output port and channel selection (1–16)
- Save and load session configurations as JSON files
- Light theme PyQt6 interface

## Requirements

- Python 3.10 or higher
- Windows 10/11 (BLE support via WinRT) — Linux/macOS work via native Bleak
- Contato hardware with up-to-date firmware

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m src
```

## Project Structure

```
contato_gui/
├── src/
│   ├── __main__.py          # Entry point
│   ├── app.py               # Application startup
│   ├── main_window.py       # Main window
│   ├── notes_selector.py    # Circular note selector widget
│   ├── combo_box.py         # Custom combo box
│   ├── instrument_dialog.py # Instrument selector dialog
│   ├── about_dialog.py      # About dialog
│   ├── splash_screen.py     # Splash screen
│   ├── ble_client.py        # BLE connection management
│   ├── ble_scanner.py       # BLE device discovery
│   ├── midi_manager.py      # MIDI output
│   ├── constants.py         # BLE UUIDs, enums, music constants
│   ├── config.py            # Save/load configuration
│   └── assets/
│       ├── splash.png       # GruPPEn logo (splash screen)
│       ├── icon.ico
│       └── logos/
│           ├── parque_tecnologico.png
│           ├── ufrj.png
│           ├── inova_ufrj.png
│           └── coppetec.png
└── references/
    └── repertorio/          # Musical piece reference data
```

## Support and Sponsorship

<table>
  <tr>
    <td align="center" colspan="1"><b>Sponsorship</b></td>
    <td align="center" colspan="2"><b>Institutional Affiliation</b></td>
    <td align="center" colspan="2"><b>Partners</b></td>
  </tr>
  <tr>
    <td align="center">
      <img src="src/assets/logos/parque_tecnologico.png" alt="UFRJ Technology Park" height="50"/><br/>
      <b>UFRJ Technology Park</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/ufrj.png" alt="UFRJ" height="50"/><br/>
      <b>Federal University<br/>of Rio de Janeiro</b>
    </td>
    <td align="center">
      <b>School of Physical Education<br/>and Sports<br/>Department of Body Arts<br/>NCE – Electronic Computing Nucleus<br/>Center for Arts and Letters</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/inova_ufrj.png" alt="Inova UFRJ" height="50"/><br/>
      <b>Inova UFRJ</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/coppetec.png" alt="Fundação Coppetec" height="50"/><br/>
      <b>Fundação Coppetec</b>
    </td>
  </tr>
</table>
