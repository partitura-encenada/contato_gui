from bleak import BleakScanner
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
)
from PyQt6.QtGui import QIcon

from protocol import BLE_MIDI_SERVICE_UUID
from constants import _asset

_ICON = _asset("icon.ico")


async def scan_devices():
    return await BleakScanner.discover(timeout=3.0, service_uuids=[BLE_MIDI_SERVICE_UUID])


class DevicePickerDialog(QDialog):
    def __init__(self, devices):
        super().__init__()
        self.selected_device = None

        self.setWindowTitle("Selecionar dispositivo BLE")
        self.setWindowIcon(QIcon(_ICON))
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Dispositivos encontrados"))
        layout.addWidget(QLabel("Selecione o dispositivo 'Contato' para conectar:"))

        self.listw = QListWidget(self)
        self.listw.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.listw.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for d in devices:
            item = QListWidgetItem(f"  {d.name or 'Unknown'}  —  {d.address}")
            item.setData(Qt.ItemDataRole.UserRole, d)
            self.listw.addItem(item)
        layout.addWidget(self.listw)

        hl = QHBoxLayout()
        hl.setSpacing(8)
        btn_cancel = QPushButton("Cancelar")
        btn_ok     = QPushButton("Conectar")
        btn_ok.setDefault(True)
        hl.addStretch()
        hl.addWidget(btn_cancel)
        hl.addWidget(btn_ok)
        layout.addLayout(hl)

        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)

        if self.listw.count():
            self.listw.setCurrentRow(0)
        self.listw.setFocus()

    def _on_ok(self) -> None:
        sel = self.listw.currentItem()
        if sel:
            self.selected_device = sel.data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            self.reject()
