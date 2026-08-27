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

from webapp.grading.bot_bridge import get_solver
from webapp.grading.test_cases import TEST_CASES

EXECUTOR_URL = os.environ.get("EXECUTOR_URL", "http://127.0.0.1:8010")


class ExecutorUnavailable(Exception):
    """Исполнитель (executor на роутере) не ответил — проверка невозможна.
    Это системный сбой, а не вина ученика: попытка в этом случае не пишется."""

    pass


def _run_student_code(code: str, test_input) -> dict:
    """Один прогон кода ученика в исполнителе на заданном входе; сетевой сбой
    на роутере/тоннеле → ExecutorUnavailable."""
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


def run_with_sample(task_id: int, code: str) -> dict:
    """«Запустить» у ученика: код гоняется через тот же харнесс, что и при
    проверке, с первым курированным входом — без сверки с эталоном. Без этого
    решение-задание (def solve(data)) молча не печатало ничего: solve() никто
    не звал (bug.4). Возвращает вход, print-вывод и результат solve()."""
    test_inputs = TEST_CASES.get(task_id)
    if not test_inputs:
        return run_free(code)
    try:
        outcome = _run_student_code(code, copy.deepcopy(test_inputs[0]))
    except ExecutorUnavailable:
        return {"ok": False, "error": "Запуск кода временно недоступен. Попробуй чуть позже."}
    outcome["input"] = _normalize(test_inputs[0])
    return outcome


def grade(task_id: int, code: str) -> dict:
    """Проверка решения: каждый тестовый вход прогоняется и в исполнителе
    (код ученика), и в эталоне; сравнение — после JSON-нормализации типов
    (_normalize). Возвращает {'all_passed', 'total', 'passed', 'results'};
    системные проблемы (нет тестов/эталона, исполнитель лежит) — {'error': …}
    без 'all_passed', по ним попытка не записывается."""
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
