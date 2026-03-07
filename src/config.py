import json

from PyQt6.QtWidgets import QFileDialog, QWidget


def save_setup(window: QWidget, parent: QWidget | None = None) -> None:
    path, _ = QFileDialog.getSaveFileName(
        parent, "Salvar Configuração", "", "JSON Files (*.json)"
    )
    if not path:
        return

    data = {
        "sections":       window.selector.sections,
        "instrument":     window.selector.current_instrument_index,
        "notes":          [c.currentText() for c in window.selector.combos],
        "midi_port_index": window.midi_output_combo.currentIndex(),
        "midi_channel":   int(window.channel_combo.currentText()),
    }
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print("Configuração salva em", path)
    except Exception as e:
        print("Erro ao salvar configuração:", e)


def load_setup(window: QWidget, parent: QWidget | None = None) -> None:
    path, _ = QFileDialog.getOpenFileName(
        parent, "Abrir Configuração", "", "JSON Files (*.json)"
    )
    if not path:
        return

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("Erro ao abrir configuração:", e)
        return

    window.selector.setSections(data.get("sections", 6))
    for combo, note in zip(window.selector.combos, data.get("notes", [])):
        combo.setCurrentText(note)
    window.selector.setInstrument(data.get("instrument", 0), None)
    window.midi_output_combo.setCurrentIndex(int(data.get("midi_port_index", 0)))
    window.channel_combo.setCurrentText(str(data.get("midi_channel", 1)))
    print("Configuração carregada de", path)
