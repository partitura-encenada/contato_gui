# Contato GUI

Aplicação desktop para controle gestual de instrumentos MIDI via Bluetooth Low Energy.

## Sobre

**Contato GUI** é uma ponte BLE → MIDI desenvolvida como pesquisa universitária pelo grupo GruPPEn (UFRJ), com apoio do Parque Tecnológico da UFRJ. Conecta o hardware Contato a qualquer sintetizador ou DAW compatível com MIDI. O dispositivo utiliza giroscópio e sensor capacitivo de toque para selecionar e acionar notas em tempo real, com baixa latência.

## Funcionalidades

- Conexão BLE automática ao dispositivo Contato
- Seletor circular interativo de notas com visualização em tempo real da posição do giroscópio
- Suporte a 1–8 seções de notas configuráveis individualmente
- Seleção de instrumento via Program Change MIDI (16 instrumentos GM)
- Configuração de sensibilidade do acelerômetro (Suave / Médio / Forte)
- Direção do mapeamento do giroscópio configurável (Esquerda / Direita)
- Seleção de porta MIDI de saída e canal (1–16)
- Salvar e carregar configurações em arquivo JSON
- Interface em PyQt6 com tema claro

## Requisitos

- Python 3.10 ou superior
- Windows 10/11 (suporte BLE via WinRT) — Linux/macOS funcionam via Bleak nativo
- Hardware Contato com firmware atualizado

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
python -m src
```

## Build (executável)

Requer [PyInstaller](https://pyinstaller.org):

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile --icon=src/assets/icon.ico --name=Contato --add-data "src/assets;assets" src/__main__.py
```

O executável é gerado em `dist/Contato.exe`. Os artefatos de build (`build/`, `dist/`, `*.spec`) são ignorados pelo git.

## Estrutura do Projeto

```
contato_gui/
├── src/
│   ├── __main__.py          # Ponto de entrada
│   ├── app.py               # Inicialização da aplicação
│   ├── main_window.py       # Janela principal
│   ├── notes_selector.py    # Widget seletor circular de notas
│   ├── combo_box.py         # ComboBox customizado
│   ├── instrument_dialog.py # Seletor de instrumento
│   ├── about_dialog.py      # Diálogo Sobre
│   ├── splash_screen.py     # Tela de carregamento
│   ├── ble_client.py        # Gerenciamento da conexão BLE
│   ├── ble_scanner.py       # Descoberta de dispositivos BLE
│   ├── midi_manager.py      # Saída MIDI
│   ├── constants.py         # UUIDs BLE, enums, constantes musicais
│   ├── config.py            # Salvar/carregar configuração
│   └── assets/
│       ├── splash.png       # Logo GruPPEn (tela inicial)
│       ├── icon.ico
│       └── logos/
│           ├── parque_tecnologico.png
│           ├── ufrj.png
│           ├── inova_ufrj.png
│           └── coppetec.png
└── references/
    └── repertorio/          # Dados de referência de peças musicais
```

## Realização e Apoio

<table>
  <tr>
    <td align="center" colspan="1"><b>Patrocínio</b></td>
    <td align="center" colspan="2"><b>Filiação Institucional</b></td>
    <td align="center" colspan="2"><b>Parceiros</b></td>
  </tr>
  <tr>
    <td align="center">
      <img src="src/assets/logos/parque_tecnologico.png" alt="Parque Tecnológico UFRJ" height="50"/><br/>
      <b>Parque Tecnológico UFRJ</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/ufrj.png" alt="UFRJ" height="50"/><br/>
      <b>Universidade Federal<br/>do Rio de Janeiro</b>
    </td>
    <td align="center">
      <b>Escola de Educação Física<br/>e Desportos<br/>Departamento de Arte Corporal<br/>NCE – Núcleo de Computação Eletrônica<br/>Centro de Letras e Artes</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/inova_ufrj.png" alt="Inova UFRJ" height="50"/><br/>
      <b>Inova UFRJ</b>
    </td>
    <td align="center">
      <img src="src/assets/logos/coppetec.png" alt="Fundação Coppetec" height="50"/><br/>
      <b>Fundação Coppetec</b>
    </td>
  </tr>
</table>
