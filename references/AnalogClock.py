import sys
import PyQt6
import PyQt6.QtCore
import PyQt6.QtGui
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer, QRectF, QTime
from PyQt6.QtGui import QPainterPath, QRegion, QColor, QPen, QPainter


class AnalogClockWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_timer()

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def _setup_window(self):
        self.setWindowTitle("Analog Clock")
        self.setGeometry(100, 100, 300, 300)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._set_window_circular_mask()

    def _set_window_circular_mask(self):
        path = QPainterPath()
        path.addEllipse(QRectF(self.rect()))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def paintEvent(self, event):
        hours_angle, minutes_angle, seconds_angle = self._get_current_angles()
        
        painter = self._get_painter()
        
        center, radius = self._get_clock_center_and_radius()

        # Fill background with translucent color
        self._draw_background(painter)

        # Draw the second hand
        self._draw_hand(painter, seconds_angle, "red", 3, radius - 30, center)

        # Draw the minute hand
        self._draw_hand(painter, minutes_angle, "blue", 5, radius - 30, center)

        # Draw the hour hand
        self._draw_hand(painter, hours_angle, "green", 7, radius - 40, center)

        # Draw the labels from 1 to 12
        self._draw_labels(painter, center, radius + 10)

    def _get_painter(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        return painter

    def _get_clock_center_and_radius(self):
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 10
        return center,radius

    def _draw_labels(self, painter, center, radius):
        """Draws the clock labels from 1 to 12, centered at their positions."""
        painter.save()
        pen = QPen(QColor("white"), 2)
        painter.setPen(pen)
        font_metrics = painter.fontMetrics()
        for i_label in range(1, 13):
            angle = (i_label * 30) % 360
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.translate(0, -radius + 25)
            painter.rotate(-angle)
            text = str(i_label)
            text_width = font_metrics.horizontalAdvance(text)
            text_height = font_metrics.height()
            painter.drawText(-text_width // 2, text_height // 2, text)
            painter.restore()
        painter.restore()

    def _get_current_angles(self):
        current_time = QTime.currentTime()
        seconds = current_time.second() % 60
        minutes = current_time.minute() % 60
        hours = current_time.hour() % 12

        seconds_angle = seconds * 6  # 360/60 = 6 degrees per second
        minutes_angle = (minutes + seconds / 60) * 6  # 360/60 = 6 degrees per minute
        hours_angle = (
            (hours + minutes / 60 + seconds / 3600) * 30
        ) % 360  # 360/12 = 30 degrees per hour
        return hours_angle, minutes_angle, seconds_angle

    def _draw_background(self, painter):
        bg_color = QColor(30, 30, 30, 128)  # RGBA, alpha=128 for 50% translucency
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())
        border_color = QColor(255, 255, 255, 64)  # Semi-transparent border
        pen = QPen(border_color, 4)
        painter.setPen(pen)
        painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))

    def _draw_hand(self, painter, angle, color, width, length, center):
        painter.save()
        painter.translate(center)
        painter.rotate(angle)
        pen = QPen(QColor(color), width)
        painter.setPen(pen)
        painter.drawLine(0, 0, 0, -length)
        painter.restore()

    def mouseDoubleClickEvent(self, event):
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnalogClockWindow()
    window.show()
    sys.exit(app.exec())