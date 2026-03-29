from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from notes_selector import SeletorCircular
from protocol import AccelLevel


class DeviceControls:
    def __init__(self, host, midi):
        self.host = host
        self.midi = midi

        self.selector = SeletorCircular(sections=6, ticks=60)
        self.selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.save_btn = QPushButton(" Salvar")
        self.load_btn = QPushButton(" Abrir")
        self.cal_btn = QPushButton(" Calibrar")
        self.about_btn = QPushButton(" Sobre")

        self.notas_spin = QSpinBox()
        self.dir_combo = QComboBox()
        self.accel_combo = QComboBox()
        self.midi_output_combo = QComboBox()
        self.channel_combo = QComboBox()
        self.tilt_check = QCheckBox()
        self.legato_check = QCheckBox()
        self.status_label = QLabel("—")

        self._setup_buttons()
        self._setup_inputs()

    def build(self):
        layout = QVBoxLayout(self.host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_topbar())
        layout.addWidget(self.selector, stretch=1)
        layout.addWidget(self._build_controls_card())
        layout.addWidget(self._build_footer())

    def _setup_buttons(self):
        style = QApplication.style()
        buttons = (
            (self.save_btn, QStyle.StandardPixmap.SP_DialogSaveButton, "Salvar configuração em arquivo"),
            (self.load_btn, QStyle.StandardPixmap.SP_DialogOpenButton, "Abrir configuração de arquivo"),
            (self.cal_btn, QStyle.StandardPixmap.SP_BrowserReload, "Calibrar giroscópio"),
            (self.about_btn, QStyle.StandardPixmap.SP_MessageBoxInformation, "Sobre o Contato GUI"),
        )

        for button, icon, name in buttons:
            button.setIcon(style.standardIcon(icon))
            button.setIconSize(QSize(16, 16))
            button.setFixedHeight(24)
            button.setAccessibleName(name)

    def _setup_inputs(self):
        self.notas_spin.setRange(1, 8)
        self.notas_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.notas_spin.setAccessibleName("Número de notas")
        self.notas_spin.setValue(6)

        self.dir_combo.addItems(["Direita", "Esquerda"])
        self.dir_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dir_combo.setAccessibleName("Direção do giroscópio")

        for level in AccelLevel:
            self.accel_combo.addItem(level.name.title(), level)
        self.accel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.accel_combo.setAccessibleName("Sensibilidade da percussão")

        self.midi_output_combo.addItems(self.midi.ports)
        self.midi_output_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.midi_output_combo.setAccessibleName("Porta de saída MIDI")

        self.channel_combo.addItems([str(i) for i in range(1, 17)])
        self.channel_combo.setFixedWidth(64)
        self.channel_combo.setAccessibleName("Canal MIDI de saída")

        self.tilt_check.setAccessibleName("Pitch bend por inclinação do antebraço")
        self.legato_check.setAccessibleName("Modo legato: a nota sustenta até tocar outra")

    def _build_topbar(self):
        frame = QFrame()
        frame.setFixedHeight(40)
        frame.setStyleSheet("QFrame { border-bottom: 1px solid #555; }")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        layout.addStretch()
        layout.addWidget(self.cal_btn)
        layout.addWidget(self.about_btn)
        return frame

    def _build_controls_card(self):
        card = QFrame()
        card.setObjectName("ControlsCard")

        outer = QVBoxLayout(card)
        outer.setContentsMargins(20, 14, 20, 16)
        outer.setSpacing(0)
        outer.addLayout(self._build_controls_grid())
        return card

    def _build_controls_grid(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)

        grid.addWidget(QLabel("Notas"), 0, 0)
        grid.addWidget(self.notas_spin, 0, 1)

        grid.addWidget(QLabel("Direção"), 1, 0)
        grid.addWidget(self.dir_combo, 1, 1)

        grid.addWidget(QLabel("Sensibilidade"), 2, 0)
        grid.addWidget(self.accel_combo, 2, 1)

        grid.addWidget(QLabel("Pitch bend"), 3, 0)
        grid.addWidget(self.tilt_check, 3, 1, Qt.AlignmentFlag.AlignRight)

        grid.addWidget(QLabel("Legato"), 4, 0)
        grid.addWidget(self.legato_check, 4, 1, Qt.AlignmentFlag.AlignRight)

        grid.addWidget(QLabel("Saída MIDI"), 5, 0)
        grid.addWidget(self._build_midi_row(), 5, 1)
        return grid

    def _build_midi_row(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.midi_output_combo, stretch=1)
        layout.addWidget(QLabel("Canal"))
        layout.addWidget(self.channel_combo)

        container = QWidget()
        container.setLayout(layout)
        return container

    def _build_footer(self):
        frame = QFrame()
        frame.setFixedHeight(22)
        frame.setStyleSheet("QFrame { background-color: #dde8ee; }")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.addWidget(self.status_label)
        layout.addStretch()
        return frame

    def set_status(self, message):
        self.status_label.setText(message)

    def set_controls_enabled(self, enabled):
        self.selector.setEnabled(enabled)
        self.notas_spin.setEnabled(enabled)
        self.dir_combo.setEnabled(enabled)
        self.accel_combo.setEnabled(enabled)
        self.tilt_check.setEnabled(enabled)
        self.legato_check.setEnabled(enabled)
        self.midi_output_combo.setEnabled(enabled)
        self.channel_combo.setEnabled(enabled)
        self.cal_btn.setEnabled(enabled)

    def rebuild_tab_order(self):
        chain = [
            self.selector.center_button,
            *self.selector.combos,
            self.notas_spin,
            self.dir_combo,
            self.accel_combo,
            self.tilt_check,
            self.legato_check,
            self.midi_output_combo,
            self.channel_combo,
        ]
        for current, nxt in zip(chain, chain[1:]):
            QWidget.setTabOrder(current, nxt)
