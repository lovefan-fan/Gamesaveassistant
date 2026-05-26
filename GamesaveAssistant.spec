# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


icon_path = Path('assets') / 'icon.ico'
exe_options = {}
if icon_path.exists():
    exe_options['icon'] = [str(icon_path)]


a = Analysis(
    ['code\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('code/data', 'data')],
    hiddenimports=['requests', 'psutil', 'python-dotenv', 'uuid', 'hashlib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GamesaveAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    **exe_options,
)
