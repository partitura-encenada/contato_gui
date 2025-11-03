import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QDial
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QFont


class NonlinearDial(QDial):
    """A dial that maps 0–100 integer range to a nonlinear (logarithmic) 0.5–10 float range,
    displaying the current value inside the dial."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(50)
        self._min = 0.5
        self._max = 10.0
        self.setNotchesVisible(True)
        self.setWrapping(False)
        self.setMinimumSize(120, 120)

    def nonlinear_value(self):
        """Map linear position to nonlinear scale (logarithmic)."""
        linear_pos = self.value() / 100.0
        return self._min * ((self._max / self._min) ** linear_pos)

    def set_nonlinear_value(self, v: float):
        """Set dial based on a nonlinear value."""
        v = max(self._min, min(v, self._max))
        linear_pos = math.log(v / self._min) / math.log(self._max / self._min)
        self.setValue(int(linear_pos * 100))

    def paintEvent(self, event):
        """Draw the base dial and overlay the current value text."""
        super().paintEvent(event)

        # Draw numeric value in the center
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        val = self.nonlinear_value()
        text = f"{val:.2f}"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)


class DialDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nonlinear Dial with Display")

        layout = QVBoxLayout(self)

        self.dial = NonlinearDial()
        layout.addWidget(self.dial, alignment=Qt.AlignmentFlag.AlignCenter)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DialDemo()
    w.resize(240, 300)
    w.show()
    sys.exit(app.exec())