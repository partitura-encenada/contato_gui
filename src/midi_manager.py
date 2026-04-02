import threading

import rtmidi


class MidiManager:
    def __init__(self, port_index: int = 0):
        self.output = rtmidi.MidiOut()
        self.ports = self.output.get_ports()
        self.open_port(port_index)

    def open_port(self, index: int) -> None:
        self.output.close_port()
        self.output.open_port(index)
        print(f"MIDI -> [{index}] {self.ports[index]}")

    def send(self, message: list[int]) -> None:
        self.output.send_message(message)

    def program_change(self, channel: int, program: int) -> None:
        self.send([0xC0 | (channel & 0x0F), program & 0x7F])

    def all_notes_off(self, channel: int) -> None:
        self.send([0xB0 | (channel & 0x0F), 123, 0])

    def preview_note(self, channel: int, note: int, duration_ms: int = 350) -> None:
        self.send([0x90 | (channel & 0x0F), note & 0x7F, 80])
        threading.Timer(
            duration_ms / 1000.0,
            self.send,
            args=([0x80 | (channel & 0x0F), note & 0x7F, 0],),
        ).start()

    def close(self) -> None:
        self.output.close_port()
