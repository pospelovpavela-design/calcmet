#!/usr/bin/env python3
"""
MetalCalc Suite — единый лаунчер.
Открывает нужный калькулятор в отдельном окне (CTkToplevel).
Существующие файлы не изменены: методы App-классов переиспользуются напрямую.
"""

import customtkinter as ctk

# При импорте модулей выполняется их код верхнего уровня
# (set_appearance_mode, таблицы данных, константы) — это ожидаемо.
from main_desktop import App as _MetalApp
from estakada_pipe import App as _PipeApp
from estakada_elec import App as _ElecApp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_HERO  = ("Segoe UI", 22, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_LABEL = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)


# ─────────────────────────────────────────────────────────────────────
#  Панели-калькуляторы (CTkToplevel, методы переиспользованы из App)
#
#  Трюк: функции Python хранят ссылку на свои globals (модуль-источник).
#  Поэтому _build_ui, _on_calculate и т.д., скопированные как атрибуты
#  класса, продолжают видеть свои таблицы данных и вспомогательные функции.
# ─────────────────────────────────────────────────────────────────────

class MetalPanel(ctk.CTkToplevel):
    """Производственные здания с мостовыми кранами."""
    _build_ui     = _MetalApp._build_ui
    _read_params  = _MetalApp._read_params
    _on_calculate = _MetalApp._on_calculate
    _on_clear     = _MetalApp._on_clear
    _set_result   = _MetalApp._set_result
    _show_results = _MetalApp._show_results

    def __init__(self, master):
        super().__init__(master)
        self.title("Металлоёмкость производственных зданий — v1.0")
        self.geometry("1400x900")
        self.resizable(True, True)
        self._build_ui()


class PipePanel(ctk.CTkToplevel):
    """Трубопроводные эстакады — v3.2F."""
    _build_ui         = _PipeApp._build_ui
    _on_select        = _PipeApp._on_select
    _show_description = _PipeApp._show_description
    _on_calculate     = _PipeApp._on_calculate
    _set_text         = _PipeApp._set_text

    def __init__(self, master):
        super().__init__(master)
        self.title("Металлоёмкость трубопроводных эстакад — v3.2F")
        self.geometry("1200x720")
        self.resizable(True, True)
        self._selected_idx = 0
        self._build_ui()


class ElecPanel(ctk.CTkToplevel):
    """Электрокабельные эстакады и галереи — v4.2F."""
    _build_ui         = _ElecApp._build_ui
    _on_select        = _ElecApp._on_select
    _show_description = _ElecApp._show_description
    _on_calculate     = _ElecApp._on_calculate
    _set_text         = _ElecApp._set_text

    def __init__(self, master):
        super().__init__(master)
        self.title("Металлоёмкость электрокабельных эстакад — v4.2F")
        self.geometry("1150x680")
        self.resizable(True, True)
        self._selected_idx = 0
        self._build_ui()


# ─────────────────────────────────────────────────────────────────────
#  Главный экран лаунчера
# ─────────────────────────────────────────────────────────────────────

class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MetalCalc Suite")
        self.geometry("520x440")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="MetalCalc Suite",
            font=FONT_HERO,
            text_color="#4fc3f7",
        ).grid(row=0, column=0, pady=(44, 4))

        ctk.CTkLabel(
            self,
            text="Выберите калькулятор",
            font=FONT_LABEL,
            text_color="#90caf9",
        ).grid(row=1, column=0, pady=(0, 30))

        btn_kw = dict(width=400, height=66, font=FONT_TITLE,
                      corner_radius=10, anchor="w")

        ctk.CTkButton(
            self,
            text="  Производственные здания",
            fg_color="#1565c0", hover_color="#0d47a1",
            command=self._open_metal,
            **btn_kw,
        ).grid(row=2, column=0, pady=7)

        ctk.CTkButton(
            self,
            text="  Трубопроводные эстакады  (v3.2F)",
            fg_color="#1b5e20", hover_color="#145214",
            command=self._open_pipe,
            **btn_kw,
        ).grid(row=3, column=0, pady=7)

        ctk.CTkButton(
            self,
            text="  Электрокабельные эстакады  (v4.2F)",
            fg_color="#4a148c", hover_color="#38006b",
            command=self._open_elec,
            **btn_kw,
        ).grid(row=4, column=0, pady=7)

        ctk.CTkLabel(
            self,
            text="MetalCalc Suite  v1.0",
            font=FONT_SMALL,
            text_color="#546e7a",
        ).grid(row=5, column=0, pady=(28, 0))

    def _open_metal(self):
        w = MetalPanel(self)
        w.focus()

    def _open_pipe(self):
        w = PipePanel(self)
        w.focus()

    def _open_elec(self):
        w = ElecPanel(self)
        w.focus()


# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
