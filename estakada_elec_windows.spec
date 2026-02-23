# -*- mode: python ; coding: utf-8 -*-
# Сборка одного .exe файла для Windows (без внешних зависимостей)

import os, sys

import customtkinter
CTK_DIR = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ["estakada_elec.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (CTK_DIR, "customtkinter"),
    ],
    hiddenimports=[
        "customtkinter",
        "darkdetect",
        "packaging",
        "PIL",
        "PIL._tkinter_finder",
        "tkinter",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pandas", "docx", "openpyxl", "lxml", "numpy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="EstakadaElec",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
