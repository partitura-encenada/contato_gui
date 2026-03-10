import sys
import os
import asyncio

from qasync import QApplication as QAsyncApplication, QEventLoop
from app import main_async

if __name__ == "__main__":
    qapp = QAsyncApplication(sys.argv)
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(main_async(qapp))
