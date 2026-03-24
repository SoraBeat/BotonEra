"""Prepara el paquete RAR para distribuir en Mediafire.
Incluye: ejecutable compilado (dist/BotonEra/) + sounds/ + config.json + LEEME.txt
Uso: py -3 make_release.py
Requiere: WinRAR instalado en la ruta por defecto, y haber corrido PyInstaller antes.
"""
from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).parent
DIST_EXE   = ROOT / "dist" / "BotonEra"
STAGING    = ROOT / "dist" / "BotonEra_Release"
OUTPUT_RAR = ROOT / "dist" / "BotonEra.rar"
WINRAR     = Path(r"C:\Program Files\WinRAR\WinRAR.exe")

LEEME_TEXT = """\
  BotonEra - Botonera de sonidos
  ================================

  COMO USAR
  ---------
  Opcion 1 (mas facil): doble clic en BotonEra.exe
  Opcion 2 (desde Python):
      pip install -r requirements.txt
      py -3 main.py

  DISCORD (ruteo de audio)
  ------------------------
  Para que tus amigos en Discord escuchen los sonidos:
  1. Instala VB-Audio Virtual Cable (gratis): https://vb-audio.com/Cable/
  2. En Discord: Configuracion > Voz > Microfono = "CABLE Output"
  3. En BotonEra header: selector Mic = "CABLE Input"

  SCRAPER (descargar mas sonidos)
  --------------------------------
  py -3 scraper.py                   # todas las categorias
  py -3 scraper.py meme              # busqueda especifica
  py -3 scraper.py --max 500         # limitar cantidad
  Reinicia la app despues del scraper para ver los sonidos nuevos.

  GitHub: https://github.com/TU_USUARIO/BotonEra
"""


def main() -> None:
    if not DIST_EXE.exists():
        print("ERROR: dist/BotonEra/ no existe. Correr primero:")
        print("  py -3 -m PyInstaller botonera.spec --clean --noconfirm")
        sys.exit(1)

    # ── Stage ───────────────────────────────────────────────────────────────
    print("Preparando carpeta de release...")
    if STAGING.exists():
        shutil.rmtree(STAGING)
    shutil.copytree(DIST_EXE, STAGING)

    sounds_src = ROOT / "sounds"
    if sounds_src.exists():
        shutil.copytree(sounds_src, STAGING / "sounds")
        count = sum(1 for _ in (STAGING / "sounds").iterdir())
        print(f"  Copiados {count} sonidos")
    else:
        print("  AVISO: carpeta sounds/ no encontrada, se omite")

    cfg_src = ROOT / "config.json"
    if cfg_src.exists():
        shutil.copy2(cfg_src, STAGING / "config.json")
        print("  Copiado config.json")

    (STAGING / "LEEME.txt").write_text(LEEME_TEXT, encoding="utf-8")
    print("  Creado LEEME.txt")

    total = sum(f.stat().st_size for f in STAGING.rglob("*") if f.is_file())
    print(f"  Total a comprimir: {total/1024/1024:.1f} MB")

    # ── Compress ────────────────────────────────────────────────────────────
    if not WINRAR.exists():
        print(f"ERROR: WinRAR no encontrado en {WINRAR}")
        print("Instala WinRAR o comprime manualmente la carpeta dist/BotonEra_Release/")
        sys.exit(1)

    if OUTPUT_RAR.exists():
        OUTPUT_RAR.unlink()

    print(f"\nComprimiendo con WinRAR (compresion maxima)...")
    result = subprocess.run(
        [
            str(WINRAR), "a",
            "-r",          # recursivo
            "-m5",         # compresion maxima
            "-s",          # solid archive
            "-ma5",        # formato RAR5
            "-ep1",        # excluir prefijo de ruta base
            str(OUTPUT_RAR),
            str(STAGING) + "\\*",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode not in (0, 1):  # WinRAR returns 1 for warnings, 0 for success
        print("ERROR al comprimir:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

    rar_size = OUTPUT_RAR.stat().st_size / 1024 / 1024
    print(f"\nListo! -> dist/BotonEra.rar  ({rar_size:.1f} MB)")
    print("Subilo a Mediafire y compartilo.")


if __name__ == "__main__":
    main()
