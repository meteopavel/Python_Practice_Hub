# -*- coding: utf-8 -*-
"""Grading engine: сверяет код ученика с эталонным решением на курированных
тестовых входах. Это единственное место, где 'правильность' определяется —
через исполнение, а не через доверие к модели.

Сам код ученика здесь НЕ выполняется — это ушло в executor/ (отдельный
сервис на роутере, за тоннелем). Здесь только оркестрация: эталон + запрос
к исполнителю + сравнение."""
import copy
import json
import os

import httpx

from bot_bridge import get_solver
from test_cases import TEST_CASES

EXECUTOR_URL = os.environ.get("EXECUTOR_URL", "http://127.0.0.1:8010")


class ExecutorUnavailable(Exception):
    pass


def _run_student_code(code: str, test_input) -> dict:
    try:
        response = httpx.post(
            f"{EXECUTOR_URL}/run",
            json={"code": code, "test_input": test_input},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        raise ExecutorUnavailable(str(exc)) from exc


def _normalize(value):
    """Эталон вызывается в процессе напрямую (без сериализации), а решение
    ученика приходит через JSON и тем самым теряет типы вроде tuple (JSON
    их не различает от list). Прогоняем эталон через тот же JSON-круглый
    обмен, чтобы сравнение было честным по обе стороны."""
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def run_free(code: str) -> dict:
    """Свободный запуск кода без сверки с эталоном — для подсказки, где
    тьютору нужно просто показать вывод print(), а не пройти тесты."""
    try:
        response = httpx.post(f"{EXECUTOR_URL}/run_free", json={"code": code}, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return {"ok": False, "error": "Запуск кода временно недоступен. Попробуй чуть позже."}


def grade(task_id: int, code: str) -> dict:
    test_inputs = TEST_CASES.get(task_id)
    if not test_inputs:
        return {"error": f"Для задания {task_id} пока нет тестовых наборов в веб-грейдере"}

    oracle = get_solver(task_id)
    if oracle is None:
        return {"error": f"Эталонное решение solve_task_{task_id} не найдено"}

    results = []
    passed = 0
    for test_input in test_inputs:
        expected = _normalize(oracle(copy.deepcopy(test_input)))
        try:
            outcome = _run_student_code(code, copy.deepcopy(test_input))
        except ExecutorUnavailable:
            return {"error": "Проверка кода временно недоступна. Попробуй чуть позже."}

        if not outcome.get("ok"):
            results.append({
                "input": _normalize(test_input),
                "passed": False,
                "error": outcome.get("error"),
            })
            continue

        actual = outcome.get("value")
        is_correct = actual == expected
        passed += int(is_correct)
        results.append({
            "input": _normalize(test_input),
            "passed": is_correct,
            "expected": expected,
            "actual": actual,
        })

    return {
        "task_id": task_id,
        "total": len(test_inputs),
        "passed": passed,
        "all_passed": passed == len(test_inputs),
        "results": results,
    }
