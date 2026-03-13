from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor

from constants import _asset


def _logo(path: str, w: int, h: int) -> QLabel:
    ratio = QApplication.primaryScreen().devicePixelRatio()
    pix = QPixmap(path).scaled(
        int(w * ratio), int(h * ratio),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    pix.setDevicePixelRatio(ratio)
    lbl = QLabel()
    lbl.setPixmap(pix)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("background: transparent;")
    return lbl


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(_logo(_asset("splash.png"), 200, 140))
        layout.addWidget(_logo(_asset("logos", "parque_tecnologico.png"), 200, 140))

        layout.addStretch()

        loading = QLabel("Procurando dispositivos...")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading.setStyleSheet("background: transparent; color: #3a6a8a; font-size: 11px;")
        layout.addWidget(loading)

        self._center()

    def _center(self) -> None:
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(234, 244, 251, 235))
        p.setPen(QColor(125, 191, 232, 180))
        p.drawRoundedRect(self.rect(), 16, 16)
