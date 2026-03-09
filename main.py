# -*- coding: utf-8 -*-
"""
Расчетный модуль металлоемкости производственных одноэтажных зданий с мостовыми кранами.
Десктопное приложение на customtkinter.
"""

import tkinter as tk
import customtkinter as ctk
import datetime
from tkinter import filedialog
from typing import Optional, Dict, Any, List
import traceback

from calculator_logic import CalculatorLogic, InputParams, SpanParams

# Темная тема
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─── Тексты подсказок ────────────────────────────────────────────────────────
TOOLTIPS: Dict[str, str] = {
    'length': (
        "Длина здания (продольный размер) — расстояние между торцами вдоль рядов колонн, м.\n"
        "Принимается кратным шагу колонн."
    ),
    'n_spans': (
        "Количество пролётов — число пространств между рядами колонн.\n"
        "Каждый пролёт задаётся независимо на отдельной вкладке."
    ),
    'span_L': (
        "Пролёт поперечной рамы L, м — расстояние между осями продольных рядов колонн.\n"
        "Стандартные значения: 18, 24, 30, 36 м (ГОСТ 23837)."
    ),
    'truss_B': (
        "Шаг стропильных ферм B, м — расстояние между фермами вдоль здания.\n"
        "Принимается 6 или 12 м."
    ),
    'column_step': (
        "Шаг колонн — расстояние между колоннами вдоль здания (6 или 12 м).\n"
        "При шаге 12 м требуются подстропильные фермы."
    ),
    'rail_level': (
        "Отметка головки рельса, м от ±0.000.\n"
        "Определяется по технологическому заданию на кран."
    ),
    'truss_type': (
        "Тип стропильных ферм:\n"
        "• Уголки — расчёт по Методу 1 (эмпирические формулы)\n"
        "• Двутавры / Молодечно — расчёт по Методу 2 (табличные данные завода)"
    ),
    'crane_capacity': (
        "Грузоподъёмность мостового крана Q, т.\n"
        "Определяется по технологическому заданию.\n"
        "Влияет на подкрановые балки, тормозные конструкции и колонны."
    ),
    'crane_count': (
        "Количество мостовых кранов в пролёте (1 или 2).\n"
        "При 2 кранах нагрузка на подкрановые конструкции возрастает."
    ),
    'brake_path': (
        "Тип тормозных конструкций:\n"
        "• С проходом — тормозная балка с настилом для обслуживания\n"
        "• Без прохода — решётчатая тормозная конструкция (легче)"
    ),
    'crane_mode': (
        "Режим работы крана по ГОСТ 25546:\n"
        "• 1К–6К — лёгкий и средний режим (αпб меньше)\n"
        "• 7К–8К — тяжёлый режим (αпб больше, конструкции тяжелее)"
    ),
    'snow': (
        "Нормативная снеговая нагрузка Sg, кН/м² (СП 20.13330.2017, Прил. Ж).\n"
        "По снеговым районам: I — 0.8, II — 1.2, III — 1.8, IV — 2.4 кН/м²."
    ),
    'dust': (
        "Нормативная нагрузка от технологической пыли на покрытие, кН/м².\n"
        "Принимается по технологическому заданию (обычно 0–1.0 кН/м²)."
    ),
    'roof': (
        "Нормативная нагрузка от кровельного покрытия, кН/м²\n"
        "(паро-, теплоизоляция, стяжка; вес прогонов не включается).\n"
        "Типично: 0.2–0.5 кН/м²."
    ),
    'purlin': (
        "Нормативная нагрузка от прогонов, кН/м².\n"
        "Принимается по конструктивной схеме прогонов.\n"
        "Типично: 0.15–0.3 кН/м²."
    ),
    'yc': (
        "Коэффициент надёжности по ответственности γn (ГОСТ 27751):\n"
        "• 1.0 — нормальный уровень ответственности\n"
        "• 1.1 — повышенный уровень\n"
        "• 1.2 — высший уровень"
    ),
    'fachwerk_load': (
        "Нормативная нагрузка на ригель фахверка от стеновых панелей, кг/м.п.\n"
        "Определяется по весу стеновых конструкций."
    ),
    'fachwerk_post': (
        "Промежуточная стойка фахверка при шаге колонн 12 м.\n"
        "Устанавливается с шагом 6 м между основными колоннами.\n"
        "Активна только при шаге колонн = 12 м."
    ),
    'building_type': (
        "Тип здания — для расчёта металлоёмкости внутренних опор трубопроводов:\n"
        "• Основные цеха — 11–22 кг/м²\n"
        "• Энергоносители — 23–40 кг/м²\n"
        "• Вспомогательные — 2–4 кг/м²"
    ),
}


# ─── Класс всплывающей подсказки ─────────────────────────────────────────────
class ToolTip:
    """Всплывающая подсказка при наведении курсора на виджет (задержка 450 мс)."""

    def __init__(self, widget: tk.Widget, text: str):
        self._widget = widget
        self._text = text
        self._tip: Optional[tk.Toplevel] = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._cancel, add="+")
        widget.bind("<ButtonPress>", self._cancel, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self._widget.after(450, self._show)

    def _cancel(self, _event=None):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self):
        if self._tip:
            return
        x = self._widget.winfo_rootx() + 28
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        outer = tk.Frame(tw, background="#1c2340",
                         highlightbackground="#4a6fa5", highlightthickness=1)
        outer.pack()
        tk.Label(
            outer, text=self._text, justify="left",
            background="#1c2340", foreground="#c8dcff",
            wraplength=380, padx=10, pady=8,
            font=("", 10),
        ).pack()

    def _hide(self):
        if self._tip:
            self._tip.destroy()
            self._tip = None


# ─── Главное окно ─────────────────────────────────────────────────────────────
class MetalCapacityApp(ctk.CTk):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.title("Расчет металлоемкости производственных зданий")
        self.geometry("1100x900")
        self.minsize(1000, 800)

        self.calculator = CalculatorLogic()
        self.span_widgets: List[Dict] = []
        self._last_results_text = ""

        # Контейнер с прокруткой
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self._create_inputs()
        self._create_button()
        self._create_results()

    # ── Хелпер: маленькая кнопка «?» с тултипом ──────────────────────────────
    def _qbtn(self, parent: ctk.CTkFrame, tip_key: str) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            parent, text="?", width=20, height=20,
            fg_color="transparent", hover_color="#2a3a5a",
            text_color="#5588cc", border_color="#3a5a8a", border_width=1,
            font=("", 10, "bold"), command=lambda: None,
            corner_radius=10,
        )
        btn.pack(side="left", padx=(1, 8))
        ToolTip(btn, TOOLTIPS.get(tip_key, ""))
        return btn

    def _create_inputs(self):
        """Создание полей ввода."""
        # Глобальные параметры
        ctk.CTkLabel(self.main_frame, text="Параметры здания",
                     font=("", 16, "bold")).pack(anchor="w", pady=(0, 8))
        frame_global = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_global.pack(fill="x", pady=4)

        ctk.CTkLabel(frame_global, text="Длина здания, м:").pack(side="left", padx=(0, 5))
        self.entry_length = ctk.CTkEntry(frame_global, placeholder_text="Длина, м", width=110)
        self.entry_length.insert(0, "60")
        self.entry_length.pack(side="left", padx=(0, 2))
        self._qbtn(frame_global, 'length')

        ctk.CTkLabel(frame_global, text="Кол-во пролётов:").pack(side="left", padx=(0, 5))
        self.var_n_spans = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(
            frame_global,
            values=["1", "2", "3", "4", "5", "6"],
            variable=self.var_n_spans,
            width=70,
        ).pack(side="left", padx=(0, 2))
        self._qbtn(frame_global, 'n_spans')

        # Вкладки пролётов
        ctk.CTkLabel(self.main_frame, text="Параметры пролётов",
                     font=("", 14, "bold")).pack(anchor="w", pady=(15, 5))
        self.tabview = ctk.CTkTabview(self.main_frame, height=320)
        self.tabview.pack(fill="x", pady=5)

        self._init_span_tabs()
        self.var_n_spans.trace_add("write", self._update_span_tabs)

    def _init_span_tabs(self):
        """Первоначальное создание вкладок пролётов."""
        n = int(self.var_n_spans.get())
        self.span_widgets = []
        for i in range(n):
            tab_name = f"Пролёт {i + 1}"
            self.tabview.add(tab_name)
            frame = self.tabview.tab(tab_name)
            w = self._create_span_widgets(frame, {})
            self.span_widgets.append(w)

    def _update_span_tabs(self, *args):
        """Пересоздать вкладки при смене кол-ва пролётов, сохранив введённые значения."""
        n = int(self.var_n_spans.get())
        saved = [self._extract_span_widget_values(w) for w in self.span_widgets]
        for tab_name in list(self.tabview.tabs()):
            self.tabview.delete(tab_name)
        self.span_widgets = []
        for i in range(n):
            tab_name = f"Пролёт {i + 1}"
            self.tabview.add(tab_name)
            frame = self.tabview.tab(tab_name)
            defaults = saved[i] if i < len(saved) else {}
            w = self._create_span_widgets(frame, defaults)
            self.span_widgets.append(w)
        self.tabview.set("Пролёт 1")

    def _create_span_widgets(self, parent_frame, defaults: dict) -> dict:
        """Создать виджеты параметров одного пролёта. Возвращает dict виджетов/переменных."""
        w = {}

        def get_d(key, default_val):
            return defaults.get(key, str(default_val))

        # --- Строка 1: Геометрия ---
        row1 = ctk.CTkFrame(parent_frame, fg_color="transparent")
        row1.pack(fill="x", pady=3)

        ctk.CTkLabel(row1, text="L (пролёт), м:").pack(side="left", padx=(0, 3))
        e = ctk.CTkEntry(row1, width=70)
        e.insert(0, get_d('span_L', '30'))
        e.pack(side="left", padx=(0, 2))
        w['entry_span_L'] = e
        self._qbtn(row1, 'span_L')

        ctk.CTkLabel(row1, text="Шаг ферм B, м:").pack(side="left", padx=(0, 3))
        var_truss_B = ctk.StringVar(value=get_d('truss_step_B', '6'))
        ctk.CTkOptionMenu(row1, values=["6", "12"], variable=var_truss_B, width=70).pack(side="left", padx=(0, 2))
        w['var_truss_B'] = var_truss_B
        self._qbtn(row1, 'truss_B')

        ctk.CTkLabel(row1, text="Шаг колонн:").pack(side="left", padx=(0, 3))
        var_col = ctk.StringVar(value=get_d('column_step', '6'))
        ctk.CTkOptionMenu(row1, values=["6", "12"], variable=var_col, width=70).pack(side="left", padx=(0, 2))
        w['var_column_step'] = var_col
        self._qbtn(row1, 'column_step')

        ctk.CTkLabel(row1, text="Уровень рельса, м:").pack(side="left", padx=(0, 3))
        e = ctk.CTkEntry(row1, width=70)
        e.insert(0, get_d('rail_level', '10'))
        e.pack(side="left", padx=(0, 2))
        w['entry_rail'] = e
        self._qbtn(row1, 'rail_level')

        # --- Строка 2: Кран ---
        row2 = ctk.CTkFrame(parent_frame, fg_color="transparent")
        row2.pack(fill="x", pady=3)

        ctk.CTkLabel(row2, text="Тип фермы:").pack(side="left", padx=(0, 3))
        var_tt = ctk.StringVar(value=get_d('truss_type', 'Уголки'))
        ctk.CTkOptionMenu(row2, values=["Уголки", "Двутавры", "Молодечно"], variable=var_tt, width=115).pack(side="left", padx=(0, 2))
        w['var_truss_type'] = var_tt
        self._qbtn(row2, 'truss_type')

        ctk.CTkLabel(row2, text="Г/П крана, т:").pack(side="left", padx=(0, 3))
        e = ctk.CTkEntry(row2, width=70)
        e.insert(0, get_d('crane_capacity', '20'))
        e.pack(side="left", padx=(0, 2))
        w['entry_crane'] = e
        self._qbtn(row2, 'crane_capacity')

        ctk.CTkLabel(row2, text="Кранов:").pack(side="left", padx=(0, 3))
        var_cc = ctk.StringVar(value=get_d('crane_count', '1'))
        ctk.CTkOptionMenu(row2, values=["1", "2"], variable=var_cc, width=65).pack(side="left", padx=(0, 2))
        w['var_crane_count'] = var_cc
        self._qbtn(row2, 'crane_count')

        ctk.CTkLabel(row2, text="Тормозные:").pack(side="left", padx=(0, 3))
        var_br = ctk.StringVar(value=get_d('brake_path', 'С проходом'))
        ctk.CTkOptionMenu(row2, values=["С проходом", "Без прохода"], variable=var_br, width=125).pack(side="left", padx=(0, 2))
        w['var_brake'] = var_br
        self._qbtn(row2, 'brake_path')

        ctk.CTkLabel(row2, text="Режим крана:").pack(side="left", padx=(0, 3))
        var_cm = ctk.StringVar(value=get_d('crane_mode', '1К-6К'))
        ctk.CTkOptionMenu(row2, values=["1К-6К", "7К-8К"], variable=var_cm, width=90).pack(side="left", padx=(0, 2))
        w['var_crane_mode'] = var_cm
        self._qbtn(row2, 'crane_mode')

        # --- Строка 3: Нагрузки ---
        row3 = ctk.CTkFrame(parent_frame, fg_color="transparent")
        row3.pack(fill="x", pady=3)

        for label, field_key, entry_key, default_val, tip_key in [
            ("Снег:",   'Q_snow',   'entry_snow',   '1.5', 'snow'),
            ("Пыль:",   'Q_dust',   'entry_dust',   '0.5', 'dust'),
            ("Кровля:", 'Q_roof',   'entry_roof',   '0.3', 'roof'),
            ("Прогон:", 'Q_purlin', 'entry_purlin', '0.2', 'purlin'),
            ("γc:",     'yc',       'entry_yc',     '1.2', 'yc'),
        ]:
            ctk.CTkLabel(row3, text=label).pack(side="left", padx=(0, 3))
            e = ctk.CTkEntry(row3, width=62)
            e.insert(0, get_d(field_key, default_val))
            e.pack(side="left", padx=(0, 2))
            w[entry_key] = e
            self._qbtn(row3, tip_key)

        # --- Строка 4: Фахверк ---
        row4 = ctk.CTkFrame(parent_frame, fg_color="transparent")
        row4.pack(fill="x", pady=3)

        ctk.CTkLabel(row4, text="Нагрузка фахверка, кг/м.п.:").pack(side="left", padx=(0, 3))
        e = ctk.CTkEntry(row4, width=70)
        e.insert(0, get_d('fachwerk_load', '0'))
        e.pack(side="left", padx=(0, 2))
        w['entry_fachwerk_load'] = e
        self._qbtn(row4, 'fachwerk_load')

        var_fp_raw = get_d('fachwerk_post', 'False')
        var_fp = ctk.BooleanVar(value=(var_fp_raw == 'True'))
        check = ctk.CTkCheckBox(row4, text="Стойка фахверка (шаг 12 м)", variable=var_fp)
        check.pack(side="left", padx=(0, 2))
        w['var_fachwerk_post'] = var_fp
        w['check_fachwerk'] = check
        self._qbtn(row4, 'fachwerk_post')

        ctk.CTkLabel(row4, text="Тип здания:").pack(side="left", padx=(0, 3))
        var_bt = ctk.StringVar(value=get_d('building_type', 'Основные'))
        ctk.CTkOptionMenu(row4, values=["Основные", "Энергоносители", "Вспомогательные"],
                          variable=var_bt, width=155).pack(side="left", padx=(0, 2))
        w['var_building_type'] = var_bt
        self._qbtn(row4, 'building_type')

        # Checkbox стойки зависит от шага колонн
        def on_col_step_change(*args, _check=check, _var=var_col):
            _check.configure(state="normal" if _var.get() == "12" else "disabled")

        var_col.trace_add("write", on_col_step_change)
        on_col_step_change()

        return w

    def _extract_span_widget_values(self, w: dict) -> dict:
        """Читает текущие значения виджетов пролёта в plain dict."""
        return {
            'span_L':         w['entry_span_L'].get(),
            'truss_step_B':   w['var_truss_B'].get(),
            'column_step':    w['var_column_step'].get(),
            'rail_level':     w['entry_rail'].get(),
            'truss_type':     w['var_truss_type'].get(),
            'crane_capacity': w['entry_crane'].get(),
            'crane_count':    w['var_crane_count'].get(),
            'crane_mode':     w['var_crane_mode'].get(),
            'brake_path':     w['var_brake'].get(),
            'Q_snow':         w['entry_snow'].get(),
            'Q_dust':         w['entry_dust'].get(),
            'Q_roof':         w['entry_roof'].get(),
            'Q_purlin':       w['entry_purlin'].get(),
            'yc':             w['entry_yc'].get(),
            'fachwerk_load':  w['entry_fachwerk_load'].get(),
            'fachwerk_post':  str(w['var_fachwerk_post'].get()),
            'building_type':  w['var_building_type'].get(),
        }

    def _create_button(self):
        """Кнопки расчета и сохранения."""
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.btn_calc = ctk.CTkButton(
            btn_frame, text="Рассчитать", command=self._on_calculate,
            height=40, font=("", 14), width=180,
        )
        self.btn_calc.pack(side="left", padx=10)

        self.btn_save = ctk.CTkButton(
            btn_frame, text="  Сохранить результаты", command=self._save_results,
            height=40, font=("", 13), width=230, state="disabled",
            fg_color="#2d5a3d", hover_color="#1e3d2a",
        )
        self.btn_save.pack(side="left", padx=10)
        ToolTip(self.btn_save, "Сохранить результаты расчёта в текстовый файл (.txt).\nДоступно после нажатия «Рассчитать».")

    def _create_results(self):
        """Область результатов."""
        ctk.CTkLabel(self.main_frame, text="Результаты расчета",
                     font=("", 16, "bold")).pack(anchor="w", pady=(10, 10))
        self.text_results = ctk.CTkTextbox(self.main_frame, height=300, font=("Consolas", 12))
        self.text_results.pack(fill="both", expand=True, pady=5)

    def _get_float(self, entry: ctk.CTkEntry, default: float, name: str) -> float:
        """Безопасное получение float из поля ввода."""
        try:
            return float(entry.get().replace(",", "."))
        except (ValueError, TypeError):
            return default

    def _get_float_from_str(self, s: str, default: float, name: str) -> float:
        """Безопасное получение float из строки."""
        try:
            return float(s.replace(",", "."))
        except (ValueError, TypeError):
            return default

    def _get_params(self) -> Optional[InputParams]:
        """Сбор параметров из полей ввода."""
        try:
            length = self._get_float(self.entry_length, 60, "длина")
            if length <= 0:
                raise ValueError("Длина здания должна быть положительной")

            spans = []
            for i, w in enumerate(self.span_widgets):
                v = self._extract_span_widget_values(w)
                span_L    = self._get_float_from_str(v['span_L'], 30, f"пролёт {i + 1} L")
                truss_B   = self._get_float_from_str(v['truss_step_B'], 6, f"пролёт {i + 1} B")
                column_step = float(v['column_step'])
                rail      = self._get_float_from_str(v['rail_level'], 10, f"пролёт {i + 1} рельс")
                if span_L <= 0 or truss_B <= 0:
                    raise ValueError(f"Геометрические параметры пролёта {i + 1} должны быть положительными")
                if column_step not in (6.0, 12.0):
                    raise ValueError(f"Шаг колонн пролёта {i + 1} должен быть 6 или 12 м")
                sp = SpanParams(
                    span_L=span_L,
                    truss_step_B=truss_B,
                    column_step=column_step,
                    rail_level=rail,
                    Q_snow=self._get_float_from_str(v['Q_snow'], 1.5, "снег"),
                    Q_dust=self._get_float_from_str(v['Q_dust'], 0.5, "пыль"),
                    Q_roof=self._get_float_from_str(v['Q_roof'], 0.3, "кровля"),
                    Q_purlin=self._get_float_from_str(v['Q_purlin'], 0.2, "прогон"),
                    yc=self._get_float_from_str(v['yc'], 1.2, "yc"),
                    truss_type=v['truss_type'],
                    crane_capacity=self._get_float_from_str(v['crane_capacity'], 20, "г/п крана"),
                    crane_count=int(v['crane_count']),
                    crane_mode=v['crane_mode'],
                    brake_path=v['brake_path'],
                    fachwerk_load=self._get_float_from_str(v['fachwerk_load'], 0, "нагрузка фахверка"),
                    fachwerk_post=(v['fachwerk_post'] == 'True'),
                    building_type=v['building_type'],
                )
                spans.append(sp)

            if not spans:
                raise ValueError("Необходимо задать хотя бы один пролёт")
            return InputParams(length=length, spans=spans)

        except Exception as e:
            self.text_results.delete("1.0", "end")
            self.text_results.insert("1.0", f"Ошибка ввода: {e}\nПроверьте корректность данных.")
            return None

    def _format_results(self, results: Dict[str, Any]) -> str:
        """Форматирование результатов в текст."""
        lines = []
        if results.get("_error"):
            tb = results.get("_traceback", "")
            return f"Ошибка расчета:\n{results['_error']}\n\n{tb}"

        def format_item(key, val):
            if not isinstance(val, dict):
                return
            method = val.get("method", 0)
            if method == 0 and val.get("note"):
                lines.append(f"  {key}: {val['note']}")
                return
            total  = val.get("total_kg") or val.get("method1_total_kg") or val.get("method2_total_kg")
            kg_m2  = val.get("kg_m2") or val.get("method1_kg_m2") or val.get("method2_kg_m2")
            m1     = val.get("method1_kg") or val.get("method1_total_kg")
            m2     = val.get("method2_kg") or val.get("method2_total_kg")
            if total is not None:
                lines.append(f"  {key}: {total:.0f} кг")
                if kg_m2 is not None:
                    lines.append(f"      ({kg_m2:.1f} кг/м²)")
                if m1 is not None and m2 is not None:
                    lines.append(f"      [Метод 1: {m1:.0f} кг, Метод 2: {m2:.0f} кг]")
                elif method == 1:
                    lines.append("      [Метод 1]")
                elif method == 2:
                    lines.append("      [Метод 2]")

        span_results_list = results.get('_spans', [])
        for span_name, span_res in span_results_list:
            lines.append(f"\n{'=' * 50}")
            lines.append(f"  {span_name}")
            lines.append('=' * 50)
            span_total = 0.0
            for key, val in span_res.items():
                format_item(key, val)
                if isinstance(val, dict):
                    span_total += (val.get('total_kg') or val.get('method1_total_kg') or val.get('method2_total_kg') or 0)
            lines.append(f"  --- Итого по пролёту: {span_total:.0f} кг ---")

        lines.append(f"\n{'=' * 50}")
        lines.append("  Общие конструкции")
        lines.append('=' * 50)
        for key in ['Фахверк', 'Опоры трубопроводов']:
            format_item(key, results.get(key, {}))

        lines.append("")
        lines.append("=" * 50)
        total_kg    = results.get("_total_kg", 0)
        area        = results.get("_area", 1)
        kg_m2_total = results.get("_kg_m2", 0)
        lines.append(f"  ИТОГО: {total_kg:.0f} кг")
        lines.append(f"  Металлоёмкость: {kg_m2_total:.1f} кг/м²")
        lines.append(f"  Площадь здания: {area:.0f} м²")
        return "\n".join(lines)

    def _on_calculate(self):
        """Обработчик кнопки Рассчитать."""
        params = self._get_params()
        if params is None:
            return
        self.text_results.delete("1.0", "end")
        self.text_results.insert("1.0", "Выполняется расчет...\n")
        self.update()
        try:
            results = self.calculator.calculate(params)
            text = self._format_results(results)
            self.text_results.delete("1.0", "end")
            self.text_results.insert("1.0", text)
            self._last_results_text = text
            self.btn_save.configure(state="normal")
        except Exception as e:
            self.text_results.delete("1.0", "end")
            self.text_results.insert("1.0", f"Ошибка:\n{e}\n\n{traceback.format_exc()}")

    def _save_results(self):
        """Сохранение результатов расчёта в текстовый файл."""
        if not self._last_results_text:
            return
        now = datetime.datetime.now()
        default_name = f"metalloemkost_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".txt",
            filetypes=[("Текстовый файл", "*.txt"), ("Все файлы", "*.*")],
            initialfile=default_name,
            title="Сохранить результаты расчёта",
        )
        if not filepath:
            return
        try:
            header = (
                "РАСЧЁТ МЕТАЛЛОЁМКОСТИ ПРОИЗВОДСТВЕННЫХ ЗДАНИЙ С МОСТОВЫМИ КРАНАМИ\n"
                f"Дата расчёта: {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
                + "=" * 60 + "\n\n"
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header)
                f.write(self._last_results_text)
        except Exception as e:
            self.text_results.insert("end", f"\n\nОшибка сохранения файла: {e}")


def main():
    app = MetalCapacityApp()
    app.mainloop()


if __name__ == "__main__":
    main()
