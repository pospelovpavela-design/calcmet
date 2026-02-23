#!/usr/bin/env python3
"""
Металлоёмкость электрокабельных эстакад и галерей — версия 4.2F
Таблицы вшиты в код (источник: mc_electrica.db, таблица electr_dict).
"""
import traceback
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_TITLE  = ("Segoe UI", 15, "bold")
FONT_LABEL  = ("Segoe UI", 12)
FONT_RESULT = ("Courier New", 12)

PAD = {"padx": 8, "pady": 4}

# ─────────────────────────────────────────────────────────────────────
#  ДАННЫЕ (из mc_electrica.db 4.2F, таблица electr_dict)
#  type_id=0 — эстакада без прохода
#  type_id=1 — галерея с проходом посередине
# ─────────────────────────────────────────────────────────────────────
CONFIGS = [
    # Эстакады без прохода (type_id=0)
    {
        "num":      "1",
        "kg_m":     0.154,
        "std_load": 150,
        "svc_load": 0,
        "type_id":  0,
        "note":     "Без прохода, нагрузка до 150 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    {
        "num":      "2",
        "kg_m":     0.191,
        "std_load": 500,
        "svc_load": 0,
        "type_id":  0,
        "note":     "Без прохода, нагрузка до 500 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    {
        "num":      "3",
        "kg_m":     0.248,
        "std_load": 1000,
        "svc_load": 0,
        "type_id":  0,
        "note":     "Без прохода, нагрузка до 1000 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    {
        "num":      "4",
        "kg_m":     0.317,
        "std_load": 1500,
        "svc_load": 0,
        "type_id":  0,
        "note":     "Без прохода, нагрузка до 1500 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    # Галереи с проходом (type_id=1)
    {
        "num":      "5",
        "kg_m":     0.379,
        "std_load": 500,
        "svc_load": 320,
        "type_id":  1,
        "note":     "С проходом посередине, нагрузка до 500 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    {
        "num":      "6",
        "kg_m":     0.482,
        "std_load": 1000,
        "svc_load": 320,
        "type_id":  1,
        "note":     "С проходом посередине, нагрузка до 1000 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    {
        "num":      "7",
        "kg_m":     0.493,
        "std_load": 1500,
        "svc_load": 320,
        "type_id":  1,
        "note":     "С проходом посередине, нагрузка до 1500 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    {
        "num":      "8",
        "kg_m":     0.535,
        "std_load": 2000,
        "svc_load": 320,
        "type_id":  1,
        "note":     "С проходом посередине, нагрузка до 2000 кг/м, шаг опор 12 м, h до низа 5 м",
    },
    {
        "num":      "9",
        "kg_m":     0.604,
        "std_load": 3000,
        "svc_load": 320,
        "type_id":  1,
        "note":     "С проходом посередине, нагрузка до 3000 кг/м, шаг опор 12 м, h до низа 5 м",
    },
]


class FloatEntry(ctk.CTkEntry):
    def get_float(self, default=0.0):
        try:
            return float(self.get().replace(",", "."))
        except ValueError:
            return default


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Металлоёмкость электрокабельных эстакад — v4.2F")
        self.geometry("1150x680")
        self.resizable(True, True)
        self._selected_idx = 0
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ── ЛЕВАЯ ПАНЕЛЬ ──
        left = ctk.CTkScrollableFrame(
            self, label_text="Выбор типа эстакады / галереи", width=400
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left.grid_columnconfigure(0, weight=1)

        # разделитель по типу
        type_header = {0: "── Эстакада без прохода ──", 1: "── Галерея с проходом ──"}
        last_type = -1
        row_idx = 0
        self._radio_var = ctk.IntVar(value=0)

        ctk.CTkLabel(
            left,
            text="№   Нагрузка кабелей, кг/м   т/м",
            font=("Courier New", 11),
            text_color="#90caf9",
        ).grid(row=row_idx, column=0, sticky="w", padx=4, pady=(4, 2))
        row_idx += 1

        for i, c in enumerate(CONFIGS):
            if c["type_id"] != last_type:
                last_type = c["type_id"]
                ctk.CTkLabel(
                    left,
                    text=type_header[c["type_id"]],
                    font=("Segoe UI", 11, "bold"),
                    text_color="#ffcc80",
                ).grid(row=row_idx, column=0, sticky="w", padx=4, pady=(8, 2))
                row_idx += 1

            svc_str = f"+{c['svc_load']} обсл." if c["svc_load"] else "без обсл."
            label = (
                f"{c['num']:<4}  {c['std_load']:<22}  {c['kg_m']:.3f}"
            )
            btn = ctk.CTkRadioButton(
                left,
                text=label,
                font=("Courier New", 11),
                variable=self._radio_var,
                value=i,
                command=self._on_select,
            )
            btn.grid(row=row_idx, column=0, sticky="w", padx=4, pady=1)
            row_idx += 1

        # разделитель
        ctk.CTkLabel(left, text="─" * 50, font=("Courier New", 10),
                     text_color="#555").grid(
            row=row_idx, column=0, sticky="w", padx=4, pady=(8, 4)
        )
        row_idx += 1

        # Длина
        ctk.CTkLabel(left, text="Длина эстакады, м:", font=FONT_LABEL).grid(
            row=row_idx, column=0, sticky="w", **PAD
        )
        row_idx += 1
        self.e_length = FloatEntry(left, width=140, placeholder_text="м")
        self.e_length.insert(0, "100")
        self.e_length.grid(row=row_idx, column=0, sticky="w", **PAD)
        row_idx += 2

        ctk.CTkButton(
            left,
            text="  Рассчитать",
            font=FONT_TITLE,
            command=self._on_calculate,
            fg_color="#1565c0",
            hover_color="#0d47a1",
            height=44,
        ).grid(row=row_idx, column=0, sticky="ew", padx=8, pady=10)

        # ── ПРАВАЯ ПАНЕЛЬ ──
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

        self.lbl_status = ctk.CTkLabel(
            self,
            text="Выберите тип эстакады/галереи и введите длину.",
            font=FONT_LABEL,
            text_color="#80cbc4",
        )
        self.lbl_status.grid(
            row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 8)
        )

        self._show_description()

    def _on_select(self):
        self._selected_idx = self._radio_var.get()
        self._show_description()

    def _show_description(self):
        c = CONFIGS[self._selected_idx]
        type_name = (
            "Электрокабельная эстакада (без прохода)"
            if c["type_id"] == 0
            else "Электрокабельная галерея (с проходом посередине)"
        )
        sep = "─" * 68
        lines = [
            "=" * 68,
            f"  КОНФИГУРАЦИЯ № {c['num']}",
            "=" * 68,
            "",
            f"  {c['note']}",
            "",
            sep,
            f"  {'Тип сооружения:':<44} {type_name}",
            f"  {'Нагрузка от кабелей (нормат., ≤):':<44} {c['std_load']:.0f} кг/м",
            f"  {'Нагрузка от обслуживающих площадок:':<44} "
            + (f"{c['svc_load']:.0f} кг/м" if c["svc_load"] else "не предусмотрена"),
            f"  {'Металлоёмкость (т/м.п.):':<44} {c['kg_m']:.3f} т/м",
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
            type_name = (
                "Эстакада (без прохода)"
                if c["type_id"] == 0
                else "Галерея (с проходом)"
            )
            sep = "─" * 68
            lines = [
                "=" * 68,
                "  РЕЗУЛЬТАТ РАСЧЁТА МЕТАЛЛОЁМКОСТИ",
                f"  Электрокабельная эстакада — конфигурация № {c['num']}",
                "=" * 68,
                "",
                f"  {c['note']}",
                "",
                sep,
                f"  {'Тип сооружения:':<44}  {type_name}",
                f"  {'Нагрузка от кабелей (≤):':<44}  {c['std_load']:.0f} кг/м",
                f"  {'Металлоёмкость на 1 м.п.:':<44}  {c['kg_m']:.3f} т/м",
                f"  {'Длина эстакады:':<44}  {length:.1f} м",
                sep,
                f"  {'ИТОГО металла:':<44}  {total_t:.2f} т",
                "=" * 68,
            ]
            if c["svc_load"]:
                lines.append(
                    f"\n  Нагрузка от обслуживающих площадок: {c['svc_load']:.0f} кг/м"
                )
            self._set_text("\n".join(lines))
            self.lbl_status.configure(
                text=f"Конф. {c['num']} | {type_name} | {length:.1f} м | Итого: {total_t:.2f} т",
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
