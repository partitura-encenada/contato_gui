from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox


class ToggleEnterComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedWidth(60)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.view().isVisible():
                self.hidePopup()
            else:
                self.showPopup()
        else:
            super().keyPressEvent(e)
