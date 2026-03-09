# -*- coding: utf-8 -*-
"""
Заглушки для GUI-модулей.

main_desktop.py, estakada_pipe.py и estakada_elec.py импортируют customtkinter
и tkinter на верхнем уровне.  Чтобы протестировать чистые расчётные функции без
реального дисплея, conftest подставляет минимальные заглушки ДО любого импорта
тестируемых модулей.

Старый test_calculator.py импортирует calculator_logic (без GUI) — он не затронут:
sys.modules.setdefault() не перезаписывает уже загруженный модуль.
"""

import sys
from unittest.mock import MagicMock


# ── Базовый виджет-заглушка ───────────────────────────────────────────────────

class _Widget:
    """Минимальная заглушка: все методы tkinter/ctk игнорируются."""

    def __init__(self, *args, **kwargs):
        pass

    # geometry / layout
    def grid(self, *a, **kw): pass
    def pack(self, *a, **kw): pass
    def grid_remove(self): pass
    def grid_forget(self): pass
    def columnconfigure(self, *a, **kw): pass
    def grid_rowconfigure(self, *a, **kw): pass

    # state / text
    def configure(self, **kw): pass
    def destroy(self): pass
    def focus(self): pass
    def update(self): pass

    # entry/textbox interface
    def get(self): return ""
    def insert(self, *a): pass
    def delete(self, *a): pass

    # scrollableframe / toplevel
    def mainloop(self): pass


class _Var:
    """Заглушка для BooleanVar / StringVar."""

    def __init__(self, value=None):
        self._v = value

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


# ── Сборка мок-модуля customtkinter ──────────────────────────────────────────

_mock_ctk = MagicMock()

for _cls_name in (
    "CTkFrame", "CTkScrollableFrame",
    "CTkEntry", "CTkTextbox",
    "CTkLabel", "CTkButton",
    "CTkComboBox", "CTkCheckBox",
    "CTk", "CTkToplevel",
):
    setattr(_mock_ctk, _cls_name, _Widget)

_mock_ctk.BooleanVar = _Var
_mock_ctk.StringVar = _Var

# ── Сборка мок-модуля tkinter ─────────────────────────────────────────────────

_mock_tk = MagicMock()
_mock_tk.Widget = _Widget

# ── Регистрация в sys.modules ─────────────────────────────────────────────────
# setdefault: не перезаписывает реальные модули, если они уже загружены.

sys.modules.setdefault("customtkinter", _mock_ctk)
sys.modules.setdefault("tkinter", _mock_tk)
sys.modules.setdefault("tkinter.messagebox", MagicMock())
sys.modules.setdefault("tkinter.filedialog", MagicMock())
