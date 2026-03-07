from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox

from ui.theme import RAISED, BORDER, ACCENT, TEXT


class ToggleEnterComboBox(QComboBox):
    """Compact combo box where Enter/Return toggles the popup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedWidth(60)
        self.setStyleSheet(f"""
            QComboBox {{
                background: {RAISED};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 4px;
                font-size: 11px;
                padding: 1px 4px;
                min-height: 20px;
            }}
            QComboBox:hover {{ border-color: {ACCENT}; }}
            QComboBox:focus {{ border-color: {ACCENT}; background: #163d41; }}
            QComboBox QAbstractItemView {{
                background: #1e293b;
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: #2563eb;
                outline: none;
            }}
        """)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if getattr(self.view, "isVisible", lambda: False)():
                self.hidePopup()
            else:
                self.showPopup()
        else:
            super().keyPressEvent(e)
