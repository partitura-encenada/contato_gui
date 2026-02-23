# Contato GUI

Desktop application for gestural MIDI instrument control via Bluetooth Low Energy.

## About

**Contato GUI** is a BLE → MIDI bridge that connects the Contato hardware to any MIDI-compatible synthesizer or DAW. The device uses a gyroscope and capacitive touch sensor to select and trigger notes in real time with low latency.

## Features

- Automatic BLE connection to the Contato device
- Interactive circular note selector with real-time gyroscope position visualization
- Support for 1–8 individually configurable note sections
- Instrument selection via MIDI Program Change (16 GM instruments)
- Accelerometer sensitivity configuration (Soft / Medium / Hard)
- Configurable gyroscope mapping direction (Left / Right)
- MIDI output port and channel selection (1–16)
- Save and load session configurations as JSON files
- Dark theme with custom PyQt6 interface

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
│   ├── constants.py         # BLE UUIDs, enums, music constants
│   ├── config.py            # Save/load configuration
│   ├── ble/
│   │   ├── scanner.py       # BLE device discovery
│   │   └── client.py        # BLE connection management
│   ├── midi/
│   │   └── manager.py       # MIDI output
│   ├── ui/
│   │   ├── app.py           # Application startup
│   │   ├── main_window.py   # Main window
│   │   ├── theme.py         # Dark theme
│   │   ├── splash.py        # Splash screen
│   │   ├── dialogs/
│   │   │   ├── about.py     # About dialog
│   │   │   └── instrument.py# Instrument selector
│   │   └── widgets/
│   │       ├── notes_selector.py  # Circular selector widget
│   │       └── combo_box.py       # Custom combo box
│   └── assets/
│       └── logos/           # Sponsor logos (add manually)
│           ├── parque_tec.png
│           ├── nce_ufrj.png
│           └── inova_ufrj.png
└── references/
    └── repertorio/          # Musical piece reference data
```

## Support and Sponsorship

This project is developed with the support of:

<table>
  <tr>
    <td align="center">
      <img src="src/assets/logos/parque_tec.png" alt="UFRJ Parque Tecnológico" height="50"/><br/>
      <b>UFRJ Parque Tecnológico</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/nce_ufrj.png" alt="NCE/UFRJ" height="50"/><br/>
      <b>Núcleo de Computação Eletrônica<br/>Instituto Tércio Pacitti de Aplicações<br/>e Pesquisas Computacionais (NCE/UFRJ)</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/inova_ufrj.png" alt="Inova UFRJ" height="50"/><br/>
      <b>Inova UFRJ</b>
    </td>
  </tr>
</table>

> **Note:** Place logo image files in `src/assets/logos/` for them to appear here and in the application's About dialog.
