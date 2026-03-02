"""Paleta de cores e folha de estilo QSS do tema escuro.
"""

BG      = "#071125"   # fundo da janela / plano de fundo profundo
SURFACE = "#1e293b"   # painéis, cartões
RAISED  = "#334155"   # campos de entrada, itens elevados
BORDER  = "#475569"   # bordas
ACCENT  = "#6bbbc5"   # ciano acinzentado — cor de destaque principal
ACCENT2 = "#3a7d86"   # ciano mais escuro — estado de hover / ativo
TEXT    = "#f1f5f9"   # texto primário
MUTED   = "#94a3b8"   # texto secundário / rótulos

STYLESHEET = f"""
/* ── Botões ──────────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 3px 12px;
}}
QPushButton:hover   {{ background-color: {ACCENT2}; border-color: {ACCENT}; color: #fff; }}
QPushButton:pressed {{ background-color: {ACCENT};  border-color: {ACCENT}; color: #fff; }}

/* ── ComboBox ────────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {RAISED};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 3px 8px;
    min-height: 24px;
}}
QComboBox:hover {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT2};
    outline: none;
}}

/* ── SpinBox ─────────────────────────────────────────────────────────────── */
QSpinBox {{
    background-color: {RAISED};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 3px 8px;
    min-height: 24px;
}}
QSpinBox:hover {{ border-color: {ACCENT}; }}

/* ── ListWidget ──────────────────────────────────────────────────────────── */
QListWidget {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    outline: none;
}}
QListWidget::item                 {{ padding: 7px 10px; border-radius: 4px; }}
QListWidget::item:selected        {{ background-color: {ACCENT2}; color: #fff; }}
QListWidget::item:hover:!selected {{ background-color: {RAISED}; }}
"""
