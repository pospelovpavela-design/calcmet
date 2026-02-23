# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

CTK_DIR = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ["estakada_elec.py"],
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
    name="EstakadaElec",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
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
    name="EstakadaElec",
)

app = BUNDLE(
    coll,
    name="EstakadaElec.app",
    icon=None,
    bundle_identifier="ru.metalcalc.estakada.elec",
    info_plist={
        "CFBundleShortVersionString": "4.2.0",
        "CFBundleVersion": "4.2.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
    },
)
