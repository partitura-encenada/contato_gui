import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog, QGridLayout, QPushButton
from PyQt6.QtGui import QIcon


class InstrumentSelectorDialog(QDialog):
    instrumentSelected = pyqtSignal(int)

    def __init__(self, instruments: list[tuple[str, int]], current_index: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Instrumento")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "assets", "icon.ico")))
        self.setModal(True)

        grid = QGridLayout(self)
        grid.setSpacing(10)
        grid.setContentsMargins(20, 20, 20, 20)

        for i, (name, _) in enumerate(instruments):
            btn = QPushButton(name)
            btn.setFixedSize(110, 40)
            btn.clicked.connect(lambda _, idx=i: (self.instrumentSelected.emit(idx), self.accept()))
            grid.addWidget(btn, i // 4, i % 4)
