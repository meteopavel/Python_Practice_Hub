# -*- coding: utf-8 -*-
"""Тир A — чистая логика многоступенчатых подсказок без HTTP/WS.

Покрывает:
- ``_level_state`` — конечный автомат статусов уровня (locked/ready/waiting/
  revealed) в зависимости от того, какие уровни уже раскрыты и сколько времени
  прошло с раскрытия предыдущего;
- ``can_reveal`` — публичный предикат «можно ли раскрыть уровень сейчас»;
- ``render_markdown`` — мини-markdown рендерер тьюторских текстов.

Время «сейчас» в проде берётся из БД (``SELECT NOW()``, см. ``_now``), чтобы
быть независимым от зоны инстанса. В тестах на это не полагаемся: ``_now``
мокается фикстурой ``frozen_now`` — так задержки 7/15 мин проверяются
детерминированно, без реального сна и без зависимости от того, что SQLite не
умеет ``NOW()`` в виде, ожидаемом кодом под MySQL."""
from datetime import datetime, timedelta, timezone

import pytest

from webapp.content import hints


# --- Вспомогательное ---------------------------------------------------------

@pytest.fixture
def frozen_now(monkeypatch):
    """Фиксированное «сейчас» для детерминированных проверок тайминга.

    Возвращает точку отсчёта и позволяет тесту сдвигать её вручную через
    ``frozen_now.tick(minutes=...)``. ``_now`` в hints всегда видит текущее
    значение — и ``_level_state`` (через аргумент now), и ``can_reveal``
    (который сам зовёт ``_now(db)``).

    ВАЖНО: ``_now`` в проде возвращает naive-время из ``SELECT NOW()`` (см.
    докстринг hints.py:52-59), а ``revealed_at`` тоже naive. Мок даёт naive,
    чтобы тесты ``_level_state``/``can_reveal`` работали в том же контракте, что
    и реальный прогон (и не падали на aware/naive-сравнении в Тире B)."""
    start = datetime(2026, 1, 1, 12, 0, 0)  # naive — как SELECT NOW() в проде

    class Clock:
        def __init__(self):
            self.value = start

        def tick(self, **kwargs):
            self.value += timedelta(**kwargs)

    clock = Clock()
    # can_reveal зовёт _now(db); подменяем именно модульную ссылку.
    monkeypatch.setattr(hints, "_now", lambda db: clock.value)
    return clock


# --- _level_state ------------------------------------------------------------

class TestLevelState:
    """``_level_state(level, revealed, now)`` → (status, available_at|None).

    Инварианты из hints.py:83-107:
      revealed — уже раскрыт;
      level 1 — ready сразу (задержки нет);
      prev не раскрыт — locked;
      задержка с prev не прошла — waiting + available_at;
      иначе ready.
    """

    def test_level1_ready_when_nothing_revealed(self, frozen_now):
        status, available_at = hints._level_state(1, {}, frozen_now.value)
        assert status == "ready"
        assert available_at is None

    def test_level1_revealed_takes_precedence_over_ready(self, frozen_now):
        # Если уровень уже раскрыт — статус revealed, даже для первого.
        revealed_at = frozen_now.value - timedelta(minutes=1)
        status, available_at = hints._level_state(1, {1: revealed_at}, frozen_now.value)
        assert status == "revealed"
        assert available_at is None

    def test_level2_locked_without_level1(self, frozen_now):
        # Предыдущий уровень не раскрыт → этот locked, ждать нечего.
        status, available_at = hints._level_state(2, {}, frozen_now.value)
        assert status == "locked"
        assert available_at is None

    def test_level2_waiting_before_delay(self, frozen_now):
        # level 1 раскрыт 1 минуту назад, задержка до 2-го — 7 минут → ждём.
        revealed_at = frozen_now.value - timedelta(minutes=1)
        status, available_at = hints._level_state(2, {1: revealed_at}, frozen_now.value)
        assert status == "waiting"
        # available_at = revealed_1 + 7 мин — это абсолютный момент готовности.
        assert available_at == revealed_at + hints.HINT_DELAYS[2]

    def test_level2_ready_after_delay(self, frozen_now):
        # level 1 раскрыт 8 минут назад (> 7) → 2-й уже доступен.
        revealed_at = frozen_now.value - timedelta(minutes=8)
        status, available_at = hints._level_state(2, {1: revealed_at}, frozen_now.value)
        assert status == "ready"
        assert available_at is None

    def test_level2_ready_exactly_at_delay_boundary(self, frozen_now):
        # now == available_at → граница считается готовой (>= в коде).
        revealed_at = frozen_now.value - hints.HINT_DELAYS[2]
        status, available_at = hints._level_state(2, {1: revealed_at}, frozen_now.value)
        assert status == "ready"
        assert available_at is None

    def test_level3_locked_without_level2(self, frozen_now):
        # level 1 раскрыт, но 2-й нет → 3-й locked (опирается на предыдущий).
        revealed_at = frozen_now.value - timedelta(hours=1)
        status, available_at = hints._level_state(3, {1: revealed_at}, frozen_now.value)
        assert status == "locked"
        assert available_at is None

    def test_level3_waiting_before_delay(self, frozen_now):
        revealed_1 = frozen_now.value - timedelta(hours=1)
        revealed_2 = frozen_now.value - timedelta(minutes=2)  # < 15 мин
        status, available_at = hints._level_state(
            3, {1: revealed_1, 2: revealed_2}, frozen_now.value
        )
        assert status == "waiting"
        assert available_at == revealed_2 + hints.HINT_DELAYS[3]

    def test_level3_ready_after_delay(self, frozen_now):
        revealed_1 = frozen_now.value - timedelta(hours=2)
        revealed_2 = frozen_now.value - timedelta(minutes=20)  # > 15 мин
        status, available_at = hints._level_state(
            3, {1: revealed_1, 2: revealed_2}, frozen_now.value
        )
        assert status == "ready"
        assert available_at is None

    def test_level2_revealed_ignores_timing(self, frozen_now):
        # Уже раскрытый уровень остаётся revealed независимо от того, сколько
        # прошло с предыдущего — это защита идемпотентности reveal.
        revealed_at = frozen_now.value - timedelta(seconds=1)
        status, _ = hints._level_state(2, {2: revealed_at}, frozen_now.value)
        assert status == "revealed"


# --- can_reveal --------------------------------------------------------------

class TestCanReveal:
    """``can_reveal(db, user_id, task_id, level)`` → bool. Опирается на
    ``_level_state``: True для ready/revealed, иначе False.

    ``can_reveal`` сам зовёт ``_now(db)`` (мокнуто фикстурой frozen_now) И
    ``get_revealed_levels(db, ...)`` — последний лезет в БД, поэтому тесты
    работают на реальном engine + student, а не на db=None."""

    def test_level1_can_reveal(self, engine, student, frozen_now):
        db = _session(engine)
        try:
            assert hints.can_reveal(db, student.id, task_id=81, level=1) is True
        finally:
            db.close()

    def test_level2_cannot_reveal_when_locked(self, engine, student, frozen_now):
        # level 1 ещё не раскрыт → 2-й locked → нельзя.
        db = _session(engine)
        try:
            assert hints.can_reveal(db, student.id, task_id=81, level=2) is False
        finally:
            db.close()

    def test_already_revealed_is_can_reveal_idempotent(self, engine, student, frozen_now):
        # Идемпотентность на уровне предиката: уже раскрытый уровень «можно
        # раскрыть» (повторный клик не должен падать с 409).
        db = _session(engine)
        try:
            hints.record_reveal(db, student.id, task_id=81, level=1)
            assert hints.can_reveal(db, student.id, task_id=81, level=1) is True
        finally:
            db.close()


def _session(engine):
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


# --- render_markdown ---------------------------------------------------------

class TestRenderMarkdown:
    """Мини-markdown: жирный, инлайн-код, ссылки, списки, блочный код, абзацы.
    HTML-escape применяется ДО подстановки разметки — это важно для XSS-стойкости
    (контент пишет тьютор, но всё равно экранируется)."""

    def test_empty_returns_empty(self):
        assert hints.render_markdown("") == ""

    def test_bold(self):
        out = hints.render_markdown("**жирный**")
        assert "<strong>жирный</strong>" in out

    def test_inline_code(self):
        out = hints.render_markdown("`print(1)`")
        assert '<code class="inline">print(1)</code>' in out

    def test_link(self):
        out = hints.render_markdown("[текст](https://example.com)")
        assert '<a href="https://example.com" target="_blank" rel="noopener">текст</a>' in out

    def test_link_rejects_javascript_protocol(self):
        # Только http(s):// — javascript:/data: не проходят регулярку, остаются
        # текстом (защита от протокол-инъекции из контента тьютора).
        out = hints.render_markdown("[x](javascript:alert(1))")
        assert "<a " not in out

    def test_unordered_list_dash(self):
        out = hints.render_markdown("- первый\n- второй")
        assert "<ul>" in out and "</ul>" in out
        assert "<li>первый</li>" in out
        assert "<li>второй</li>" in out

    def test_unordered_list_asterisk(self):
        out = hints.render_markdown("* первый\n* второй")
        assert "<li>первый</li>" in out and "<li>второй</li>" in out

    def test_fenced_code_block(self):
        md = "```\nx = 1\ny = 2\n```"
        out = hints.render_markdown(md)
        assert '<pre class="block"><code>' in out
        assert "x = 1" in out and "y = 2" in out

    def test_indented_code_block(self):
        md = "    x = 1\n    y = 2"
        out = hints.render_markdown(md)
        assert '<pre class="block"><code>' in out
        assert "x = 1" in out

    def test_paragraph(self):
        out = hints.render_markdown("Просто текст.")
        assert out.startswith("<p>") and out.endswith("</p>")
        assert "Просто текст." in out

    def test_html_escaped_in_text(self):
        # Сырой тег из контента не должен пройти как HTML.
        out = hints.render_markdown("<script>alert(1)</script>")
        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    def test_html_escaped_in_code_block(self):
        out = hints.render_markdown("```\n<b>x</b>\n```")
        assert "<b>x</b>" not in out
        assert "&lt;b&gt;" in out

    def test_multiple_blocks(self):
        # Проверка, что блоки разных типов склеиваются корректно.
        md = "Абзац\n\n- пункт\n\n`код`"
        out = hints.render_markdown(md)
        assert "<p>" in out
        assert "<ul>" in out
        assert "inline" in out
