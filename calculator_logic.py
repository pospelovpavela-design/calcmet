# -*- coding: utf-8 -*-
"""
Расчетный модуль металлоемкости производственных одноэтажных зданий с мостовыми кранами.
Метод 1: эмпирические формулы из методичек.
Метод 2: чтение таблиц (xlsx, docx).
"""

import os
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass

# Импорт парсеров таблиц
try:
    from table_parsers import (
        parse_coverage_xlsx_full,
        read_xlsx_fachwerk,
        read_docx_crane_beams,
        read_docx_brake,
        get_project_root,
    )
except ImportError:
    parse_coverage_xlsx_full = read_xlsx_fachwerk = read_docx_crane_beams = read_docx_brake = None
    get_project_root = lambda: os.path.dirname(os.path.abspath(__file__))


@dataclass
class SpanParams:
    """Параметры одного пролёта."""
    span_L: float          # Пролет здания L, м
    truss_step_B: float    # Шаг ферм B, м
    column_step: float     # Шаг колонн: 6 или 12 м
    rail_level: float      # Уровень головки рельса, м
    Q_snow: float          # Снег, кН/м2
    Q_dust: float          # Пыль, кН/м2
    Q_roof: float          # Кровля, кН/м2
    Q_purlin: float        # Вес прогона, кН/м2
    yc: float              # Коэффициент ответственности
    truss_type: str        # Уголки, Двутавры, Молодечно
    crane_capacity: float  # Грузоподъемность крана, т
    crane_count: int       # 1 или 2
    crane_mode: str        # Режим работы: '1К-6К' или '7К-8К'
    brake_path: str        # С проходом, Без прохода
    fachwerk_load: float   # Нагрузка на ригеля фахверка, кг/м.п.
    fachwerk_post: bool    # Стойка фахверка (только при шаге 12м)
    building_type: str     # Тип здания для опор трубопроводов


class InputParams:
    """Входные параметры расчета (многопролётное здание)."""

    def __init__(self, length: float, spans: List[SpanParams]):
        self.length = length  # Длина здания (продольный размер), м
        self.spans = spans    # Список параметров пролётов

    @property
    def width(self) -> float:
        """Полная ширина здания = сумма пролётов."""
        return sum(sp.span_L for sp in self.spans)


# === ЭМПИРИЧЕСКИЕ КОНСТАНТЫ ИЗ МЕТОДИК ===
RHO = 78.5  # кН/м3 плотность стали
RY = 24e4   # кН/м2 (24 кН/см2)
GAMMA_F = 1.05  # для стального проката
GAMMA_F_SNOW = 1.4
GAMMA_F_DUST = 1.3
GAMMA_C_TECH = 1.2
Q_RAIL = 1.13  # кН/м вес рельса
K_PB = 1.4     # конструктивный коэффициент подкрановой балки
PSI_K_TOP = 1.5
PSI_K_BOT = 2.0
K_M_TOP = 0.25
K_M_BOT = 0.45
G_ST = 0.25    # кН/м2 вес стен
H_SH = 3.5     # м высота шатра
H_F = 0.6      # м заглубление базы
H_CRANE = 4.0  # м высота крана от рельса
A_GAP = 0.3    # м зазор

# Таблица αпб по грузоподъемности (7К-8К / 1К-6К)
ALPHA_PB_TABLE = {
    10: (0.45, 0.22), 20: (0.55, 0.27), 30: (0.65, 0.32), 50: (0.7, 0.35),
    80: (0.75, 0.38), 100: (0.8, 0.4), 125: (0.875, 0.44), 200: (0.95, 0.48),
    250: (1.0, 0.5), 300: (1.05, 0.53)
}

# Таблица q (нормативные эквивалентные нагрузки кранов), кН/м
Q_CRANE_TABLE = {10: 80, 20: 120, 30: 160, 50: 220, 80: 280, 100: 320, 125: 360, 200: 450, 250: 500, 300: 550}

# Таблица прогонов: (q_pr кН/м, m_pr кг) для пролета 6м и 12м
PROGON_6M = [(0.45, 110.4), (0.65, 126), (0.9, 144), (1.25, 166.2), (1.7, 190.8), (2.25, 288), (3.0, 332.4), (3.8, 381.6),
             (1.9, 197.4), (2.2, 219.6), (2.3, 256.2), (2.7, 295.2), (3.4, 321.6), (4.0, 366), (5.8, 450.6), (6.5, 493.2), (9.0, 576.6)]
PROGON_12M = [(0.15, 381.6), (0.3, 576), (0.45, 664.8), (0.65, 763.2), (0.2, 394.8), (0.3, 439.2), (0.4, 519.6), (0.5, 590.4),
              (1.2, 901.2), (1.4, 986.4), (2.0, 1153.2), (0.63, 285), (0.81, 340), (1.13, 395), (1.68, 550), (1.85, 590), (3.22, 780)]


def _interpolate_table(table: list, q_pr: float) -> float:
    """Подбор массы прогона по таблице (ближайший больший q)."""
    sorted_t = sorted(table, key=lambda x: x[0])
    for q, m in sorted_t:
        if q_pr <= q:
            return m
    return sorted_t[-1][1] if sorted_t else 0


def _get_alpha_pb(Q: float, mode: str = '7К-8К') -> float:
    """Коэффициент αпб по грузоподъемности.
    mode='7К-8К' → индекс 0; mode='1К-6К' → индекс 1."""
    idx = 0 if '7' in mode else 1  # '7' однозначно в '7К-8К', не в '1К-6К'
    keys = sorted(ALPHA_PB_TABLE.keys())
    for k in keys:
        if Q <= k:
            return ALPHA_PB_TABLE[k][idx]
    return ALPHA_PB_TABLE[keys[-1]][idx]


def _get_q_rail(Q: float) -> float:
    """Вес рельса по г/п, кН/м."""
    if Q <= 30:
        return 0.461
    elif Q <= 50:
        return 0.598
    elif Q <= 80:
        return 0.831
    elif Q <= 320:
        return 1.135
    else:
        return 1.417


class CalculatorLogic:
    """Класс расчета металлоемкости."""

    def __init__(self, project_root: Optional[str] = None):
        self.root = project_root or get_project_root()
        self._coverage_data = None
        self._fachwerk_data = None
        self._crane_beams = None
        self._brake = None

    def _load_tables(self):
        """Загрузка таблиц Метода 2."""
        base = self.root
        coverage_paths = [
            os.path.join(base, "металлоекмсоть покрытия.xlsx"),
            os.path.join(base, "Металлоемкость", "Тип 1 здания с кранами", "металлоекмсоть покрытия.xlsx"),
            os.path.join(os.path.expanduser("~/Desktop"), "Металлоемкость", "Тип 1 здания с кранами", "металлоекмсоть покрытия.xlsx"),
        ]
        fachwerk_paths = [
            os.path.join(base, "Металлоёмкость фахверк.xlsx"),
            os.path.join(base, "Металлоемкость", "Тип 1 здания с кранами", "Металлоёмкость фахверк.xlsx"),
            os.path.join(os.path.expanduser("~/Desktop"), "Металлоемкость", "Тип 1 здания с кранами", "Металлоёмкость фахверк.xlsx"),
        ]
        crane_paths = [
            os.path.join(base, "Таблица металлоемкости на подкрановые конструкции.docx"),
            os.path.join(base, "Металлоемкость", "Тип 1 здания с кранами", "Таблица металлоемкости на подкрановые конструкции.docx"),
            os.path.join(os.path.expanduser("~/Desktop"), "Металлоемкость", "Тип 1 здания с кранами", "Таблица металлоемкости на подкрановые конструкции.docx"),
        ]
        brake_paths = [
            os.path.join(base, "Таблица металлоемкости на тормозные конструкции.docx"),
            os.path.join(base, "Металлоемкость", "Тип 1 здания с кранами", "Таблица металлоемкости на тормозные конструкции.docx"),
            os.path.join(os.path.expanduser("~/Desktop"), "Металлоемкость", "Тип 1 здания с кранами", "Таблица металлоемкости на тормозные конструкции.docx"),
        ]
        for p in coverage_paths:
            if os.path.exists(p) and parse_coverage_xlsx_full:
                self._coverage_data = parse_coverage_xlsx_full(p)
                break
        for p in fachwerk_paths:
            if os.path.exists(p) and read_xlsx_fachwerk:
                self._fachwerk_data = read_xlsx_fachwerk(p)
                break
        for p in crane_paths:
            if os.path.exists(p) and read_docx_crane_beams:
                self._crane_beams = read_docx_crane_beams(p)
                break
        for p in brake_paths:
            if os.path.exists(p) and read_docx_brake:
                self._brake = read_docx_brake(p)
                break

    def calc_progony(self, sp: SpanParams, length: float) -> Dict[str, Any]:
        """Прогоны: только Метод 1."""
        g_sv_n = 0.2 if sp.truss_step_B == 6 else 0.3
        a_pr = 3.0  # шаг прогонов, м (стандартный для обоих типов ферм)
        q_pr = (sp.Q_roof + g_sv_n * GAMMA_F + sp.Q_snow * GAMMA_F_SNOW + sp.Q_dust * GAMMA_F_DUST + 1.0 * GAMMA_C_TECH) * a_pr * sp.yc
        table = PROGON_6M if sp.truss_step_B == 6 else PROGON_12M
        m_pr = _interpolate_table(table, q_pr)
        # Количество прогонов в одном отсеке (шаг ферм B):
        # span_L / a_pr — число пролётов между прогонами, +1 — включая оба крайних прогона
        n_pr = int(sp.span_L / a_pr) + 1
        g_pr_kg_m2 = m_pr * n_pr / (sp.span_L * sp.truss_step_B)
        return {'method': 1, 'kg_m2': g_pr_kg_m2, 'total_kg': g_pr_kg_m2 * length * sp.span_L, 'm_pr': m_pr, 'n_pr': n_pr}

    def calc_svyazi_pokrytiya(self, sp: SpanParams, length: float) -> Dict[str, Any]:
        """Связи по покрытию: только Метод 2."""
        if not self._coverage_data:
            return {'method': 2, 'kg_m2': 15 if sp.truss_step_B == 6 else 35, 'total_kg': 0}
        svyazi = self._coverage_data.get('svyazi', {'до 120': {6: 15, 12: 35}, 'до 400': {6: 40, 12: 55}})
        gpp = 'до 400' if sp.crane_capacity > 120 else 'до 120'
        kg_m2 = svyazi.get(gpp, {}).get(int(sp.truss_step_B), 15 if sp.truss_step_B == 6 else 35)
        area = length * sp.span_L
        return {'method': 2, 'kg_m2': kg_m2, 'total_kg': kg_m2 * area}

    def calc_stropilnye_fermy(self, sp: SpanParams, length: float, g_pr: float) -> Dict[str, Any]:
        """Стропильные фермы: Метод 1 и 2. Уголки - оба, Двутавры/Молодечно - только Метод 2."""
        g_f_n = 0.25 if sp.truss_step_B == 6 else 0.35
        g_pr_kN = g_pr / 1000 * 9.81 if g_pr > 1 else g_pr
        g_n = sp.Q_roof + g_pr_kN + g_f_n + sp.Q_snow + sp.Q_dust + 1.0
        alpha_f = 1.4
        G_f_1_kN = (g_n * sp.truss_step_B / 1000 + 0.018) * alpha_f * sp.span_L ** 2 / 0.85 * sp.yc
        G_f_1 = G_f_1_kN * 100  # кН -> кг
        g_f_1 = G_f_1 / (sp.truss_step_B * sp.span_L)
        n_trusses = int(length / sp.truss_step_B) + 1
        result = {'method1_kg': G_f_1, 'method1_kg_m2': g_f_1, 'total_kg': G_f_1 * n_trusses}
        if self._coverage_data and sp.truss_type in ('Двутавры', 'Молодечно'):
            q_obsh = ((sp.Q_snow + sp.Q_dust + sp.Q_roof + g_pr) / sp.truss_step_B) * sp.yc * 1000 / 9.81
            fermy = self._coverage_data.get('fermy', {})
            span = min([s for s in [18, 24, 30, 36] if s >= sp.span_L], default=36)
            key = (sp.truss_type, span)
            tbl = fermy.get(key, {}) if isinstance(fermy, dict) else {}
            loads = sorted([k for k in tbl.keys() if tbl.get(k) is not None])
            metal = None
            for ld in loads:
                if q_obsh <= ld:
                    metal = tbl[ld]
                    break
            if metal is None and loads:
                metal = tbl[loads[-1]]
            if metal is not None:
                result['method2_kg'] = metal * 1000
                result['method2_kg_m2'] = metal * 1000 / (sp.truss_step_B * sp.span_L)
                result['used_method'] = 2
                result['weight_for_formulas'] = metal * 1000
                result['total_kg'] = result['method2_kg'] * n_trusses
        elif sp.truss_type == 'Уголки':
            result['used_method'] = 1
            result['weight_for_formulas'] = G_f_1
        return result

    def calc_podstropilnye(self, sp: SpanParams, length: float, g_n: float, g_f: float) -> Dict[str, Any]:
        """Подстропильные фермы: Метод 1 и 2. R = g_n * B * L / 2."""
        if sp.column_step != 12:
            return {'method': 0, 'total_kg': 0, 'note': 'Только при шаге колонн 12 м'}
        R = g_n * sp.column_step * sp.span_L / 2
        alpha_pf = (R - 100) * 0.0002 + 0.044 if 100 <= R <= 400 else (0.044 if R < 100 else 0.104)
        G_pf_1_kN = alpha_pf * sp.column_step ** 2
        G_pf_1 = G_pf_1_kN * 100  # кН -> кг
        result = {'method1_kg': G_pf_1, 'method1_kg_m2': G_pf_1 * 2 / (sp.column_step * sp.span_L)}
        if self._coverage_data:
            podstr = self._coverage_data.get('podstropilnye', {})
            R_round = min([r for r in podstr.keys() if r >= R], default=list(podstr.keys())[-1] if podstr else 144)
            metal = podstr.get(R_round)
            if metal is not None:
                metal_kg = metal * 1000 if metal < 100 else metal
                result['method2_kg'] = metal_kg
                result['method2_kg_m2'] = metal_kg * 2 / (sp.column_step * sp.span_L)
        n_pf = int(length / sp.column_step)
        result['total_kg'] = (result.get('method2_kg', result.get('method1_kg', 0))) * n_pf
        return result

    def calc_podkranovye_balki(self, sp: SpanParams, length: float) -> Dict[str, Any]:
        """Подкрановые балки: Метод 1 и 2. Масса = балки + тормозные."""
        B = sp.column_step
        if B not in (6, 12):
            return {'method': 0, 'total_kg': 0}

        # M1: αпб зависит от режима работы крана
        alpha_pb = _get_alpha_pb(sp.crane_capacity, sp.crane_mode)
        # Базовый αпб для режима 7К-8К — нужен для масштабирования M2
        alpha_pb_78 = _get_alpha_pb(sp.crane_capacity, '7К-8К')
        q_r = _get_q_rail(sp.crane_capacity)
        G_pb_1 = (alpha_pb * B + q_r) * B * K_PB
        n_cols = int(length / B) + 1
        n_beams = n_cols - 1
        total_1 = G_pb_1 * n_beams * 2
        result = {'method1_kg_per_beam': G_pb_1, 'method1_total_kg': total_1}
        # Коэффициент режима для М2: используем формульное соотношение
        # (alpha*B + q_r) / (alpha_78*B + q_r) — согласовано с формулой М1
        # и даёт 43–48% снижения для 1К-6К, что соответствует диапазону 40–50%.
        G_pb_78_base = alpha_pb_78 * B + q_r
        mode_ratio = (alpha_pb * B + q_r) / G_pb_78_base if G_pb_78_base > 0 else 1.0

        brake_kg = 0
        if self._brake:
            row_type = 'Средний' if n_cols > 2 else 'Крайний'
            gpr_keys = [5, 10, 20, 32, 50, 80, 100, 125, 200, 400]
            gpr = min([k for k in gpr_keys if k >= sp.crane_capacity], default=400)
            key = (int(B), row_type, sp.brake_path, gpr, sp.crane_count)
            brake_per_m_78 = self._brake.get(key, 80 if sp.brake_path == 'Без прохода' else 100)
            brake_kg = brake_per_m_78 * mode_ratio * B * n_beams * 2
        beam_total = total_1
        if self._crane_beams:
            gpr_keys = [5, 10, 20, 32, 50, 80, 100, 125, 200, 400]
            gpr = min([k for k in gpr_keys if k >= sp.crane_capacity], default=400)
            key = (int(B), gpr, sp.crane_count)
            G_pb_1_78 = (alpha_pb_78 * B + q_r) * B * K_PB
            beam_kg_m_78 = self._crane_beams.get(key, G_pb_1_78 / B)
            beam_kg_m = beam_kg_m_78 * mode_ratio
            beam_total = beam_kg_m * B * n_beams * 2
            result['method2_total_kg'] = beam_total + brake_kg
            result['method2_beam_kg_m'] = beam_kg_m
        result['brake_kg'] = brake_kg
        result['total_kg'] = beam_total + brake_kg
        return result

    def calc_columns(self, sp: SpanParams, length: float, g_pr: float, g_f: float, g_pf: float, G_pb: float) -> Dict[str, Any]:
        """Колонны: только Метод 1."""
        B = sp.column_step
        # Высота подкрановой балки (Таблица 5 методики)
        h_b = B / 6 if sp.crane_capacity <= 50 else B / 7
        # Высота рельса (Таблица 4 методики): КР70/80/100/120 по г/п крана
        if sp.crane_capacity <= 20:
            h_r = 0.130  # КР70
        elif sp.crane_capacity <= 50:
            h_r = 0.150  # КР80
        elif sp.crane_capacity <= 80:
            h_r = 0.170  # КР100
        else:
            h_r = 0.180  # КР120
        # Отметка головы колонны (низ фермы) от ±0.000
        H2 = sp.rail_level + H_CRANE + 0.1 + A_GAP
        H2 = round(H2 * 2) / 2
        # Надкрановая высота: от низа подкрановой балки до головы колонны
        # Низ балки = rail_level - h_r - h_b; голова = H2
        H_v = H2 - sp.rail_level + h_b + h_r
        # Подкрановая высота: от подошвы фундамента до низа подкрановой балки
        # H_F — заглубление базы ниже ±0.000
        H_n = sp.rail_level - h_b - h_r + H_F
        G_st_v = G_ST * (H_v * 1.0 + H_SH) * B
        sum_F_v = (sp.Q_roof + g_pr + g_f + sp.Q_snow + sp.Q_dust + 1.0) * B * sp.span_L / 2 + G_st_v
        if sp.column_step == 12 and g_pf > 0:
            sum_F_v += g_pf / 100 * 1.05  # g_pf в кг, переводим в кН
        G_kv_kN = (sum_F_v * RHO * PSI_K_TOP * H_v / K_M_TOP) / RY
        G_kv = G_kv_kN * 100  # кН -> кг
        G_st_n = G_ST * (H_n - H_F) * 1 * B
        q_c = Q_CRANE_TABLE.get(min([k for k in Q_CRANE_TABLE if k >= sp.crane_capacity], default=300), 320)
        Dmax = q_c * B * 1.1 * 0.85 * 1.0
        sum_F_n = sum_F_v + Dmax + G_pb / 100 + G_st_n + G_kv_kN
        G_kn_kN = (sum_F_n * RHO * PSI_K_BOT * H_n / K_M_BOT) / RY
        G_kn = G_kn_kN * 100  # кН -> кг
        G_k = G_kv + G_kn
        n_cols_per_row = int(length / B) + 1
        n_cols = n_cols_per_row * 2  # два ряда колонн (крайние оси)
        total = G_k * n_cols
        return {'method': 1, 'kg_per_column': G_k, 'total_kg': total, 'kg_m2': total / (length * sp.span_L)}

    def calc_fachwerk(self, spans: List[SpanParams], length: float) -> Dict[str, Any]:
        """Фахверк: только Метод 2. Торцы — все пролёты, продольные — только крайние."""
        total_kg = 0
        n = len(spans)
        for i, sp in enumerate(spans):
            H_building = sp.rail_level + 5.0
            if H_building <= 10:
                h_key = 10
            elif H_building <= 20:
                h_key = 20
            else:
                h_key = 40
            load_key = 0 if sp.fachwerk_load <= 100 else 300
            scheme = 'III' if (sp.column_step == 12 and sp.fachwerk_post) else ('II' if sp.column_step == 12 else 'I')
            if not self._fachwerk_data:
                kg_m2 = 25 if scheme == 'II' else (45 if scheme == 'III' else 10)
            else:
                fw = self._fachwerk_data.get('fachwerk', {})
                kg_m2 = fw.get((scheme, h_key, load_key), 25)
            # Торцы: каждый пролёт вносит свою долю торцевых стен
            wall_area = 2 * sp.span_L * H_building
            # Продольные стены: только крайние пролёты
            if i == 0:
                wall_area += length * H_building
            if i == n - 1:
                wall_area += length * H_building
            total_kg += kg_m2 * wall_area
        return {'method': 2, 'total_kg': total_kg}

    def calc_opory_truboprovodov(self, spans: List[SpanParams], length: float) -> Dict[str, Any]:
        """Внутренние опоры трубопроводов: только Метод 2."""
        total_kg = 0
        for sp in spans:
            if not self._fachwerk_data:
                rng = (11, 22) if sp.building_type == 'Основные' else ((23, 40) if sp.building_type == 'Энергоносители' else (2, 4))
            else:
                opory = self._fachwerk_data.get('opory_truboprovodov', {})
                rng = opory.get(sp.building_type, (11, 22))
            max_kg_m2 = rng[1]
            total_kg += max_kg_m2 * length * sp.span_L
        return {'method': 2, 'total_kg': total_kg}

    def _calc_span(self, sp: SpanParams, length: float) -> Dict[str, Any]:
        """Цепочка per-span расчётов. Возвращает dict с результатами элементов."""
        results = {}

        # 1. Прогоны
        r_pr = self.calc_progony(sp, length)
        results['Прогоны'] = r_pr
        g_pr = r_pr['kg_m2']

        # 2. Связи по покрытию
        r_sv = self.calc_svyazi_pokrytiya(sp, length)
        results['Связи по покрытию'] = r_sv

        # 3. Стропильные фермы
        r_f = self.calc_stropilnye_fermy(sp, length, g_pr)
        results['Стропильные фермы'] = r_f
        g_f = r_f.get('method1_kg_m2', r_f.get('method2_kg_m2', 0))
        if 'weight_for_formulas' in r_f:
            g_f = r_f['weight_for_formulas'] / (sp.truss_step_B * sp.span_L)

        # 4. Подстропильные (g_n в кН/м²)
        g_pr_kN = g_pr / 1000 * 9.81 if g_pr > 1 else g_pr
        g_f_kN = g_f / 1000 * 9.81 if g_f > 1 else g_f
        g_n = sp.Q_roof + g_pr_kN + g_f_kN + sp.Q_snow + sp.Q_dust + 1.0
        r_pf = self.calc_podstropilnye(sp, length, g_n, g_f)
        results['Подстропильные фермы'] = r_pf
        g_pf = r_pf.get('method1_kg', r_pf.get('method2_kg', 0)) if sp.column_step == 12 else 0

        # 5. Подкрановые балки
        r_pb = self.calc_podkranovye_balki(sp, length)
        results['Подкрановые балки'] = r_pb
        G_pb = r_pb.get('method1_kg_per_beam', 2500) if r_pb else 2500

        # 6. Колонны
        r_k = self.calc_columns(sp, length, g_pr_kN, g_f_kN, g_pf, G_pb)
        results['Колонны'] = r_k

        return results

    def calculate(self, p: InputParams) -> Dict[str, Any]:
        """Полный расчет. Возвращает итоговую таблицу."""
        self._load_tables()
        results = {}
        try:
            span_results_list = []
            for i, sp in enumerate(p.spans):
                span_name = f"Пролёт {i + 1} (L={sp.span_L:.0f}м)"
                span_res = self._calc_span(sp, p.length)
                span_results_list.append((span_name, span_res))

            results['_spans'] = span_results_list
            results['Фахверк'] = self.calc_fachwerk(p.spans, p.length)
            results['Опоры трубопроводов'] = self.calc_opory_truboprovodov(p.spans, p.length)

            # Суммирование итогов
            total_kg = 0
            for span_name, span_res in span_results_list:
                for k, v in span_res.items():
                    if isinstance(v, dict):
                        total_kg += v.get('total_kg', 0) or 0
            total_kg += results['Фахверк'].get('total_kg', 0)
            total_kg += results['Опоры трубопроводов'].get('total_kg', 0)

            area = p.length * p.width
            results['_total_kg'] = total_kg
            results['_area'] = area
            results['_kg_m2'] = total_kg / area if area > 0 else 0

        except Exception as e:
            import traceback
            results['_error'] = str(e)
            results['_traceback'] = traceback.format_exc()
        return results
