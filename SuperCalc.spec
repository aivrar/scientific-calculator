# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('tkinterdnd2')
datas += collect_data_files('matplotlib')


a = Analysis(
    ['super_calc.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['matplotlib.backends.backend_tkagg', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'IPython', 'jupyter', 'notebook', 'tornado', 'zmq', 'pytest', 'pandas', 'sklearn', 'tensorflow', 'torch', 'wx'],
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
    name='SuperCalc',
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
)
