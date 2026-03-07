import sys
import os
import asyncio

# Ensure src/ is on the path so sibling packages resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from qasync import QApplication as QAsyncApplication, QEventLoop
from ui.app import main_async

if __name__ == "__main__":
    qapp = QAsyncApplication(sys.argv)
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main_async(qapp))
