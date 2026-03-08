"""Descoberta de dispositivos BLE MIDI próximos.

Utiliza o BleakScanner para varrer anúncios BLE filtrando pelo UUID
do serviço BLE MIDI padrão, e apresenta um diálogo de seleção ao usuário.
"""
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
)
from PyQt6.QtGui import QIcon
from bleak import BleakScanner

from constants import BLE_MIDI_SERVICE_UUID


async def scan_devices() -> list:
    """Varre dispositivos BLE MIDI e retorna a lista encontrada (timeout 3s)."""
    return await BleakScanner.discover(
        timeout=3.0,
        service_uuids=[BLE_MIDI_SERVICE_UUID],
    )


def pick_device(devices: list, parent=None):
    """Exibe diálogo modal para o usuário escolher um dispositivo da lista.

    Retorna o BleakDevice selecionado, ou None se o usuário cancelar.
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle("Selecionar dispositivo BLE")
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    dlg.setWindowIcon(QIcon(icon_path))
    dlg.setModal(True)
    dlg.setMinimumWidth(360)

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)

    # Cabeçalho do diálogo
    heading = QLabel("Dispositivos encontrados")
    sub = QLabel("Selecione o dispositivo 'Contato' para conectar:")
    layout.addWidget(heading)
    layout.addWidget(sub)

    # Lista de dispositivos descobertos (nome + endereço MAC)
    listw = QListWidget(dlg)
    listw.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    listw.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    for d in devices:
        item = QListWidgetItem(f"  {d.name or 'Unknown'}  —  {d.address}")
        item.setData(Qt.ItemDataRole.UserRole, d)
        listw.addItem(item)
    layout.addWidget(listw)

    # Botões de ação
    hl = QHBoxLayout()
    hl.setSpacing(8)
    btn_cancel = QPushButton("Cancelar")
    btn_ok     = QPushButton("Conectar")
    btn_ok.setDefault(True)
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
