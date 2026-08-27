# -*- coding: utf-8 -*-
"""bug.4: «Запустить» у ученика — режим с данными на входе (task_id).

Раньше код ученика исполнялся как plain-скрипт (stdin пуст, solve() никто не
звал) — любое решение-задание молча давало «Код выполнен» + «(нет вывода)».
Теперь при task_id код гоняется через тот же харнесс, что и при проверке,
с первым курированным входом: фронт получает вход, print-вывод и результат
solve(). Без task_id (редактор подсказки тьютора) — прежнее поведение.

Два тира:
  - sandbox (реальный subprocess, без моков): run_student_code возвращает
    stdout, напечатанный до маркера результата — и при успехе, и при ошибке;
  - HTTP-контракт /api/solve/run_free: ветвление по task_id (исполнитель
    подменён monkeypatch'ем — как внешний сервис он в юнит-тестах недоступен).
"""
from executor.sandbox import run_student_code
from webapp.grading import grading
from webapp.grading.test_cases import TEST_CASES
from webapp.routes import tasks_api


# --- sandbox: stdout до маркера ---------------------------------------------

class TestRunStudentCodeStdout:
    def test_prints_and_value_returned(self):
        # print'ы ученика идут до маркера, результат solve() — после: должны
        # вернуться и то, и другое.
        code = "print('hello')\n\n\ndef solve(data):\n    return sum(data)"
        result = run_student_code(code, [1, 2, 3])
        assert result["ok"] is True
        assert result["value"] == 6
        assert result["stdout"] == "hello\n"

    def test_no_solve_prints_preserved_in_error(self):
        # solve нет — харнесс ловит NameError, но print'ы до него не теряются.
        result = run_student_code("print('scratch')", [1])
        assert result["ok"] is False
        assert "solve" in result["error"]
        assert result["stdout"] == "scratch\n"

    def test_syntax_error_reports_stderr(self):
        result = run_student_code("def solve(data)\n    pass", [1])
        assert result["ok"] is False
        assert "SyntaxError" in result["error"]


# --- HTTP: ветвление /api/solve/run_free по task_id --------------------------

def _patch_run_free(monkeypatch, result):
    # run_free виден через два биндинга: прямой импорт в tasks_api (роут)
    # и глобаль grading (fallback из run_with_sample) — подменяем оба.
    monkeypatch.setattr(tasks_api, "run_free", lambda code: result)
    monkeypatch.setattr(grading, "run_free", lambda code: result)


class TestSolveRunFreeApi:
    def test_unauth_returns_401(self, client):
        r = client.post("/api/solve/run_free", json={"code": "x"})
        assert r.status_code == 401

    def test_with_task_id_runs_harness_on_first_input(self, student_client, monkeypatch):
        task_id = min(TEST_CASES)
        calls = []

        def fake_run(code, test_input):
            calls.append((code, test_input))
            return {"ok": True, "value": 42, "stdout": "hi\n"}

        monkeypatch.setattr(grading, "_run_student_code", fake_run)
        r = student_client.post("/api/solve/run_free", json={"code": "def solve(data): ...", "task_id": task_id})
        assert r.status_code == 200
        body = r.json()
        # Ответ = результат исполнителя + вход, на котором гоняли (для рендера).
        assert body == {"ok": True, "value": 42, "stdout": "hi\n", "input": TEST_CASES[task_id][0]}
        assert calls == [("def solve(data): ...", TEST_CASES[task_id][0])]

    def test_without_task_id_keeps_plain_script_mode(self, student_client, monkeypatch):
        # Режим без входа (когда task_id ещё не выбран / совместимость) —
        # прежний run_free, харнесс не зовётся.
        _patch_run_free(monkeypatch, {"ok": True, "stdout": "hello\n"})
        r = student_client.post("/api/solve/run_free", json={"code": "print('hello')"})
        assert r.status_code == 200
        assert r.json() == {"ok": True, "stdout": "hello\n"}

    def test_unknown_task_id_falls_back_to_plain_mode(self, student_client, monkeypatch):
        _patch_run_free(monkeypatch, {"ok": True, "stdout": ""})
        r = student_client.post("/api/solve/run_free", json={"code": "x", "task_id": 999999})
        assert r.status_code == 200
        assert r.json() == {"ok": True, "stdout": ""}

    def test_executor_unavailable_returns_friendly_error(self, student_client, monkeypatch):
        def raise_unavailable(code, test_input):
            raise grading.ExecutorUnavailable("connection refused")

        monkeypatch.setattr(grading, "_run_student_code", raise_unavailable)
        r = student_client.post("/api/solve/run_free", json={"code": "x", "task_id": min(TEST_CASES)})
        assert r.status_code == 200
        assert r.json() == {"ok": False, "error": "Запуск кода временно недоступен. Попробуй чуть позже."}
