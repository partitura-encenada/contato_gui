"""Diálogo 'Sobre' com informações do projeto e créditos dos patrocinadores.

Logos dos patrocinadores são carregados de src/assets/logos/.
Se um arquivo de logo não for encontrado, o nome da instituição é exibido como texto.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
)
from PyQt6.QtGui import QPixmap

from ui.theme import BG, SURFACE, BORDER, ACCENT, TEXT, MUTED

# Diretório onde os logos dos patrocinadores devem ser colocados
_LOGOS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logos")

# Patrocinadores: (nome_do_arquivo_logo, nome_completo_da_instituição)
_SPONSORS = [
    ("parque_tec.png",  "UFRJ Parque Tecnológico"),
    ("nce_ufrj.png",    "NCE / Instituto Tércio Pacitti (UFRJ)"),
    ("inova_ufrj.png",  "Inova UFRJ"),
]


def _sponsor_widget(logo_file: str, name: str) -> QLabel | QFrame:
    """Retorna um widget com o logo do patrocinador ou texto como fallback."""
    logo_path = os.path.join(_LOGOS_DIR, logo_file)
    pix = QPixmap(logo_path)

    if not pix.isNull():
        # Exibe o logo redimensionado mantendo proporção
        lbl = QLabel()
        lbl.setPixmap(pix.scaled(
            130, 56,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("background: transparent;")
        lbl.setToolTip(name)
        return lbl
    else:
        # Fallback: nome da instituição em texto
        lbl = QLabel(name)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: {MUTED}; font-size: 10px; background: transparent; font-weight: bold;"
        )
        return lbl


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre")
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG};
                border: 1px solid {BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(0)

        # ── Título e descrição ────────────────────────────────────────────────
        title = QLabel("Sobre")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {TEXT}; background: transparent;"
        )

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
        desc.setStyleSheet(f"color: {MUTED}; background: transparent; font-size: 11px;")

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(desc)
        layout.addSpacing(10)

        # ── Logo do aplicativo ────────────────────────────────────────────────
        splash_path = os.path.join(os.path.dirname(__file__), "..", "..", "splash.png")
        pix = QPixmap(splash_path).scaled(
            60, 60,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        app_logo = QLabel()
        app_logo.setPixmap(pix)
        app_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_logo.setStyleSheet("background: transparent;")
        layout.addWidget(app_logo)
        layout.addSpacing(14)

        # ── Divisor ───────────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {BORDER}; background: {BORDER}; max-height: 1px;")
        layout.addWidget(line)
        layout.addSpacing(12)

        # ── Seção de patrocinadores ───────────────────────────────────────────
        support_lbl = QLabel("Realização e Apoio")
        support_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        support_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {ACCENT}; background: transparent;"
        )
        layout.addWidget(support_lbl)
        layout.addSpacing(10)

        # Logos lado a lado; fallback para texto se os arquivos não existirem
        sponsors_row = QHBoxLayout()
        sponsors_row.setSpacing(16)
        sponsors_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for logo_file, name in _SPONSORS:
            sponsors_row.addWidget(_sponsor_widget(logo_file, name))

        layout.addLayout(sponsors_row)
        layout.addStretch()
