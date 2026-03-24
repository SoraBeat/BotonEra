# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for BotonEra – single-folder build."""

import sys
from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Logo SVG + Icon
        (str(project_root / 'assets' / 'logo.svg'), 'assets'),
        (str(project_root / 'assets' / 'icon.ico'), 'assets'),
    ],
    hiddenimports=[
        # PyQt6 modules that PyInstaller may miss
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.sip',
        # Audio
        'sounddevice',
        'soundfile',
        'miniaudio',
        'numpy',
        # Our packages
        'src',
        'src.audio_engine',
        'src.device_manager',
        'src.sound_manager',
        'src.main_window',
        'src.styles',
        'src.styles.theme',
        'src.widgets',
        'src.widgets.add_sound_dialog',
        'src.widgets.flow_layout',
        'src.widgets.footer_bar',
        'src.widgets.header_bar',
        'src.widgets.media_player_bar',
        'src.widgets.sound_button',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'PIL',
        'cv2',
        'pandas',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BotonEra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no consola negra al abrir
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BotonEra',
)
