# Tela de carregamento exibida durante a varredura BLE inicial.

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtGui import QPixmap


class SplashScreen(QSplashScreen):
    def __init__(self):
        image_path = os.path.join(os.path.dirname(__file__), "splash.png")
        pix = QPixmap(image_path).scaled(
            500, 500,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        super().__init__(pix)
