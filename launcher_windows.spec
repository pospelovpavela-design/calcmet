# -*- mode: python ; coding: utf-8 -*-
# Единый EXE MetalCalc Suite для Windows

import os
import customtkinter

CTK_DIR = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[(CTK_DIR, "customtkinter")],
    hiddenimports=[
        "customtkinter",
        "darkdetect",
        "packaging",
        "PIL",
        "PIL._tkinter_finder",
        "tkinter",
        "tkinter.messagebox",
        "main_desktop",
        "estakada_pipe",
        "estakada_elec",
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
    name="MetalCalcSuite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
