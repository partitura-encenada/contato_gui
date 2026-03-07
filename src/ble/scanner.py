from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
)
from bleak import BleakScanner

from constants import BLE_MIDI_SERVICE_UUID

# Import lazily to avoid circular issues at module load time
def _theme():
    from ui.theme import BG, SURFACE, BORDER, ACCENT, ACCENT2, TEXT, MUTED
    return BG, SURFACE, BORDER, ACCENT, ACCENT2, TEXT, MUTED


async def scan_devices() -> list:
    """Scan for BLE MIDI devices and return the list."""
    return await BleakScanner.discover(
        timeout=3.0,
        service_uuids=[BLE_MIDI_SERVICE_UUID],
    )


def pick_device(devices: list, parent=None):
    """Show a dialog to pick one device from a pre-scanned list.

    Returns the selected BleakDevice, or None if cancelled.
    """
    BG, SURFACE, BORDER, ACCENT, ACCENT2, TEXT, MUTED = _theme()

    dlg = QDialog(parent)
    dlg.setWindowTitle("Selecionar dispositivo BLE")
    dlg.setModal(True)
    dlg.setMinimumWidth(360)
    dlg.setStyleSheet(f"QDialog {{ background: {BG}; }}")

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)

    heading = QLabel("Dispositivos encontrados")
    heading.setStyleSheet(
        f"color: {TEXT}; font-size: 14px; font-weight: bold; background: transparent;"
    )
    sub = QLabel("Selecione o dispositivo 'Contato' para conectar:")
    sub.setStyleSheet(f"color: {MUTED}; font-size: 12px; background: transparent;")
    layout.addWidget(heading)
    layout.addWidget(sub)

    listw = QListWidget(dlg)
    listw.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    listw.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    for d in devices:
        item = QListWidgetItem(f"  {d.name or 'Unknown'}  —  {d.address}")
        item.setData(Qt.ItemDataRole.UserRole, d)
        listw.addItem(item)
    layout.addWidget(listw)

    hl = QHBoxLayout()
    hl.setSpacing(8)
    btn_cancel = QPushButton("Cancelar")
    btn_ok     = QPushButton("Conectar")
    btn_ok.setStyleSheet(
        f"QPushButton {{ background: {ACCENT2}; color: #fff; border: 1px solid {ACCENT};"
        f"border-radius: 6px; padding: 5px 18px; font-weight: bold; }}"
        f"QPushButton:hover {{ background: {ACCENT}; }}"
    )
    hl.addStretch()
    hl.addWidget(btn_cancel)
    hl.addWidget(btn_ok)
    layout.addLayout(hl)

    result: dict = {"device": None}

    def on_ok():
        sel = listw.currentItem()
        if sel:
            result["device"] = sel.data(Qt.ItemDataRole.UserRole)
            dlg.accept()
        else:
            dlg.reject()

    btn_ok.clicked.connect(on_ok)
    btn_cancel.clicked.connect(dlg.reject)
    listw.setCurrentRow(0)
    listw.setFocus()

    return result["device"] if dlg.exec() else None
