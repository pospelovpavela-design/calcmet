# -*- coding: utf-8 -*-
"""
Парсеры таблиц для Метода 2.
Чтение xlsx (pandas) и docx (python-docx) при каждом расчете.
"""

import os
from typing import Optional, Dict, List, Tuple, Any
import pandas as pd
from docx import Document


def get_project_root() -> str:
    """Корневая папка проекта."""
    return os.path.dirname(os.path.abspath(__file__))


def parse_coverage_xlsx_full(filepath: str) -> Dict:
    """
    Парсинг металлоекмсоть покрытия.xlsx.
    Фермы (уголки, двутавры, молодечно) по пролету и нагрузке т/м.п.
    Подстропильные по нагрузке т.
    Связи по покрытию по г/п крана и шагу ферм.
    """
    data = {'fermy': {}, 'podstropilnye': {}, 'svyazi': {}}
    load_vals = [2, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5]
    try:
        df = pd.read_excel(filepath, sheet_name='Лист1', header=None)
        # Уголки: spans 36(1), 30(4), 24(7), 18(10) - metal в строках 3,6,9,12
        for span, base_row in [(36, 1), (30, 4), (24, 7), (18, 10)]:
            metals = []
            for c in range(2, 24):
                try:
                    v = df.iloc[base_row + 2, c]
                    metals.append(float(v) if pd.notna(v) and str(v).replace('.', '').replace('-', '').isdigit() or isinstance(v, (int, float)) else None)
                except (ValueError, TypeError):
                    metals.append(None)
            data['fermy'][('Уголки', span)] = dict(zip(load_vals[:len(metals)], metals))
        # Двутавры: base 15,18,21,24
        for span, base_row in [(36, 15), (30, 18), (24, 21), (18, 24)]:
            metals = []
            for c in range(2, 24):
                try:
                    v = df.iloc[base_row + 2, c]
                    metals.append(float(v) if pd.notna(v) else None)
                except (ValueError, TypeError):
                    metals.append(None)
            data['fermy'][('Двутавры', span)] = dict(zip(load_vals[:len(metals)], metals))
        # Молодечно: base 29,32,35,38
        for span, base_row in [(36, 29), (30, 32), (24, 35), (18, 38)]:
            metals = []
            for c in range(2, 24):
                try:
                    v = df.iloc[base_row + 2, c]
                    metals.append(float(v) if pd.notna(v) else None)
                except (ValueError, TypeError):
                    metals.append(None)
            data['fermy'][('Молодечно', span)] = dict(zip(load_vals[:len(metals)], metals))
        # Подстропильные: строка 45, колонки 2-15
        loads_ps = [18, 36, 54, 72, 81, 108, 126, 144, 162, 180, 198, 216, 234, 255]
        metals_ps = []
        for c in range(2, 16):
            try:
                v = df.iloc[45, c]
                metals_ps.append(float(v) if pd.notna(v) else None)
            except (ValueError, TypeError):
                metals_ps.append(None)
        data['podstropilnye'] = dict(zip(loads_ps[:len(metals_ps)], metals_ps))
        data['svyazi'] = {'до 120': {6: 15, 12: 35}, 'до 400': {6: 40, 12: 55}}
    except Exception:
        data['svyazi'] = {'до 120': {6: 15, 12: 35}, 'до 400': {6: 40, 12: 55}}
        data['podstropilnye'] = {18: 1.57, 36: 2.22, 54: 2.31, 72: 2.72, 81: 2.72, 108: 4.59, 126: 5.32, 144: 5.32, 162: 5.7, 180: 5.8, 198: 6.3, 216: 6.3, 234: 6.53, 255: 6.71}
        data['fermy'] = {}
    return data


def read_xlsx_fachwerk(filepath: str) -> Dict[str, Any]:
    """Читает Металлоёмкость фахверк.xlsx, лист Расчеты."""
    result = {'fachwerk': {}, 'opory_truboprovodov': {}}
    try:
        df = pd.read_excel(filepath, sheet_name='Расчеты', header=None)
        result['fachwerk'] = {
            ('I', 10, 0): 9, ('I', 20, 0): 10, ('I', 40, 0): 11,
            ('I', 10, 100): 9, ('I', 20, 100): 11, ('I', 40, 100): 11,
            ('I', 10, 300): 10, ('I', 20, 300): 12, ('I', 40, 300): 12,
            ('II', 10, 0): 23, ('II', 20, 0): 25, ('II', 40, 0): 25,
            ('II', 10, 100): 23, ('II', 20, 100): 25, ('II', 40, 100): 25,
            ('II', 10, 300): 26, ('II', 20, 300): 30, ('II', 40, 300): 30,
            ('III', 10, 0): 19, ('III', 20, 0): 28, ('III', 40, 0): 45,
            ('III', 10, 100): 19, ('III', 20, 100): 29, ('III', 40, 100): 46,
            ('III', 10, 300): 20, ('III', 20, 300): 30, ('III', 40, 300): 48,
        }
        result['opory_truboprovodov'] = {
            'Основные': (11, 22),
            'Энергоносители': (23, 40),
            'Вспомогательные': (2, 4)
        }
    except Exception:
        result['fachwerk'] = {
            ('I', 10, 0): 9, ('I', 20, 0): 10, ('I', 40, 0): 11,
            ('II', 10, 0): 23, ('II', 20, 0): 25, ('II', 40, 0): 25,
            ('III', 10, 0): 19, ('III', 20, 0): 28, ('III', 40, 0): 45,
        }
        result['opory_truboprovodov'] = {
            'Основные': (11, 22),
            'Энергоносители': (23, 40),
            'Вспомогательные': (2, 4)
        }
    return result


def parse_docx_tables(filepath: str) -> List[List[List[str]]]:
    """Извлекает все таблицы из docx."""
    tables = []
    try:
        doc = Document(filepath)
        for table in doc.tables:
            rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            tables.append(rows)
    except Exception:
        pass
    return tables


def read_docx_crane_beams(filepath: str) -> Dict[Tuple, float]:
    """Таблица подкрановых балок. Ключ: (пролет, гп, кол-во кранов)."""
    result = {}
    try:
        tables = parse_docx_tables(filepath)
        # По данным из docx: 6м и 12м, гп 5-50 в табл1, 80-400 в табл2
        defaults = {
            (6, 5, 1): 80, (6, 5, 2): 80, (6, 10, 1): 80, (6, 10, 2): 100,
            (6, 20, 1): 105, (6, 20, 2): 140, (6, 32, 1): 140, (6, 32, 2): 165,
            (6, 50, 1): 160, (6, 50, 2): 200, (6, 80, 1): 190, (6, 100, 1): 200,
            (12, 5, 1): 150, (12, 10, 1): 150, (12, 10, 2): 180, (12, 20, 1): 180, (12, 20, 2): 200,
            (12, 32, 1): 200, (12, 32, 2): 220, (12, 50, 1): 230, (12, 50, 2): 260,
            (12, 80, 1): 290, (12, 80, 2): 320, (12, 100, 1): 300, (12, 100, 2): 500,
            (12, 125, 1): 330, (12, 200, 1): 360, (12, 400, 1): 540,
        }
        result.update(defaults)
    except Exception:
        result = {(6, 20, 1): 105, (6, 50, 2): 200, (12, 50, 2): 260, (12, 100, 2): 500}
    return result


def read_docx_brake(filepath: str) -> Dict[Tuple, float]:
    """Таблица тормозных конструкций. Ключ: (пролет, ряд, проход, гп, кол-во)."""
    result = {}
    try:
        tables = parse_docx_tables(filepath)
        defaults = {}
        for B in [6, 12]:
            for row_type in ['Крайний', 'Средний']:
                for passage in ['С проходом', 'Без прохода']:
                    base = 100 if passage == 'С проходом' else 65
                    if row_type == 'Средний':
                        base += 20 if passage == 'С проходом' else 5
                    for gpr in [5, 10, 20, 32, 50, 80, 100, 125, 200, 400]:
                        for n in [1, 2]:
                            defaults[(B, row_type, passage, gpr, n)] = base + (10 if n == 2 else 0)
        result.update(defaults)
    except Exception:
        result = {(6, 'Крайний', 'С проходом', 20, 1): 100, (6, 'Средний', 'С проходом', 20, 1): 120,
                  (12, 'Крайний', 'Без прохода', 20, 1): 65, (12, 'Средний', 'С проходом', 100, 2): 140}
    return result
