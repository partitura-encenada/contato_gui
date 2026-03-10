import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication,
)
from PyQt6.QtGui import QPixmap

_LOGOS = os.path.join(os.path.dirname(__file__), "assets", "logos")


def _logo(filename: str, w: int = 130, h: int = 56) -> QLabel:
    ratio = QApplication.primaryScreen().devicePixelRatio()
    pix = QPixmap(os.path.join(_LOGOS, filename)).scaled(
        int(w * ratio), int(h * ratio),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    pix.setDevicePixelRatio(ratio)
    lbl = QLabel()
    lbl.setPixmap(pix)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


def _text_entry(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("color: #1a3a4a; font-size: 11px;")
    return lbl


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #3a6a8a;")
    return lbl


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    return line


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(0)

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

        layout.addWidget(_divider())
        layout.addSpacing(12)
        layout.addWidget(_section_title("Patrocínio"))
        layout.addSpacing(8)

        row_pat = QHBoxLayout()
        row_pat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_pat.addWidget(_logo("parque_tecnologico.png", 160, 60))
        layout.addLayout(row_pat)
        layout.addSpacing(14)

        layout.addWidget(_divider())
        layout.addSpacing(12)
        layout.addWidget(_section_title("Filiação Institucional"))
        layout.addSpacing(8)

        row_fil = QHBoxLayout()
        row_fil.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_fil.addWidget(_logo("ufrj.png", 130, 56))
        layout.addLayout(row_fil)
        layout.addSpacing(6)

        for name in [
            "Escola de Educação Física e Desportos",
            "Departamento de Arte Corporal",
            "NCE – Núcleo de Computação Eletrônica",
            "Centro de Letras e Artes",
        ]:
            layout.addWidget(_text_entry(name))
            layout.addSpacing(2)

        layout.addSpacing(14)

        layout.addWidget(_divider())
        layout.addSpacing(12)
        layout.addWidget(_section_title("Parceiros"))
        layout.addSpacing(8)

        row_par = QHBoxLayout()
        row_par.setSpacing(20)
        row_par.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_par.addWidget(_logo("inova_ufrj.png"))
        row_par.addWidget(_logo("coppetec.png"))
        layout.addLayout(row_par)

        layout.addStretch()
