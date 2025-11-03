import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QDialog, QVBoxLayout, QGridLayout,
    QLabel, QScrollArea, QHBoxLayout
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize

# --- Example instrument data ---
INSTRUMENTS = [
    ("Piano", "🎹"),
    ("Guitar", "🎸"),
    ("Violin", "🎻"),
    ("Drums", "🥁"),
    ("Flute", "🎶"),
    ("Trumpet", "🎺"),
    ("Saxophone", "🎷"),
    ("Cello", "🎻"),
    ("Harp", "🪕"),
    ("Synth", "🎛️"),
]


class InstrumentSelectorDialog(QDialog):
    """Dialog window showing a grid of instrument icons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Instrument")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Scrollable area (for many instruments)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(12)

        # Add instrument buttons
        for i, (name, emoji) in enumerate(INSTRUMENTS):
            btn = QPushButton(f"{emoji} {name}")
            btn.setIconSize(QSize(48, 48))
            btn.setFixedHeight(48)
            btn.clicked.connect(lambda _, n=name, e=emoji: self.select_instrument(n, e))
            grid.addWidget(btn, i // 2, i % 2)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.selected_instrument = None

    def select_instrument(self, name, emoji):
        self.selected_instrument = (name, emoji)
        self.accept()


class InstrumentButton(QWidget):
    """Main widget: a button showing the current instrument icon, opens selection dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_name, self.current_icon = "Piano", "🎹"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QPushButton(self.current_icon)
        self.button.setFixedSize(80, 80)
        self.button.setStyleSheet("""
            QPushButton {
                font-size: 32px;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        self.button.clicked.connect(self.open_selector)
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignCenter)

    def open_selector(self):
        dialog = InstrumentSelectorDialog(self)
        if dialog.exec():
            name, emoji = dialog.selected_instrument
            if name:
                self.current_name = name
                self.current_icon = emoji
                self.button.setText(emoji)


class DemoWindow(QWidget):
    """Demo application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instrument Selector Example")
        layout = QVBoxLayout(self)

        self.selector = InstrumentButton()
        layout.addWidget(self.selector, alignment=Qt.AlignmentFlag.AlignCenter)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DemoWindow()
    w.resize(300, 300)
    w.show()
    sys.exit(app.exec())
    