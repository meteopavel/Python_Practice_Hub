# -*- coding: utf-8 -*-
"""Справочные материалы — учебные ноутбуки (1_introduction/,
2_loops_and_conditions/ и т.д. в `webapp/content/notebooks/`), что и раньше
лежали только как Jupyter-тетрадки. Здесь не БД и не отдельный конвертированный
формат — .ipynb читается напрямую (это просто JSON), один раз при старте
приложения, и держится в памяти. Ноутбуки маленькие (~470KB на все 36),
без картинок/attachments — только code-ячейки, объяснение зашито в них
как строки-докстринги. Собственный парсер вместо nbconvert: контента
слишком мало и однообразно, чтобы тащить чужой шаблон/CSS, который потом
пришлось бы перекраивать под дизайн-систему сайта."""
import json
import re
from pathlib import Path

# Папка с модулями-ноутбуками (1_introduction/, 2_loops_and_conditions/ и т.д.)
# — рядом с этим файлом, в `webapp/content/notebooks/`.
_ROOT = Path(__file__).resolve().parent / "notebooks"

# Заголовки модулей — только 5, руками, без эвристик.
_MODULE_TITLES = {
    "1_introduction": "Введение",
    "2_loops_and_conditions": "Циклы и условия",
    "3_functions": "Функции",
    "4_dicts_and_sets": "Словари и множества",
    "5_strings": "Строки",
}

# Часть ноутбуков начинается сразу с докстринга-объяснения, без
# декоративного баннера "### Название ###" в первой ячейке — для них
# заголовок руками, по содержанию файла.
_TITLE_OVERRIDES = {
    ("1_introduction", "0_venv_install"): "Установка и работа с venv",
    ("1_introduction", "1_intro"): "Дзен Python",
    ("1_introduction", "2_exercise_0"): "Разбор первой программы",
    ("1_introduction", "3_first_code"): "Первая программа",
    ("1_introduction", "13_lists_(extended_version)"): "Списки (расширенная версия)",
    ("3_functions", "25_func_exercises"): "Задачи на функции",
}

_NUM_PREFIX = re.compile(r"^(\d+)_")


def _sort_key(filename: str) -> tuple:
    m = _NUM_PREFIX.match(filename)
    return (int(m.group(1)), filename) if m else (10_000, filename)


def _extract_title(module: str, slug: str, first_cell_source: str) -> str:
    override = _TITLE_OVERRIDES.get((module, slug))
    if override:
        return override
    for line in first_cell_source.split("\n")[:6]:
        stripped = line.strip("# \t")
        if stripped and stripped != '"""':
            return stripped
    return slug.replace("_", " ").capitalize()


def _load_notebook(path: Path) -> list:
    """Возвращает список ячеек: [{"code": str, "output": str|None, "is_error": bool}]."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        output_text = None
        is_error = False
        for out in cell.get("outputs", []):
            output_type = out.get("output_type")
            if output_type == "stream":
                output_text = (output_text or "") + "".join(out.get("text", []))
            elif output_type == "execute_result":
                data = out.get("data", {}).get("text/plain", [])
                output_text = (output_text or "") + "".join(data)
            elif output_type == "error":
                is_error = True
                trace = out.get("traceback", [])
                output_text = (output_text or "") + "\n".join(trace)
        cells.append({"code": source, "output": output_text, "is_error": is_error})
    return cells


def _build_manifest():
    manifest = {}
    notebooks = {}
    for module, title in _MODULE_TITLES.items():
        module_dir = _ROOT / module
        if not module_dir.is_dir():
            continue
        lessons = []
        files = sorted(module_dir.glob("*.ipynb"), key=lambda p: _sort_key(p.name))
        for path in files:
            slug = path.stem
            cells = _load_notebook(path)
            if not cells:
                continue
            lesson_title = _extract_title(module, slug, cells[0]["code"])
            lessons.append({"slug": slug, "title": lesson_title})
            notebooks[(module, slug)] = {"title": lesson_title, "cells": cells}
        if lessons:
            manifest[module] = {"title": title, "lessons": lessons}
    return manifest, notebooks


MATERIALS_MANIFEST, _NOTEBOOKS = _build_manifest()


def get_lesson(module: str, slug: str):
    return _NOTEBOOKS.get((module, slug))
