# -*- coding: utf-8 -*-
"""Многоступенчатые подсказки для заданий 81..100.

Три уровня на каждое задание:
  1 — абстрактная: куда двигаться, на что обратить внимание.
  2 — конкретная со ссылками на материалы/функции; доступна через 7 минут
      после раскрытия 1-й.
  3 — почти готовое решение с пометками что доделать; доступна ещё через
      15 минут после раскрытия 2-й.

Тайминг считается ТОЛЬКО на сервере — по отметкам HintReveal. Клиентскому
таймеру верить нельзя: часы на устройстве ученика тривиально подменить,
поэтому «когда уровень стал доступен» определяется revealed_at предыдущего
уровня, а не временем, пришедшим из браузера.

Контент (Hint) правит тьютор через админку; здесь — только логика доступа
и мини-markdown-рендерер (в духе materials.py: проект избегает тяжёлых
зависимостей)."""
import html
import re
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Hint, HintReveal

# Задания, к которым привязаны подсказки. Это курируемая база, как и
# TEST_CASES: добавить задание = расширить диапазон здесь.
HINTED_TASK_IDS: Iterable[int] = range(81, 101)

LEVELS = (1, 2, 3)

# Задержка от раскрытия предыдущего уровня до доступности следующего.
# Уровень 1 доступен сразу (предыдущего нет).
HINT_DELAYS: dict[int, timedelta] = {
    1: timedelta(0),
    2: timedelta(minutes=7),
    3: timedelta(minutes=15),
}


def has_hints(task_id: int) -> bool:
    return task_id in HINTED_TASK_IDS


def _now(db: Session) -> datetime:
    """«Сейчас» берём ИЗ БД (SELECT NOW()), а не из Python. БД хостинга
    работает в локальной зоне (MSK), её func.now() — локальное время; и
    revealed_at пишется тоже func.now()-сервером. Сравнивая обе стороны в
    зоне БД, мы независимы от того, в какой именно зоне работает инстанс:
    разность корректна всегда. datetime.now(utc) тут использовать нельзя —
    получили бы сдвиг в 3 часа против локального revealed_at."""
    return db.execute(select(func.now())).scalar()


def get_hint_content(db: Session, task_id: int) -> dict[int, str]:
    """Все тексты уровней для задания: {level: markdown}. Уровни без записи
    отсутствуют в словаре (фронт считает их пустыми/незаведёнными)."""
    rows = db.execute(
        select(Hint.level, Hint.content).where(Hint.task_id == task_id)
    ).all()
    return {level: content for level, content in rows}


def get_revealed_levels(db: Session, user_id: int, task_id: int) -> dict[int, datetime]:
    """{level: revealed_at} для уже раскрытых учеником уровней. Время — в
    зоне БД (как есть, без приведения к UTC): сравниваем с _now(db) тоже в
    зоне БД, так обе стороны в одной шкале."""
    rows = db.execute(
        select(HintReveal.level, HintReveal.revealed_at).where(
            HintReveal.user_id == user_id, HintReveal.task_id == task_id
        )
    ).all()
    return {level: revealed_at for level, revealed_at in rows}


def _level_state(level, revealed: dict[int, datetime], now: datetime):
    """Внутренняя: статус одного уровня без контента.

    Возвращает (status, available_at):
      locked   — предыдущий уровень ещё не раскрыт, этот недоступен.
      ready    — доступен к раскрытию учеником (задержка прошла / её нет).
      revealed — уже раскрыт.
      waiting  — задержка ещё не прошла, ждём; available_at — когда станет ready
                 (в зоне БД; для API переводится в UTC отдельно).

    now — «сейчас» в зоне БД (из _now), revealed — тоже в зоне БД: сравнение
    корректно при любой зоне инстанса.
    """
    if level in revealed:
        return "revealed", None
    if level == 1:
        # Первый уровень — без задержки, доступен сразу по клику.
        return "ready", None
    prev = level - 1
    if prev not in revealed:
        return "locked", None
    available_at = revealed[prev] + HINT_DELAYS[level]
    if now >= available_at:
        return "ready", None
    return "waiting", available_at


def _available_at_utc(db: Session, available_at_local: datetime) -> str:
    """Перевод available_at (зона БД, naive) в UTC ISO-строку для API.

    Таймзону инстанса из приложения надёжно не узнать, поэтому вычисляем
    смещение эмпирически: db_offset = NOW(БД) − utcnow(). Для MSK это +3ч.
    Вычитая его из локальной метки, получаем честный абсолютный момент в UTC,
    и фронт рисует корректный обратный отсчёт при любой зоне инстанса."""
    if available_at_local is None:
        return None
    utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_now = _now(db)
    db_offset = db_now - utc_now  # на сколько зона БД «впереди» UTC
    return (available_at_local - db_offset).replace(tzinfo=timezone.utc).isoformat()


def available_levels(db: Session, user_id: int, task_id: int) -> list[dict]:
    """Полное состояние подсказок задания для ученика.

    Контент отдаётся ТОЛЬКО для revealed — остальные уровни ученик не должен
    видеть даже пустыми (статус готовности не должен раскрывать суть).
    available_at (ISO-строка UTC) отдаётся для waiting, чтобы фронт нарисовал
    обратный отсчёт; для waiting сервер — источник правды о готовности,
    фронт по достижении нуля перезапрашивает состояние.
    """
    now = _now(db)
    revealed = get_revealed_levels(db, user_id, task_id)
    content_by_level = get_hint_content(db, task_id)
    result = []
    for level in LEVELS:
        status, available_at = _level_state(level, revealed, now)
        item: dict = {"level": level, "status": status}
        if status == "revealed":
            item["content"] = content_by_level.get(level, "")
        if status == "waiting" and available_at is not None:
            item["available_at"] = _available_at_utc(db, available_at)
        result.append(item)
    return result


def can_reveal(db: Session, user_id: int, task_id: int, level: int) -> bool:
    """Можно ли раскрыть уровень сейчас: не заблокирован предыдущим и
    задержка прошла (или её нет). Уже раскрытый тоже «можно» — идемпотентно."""
    now = _now(db)
    revealed = get_revealed_levels(db, user_id, task_id)
    status, _ = _level_state(level, revealed, now)
    return status in ("ready", "revealed")


def record_reveal(db: Session, user_id: int, task_id: int, level: int) -> None:
    """Фиксируем раскрытие уровня. Идемпотентно: повторный клик по уже
    раскрытому не создаёт дубль (UNIQUE-ограничение) и НЕ сдвигает
    revealed_at — иначе можно было бы обнулить таймер следующего уровня.

    revealed_at НЕ задаём явно — пусть ставит server_default=func.now(),
    то есть локальное время БД. Сравниваем затем с _now(db) (тоже зона БД),
    так обе стороны в одной шкале и зона инстанса не имеет значения.
    Раньше писали datetime.now(utc) и сравнивали с локальным — был сдвиг 3ч."""
    existing = db.execute(
        select(HintReveal).where(
            HintReveal.user_id == user_id,
            HintReveal.task_id == task_id,
            HintReveal.level == level,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    db.add(HintReveal(user_id=user_id, task_id=task_id, level=level))
    db.commit()


# ---------------------------------------------------------------------------
# Markdown-рендерер
# ---------------------------------------------------------------------------
# Минимальный, в духе materials.py. Поддерживает:
#   **жирный**, `инлайн-код`, [текст](url),
#   строки с «- » → маркированный список,
#   блочный код — строки с отступом ≥4 пробелов ИЛИ ```-огороженный блок,
#   пустая строка — разделитель абзацев.
# HTML-escape применяется к сырому тексту ДО подстановки разметки, поэтому
# injected-теги из контента тьютора остаются текстом.

_INLINE_PATTERNS = [
    # Инлайн-код — первым, чтобы внутри не сработали жирный/ссылки.
    (re.compile(r"`([^`]+)`"), r'<code class="inline">\1</code>'),
    # Жирный.
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
]

# Ссылка [текст](url). URL ограничиваем http(s)://, чтобы markdown нельзя
# было превратить в протокол-инъекцию (javascript:, data: и пр.).
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def _render_inline(text: str) -> str:
    # Сначала экранируем всё — дальше подставляем только известные теги с
    # отдельно экранированными значениями (url в href, текст в тело ссылки).
    out = _escape(text)
    out = _LINK_RE.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" target="_blank" rel="noopener">{m.group(1)}</a>',
        out,
    )
    for pattern, replacement in _INLINE_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def render_markdown(text: str) -> str:
    """Рендерит markdown в HTML-фрагмент (без <p>-обёртки верхнего уровня)."""
    if not text:
        return ""

    lines = text.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        raw = lines[i]
        stripped = raw.strip()

        # Пустая строка — разделитель, пропускаем.
        if not stripped:
            i += 1
            continue

        # Блочный код в ограде ``` ... ```.
        if stripped.startswith("```"):
            i += 1
            code_lines: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # пропускаем закрывающую ограду
            blocks.append(f'<pre class="block"><code>{_escape(chr(10).join(code_lines))}</code></pre>')
            continue

        # Блочный код по отступу (≥4 пробелов) — подряд идущие строки.
        if raw.startswith("    "):
            code_lines = []
            while i < n and (lines[i].startswith("    ") or lines[i].strip() == ""):
                # Не включаем хвостовые пустые строки внутрь блока, но
                # прерываем блок, если после пустой идёт не-код.
                if lines[i].strip() == "" and i + 1 < n and not lines[i + 1].startswith("    "):
                    break
                code_lines.append(lines[i][4:] if lines[i].startswith("    ") else "")
                i += 1
            blocks.append(f'<pre class="block"><code>{_escape(chr(10).join(code_lines))}</code></pre>')
            continue

        # Маркированный список: подряд идущие строки «- ...».
        if stripped.startswith("- ") or stripped.startswith("* "):
            items: list[str] = []
            while i < n and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                item_text = lines[i].strip()[2:]
                items.append(f"<li>{_render_inline(item_text)}</li>")
                i += 1
            blocks.append(f"<ul>{''.join(items)}</ul>")
            continue

        # Абзац: собираем подряд идущие непустые строки до разделителя/блока.
        para_lines: list[str] = []
        while i < n:
            cur = lines[i]
            s = cur.strip()
            if not s:
                break
            if s.startswith("```") or cur.startswith("    ") or s.startswith("- ") or s.startswith("* "):
                break
            para_lines.append(s)
            i += 1
        blocks.append(f"<p>{_render_inline(' '.join(para_lines))}</p>")

    return "\n".join(blocks)
