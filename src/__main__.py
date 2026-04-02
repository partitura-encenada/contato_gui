import asyncio
import sys

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QCheckBox, QPushButton
from qasync import QApplication as QAsyncApplication, QEventLoop

from device_picker_dialog import DevicePickerDialog, scan_devices
from main_window import MainWindow
from splash_screen import SplashScreen


APP_STYLESHEET = """
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
QTabBar::tab          { background: #dde8ee; border: 1px solid #7dbfe8; border-bottom: none; padding: 4px 10px; margin-right: 2px; }
QTabBar::tab:selected { background: #eaf4fb; }
QTabBar::tab:hover    { background: #d0ecf8; }
"""

APP_ACCESSIBLE_DESCRIPTION = (
    "Contato, o instrumento musical para ser dançado."
    "Use Tab para navegar pelos controles."
    "As notas musicais ficam no início da navegação, seguidas das configurações. "
    "Aguardando conexão com o dispositivo Contato."
)


class EnterKeyFilter(QObject):
    def eventFilter(self, obj, event):
        is_enter = event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if is_enter and isinstance(obj, (QPushButton, QCheckBox)):
            obj.click()
            return True
        return False


async def run_application(app):
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    splash = SplashScreen()
    splash.show()
    app.processEvents()
    devices = await scan_devices()
    splash.close()

    dialog = DevicePickerDialog(devices)
    if not dialog.exec():
        app.quit()
        return

    window = MainWindow(app)
    window.add_device(dialog.selected_device)
    window.setAccessibleName(APP_ACCESSIBLE_DESCRIPTION)
    window.show()

    await asyncio.sleep(0)
    window.setFixedSize(window.size())
    screen = app.primaryScreen().availableGeometry()
    window.move((screen.width() - window.width()) // 2, screen.top())

    await app_close_event.wait()


if __name__ == "__main__":
    app = QAsyncApplication(sys.argv)
    app.installEventFilter(EnterKeyFilter(app))
    app.setStyleSheet(APP_STYLESHEET)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    with event_loop:
        event_loop.run_until_complete(run_application(app))
