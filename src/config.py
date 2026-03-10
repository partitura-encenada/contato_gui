import json

from PyQt6.QtWidgets import QFileDialog, QWidget


def save_setup(window: QWidget, parent: QWidget | None = None) -> None:
    path, _ = QFileDialog.getSaveFileName(
        parent, "Salvar Configuração", "", "JSON Files (*.json)"
    )
    if not path:
        return

    data = {
        "sections":        window.selector.sections,
        "instrument":      window.selector.current_instrument_index,
        "notes":           [c.currentText() for c in window.selector.combos],
        "midi_port_index": window.midi_output_combo.currentIndex(),
        "midi_channel":    int(window.channel_combo.currentText()),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print("Configuração salva em", path)


def load_setup(window: QWidget, parent: QWidget | None = None) -> None:
    path, _ = QFileDialog.getOpenFileName(
        parent, "Abrir Configuração", "", "JSON Files (*.json)"
    )
    if not path:
        return

    with open(path, "r") as f:
        data = json.load(f)

    window.selector.setSections(data["sections"])
    for combo, note in zip(window.selector.combos, data["notes"]):
        combo.setCurrentText(note)
    window.selector.setInstrument(data["instrument"], None)
    window.midi_output_combo.setCurrentIndex(data["midi_port_index"])
    window.channel_combo.setCurrentText(str(data["midi_channel"]))
    print("Configuração carregada de", path)
