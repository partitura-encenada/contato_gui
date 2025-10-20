import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from GyroDisplay import GyroDisplay
import asyncio
from qasync import QApplication, QEventLoop

class AppLayout(QVBoxLayout):
    def __init__(self, parent = None):
        super().__init__(parent)
        # Init layout
        self.gyro_display = GyroDisplay()
        self.addWidget = self.gyro_display

async def main(app):
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    AppLayout()
    await app_close_event.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    asyncio.run(main(app), loop_factory=QEventLoop)
    
