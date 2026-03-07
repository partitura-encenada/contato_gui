import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap

from ui.theme import BG, SURFACE, BORDER, ACCENT, TEXT, MUTED


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre")
        self.setFixedSize(380, 260)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG};
                border: 1px solid {BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(8)

        title = QLabel("BLE MIDI Client")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {TEXT}; background: transparent;"
        )

        desc = QLabel("A BLE sensor → MIDI bridge.\nBuilt for low-latency experimentation.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {MUTED}; background: transparent; line-height: 1.5;")

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(desc)
        layout.addStretch()

        splash_path = os.path.join(os.path.dirname(__file__), "..", "..", "splash.png")
        pix = QPixmap(splash_path).scaled(
            72, 72,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        logo = QLabel()
        logo.setPixmap(pix)
        logo.setStyleSheet("background: transparent;")

        logos = QHBoxLayout()
        logos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logos.addWidget(logo)
        layout.addLayout(logos)
