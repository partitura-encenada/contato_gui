import os
import sys


def _asset(*parts):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", *parts)

from PyQt6.QtGui import QColor

PRIMARY_COLOR = QColor(100, 180, 255)
PORT_INDEX    = 0

# Instrumentos contínuos do GM selecionados para uso com o Contato.
# Cada entrada: (nome, número_de_programa_GM_0_indexado)
INSTRUMENTS: list[tuple[str, int]] = [
    ("Flauta",       73),  ("Oboé",         68),
    ("Clarinete",    71),  ("Trompa",        60),
    ("Trompete",     56),  ("Trombone",      57),
    ("Violino",      40),  ("Viola",         41),
    ("Violoncelo",   42),  ("Contrabaixo",   43),
    ("Cordas",       48),  ("Coro",          52),
    ("Voz",          54),  ("Órgão",         19),
    ("Pad",   89),  ("Pad Halo",      94),
]
