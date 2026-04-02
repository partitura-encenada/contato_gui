from bleak import BleakScanner
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from constants import _asset
from protocol import BLE_MIDI_SERVICE_UUID

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

        self.list_widget = QListWidget(self)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.list_widget)

        for device in devices:
            item = QListWidgetItem(f"  {device.name}  —  {device.address}")
            item.setData(Qt.ItemDataRole.UserRole, device)
            self.list_widget.addItem(item)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        buttons_row.addStretch()

        cancel_button = QPushButton("Cancelar")
        connect_button = QPushButton("Conectar")
        connect_button.setDefault(True)
        buttons_row.addWidget(cancel_button)
        buttons_row.addWidget(connect_button)
        layout.addLayout(buttons_row)

        cancel_button.clicked.connect(self.reject)
        connect_button.clicked.connect(self._accept_selected_device)

        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)
        self.list_widget.setFocus()

    def _accept_selected_device(self):
        current_item = self.list_widget.currentItem()
        self.selected_device = current_item.data(Qt.ItemDataRole.UserRole)
        self.accept()
