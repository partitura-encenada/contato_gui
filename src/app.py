import asyncio
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QTabWidget, QTabBar,
)
from PyQt6.QtGui import QIcon, QAccessible, QAccessibleEvent
from qasync import asyncSlot

from ble_client import BleConnection
from ble_scanner import scan_devices
from midi_manager import MidiManager
from constants import PORT_INDEX
from main_window import MainWindow
from splash_screen import SplashScreen

_ICON = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")


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


class AppWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app      = app
        self._picking = False

        self.setWindowTitle("Contato GUI")
        self.setWindowIcon(QIcon(_ICON))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget(self)
        self.tabs.tabBarClicked.connect(self._on_tab_bar_clicked)
        self.tabs.currentChanged.connect(self._on_current_changed)
        layout.addWidget(self.tabs)

        # Permanent "+" tab — always the last tab
        self.tabs.addTab(QWidget(), "+")

    @property
    def _plus_idx(self) -> int:
        return self.tabs.count() - 1

    def add_device(self, device) -> None:
        ble  = BleConnection()
        midi = MidiManager(PORT_INDEX)
        page = MainWindow(ble=ble, midi=midi, device=device)
        idx  = self._plus_idx  # insert before "+"
        self.tabs.insertTab(idx, page, device.name or device.address)
        self.tabs.setCurrentIndex(idx)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet(
            "QPushButton { border: 1px solid #7dbfe8; background: transparent;"
            "              padding: 0; font-size: 12px; }"
            "QPushButton:hover { background: #d0ecf8; }"
        )
        close_btn.clicked.connect(lambda: self._close_tab(self.tabs.indexOf(page)))
        self.tabs.tabBar().setTabButton(idx, QTabBar.ButtonPosition.RightSide, close_btn)

    def _on_tab_bar_clicked(self, index: int) -> None:
        if index == self._plus_idx and not self._picking:
            asyncio.ensure_future(self._open_picker())

    def _on_current_changed(self, index: int) -> None:
        if index == self._plus_idx and self._plus_idx > 0:
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(self._plus_idx - 1)
            self.tabs.blockSignals(False)

    async def _open_picker(self) -> None:
        self._picking = True
        try:
            devices = await scan_devices()
            dlg = DevicePickerDialog(devices)
            future = asyncio.get_event_loop().create_future()
            dlg.finished.connect(future.set_result)
            dlg.open()
            if await future == QDialog.DialogCode.Accepted:
                self.add_device(dlg.selected_device)
        finally:
            self._picking = False

    def _cleanup_page(self, page: MainWindow) -> None:
        asyncio.create_task(page.ble.stop())
        for ch in range(16):
            page.midi.all_notes_off(ch)
        page.midi.close()
        page.deleteLater()

    def _close_tab(self, index: int) -> None:
        self._cleanup_page(self.tabs.widget(index))
        self.tabs.removeTab(index)
        if self.tabs.count() == 1:  # only "+" remains
            self.close()

    def closeEvent(self, event) -> None:
        while self.tabs.count() > 1:
            self._cleanup_page(self.tabs.widget(0))
            self.tabs.removeTab(0)
        self.app.quit()
        super().closeEvent(event)


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

    window = AppWindow(app)
    window.add_device(dlg.selected_device)
    window.show()
    await asyncio.sleep(0)
    window.setFixedSize(window.size())
    screen = app.primaryScreen().availableGeometry()
    window.move((screen.width() - window.width()) // 2, screen.top())

    window.setAccessibleName(
        "Contato GUI. Instrumento MIDI gestual via Bluetooth. "
        "Use Tab para navegar pelos controles. "
        "As notas musicais ficam no início da navegação, seguidas das configurações. "
        "Aguardando conexão com o dispositivo Contato."
    )
    QAccessible.updateAccessibility(QAccessibleEvent(window, QAccessible.Event.Alert))

    await app_close_event.wait()
