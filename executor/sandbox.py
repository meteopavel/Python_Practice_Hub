# -*- coding: utf-8 -*-
"""Исполнение кода ученика в изолированном процессе.

Это ядро проверки: код ученика никогда не выполняется в процессе веб-сервера.
Он пишется во временный файл, оборачивается в харнесс, который читает вход из
stdin и печатает результат в JSON, и запускается отдельным интерпретатором
python с ограничением по времени, по памяти и с урезанным окружением (чтобы
код ученика не мог прочитать переменные окружения сервера, например токены).

Что сознательно НЕ сделано на этом шаге (осознанный пробел под MVP,
не притворяемся, что его нет): нет сетевой/файловой изоляции (контейнер),
код ученика технически может пойти в сеть или потрогать диск. Это приемлемо,
пока грейдер гоняется локально с одним учеником; для облачного деплоя это
должно быть обёрнуто в Docker (--network none, read-only rootfs) — тот шаг
описан в плане платформы и пока не реализован специально, чтобы не
вайбкодить ядро вслепую."""
import json
import resource
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_SECONDS = 5
CPU_LIMIT_SECONDS = 5
MEMORY_LIMIT_BYTES = 256 * 1024 * 1024  # 256 MB

RESULT_MARKER = "###RESULT###"

HARNESS_TEMPLATE = '''
import copy
import json
import sys

{student_code}

def _main():
    data = json.loads(sys.stdin.read())
    try:
        value = solve(copy.deepcopy(data))
        print({marker!r} + json.dumps({{"ok": True, "value": value}}, ensure_ascii=False, default=str))
    except Exception as exc:
        print({marker!r} + json.dumps({{"ok": False, "error": f"{{type(exc).__name__}}: {{exc}}"}}, ensure_ascii=False))

if __name__ == "__main__":
    _main()
'''


def _limit_resources():
    # preexec_fn выполняется в дочернем процессе после fork, до exec —
    # лимиты применяются только к процессу ученика, не к серверу.
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (CPU_LIMIT_SECONDS, CPU_LIMIT_SECONDS))
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    except (ValueError, OSError):
        pass


def run_student_code(code: str, test_input) -> dict:
    """Ученик обязан определить функцию solve(data). Возвращает
    {"ok": True, "value": ...} либо {"ok": False, "error": "..."}."""
    harness = HARNESS_TEMPLATE.format(student_code=code, marker=RESULT_MARKER)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(harness)
        script_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            input=json.dumps(test_input, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            preexec_fn=_limit_resources,
            env={"PATH": "/usr/bin:/bin"},
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Превышено время выполнения ({TIMEOUT_SECONDS} сек) — проверь на бесконечный цикл"}
    finally:
        Path(script_path).unlink(missing_ok=True)

    idx = proc.stdout.rfind(RESULT_MARKER)
    if idx == -1:
        stderr_tail = proc.stderr.strip()[-800:]
        return {
            "ok": False,
            "error": stderr_tail or "Код не вернул результат — убедись, что функция называется solve(data)",
        }

    try:
        return json.loads(proc.stdout[idx + len(RESULT_MARKER):])
    except json.JSONDecodeError:
        return {"ok": False, "error": "Не удалось разобрать результат выполнения"}


def run_free_code(code: str) -> dict:
    """Свободный запуск без эталона и без ожидания solve(data) — код
    ученика/тьютора выполняется как есть, stdout возвращается как текст.
    Нужен для подсказки, где print('hello') должен просто отработать."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        script_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            input="",
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            preexec_fn=_limit_resources,
            env={"PATH": "/usr/bin:/bin"},
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Превышено время выполнения ({TIMEOUT_SECONDS} сек) — проверь на бесконечный цикл"}
    finally:
        Path(script_path).unlink(missing_ok=True)

    if proc.returncode != 0:
        stderr_tail = proc.stderr.strip()[-800:]
        return {"ok": False, "error": stderr_tail or f"Код завершился с ошибкой (код {proc.returncode})", "stdout": proc.stdout}

    return {"ok": True, "stdout": proc.stdout}
