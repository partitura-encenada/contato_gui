import rtmidi


class MidiManager:
    def __init__(self, port_index: int = 0):
        self._out   = rtmidi.MidiOut()
        self._ports: list[str] = self._out.get_ports()

        if self._ports:
            idx = max(0, min(port_index, len(self._ports) - 1))
            self._out.open_port(idx)
            print(f"MIDI → [{idx}] {self._ports[idx]}")
        else:
            print("MIDI: nenhuma porta de saída disponível.")

    @property
    def ports(self) -> list[str]:
        return list(self._ports)

    def open_port(self, idx: int) -> None:
        self._out.close_port()
        if 0 <= idx < len(self._ports):
            self._out.open_port(idx)
            print(f"MIDI → [{idx}] {self._ports[idx]}")

    def send(self, msg: list) -> None:
        try:
            self._out.send_message(msg)
        except Exception as e:
            print("MIDI send error:", e)

    def program_change(self, channel: int, program: int) -> None:
        status = 0xC0 | (channel & 0x0F)
        self.send([status, program & 0x7F])
        print(f"Program Change → ch={channel + 1}, prog={program}")
