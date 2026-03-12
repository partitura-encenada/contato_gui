import threading
import rtmidi


class MidiManager:
    def __init__(self, port_index: int = 0):
        self._out   = rtmidi.MidiOut()
        self._ports: list[str] = self._out.get_ports()
        self._out.open_port(port_index)
        print(f"MIDI -> [{port_index}] {self._ports[port_index]}")

    @property
    def ports(self) -> list[str]:
        return list(self._ports)

    def open_port(self, idx: int) -> None:
        self._out.close_port()
        self._out.open_port(idx)
        print(f"MIDI → [{idx}] {self._ports[idx]}")

    def send(self, msg: list) -> None:
        self._out.send_message(msg)

    def program_change(self, channel: int, program: int) -> None:
        status = 0xC0 | (channel & 0x0F)
        self.send([status, program & 0x7F])
        print(f"Program Change → ch={channel + 1}, prog={program}")

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
        self._out.close_port()
