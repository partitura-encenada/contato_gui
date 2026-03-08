"""ComboBox compacto para seleção de nota no seletor circular.

Enter/Return alterna a visibilidade do popup em vez de confirmar a seleção,
facilitando a navegação no layout circular sem fechar acidentalmente.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox

class ToggleEnterComboBox(QComboBox):
    """ComboBox compacto onde Enter/Return alterna o popup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedWidth(60)

    def keyPressEvent(self, e):
        """Alterna popup com Enter/Return; demais teclas seguem comportamento padrão."""
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.view().isVisible():
                self.hidePopup()
            else:
                self.showPopup()
        else:
            super().keyPressEvent(e)
