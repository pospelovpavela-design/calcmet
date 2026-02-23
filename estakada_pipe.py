#!/usr/bin/env python3
"""
Металлоёмкость трубопроводных эстакад — версия 3.2F
Таблицы вшиты в код (источник: mc_energfl.db, таблица enrg_overpass).
"""
import traceback
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_TITLE  = ("Segoe UI", 15, "bold")
FONT_LABEL  = ("Segoe UI", 12)
FONT_SMALL  = ("Segoe UI", 11)
FONT_RESULT = ("Courier New", 12)

PAD = {"padx": 8, "pady": 4}

# ─────────────────────────────────────────────────────────────────────
#  ДАННЫЕ (из mc_energfl.db 3.2F, таблица enrg_overpass)
#  Поля: num_id, max_pipes, max_pipe_d_mm, std_load_kgm,
#         svc_load_kgm, met_per_m_tm, pipes_low, pipes_high,
#         factor_ind, factor_val, note
# ─────────────────────────────────────────────────────────────────────
CONFIGS = [
    {
        "num":        "1",
        "max_pipes":  2,
        "max_d_mm":   500,
        "std_load":   665.08,
        "svc_load":   320,
        "kg_m":       0.405,
        "pipes_low":  1,
        "pipes_high": 5,
        "note":       "2 тр. от Ø159×6 до Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "2",
        "max_pipes":  2,
        "max_d_mm":   1000,
        "std_load":   2426.3,
        "svc_load":   320,
        "kg_m":       0.475,
        "pipes_low":  1,
        "pipes_high": 5,
        "note":       "2 тр. от Ø530×6 до Ø1020×16, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "3а",
        "max_pipes":  6,
        "max_d_mm":   500,
        "std_load":   918.6,
        "svc_load":   320,
        "kg_m":       0.518,
        "pipes_low":  6,
        "pipes_high": 11,
        "note":       "6 тр. от Ø159×9 до Ø325×9, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "3б",
        "max_pipes":  6,
        "max_d_mm":   500,
        "std_load":   1995.24,
        "svc_load":   320,
        "kg_m":       0.585,
        "pipes_low":  6,
        "pipes_high": 11,
        "note":       "6 тр. от Ø325×9 и Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "4",
        "max_pipes":  6,
        "max_d_mm":   1000,
        "std_load":   3756.46,
        "svc_load":   320,
        "kg_m":       0.625,
        "pipes_low":  6,
        "pipes_high": 11,
        "note":       "2 тр. Ø1020×16 + 4 тр. Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "5",
        "max_pipes":  6,
        "max_d_mm":   2000,
        "std_load":   5800.3,
        "svc_load":   320,
        "kg_m":       0.312,
        "pipes_low":  6,
        "pipes_high": 11,
        "note":       "1 тр. Ø2040×20 + 5 тр. Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "6",
        "max_pipes":  6,
        "max_d_mm":   3000,
        "std_load":   10596.3,
        "svc_load":   320,
        "kg_m":       0.646,
        "pipes_low":  6,
        "pipes_high": 11,
        "note":       "1 тр. Ø3050×25 + 5 тр. Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "7",
        "max_pipes":  4,
        "max_d_mm":   500,
        "std_load":   665.08,
        "svc_load":   320,
        "kg_m":       0.689,
        "pipes_low":  4,
        "pipes_high": 11,
        "note":       "4 (2+2) тр. от Ø159×6 до Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "8",
        "max_pipes":  4,
        "max_d_mm":   1000,
        "std_load":   2426.3,
        "svc_load":   320,
        "kg_m":       0.829,
        "pipes_low":  4,
        "pipes_high": 11,
        "note":       "4 (2+2) тр. от Ø530×6 до Ø1020×16, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "9а",
        "max_pipes":  6,
        "max_d_mm":   500,
        "std_load":   918.6,
        "svc_load":   320,
        "kg_m":       0.708,
        "pipes_low":  12,
        "pipes_high": 25,
        "note":       "12 тр. от Ø159×9 до Ø325×9, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "9б",
        "max_pipes":  12,
        "max_d_mm":   500,
        "std_load":   1995.24,
        "svc_load":   320,
        "kg_m":       1.03,
        "pipes_low":  12,
        "pipes_high": 25,
        "note":       "12 тр. от Ø325×9 до Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "10",
        "max_pipes":  12,
        "max_d_mm":   1000,
        "std_load":   3756.46,
        "svc_load":   320,
        "kg_m":       1.11,
        "pipes_low":  12,
        "pipes_high": 25,
        "note":       "4 (2+2) тр. Ø1020×16 + 8 (4+4) тр. Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "11",
        "max_pipes":  12,
        "max_d_mm":   2000,
        "std_load":   5800.3,
        "svc_load":   320,
        "kg_m":       1.303,
        "pipes_low":  12,
        "pipes_high": 25,
        "note":       "4 (2+2) тр. Ø1020×16 + 8 (4+4) тр. Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
    {
        "num":        "12",
        "max_pipes":  12,
        "max_d_mm":   3000,
        "std_load":   10596.3,
        "svc_load":   320,
        "kg_m":       1.6,
        "pipes_low":  12,
        "pipes_high": 25,
        "note":       "2(1+1) тр. Ø3050×25 + 10(5+5) тр. Ø530×10, шаг опор 12 м, h до низа 7 м",
    },
]


# ─────────────────────────────────────────────────────────────────────
#  Вспомогательный виджет
# ─────────────────────────────────────────────────────────────────────
class FloatEntry(ctk.CTkEntry):
    def get_float(self, default=0.0):
        try:
            return float(self.get().replace(",", "."))
        except ValueError:
            return default


# ─────────────────────────────────────────────────────────────────────
#  Приложение
# ─────────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Металлоёмкость трубопроводных эстакад — v3.2F")
        self.geometry("1200x720")
        self.resizable(True, True)
        self._selected_idx = 0
        self._build_ui()

    # ── построение UI ────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ── ЛЕВАЯ ПАНЕЛЬ — выбор конфигурации + параметры ──
        left = ctk.CTkScrollableFrame(
            self, label_text="Выбор конфигурации эстакады", width=380
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left.grid_columnconfigure(0, weight=1)

        # заголовок таблицы
        ctk.CTkLabel(
            left,
            text="№    Трубы  Ø макс, мм  q, кг/м    т/м",
            font=("Courier New", 11),
            text_color="#90caf9",
        ).grid(row=0, column=0, sticky="w", padx=4, pady=(4, 2))

        # строки конфигурации — radiobutton-кнопки
        self._radio_var = ctk.IntVar(value=0)
        self._row_btns = []
        for i, c in enumerate(CONFIGS):
            label = (
                f"{c['num']:<4}  {str(c['pipes_low'])+'–'+str(c['pipes_high']):<7}"
                f"  {c['max_d_mm']:<12}"
                f"  {c['std_load']:<10.1f}"
                f"  {c['kg_m']:.3f}"
            )
            btn = ctk.CTkRadioButton(
                left,
                text=label,
                font=("Courier New", 11),
                variable=self._radio_var,
                value=i,
                command=self._on_select,
            )
            btn.grid(row=i + 1, column=0, sticky="w", padx=4, pady=1)
            self._row_btns.append(btn)

        # разделитель
        ctk.CTkLabel(left, text="─" * 52, font=("Courier New", 10),
                     text_color="#555").grid(
            row=len(CONFIGS) + 1, column=0, sticky="w", padx=4, pady=(8, 4)
        )

        # длина эстакады
        r = len(CONFIGS) + 2
        ctk.CTkLabel(left, text="Длина эстакады, м:", font=FONT_LABEL).grid(
            row=r, column=0, sticky="w", **PAD
        )
        r += 1
        self.e_length = FloatEntry(left, width=140, placeholder_text="м")
        self.e_length.insert(0, "100")
        self.e_length.grid(row=r, column=0, sticky="w", **PAD)
        r += 1

        # кнопка расчёта
        r += 1
        ctk.CTkButton(
            left,
            text="  Рассчитать",
            font=FONT_TITLE,
            command=self._on_calculate,
            fg_color="#1565c0",
            hover_color="#0d47a1",
            height=44,
        ).grid(row=r, column=0, sticky="ew", padx=8, pady=10)

        # ── ПРАВАЯ ПАНЕЛЬ — описание + результат ──
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right, text="Результаты расчёта", font=FONT_TITLE
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.txt = ctk.CTkTextbox(
            right, font=FONT_RESULT, wrap="word", state="disabled"
        )
        self.txt.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        # статусная строка
        self.lbl_status = ctk.CTkLabel(
            self, text="Выберите конфигурацию и введите длину эстакады.",
            font=FONT_LABEL, text_color="#80cbc4"
        )
        self.lbl_status.grid(
            row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 8)
        )

        # показать описание первой конфигурации
        self._show_description()

    # ── обработчики ──────────────────────────────────────────────────
    def _on_select(self):
        self._selected_idx = self._radio_var.get()
        self._show_description()

    def _show_description(self):
        c = CONFIGS[self._selected_idx]
        sep = "─" * 68
        lines = [
            "=" * 68,
            f"  КОНФИГУРАЦИЯ № {c['num']}",
            "=" * 68,
            "",
            f"  Описание: {c['note']}",
            "",
            sep,
            f"  {'Количество труб (диапазон):':<42} {c['pipes_low']}–{c['pipes_high']} шт.",
            f"  {'Макс. диаметр трубы:':<42} Ø{c['max_d_mm']} мм",
            f"  {'Станд. нагрузка на эстакаду (q):':<42} {c['std_load']:.2f} кг/м",
            f"  {'Нагрузка от обслуживающих площадок:':<42} {c['svc_load']:.0f} кг/м",
            f"  {'Металлоёмкость (т/м.п.):':<42} {c['kg_m']:.3f} т/м",
            sep,
            "",
            "  → Введите длину эстакады и нажмите «Рассчитать».",
        ]
        self._set_text("\n".join(lines))

    def _on_calculate(self):
        try:
            length = self.e_length.get_float(0.0)
            if length <= 0:
                messagebox.showwarning("Ошибка", "Введите длину эстакады > 0.")
                return
            c = CONFIGS[self._selected_idx]
            total_t = c["kg_m"] * length
            sep = "─" * 68
            lines = [
                "=" * 68,
                "  РЕЗУЛЬТАТ РАСЧЁТА МЕТАЛЛОЁМКОСТИ",
                f"  Трубопроводная эстакада — конфигурация № {c['num']}",
                "=" * 68,
                "",
                f"  {c['note']}",
                "",
                sep,
                f"  {'Металлоёмкость на 1 м.п.:':<44}  {c['kg_m']:.3f} т/м",
                f"  {'Длина эстакады:':<44}  {length:.1f} м",
                sep,
                f"  {'ИТОГО металла:':<44}  {total_t:.2f} т",
                "=" * 68,
                "",
                f"  Нормативная нагрузка (q):  {c['std_load']:.2f} кг/м",
                f"  Обслуживающие площадки:    {c['svc_load']:.0f} кг/м",
            ]
            self._set_text("\n".join(lines))
            self.lbl_status.configure(
                text=f"Конф. {c['num']} | {length:.1f} м | Итого: {total_t:.2f} т",
                text_color="#80cbc4",
            )
        except Exception:
            messagebox.showerror("Ошибка", traceback.format_exc())

    def _set_text(self, text: str):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", text)
        self.txt.configure(state="disabled")


# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
