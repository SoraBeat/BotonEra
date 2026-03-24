# AGENTS.md — Contexto para asistentes de IA

Este archivo describe la arquitectura, patrones y convenciones del proyecto BotonEra para asistentes de IA (Claude Code, Cursor, Copilot, etc.).

---

## Proposito del proyecto

BotonEra es una botonera de sonidos de escritorio construida con Python + PyQt6. Permite reproducir efectos de sonido al instante con salida dual: auriculares locales Y un cable de audio virtual para que Discord capture el audio como microfono. Soporta busqueda en tiempo real, lazy loading, atajos de teclado, y un scraper para descargar sonidos de myinstants.com.

## Como ejecutar

```bash
pip install -r requirements.txt
py -3 main.py
```

El scraper:
```bash
py -3 scraper.py [termino] [--max N] [--workers N]
```

## Como compilar el ejecutable

```bash
# 1. Dependencias de build (ademas de requirements.txt)
pip install pyinstaller pillow

# 2. Generar icono (crea assets/icon.ico con 6 tamaños)
py -3 make_icon.py

# 3. Compilar (genera dist/BotonEra/BotonEra.exe)
py -3 -m PyInstaller botonera.spec --clean --noconfirm

# 4. Empaquetar para Mediafire (genera dist/BotonEra.rar)
py -3 make_release.py
```

Archivos relacionados al build:
- `botonera.spec` — configuracion de PyInstaller (icono, hiddenimports, datas)
- `make_icon.py` — genera `assets/icon.ico` programaticamente con Pillow
- `make_release.py` — arma `dist/BotonEra_Release/` y lo comprime con WinRAR

---

## Mapa de archivos criticos

| Archivo | Clase / Funcion principal | Responsabilidad |
|---|---|---|
| `main.py` | — | Entry point: QApplication, stylesheet global, MainWindow |
| `src/audio_engine.py` | `AudioEngine`, `PlaybackHandle` | Reproduccion de audio en hilos daemon; doble OutputStream (auriculares + virtual cable) |
| `src/sound_manager.py` | `SoundManager`, `SoundEntry` | Carga/guarda `config.json`; importa archivos a `sounds/`; decodifica audio bajo demanda |
| `src/device_manager.py` | `get_output_devices()` | Enumera dispositivos de salida via sounddevice |
| `src/main_window.py` | `MainWindow`, `SoundGrid` | Ventana principal; lazy loading (PAGE_SIZE=50); busqueda; conecta todos los widgets |
| `src/styles/theme.py` | `STYLESHEET`, constantes de color | Hoja de estilos QSS global + paleta de colores + listas de colores/emojis para botones |
| `src/widgets/header_bar.py` | `HeaderBar` | Header frameless: drag-to-move, selectores de dispositivo, boton +, controles de ventana |
| `src/widgets/footer_bar.py` | `FooterBar` | Stop All + volumen maestro |
| `src/widgets/media_player_bar.py` | `MediaPlayerBar`, `_ProgressBar` | Barra de reproduccion actual; stack de sonidos activos; actualiza cada 100ms |
| `src/widgets/sound_button.py` | `SoundButton`, `AddSoundButton` | Card de sonido 140x118px con animaciones (glow, ripple, pulse); context menu |
| `src/widgets/add_sound_dialog.py` | `AddSoundDialog` | Dialog para importar/editar sonido: file picker, drag-drop, color swatch, emoji grid, keybind |
| `src/widgets/flow_layout.py` | `FlowLayout` | Layout personalizado que envuelve widgets como texto; omite widgets ocultos |
| `scraper.py` | `main()`, `collect_from_source()` | Scraper HTML de myinstants.com; 16 fuentes; deduplicacion por URL de MP3 |

---

## Patrones clave — NO romper

### PyQt6 unicamente
Usar SIEMPRE `from PyQt6.QtCore import ...` etc. **Nunca** PyQt5. Los paths de importacion son diferentes y son incompatibles.

### Llamadas Qt solo en el hilo principal
`AudioEngine._worker` corre en un hilo daemon. Cualquier actualizacion de UI desde ahi debe hacerse via:
```python
QTimer.singleShot(0, lambda: some_qt_call())
```
`PlaybackHandle.frames_played` es la unica excepcion: es un `int` Python asignado atomicamente bajo el GIL, seguro de leer desde el hilo principal y escribir desde el hilo de audio sin lock.

### AddSoundButton siempre al final del layout
`FlowLayout` de `SoundGrid` siempre termina con el `AddSoundButton`. El patron para insertar un `SoundButton` es:
```python
last_item = layout.takeAt(layout.count() - 1)  # saca AddSoundButton
layout.addWidget(new_btn)
if last_item and last_item.widget():
    layout.addWidget(last_item.widget())        # re-agrega AddSoundButton al final
```
No alterar este patron sin considerar todas las partes que lo usan: `_load_more`, `_add_sound_button`, `_filter_sounds`.

### Lazy loading
- `PAGE_SIZE = 50` definido en `main_window.py` a nivel de modulo
- `_all_entries`: lista maestra de todos los `SoundEntry`
- `_filtered_entries`: subconjunto actualmente visible (por busqueda)
- `_loaded_count`: cuantos de `_filtered_entries` ya tienen `SoundButton` en el layout
- `_load_more()`: crea botones para el siguiente batch; tiene guard `_loading` para re-entrancia
- `_filter_sounds()`: desconecta todos los botones del layout (sin deletearlos), resetea `_loaded_count=0`, llama `_load_more()`
- Los `SoundButton` destruidos del layout se mantienen en `_sound_buttons` dict para reutilizacion

### SoundButton es 140x118px fijo
El tamano esta hardcodeado en `SoundButton.__init__` con `setFixedSize(140, 118)`. El `FlowLayout` no hace wrapping con tamanos variables. No cambiar sin revisar el layout.

### FlowLayout omite widgets ocultos
`FlowLayout._do_layout()` tiene un check `if w is not None and not w.isVisible(): continue`. Esto es intencional — la busqueda oculta botones y el layout se reajusta automaticamente.

---

## Flujo de datos — ciclo de vida de reproduccion

```
MainWindow.__init__
  └─ SoundManager._load_config()         # lee config.json
  └─ AudioEngine.__init__()              # sin streams aun
  └─ _populate_sounds()                  # crea _all_entries, llama _load_more()
       └─ _load_more()                   # crea SoundButton para primeros 50

Usuario clickea un SoundButton
  └─ SoundButton.mouseReleaseEvent()
  └─ SoundButton.clicked.emit(entry)
  └─ MainWindow._on_sound_clicked(entry)
       ├─ [si ya esta playing] handle.stop() → media_bar.clear(entry.id) → return
       └─ SoundManager.ensure_audio_loaded(entry)   # decodifica MP3/WAV a numpy array
       └─ AudioEngine.play(audio_data, samplerate, ..., on_finished=on_done)
            └─ hilo daemon: 2x OutputStream (monitor + mic) → escribe chunks
            └─ handle.frames_played = i  (cada chunk)
       └─ SoundButton.set_playing(True)
       └─ MediaPlayerBar.set_playing(entry, handle)
            └─ QTimer 100ms → _tick() → lee handle.progress / elapsed_sec

Sonido termina naturalmente (on_done callback desde hilo de audio)
  └─ QTimer.singleShot(0, lambda: btn.set_playing(False))
  └─ QTimer.singleShot(0, lambda: media_bar.clear(entry.id))
```

---

## Schema de config.json

```json
{
  "mic_device_id": null,        // int | null — ID del dispositivo de Discord mic
  "monitor_device_id": null,    // int | null — ID del dispositivo de auriculares
  "volume": 1.0,                // float 0.0–1.0 — volumen maestro
  "sounds": [
    {
      "id": "f989b54c2d5d",     // string — hex 12 chars, UUID parcial
      "name": "Nombre",         // string — nombre del sonido
      "path": "C:\\...\\sounds\\archivo.mp3",  // string — path absoluto al archivo
      "color": "#6C63FF",       // string — hex color del boton
      "emoji": "🔊",            // string — emoji del boton
      "keybind": ""             // string — atajo de teclado (ej. "Ctrl+K") o vacio
    }
  ]
}
```

`config.json` se genera en runtime. **No commitear al repositorio.**

---

## Scraper — arquitectura

- Fuentes: 16 URLs de myinstants.com (ver `ALL_SOURCES` en `scraper.py`)
- Tecnica: parsea HTML con BeautifulSoup, extrae URL MP3 del atributo `onclick` de botones de play via regex `play\('(/[^']+\.mp3)'`
- Deduplicacion: `seen_urls: set[str]` de paths de MP3 (no URLs completas) — evita duplicados entre fuentes
- Descarga: `ThreadPoolExecutor` con N workers, chunks de 64KB
- Persistencia: agrega nuevas entradas a `config.json["sounds"]`; no sobreescribe entradas existentes

---

## Lo que NO hacer

- **No usar PyQt5** — el proyecto usa PyQt6; los imports son diferentes
- **No llamar metodos Qt directamente desde hilos de audio** — usar `QTimer.singleShot(0, ...)`
- **No commitear `sounds/` ni `config.json`** — estan en `.gitignore`; contienen datos personales del usuario
- **No instalar ffmpeg** — `miniaudio` decodifica MP3 sin ffmpeg; es la dependencia correcta
- **No eliminar `AddSoundButton` del layout** — siempre debe ser el ultimo widget en `FlowLayout`
- **No crear `QWidget` fuera del hilo principal** — PyQt6 no es thread-safe para creacion de widgets
- **No cambiar el tamano de `SoundButton`** sin revisar `FlowLayout` y los calculos de layout
- **No omitir el guard `_loading`** en `_load_more()` — puede causar re-entrancia al invalidar el layout

---

## Paleta de colores (src/styles/theme.py)

```python
BG           = "#0A0A0F"    # fondo de ventana
BG_PANEL     = "#12121A"    # paneles (header, footer, search)
BG_CARD      = "#1A1A26"    # cards de botones
BORDER       = "#2A2A3E"    # bordes normales
ACCENT_PURPLE = "#6C63FF"   # acento principal
ACCENT_CYAN   = "#00D9FF"   # acento secundario
ACCENT_GREEN  = "#00FF88"   # indicador de reproduccion activa
TEXT_PRIMARY  = "#E8E8F0"   # texto principal
TEXT_SECONDARY = "#6B6B8A"  # texto secundario/dimmed
```
