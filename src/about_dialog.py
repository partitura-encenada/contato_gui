"""Diálogo 'Sobre' com informações do projeto e créditos dos patrocinadores."""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
)
from PyQt6.QtGui import QPixmap


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(0)

        # ── Título e descrição ────────────────────────────────────────────────
        title = QLabel("Sobre")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc = QLabel(
            "Contato GUI é uma interface de controle musical gestual que conecta o hardware Contato "
            "a instrumentos MIDI via Bluetooth Low Energy. O dispositivo utiliza um giroscópio para "
            "mapear a inclinação do performer a uma paleta de notas configurável, acionadas por um "
            "sensor capacitivo de toque. O sistema foi projetado para performances ao vivo com baixa "
            "latência, permitindo expressividade gestual em tempo real. As configurações de notas, "
            "instrumento, sensibilidade e direção são ajustáveis e podem ser salvas para reutilização."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(desc)
        layout.addSpacing(10)

        # ── Logo do aplicativo ────────────────────────────────────────────────
        splash_path = os.path.join(os.path.dirname(__file__), "assets", "splash.png")
        pix = QPixmap(splash_path).scaled(
            60, 60,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        app_logo = QLabel()
        app_logo.setPixmap(pix)
        app_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_logo)
        layout.addSpacing(14)

        # ── Divisor ───────────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        layout.addSpacing(12)

        # ── Seção de patrocinadores ───────────────────────────────────────────
        support_lbl = QLabel("Realização e Apoio")
        support_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(support_lbl)
        layout.addSpacing(10)

        logos_dir = os.path.join(os.path.dirname(__file__), "assets", "logos")
        sponsors = [
            ("parque_tec.png",  "UFRJ Parque Tecnológico"),
            ("nce_ufrj.png",    "NCE / Instituto Tércio Pacitti (UFRJ)"),
            ("inova_ufrj.png",  "Inova UFRJ"),
        ]
        sponsors_row = QHBoxLayout()
        sponsors_row.setSpacing(16)
        sponsors_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for logo_file, name in sponsors:
            lbl = QLabel()
            lbl.setPixmap(QPixmap(os.path.join(logos_dir, logo_file)).scaled(
                130, 56,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
            lbl.setToolTip(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sponsors_row.addWidget(lbl)

        layout.addLayout(sponsors_row)
        layout.addStretch()
