from bleak import BleakScanner
from constants import BLE_MIDI_SERVICE_UUID


async def scan_devices():
    return await BleakScanner.discover(timeout=3.0, service_uuids=[BLE_MIDI_SERVICE_UUID])
