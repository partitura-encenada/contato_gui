"""Inicialização da aplicação

Aplica o tema escuro, exibe a tela de carregamento, varre dispositivos BLE,
apresenta o seletor de dispositivo e, após a conexão, abre a janela principal.
"""

import asyncio

from ble_scanner import scan_devices, pick_device
from ble_client import BleConnection
from midi_manager import MidiManager
from constants import PORT_INDEX
from main_window import MainWindow
from splash_screen import SplashScreen


async def main_async(app) -> None:
    """Corrotina principal: varre BLE, conecta e exibe a janela."""
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

    # Exibe splash enquanto a varredura BLE ocorre em segundo plano
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    devices = await scan_devices()

    splash.close()

    selected = pick_device(devices, parent=None)
    if not selected:
        print("Nenhum dispositivo selecionado — encerrando.")
        app.quit()
        return

    midi = MidiManager(PORT_INDEX)
    ble  = BleConnection()
    
    win = MainWindow(ble=ble, midi=midi, device=selected)
    win.setWindowTitle("Contato GUI")
    win.show()

    # Aguarda o sinal de fechamento da aplicação antes de encerrar o loop
    await app_close_event.wait()
