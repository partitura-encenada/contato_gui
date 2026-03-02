"""Diálogo de seleção de instrumento MIDI.

Exibe uma grade de botões com emoji e nome de cada instrumento GM disponível.
O instrumento atualmente ativo é destacado visualmente.
"""
import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog, QGridLayout, QPushButton
from PyQt6.QtGui import QIcon

from ui.theme import BG, SURFACE, RAISED, BORDER, ACCENT, ACCENT2, TEXT


class InstrumentSelectorDialog(QDialog):
    instrumentSelected = pyqtSignal(int)  # emitido com o índice do instrumento escolhido

    def __init__(self, instruments: list[tuple[str, str]], current_index: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Instrumento")
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

        # Grade de 4 colunas com um botão por instrumento
        grid = QGridLayout(self)
        grid.setSpacing(10)
        grid.setContentsMargins(20, 20, 20, 20)

        for i, (icon, name) in enumerate(instruments):
            btn = QPushButton(f"{icon}\n{name}")
            btn.setFixedSize(110, 68)
            if i == current_index:
                # Destaque visual para o instrumento selecionado atualmente
                btn.setStyleSheet(
                    f"QPushButton {{ background: {ACCENT2}; border: 2px solid {ACCENT};"
                    f"border-radius: 8px; font-size: 12px; font-weight: bold; color: #fff; }}"
                    f"QPushButton:hover {{ background: {ACCENT}; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {RAISED}; border: 1px solid {BORDER};"
                    f"border-radius: 8px; font-size: 12px; color: {TEXT}; }}"
                    f"QPushButton:hover {{ background: {ACCENT2}; border-color: {ACCENT}; }}"
                )
            btn.clicked.connect(lambda _, idx=i: self._select(idx))
            grid.addWidget(btn, i // 4, i % 4)

    def _select(self, idx: int) -> None:
        """Emite o índice selecionado e fecha o diálogo."""
        self.instrumentSelected.emit(idx)
        self.accept()
