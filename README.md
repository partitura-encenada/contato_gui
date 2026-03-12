# Contato GUI
[![en](https://img.shields.io/badge/lang-en-red.svg)](README.en.md)

Aplicação desktop para controle gestual de instrumentos MIDI via Bluetooth Low Energy.

## Sobre

**Contato GUI** é uma interface gráfica desenvolvida para pesquisa universitária pelo Grupo de Pesquisa Partitura Encenada (GruPPEn), com apoio do Parque Tecnológico da UFRJ. Conecta o hardware Contato a qualquer sintetizador ou DAW compatível com MIDI. O dispositivo utiliza giroscópio e sensor capacitivo de toque para selecionar e acionar notas em tempo real.

## Funcionalidades

- Conexão BLE automática ao dispositivo Contato
- **Múltiplos dispositivos simultâneos**, cada um em sua própria aba
- Seletor circular interativo de notas com visualização em tempo real da posição do giroscópio
- Suporte a 1–8 seções de notas configuráveis individualmente
- Seleção de instrumento via Program Change MIDI (16 instrumentos GM)
- Configuração de sensibilidade do acelerômetro (Suave / Médio / Forte)
- Direção do mapeamento do giroscópio configurável (Esquerda / Direita)
- Pitch bend pela inclinação do antebraço, com zona morta de ±10°
- Modo Legato: a nota segura sozinha até você tocar outra ou acionar a percussão
- Seleção de porta MIDI de saída e canal (1–16)
- Salvar e carregar configurações em arquivo JSON

## Acessibilidade

- Compatível com leitores de tela (Narrator e NVDA)
- Navegação completa por teclado via Tab e setas
- Anúncio automático da descrição do app ao iniciar
- Nomes acessíveis descritivos em todos os controles e abas
- Notas com sustenido anunciadas por extenso (ex.: "Dó Sustenido 3")
- Ordem de navegação: notas primeiro, painel de configurações depois

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

O executável é gerado em `dist/Contato.exe`.

## Estrutura do Projeto

```
contato_gui/
├── repertorio/ # Setups para testes
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
