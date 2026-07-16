# -*- coding: utf-8 -*-
"""Grading engine: сверяет код ученика с эталонным решением на курированных
тестовых входах. Это единственное место, где 'правильность' определяется —
через исполнение, а не через доверие к модели."""
import copy
import json

from bot_bridge import get_solver
from sandbox import run_student_code
from test_cases import TEST_CASES


def _normalize(value):
    """Эталон вызывается в процессе напрямую (без сериализации), а решение
    ученика приходит через JSON и тем самым теряет типы вроде tuple (JSON
    их не различает от list). Прогоняем эталон через тот же JSON-круглый
    обмен, чтобы сравнение было честным по обе стороны."""
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


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
        outcome = run_student_code(code, copy.deepcopy(test_input))

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
