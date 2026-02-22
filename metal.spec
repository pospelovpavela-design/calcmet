# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

PROJ_DIR  = os.path.abspath(".")
DATA_DIR  = os.path.join(PROJ_DIR, "Тип 1 здания с кранами")
CTK_DIR   = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ["main_desktop.py"],
    pathex=[PROJ_DIR],
    binaries=[],
    datas=[
        # Таблицы данных
        (DATA_DIR, "Тип 1 здания с кранами"),
        # Ресурсы customtkinter (темы, шрифты, иконки)
        (CTK_DIR, "customtkinter"),
    ],
    hiddenimports=[
        "customtkinter",
        "docx",
        "docx.oxml",
        "docx.oxml.ns",
        "pandas",
        "pandas.io.formats.excel",
        "openpyxl",
        "openpyxl.styles",
        "PIL",
        "PIL._tkinter_finder",
        "darkdetect",
        "packaging",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="МеталлоёмкостьЗданий",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,   # без консольного окна
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
    name="МеталлоёмкостьЗданий",
)

# macOS: создать .app bundle
app = BUNDLE(
    coll,
    name="МеталлоёмкостьЗданий.app",
    icon=None,
    bundle_identifier="ru.metalcalc.buildings",
    info_plist={
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,  # поддержка Dark Mode
    },
)
