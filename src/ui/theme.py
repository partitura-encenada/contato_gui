"""Dark theme palette and focused QSS stylesheet.

Rules here are intentionally narrow — broad QWidget/QFrame/QLabel rules
are avoided to prevent Qt's stylesheet inheritance from clobbering things
like label transparency or native subcontrol rendering (arrows, etc.).

Background colours and text colours come from the QPalette set in app.py
via the Fusion style, so most widgets "just work" without extra rules.
"""

BG      = "#0f172a"   # window / deep background
SURFACE = "#1e293b"   # panels, cards
RAISED  = "#334155"   # inputs, elevated items
BORDER  = "#475569"   # borders
ACCENT  = "#6bbbc5"   # grayish cyan accent
ACCENT2 = "#3a7d86"   # darker grayish cyan (hover / active)
TEXT    = "#f1f5f9"   # primary text
MUTED   = "#94a3b8"   # secondary / label text

STYLESHEET = f"""
/* ── Buttons ─────────────────────────────────────────────────────────────── */
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
