import asyncio

from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout,
    QPushButton, QTabWidget, QTabBar,
)
from PyQt6.QtGui import QIcon

from ble_client import BleConnection
from device_picker_dialog import scan_devices, DevicePickerDialog
from midi_manager import MidiManager
from constants import PORT_INDEX, _asset
from device_tab import DeviceTab

_ICON = _asset("icon.ico")

class MainWindow(QWidget):
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

        # Aba "+" permanente — sempre posicionada como a última aba
        self.tabs.addTab(QWidget(), "+")

    @property
    def _plus_idx(self) -> int:
        return self.tabs.count() - 1

    def add_device(self, device) -> None:
        ble  = BleConnection()
        midi = MidiManager(PORT_INDEX)
        page = DeviceTab(ble=ble, midi=midi, device=device)
        idx  = self._plus_idx  # inserir antes do "+"
        label = device.name
        self.tabs.insertTab(idx, page, label)
        self.tabs.setCurrentIndex(idx)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(16, 16)
        close_btn.setAccessibleName(f"Fechar {label}")
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
        devices = await scan_devices()
        dlg = DevicePickerDialog(devices)
        future = asyncio.get_event_loop().create_future()
        dlg.finished.connect(future.set_result)
        dlg.open()
        if await future == QDialog.DialogCode.Accepted:
            self.add_device(dlg.selected_device)
        self._picking = False

    def _cleanup_page(self, page: DeviceTab) -> None:
        asyncio.create_task(page.ble.stop())
        for ch in range(16):
            page.midi.all_notes_off(ch)
        page.midi.close()
        page.deleteLater()

    def _close_tab(self, index: int) -> None:
        self._cleanup_page(self.tabs.widget(index))
        self.tabs.removeTab(index)
        if self.tabs.count() == 1:  # só a aba "+" permanece
            self.close()

    def closeEvent(self, event) -> None:
        while self.tabs.count() > 1:
            self._cleanup_page(self.tabs.widget(0))
            self.tabs.removeTab(0)
        self.app.quit()
        super().closeEvent(event)
