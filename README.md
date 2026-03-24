# BotonEra 🎛️

**Botonera de sonidos para Windows** — reproducí efectos de sonido al instante, con ruteo dual para que tus amigos de Discord también los escuchen.

---

## Funcionalidades

- **Grid de sonidos** con colores y emojis personalizables por botón
- **Ruteo dual de audio** — suena en tus auriculares Y en Discord al mismo tiempo (via VB-Audio Virtual Cable)
- **Barra de reproducción** — muestra el sonido actual con barra de progreso y tiempo transcurrido
- **Búsqueda en tiempo real** — filtrá tu librería por nombre
- **Carga lazy** — miles de sonidos sin lag (carga de a 50 al hacer scroll)
- **Atajos de teclado** — asigná una tecla a cualquier sonido
- **Importar sonidos** — arrastrá archivos o usá el explorador; personalizá nombre, color, emoji y atajo
- **Scraper integrado** — descargá sonidos de myinstants.com automáticamente
- **Volumen maestro** — control global de volumen en el footer
- **Ventana frameless** — diseño moderno, arrastrable, redimensionable

---

## Capturas de pantalla

> *Próximamente — podés agregar screenshots en esta sección.*

---

## Requisitos del sistema

| Requisito | Detalle |
|---|---|
| Sistema operativo | Windows 10 / 11 |
| Python | 3.10 o superior |
| VB-Audio Virtual Cable | Solo necesario para ruteo a Discord |

---

## Instalacion

### Opcion A — Descarga directa (Mediafire)

La descarga de Mediafire incluye **todos los sonidos** y la configuracion lista para usar.

1. Descarga y descomprimí el **RAR** desde Mediafire
2. Instalá las dependencias (solo la primera vez):
   ```
   pip install -r requirements.txt
   ```
3. Ejecutá la app:
   ```
   py -3 main.py
   ```
   — o doble clic en **`BotonEra.exe`** (no requiere Python)

La carpeta `sounds/` y el archivo `config.json` ya vienen incluidos con sonidos precargados.

---

### Opcion B — Desde codigo fuente (GitHub)

1. Clona el repositorio:
   ```
   git clone https://github.com/TU_USUARIO/BotonEra.git
   cd BotonEra
   ```
2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
3. Ejecutá la app:
   ```
   py -3 main.py
   ```

La app crea `config.json` y la carpeta `sounds/` automáticamente en el primer uso.

---

## Primeros pasos

### Agregar un sonido

1. Hacé clic en el botón **`+`** (header superior derecho, o al final del grid)
2. Arrastrá un archivo de audio al recuadro, o hacé clic en **Buscar archivo**
3. Elegí un nombre, color y emoji
4. (Opcional) Asigná una tecla en el campo **Atajo de teclado**
5. Hacé clic en **Agregar**

### Reproducir / detener

- **Click izquierdo** en un botón → reproduce el sonido
- **Click izquierdo** de nuevo → lo detiene
- **■ Stop All** (footer izquierdo) → detiene todo al mismo tiempo

### Editar o eliminar un sonido

- **Click derecho** sobre un botón → menú contextual con opciones de renombrar, cambiar color/emoji, asignar tecla o eliminar

---

## Configuracion de Discord (ruteo de audio)

Para que tus amigos de Discord escuchen los sonidos, necesitás un cable de audio virtual:

1. **Descargá e instalá** [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) (gratuito)
2. **En Discord:** Configuracion → Voz y Video → Dispositivo de entrada → seleccioná **"CABLE Output (VB-Audio Virtual Cable)"**
3. **En BotonEra:** En el header, en el selector **🎤 Discord Mic** → seleccioná **"CABLE Input (VB-Audio Virtual Cable)"**
4. **En BotonEra:** En el selector **🎧 Auriculares** → seleccioná tu dispositivo de audio habitual

A partir de ahora, cada sonido que reproduzcas se escuchará en tus auriculares **y** en Discord.

---

## Scraper — descargar sonidos de myinstants.com

El scraper descarga sonidos de [myinstants.com](https://www.myinstants.com) y los agrega directamente a tu librería.

```bash
# Descargar sonidos de TODAS las categorias (Memes, Viral, Anime, etc.)
py -3 scraper.py

# Buscar por termino especifico
py -3 scraper.py meme
py -3 scraper.py anime

# Limitar cantidad de sonidos
py -3 scraper.py --max 200

# Usar mas hilos para descargar mas rapido
py -3 scraper.py --workers 12

# Combinado
py -3 scraper.py meme --max 500 --workers 8
```

**Categorias disponibles sin filtro:** Tendencias, Recientes, Anime & Manga, Games, Memes, Movies, Music, Politics, Pranks, Reactions, Sound Effects, Sports, Television, TikTok Trends, Viral, WhatsApp Audios.

Despues de correr el scraper, **reiniciá la app** para ver los sonidos nuevos.

---

## Atajos de teclado

### Asignar un atajo

1. Click derecho sobre un botón → **Asignar tecla**
   — o —
   Al agregar/editar un sonido, hacer click en el campo **Atajo de teclado** y presionar la combinacion de teclas deseada

2. Guardá con **Aceptar**

### Usar atajos

Presioná la tecla asignada en cualquier momento (con la barra de busqueda sin foco) para reproducir el sonido correspondiente.

> **Nota:** Los atajos solo funcionan cuando el foco no esta en la barra de busqueda.

---

## Estructura del proyecto

```
BotonEra/
├── main.py                  # Punto de entrada — inicializa PyQt6 y abre la ventana
├── scraper.py               # Scraper para descargar sonidos de myinstants.com
├── requirements.txt         # Dependencias Python
├── assets/
│   └── logo.svg             # Logo de la app
└── src/
    ├── audio_engine.py      # Motor de audio dual (auriculares + Discord)
    ├── device_manager.py    # Enumeracion de dispositivos de audio del sistema
    ├── sound_manager.py     # Gestion de la libreria de sonidos y config.json
    ├── main_window.py       # Ventana principal, grid, lazy loading, busqueda
    ├── styles/
    │   └── theme.py         # Paleta de colores y hoja de estilos QSS global
    └── widgets/
        ├── header_bar.py       # Header: logo, selectores de dispositivo, boton +
        ├── footer_bar.py       # Footer: Stop All, volumen maestro
        ├── media_player_bar.py # Barra de reproduccion actual con progreso
        ├── sound_button.py     # Boton de sonido animado (card 140x118)
        ├── add_sound_dialog.py # Dialog para importar/editar sonidos
        └── flow_layout.py      # Layout de grilla que envuelve botones como texto
```

> **GitHub:** `sounds/` y `config.json` no se incluyen en el repositorio.
> **Mediafire:** el ZIP incluye ambas carpetas con contenido precargado.

---

## Formatos de audio soportados

| Formato | Soporte |
|---|---|
| MP3 | via miniaudio |
| WAV | via soundfile |
| OGG | via soundfile |
| FLAC | via soundfile |

---

## Dependencias

| Libreria | Version minima | Uso |
|---|---|---|
| PyQt6 | 6.6.0 | Interfaz grafica |
| sounddevice | 0.4.6 | Reproduccion de audio en multiples dispositivos |
| soundfile | 0.12.1 | Decodificacion de WAV / OGG / FLAC |
| numpy | 1.24.0 | Procesamiento de arrays de audio |
| miniaudio | 1.57 | Decodificacion de MP3 |
| requests | — | HTTP para el scraper |
| beautifulsoup4 | — | Parsing HTML para el scraper |

---

## Build — compilar el ejecutable

Para generar `BotonEra.exe` desde el codigo fuente:

### 1. Instalar PyInstaller y Pillow

```bash
pip install pyinstaller pillow
```

### 2. Generar el icono

```bash
py -3 make_icon.py
```

Esto crea `assets/icon.ico` con tamaños 16×16 hasta 256×256.

### 3. Compilar

```bash
py -3 -m PyInstaller botonera.spec --clean --noconfirm
```

El ejecutable queda en `dist/BotonEra/BotonEra.exe`.

### 4. Preparar release para Mediafire (RAR)

```bash
py -3 make_release.py
```

Esto crea `dist/BotonEra.rar` con el ejecutable + `sounds/` + `config.json` + `LEEME.txt`.

---

## Licencia

MIT License — libre para uso personal y comercial.

---

*Hecho con Python + PyQt6*
