from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QColor, QPainter


class LoadingOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setVisible(False)

        self._label = QLabel(self)
        font = self._label.font()
        font.setPointSize(14)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self._label)
        layout.addStretch()

    def show_overlay(self, message):
        self._label.setText(message)
        self.resize(self.parent().size())
        self.raise_()
        self.setVisible(True)

    def hide_overlay(self):
        self.setVisible(False)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(234, 244, 251, 210))
