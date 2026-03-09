"""Inicialização da aplicação

Aplica o tema escuro, exibe a tela de carregamento, varre dispositivos BLE,
apresenta o seletor de dispositivo e, após a conexão, abre a janela principal.
"""

import asyncio
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
)
from PyQt6.QtGui import QIcon
from bleak import BleakScanner

from ble_client import BleConnection
from midi_manager import MidiManager
from constants import PORT_INDEX, BLE_MIDI_SERVICE_UUID
from main_window import MainWindow
from splash_screen import SplashScreen


async def main_async(app) -> None:
    app.setStyleSheet("""
        QWidget     { background-color: #eaf4fb; color: #1a3a4a; }
        QPushButton { background-color: #f5fbff; border: 1px solid #7dbfe8; border-radius: 6px; padding: 4px 10px; }
        QPushButton:hover   { background-color: #d0ecf8; }
        QPushButton:pressed { background-color: #7dbfe8; }
        QComboBox   { border: 1px solid #7dbfe8; padding: 4px }
        QSpinBox    { background-color: #f5fbff; border: 1px solid #7dbfe8; padding: 4px; }
        QListWidget { background-color: #f5fbff; border: 1px solid #7dbfe8; border-radius: 8px; outline: 0; }
        QListWidget::item:selected { background-color: #7dbfe8; color: #1a3a4a; outline: 0; }
    """)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # 3s BLE scan filtered by MIDI service UUID
    devices = await BleakScanner.discover(timeout=3.0, service_uuids=[BLE_MIDI_SERVICE_UUID])

    splash.close()

    # Device picker dialog
    dlg = QDialog()
    dlg.setWindowTitle("Selecionar dispositivo BLE")
    dlg.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "assets", "icon.ico")))
    dlg.setModal(True)
    dlg.setMinimumWidth(360)

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    layout.addWidget(QLabel("Dispositivos encontrados"))
    layout.addWidget(QLabel("Selecione o dispositivo 'Contato' para conectar:"))

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

    selected = result["device"] if dlg.exec() else None
    if not selected:
        print("Nenhum dispositivo selecionado — encerrando.")
        app.quit()
        return

    midi = MidiManager(PORT_INDEX)
    ble  = BleConnection()

    win = MainWindow(ble=ble, midi=midi, device=selected)
    win.setWindowTitle("Contato GUI")
    win.show()

    await app_close_event.wait()
