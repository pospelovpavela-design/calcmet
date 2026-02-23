# -*- mode: python ; coding: utf-8 -*-
# Единое приложение MetalCalc Suite для macOS

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
    [],
    exclude_binaries=True,
    name="MetalCalcSuite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MetalCalcSuite",
)

app = BUNDLE(
    coll,
    name="MetalCalcSuite.app",
    icon=None,
    bundle_identifier="ru.metalcalc.suite",
    info_plist={
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
    },
)
