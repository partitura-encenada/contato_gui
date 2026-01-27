import sys
import asyncio

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer

from qasync import QEventLoop
import rtmidi

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# ---------------- BLE UUIDs ----------------

BLE_MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
BLE_MIDI_CHAR_UUID    = "7772e5db-3868-4112-a1a9-f2669d106bf3"

# ---------------- MIDI ---------------------

MIDI_PORT_INDEX = 1   # <-- requested: port index 1

# ------------------------------------------


class BleMidiWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BLE MIDI Bridge (minimal)")
        self.resize(300, 100)

        self.label = QLabel("Starting…")
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        # ---- MIDI OUT ----
        self.midi = rtmidi.MidiOut()
        ports = self.midi.get_ports()

        if not ports:
            raise RuntimeError("No MIDI output ports available")

        if MIDI_PORT_INDEX >= len(ports):
            raise RuntimeError(f"MIDI port {MIDI_PORT_INDEX} not available")

        self.midi.open_port(MIDI_PORT_INDEX)
        print(f"MIDI OUT → [{MIDI_PORT_INDEX}] {ports[MIDI_PORT_INDEX]}")

        self.client: BleakClient | None = None

        # start async logic once Qt loop is running
        QTimer.singleShot(0, self.start)

    # ---------- BLE CALLBACK ----------

    def ble_midi_callback(
        self,
        _: BleakGATTCharacteristic,
        data: bytearray
    ):
        raw = bytes(data)
        if len(raw) < 3:
            return

        # send last MIDI message (same behavior as original App.py)
        msg = list(raw[-3:])
        print(msg)
        self.midi.send_message(msg)

    # ---------- MAIN ASYNC ----------

    def start(self):
        asyncio.create_task(self.run())

    async def run(self):
        self.label.setText("Scanning BLE…")

        devices = await BleakScanner.discover(
            timeout=3.0,
            service_uuids=[BLE_MIDI_SERVICE_UUID]
        )

        if not devices:
            self.label.setText("No BLE MIDI device found")
            return

        device = devices[0]
        print(f"Connecting to {device.name} ({device.address})")
        self.label.setText("Connecting…")

        async with BleakClient(device) as client:
            self.client = client
            print("Connected")
            self.label.setText("Connected ✓")

            await client.start_notify(
                BLE_MIDI_CHAR_UUID,
                self.ble_midi_callback
            )

            # keep alive
            while True:
                await asyncio.sleep(1)


# ---------- ENTRY POINT ----------

def main():
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    win = BleMidiWindow()
    win.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
