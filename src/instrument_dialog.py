"""Diálogo de seleção de instrumento MIDI.

Exibe uma grade de botões com emoji e nome de cada instrumento GM disponível.
O instrumento atualmente ativo é destacado visualmente.
"""
import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog, QGridLayout, QPushButton
from PyQt6.QtGui import QIcon

class InstrumentSelectorDialog(QDialog):
    instrumentSelected = pyqtSignal(int)  # emitido com o índice do instrumento escolhido

    def __init__(self, instruments: list[tuple[str, str]], current_index: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Instrumento")
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setModal(True)

        # Grade de 4 colunas com um botão por instrumento
        grid = QGridLayout(self)
        grid.setSpacing(10)
        grid.setContentsMargins(20, 20, 20, 20)

        for i, (icon, name) in enumerate(instruments):
            btn = QPushButton(f"{icon}\n{name}")
            btn.setFixedSize(110, 68)
            btn.clicked.connect(lambda _, idx=i: self._select(idx))
            grid.addWidget(btn, i // 4, i % 4)

    def _select(self, idx: int) -> None:
        """Emite o índice selecionado e fecha o diálogo."""
        self.instrumentSelected.emit(idx)
        self.accept()
