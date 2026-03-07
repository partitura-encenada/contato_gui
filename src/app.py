"""Inicialização da aplicação e fluxo principal de arranque.

Aplica o tema escuro, exibe a tela de carregamento, varre dispositivos BLE,
apresenta o seletor de dispositivo e, após a conexão, abre a janela principal.
"""

import asyncio

from PyQt6.QtGui import QPalette, QColor

from ble_scanner import scan_devices, pick_device
from ble_client import BleConnection
from midi_manager import MidiManager
from constants import PORT_INDEX
from main_window import MainWindow
from splash_screen import SplashScreen
from theme import STYLESHEET, BG, SURFACE, RAISED, TEXT, ACCENT, ACCENT2


def _apply_dark_palette(app) -> None:
    """Aplica estilo Fusion com QPalette escura.

    Usar QPalette em vez de QSS para subcontroles nativos (setas, barras de
    rolagem, botões de spinbox) garante que renderizem em cores claras
    automaticamente, sem necessidade de regras QSS adicionais.
    """
    app.setStyle("Fusion")

    p = QPalette()
    c = QColor
    p.setColor(QPalette.ColorRole.Window,          c(BG))
    p.setColor(QPalette.ColorRole.WindowText,       c(TEXT))
    p.setColor(QPalette.ColorRole.Base,             c(RAISED))
    p.setColor(QPalette.ColorRole.AlternateBase,    c(SURFACE))
    p.setColor(QPalette.ColorRole.ToolTipBase,      c(SURFACE))
    p.setColor(QPalette.ColorRole.ToolTipText,      c(TEXT))
    p.setColor(QPalette.ColorRole.Text,             c(TEXT))
    p.setColor(QPalette.ColorRole.Button,           c(SURFACE))
    p.setColor(QPalette.ColorRole.ButtonText,       c(TEXT))
    p.setColor(QPalette.ColorRole.BrightText,       c(ACCENT))
    p.setColor(QPalette.ColorRole.Link,             c(ACCENT))
    p.setColor(QPalette.ColorRole.Highlight,        c(ACCENT2))
    p.setColor(QPalette.ColorRole.HighlightedText,  c("#ffffff"))

    # Cores para widgets desabilitados
    dis = QPalette.ColorGroup.Disabled
    p.setColor(dis, QPalette.ColorRole.WindowText, c("#475569"))
    p.setColor(dis, QPalette.ColorRole.Text,        c("#475569"))
    p.setColor(dis, QPalette.ColorRole.ButtonText,  c("#475569"))

    app.setPalette(p)


async def main_async(app) -> None:
    """Corrotina principal: configura tema, varre BLE, conecta e exibe a janela."""
    _apply_dark_palette(app)
    app.setStyleSheet(STYLESHEET)

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
