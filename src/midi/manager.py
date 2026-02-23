"""Gerenciador de saída MIDI via python-rtmidi.

Abstrai a abertura de portas e o envio de mensagens MIDI brutas,
incluindo Program Change para seleção de instrumento.
"""

import rtmidi


class MidiManager:
    def __init__(self, port_index: int = 0):
        """Inicializa a saída MIDI e abre a porta no índice especificado."""
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
        """Lista de nomes das portas MIDI de saída disponíveis no sistema."""
        return list(self._ports)

    def open_port(self, idx: int) -> None:
        """Fecha a porta atual e abre a porta no índice especificado."""
        self._out.close_port()
        if 0 <= idx < len(self._ports):
            self._out.open_port(idx)
            print(f"MIDI → [{idx}] {self._ports[idx]}")

    def send(self, msg: list) -> None:
        """Envia uma mensagem MIDI bruta (lista de bytes) para a porta aberta."""
        try:
            self._out.send_message(msg)
        except Exception as e:
            print("MIDI send error:", e)

    def program_change(self, channel: int, program: int) -> None:
        """Envia Program Change para selecionar instrumento GM no canal especificado."""
        status = 0xC0 | (channel & 0x0F)
        self.send([status, program & 0x7F])
        print(f"Program Change → ch={channel + 1}, prog={program}")
