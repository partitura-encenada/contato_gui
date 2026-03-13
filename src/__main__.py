import sys
import asyncio

from qasync import QApplication as QAsyncApplication, QEventLoop

from main_window import MainWindow
from device_picker_dialog import scan_devices, DevicePickerDialog
from splash_screen import SplashScreen


async def main_async(app) -> None:
    app.setStyleSheet("""
        QWidget     { background-color: #eaf4fb; color: #1a3a4a; }
        QPushButton { background-color: #f5fbff; border: 1px solid #7dbfe8; padding: 4px 10px; }
        QPushButton:hover   { background-color: #d0ecf8; }
        QPushButton:pressed { background-color: #7dbfe8; }
        QComboBox   { border: 1px solid #7dbfe8; padding: 4px }
        QSpinBox    { background-color: #f5fbff; border: 1px solid #7dbfe8; padding: 4px; }
        QListWidget { background-color: #f5fbff; border: 1px solid #7dbfe8; border-radius: 8px; outline: 0; }
        QListWidget::item:selected { background-color: #7dbfe8; color: #1a3a4a; outline: 0; }
        QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #7dbfe8; background-color: #f5fbff; }
        QCheckBox::indicator:checked { background-color: #7dbfe8; }
        QTabWidget::pane { border: 1px solid #7dbfe8; border-top: none; }
        QTabBar::tab          { background: #dde8ee; border: 1px solid #7dbfe8;
                                border-bottom: none; padding: 4px 10px; margin-right: 2px; }
        QTabBar::tab:selected { background: #eaf4fb; }
        QTabBar::tab:hover    { background: #d0ecf8; }
    """)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    splash = SplashScreen()
    splash.show()
    app.processEvents()
    devices = await scan_devices()
    splash.close()

    dlg = DevicePickerDialog(devices)
    if not dlg.exec():
        print("Nenhum dispositivo selecionado — encerrando.")
        app.quit()
        return

    window = MainWindow(app)
    window.add_device(dlg.selected_device)
    window.show()
    await asyncio.sleep(0)
    window.setFixedSize(window.size())
    screen = app.primaryScreen().availableGeometry()
    window.move((screen.width() - window.width()) // 2, screen.top())

    # Anuncia uma descrição do app para leitores de tela (Narrator/NVDA) ao iniciar
    window.setAccessibleName(
        "Contato GUI. Instrumento MIDI gestual via Bluetooth. "
        "Use Tab para navegar pelos controles. "
        "As notas musicais ficam no início da navegação, seguidas das configurações. "
        "Aguardando conexão com o dispositivo Contato."
    )

    await app_close_event.wait()

if __name__ == "__main__":
    qapp = QAsyncApplication(sys.argv)
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main_async(qapp))
