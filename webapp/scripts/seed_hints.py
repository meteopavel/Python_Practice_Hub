# -*- coding: utf-8 -*-
"""Одноразовая загрузка курированных подсказок для заданий 0 и 81..100.

Запуск (внутри контейнера app на Frankfurt, WORKDIR=/app):
    docker compose exec app python -m webapp.scripts.seed_hints

Идемпотентно: для каждой пары (task_id, level) делает upsert — повторный
запуск обновит тексты, не создавая дублей (UNIQUE(task_id, level) в модели
Hint). Если тьютор уже отредактировал подсказку через админку, этот скрипт
ПЕРЕЗАПИШЕТ её — поэтому запускать стоит только для начального наполнения
или осознанного сброса к эталонному тексту.

Три уровня на задание:
  1 — абстракция: куда двигаться, на что обратить внимание.
  2 — конкретика со ссылками на документацию Python.
  3 — почти готовое решение с пометками TODO что доделать.

Формат контента — markdown (см. content/hints.py render_markdown).
"""
from webapp.core.db import Base, SessionLocal, engine
import webapp.core.models  # noqa: F401 — регистрирует все таблицы в Base.metadata (нужно для create_all)
from webapp.core.models import Hint

# task_id -> {level -> markdown}
HINTS_DATA: dict[int, dict[int, str]] = {
    # 0 — служебная тестовая задача (feat.2): на ней тьютор и ученик
    # отрабатывают механику проекта, в т.ч. панель подсказок. Содержание
    # простое, как и сама задача («сумма списка»), — цель не научить, а дать
    # рабочий контент всех трёх уровней для прогона UI.
    0: {
        1: "Нужно сложить все элементы списка. Заведи переменную-аккумулятор (начни с 0) и проходи по списку циклом, добавляя каждый элемент.",
        2: "Заведи `result = 0`, в цикле `for x in data:` делай `result += x`.\n\n- [Цикл for](https://docs.python.org/3/tutorial/controlflow.html#for-statements)",
        3: "```python\nresult = 0\nfor x in data:\n    result += ...  # TODO: что добавить?\nreturn result\n```",
    },
    81: {
        1: "Подумай, как пройти по списку и для каждой позиции взять **текущий и следующий** элемент. Сколько всего пар получится для списка длины n? Кортеж (пара) записывается круглыми скобками: `(a, b)`.",
        2: "Перебирай индексы `i` от 0 до `len(data) - 1`, бери `data[i]` и `data[i + 1]`. Это удобно собрать через генератор списка.\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges) — диапазон индексов\n- [Кортежи](https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences)",
        3: "```python\nresult = []\nfor i in range(len(data) - 1):\n    result.append(...)  # TODO: кортеж из data[i] и data[i + 1]\nreturn result\n```",
    },
    82: {
        1: "В арифметической прогрессии **разность между соседними элементами постоянна**. Найди эту разность по первым двум элементам и проверь, что она одинакова для всех пар. Не забудь списки длины 0 и 1 — они прогрессия по определению.",
        2: "Разность `d = data[1] - data[0]`. В цикле проверь все пары `data[i] - data[i-1]`. Верни строку с эмодзи точно как в примере (`✅ Да` / `❌ Нет`).\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\nif len(data) < 2:\n    return '✅ Да'\nd = data[1] - data[0]\nfor i in range(1, len(data)):\n    if data[i] - data[i - 1] != ...:  # TODO: с чем сравнить разность?\n        return '❌ Нет'\nreturn ...  # TODO: что вернуть, если все разности равны d?\n```",
    },
    83: {
        1: "Для каждого слова посчитай количество гласных букв и запоминай лучшее. Гласные — это `a, e, i, o, u` (и заглавные). Подумай, как одной строкой посчитать гласные в слове.",
        2: "`sum(1 for ch in word if ch in 'aeiouAEIOU')` считает гласные. Храни `best_word` и `best_count`, обновляй когда нашёл больше.\n\n- [Генераторные выражения](https://docs.python.org/3/tutorial/classes.html#generator-expressions)",
        3: "```python\nvowels = 'aeiouAEIOU'\nbest_word = data[0]\nbest_count = sum(1 for ch in data[0] if ch in vowels)\nfor word in data[1:]:\n    count = ...  # TODO: посчитать гласные в word\n    if count > ...:  # TODO: условие обновления лучшего\n        best_count = count\n        best_word = word\nreturn best_word\n```",
    },
    84: {
        1: "Внимательно с нумерацией: «нечётные позиции» в условии (1, 3, 5... при счёте с единицы) соответствуют **чётным индексам** 0, 2, 4... в Python (индексация с нуля). Значит оставить надо элементы с чётными индексами.",
        2: "`enumerate(data)` даёт пары `(индекс, значение)`. Бери те, где индекс чётный (`i % 2 == 0`).\n\n- [enumerate](https://docs.python.org/3/library/functions.html#enumerate)",
        3: "```python\nreturn [item for i, item in enumerate(data) if ...]  # TODO: условие на i (чётный индекс)\n```",
    },
    85: {
        1: "Для каждого слова в списке нужна его **перевёрнутая версия**. Какой способ перевернуть строку в Python самый короткий? Подсказка: это связано со срезами.",
        2: "Срез `word[::-1]` переворачивает строку (отрицательный шаг). Примени его к каждому элементу списка через генератор списка.\n\n- [Срезы строк](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nreturn [word[...] for word in data]  # TODO: какой срез переворачивает строку?\n```",
    },
    86: {
        1: "Для каждого числа посчитай **сумму его цифр** и найди число с максимумом. Как превратить число в его цифры? Не забудь отрицательные — бери модуль.",
        2: "`sum(int(d) for d in str(abs(n)))` — сумма цифр. `abs()` для отрицательных. Сравнивай суммы, запоминай лучшее число.\n\n- [abs](https://docs.python.org/3/library/functions.html#abs)",
        3: "```python\ndef digit_sum(n):\n    return sum(int(d) for d in str(abs(n)))\nbest = data[0]\nbest_sum = digit_sum(data[0])\nfor num in data[1:]:\n    s = ...  # TODO: сумма цифр num\n    if s > ...:  # TODO: условие обновления\n        best_sum = s\n        best = num\nreturn best\n```",
    },
    87: {
        1: "Посчитай отдельно количество чётных и нечётных чисел, затем сравни. Как определить чётность числа одним действием?",
        2: "`x % 2 == 0` — число чётное. Чётные можно сложить, нечётные = `len(data) - чётные`. Сравни и верни строку с эмодзи.",
        3: "```python\neven = sum(1 for x in data if ...)  # TODO: условие чётности\nodd = len(data) - even\nreturn '✅ Одинаково' if ... else '❌ Не одинаково'  # TODO: условие равенства\n```",
    },
    88: {
        1: "Остаток от деления на 3 бывает только 0, 1 или 2. Для каждого числа определи остаток и добавь число в нужную группу. Какая структура данных подходит для соответствия «ключ → список значений»?",
        2: "Словарь: `result.setdefault(key, []).append(num)`. Ключ — это `num % 3`.\n\n- [dict.setdefault](https://docs.python.org/3/library/stdtypes.html#dict.setdefault)",
        3: "```python\nresult = {}\nfor num in data:\n    key = ...  # TODO: остаток от деления на 3\n    result.setdefault(key, []).append(...)  # TODO: что добавить?\nreturn result\n```",
    },
    89: {
        1: "Префикс длины k — это **первые k букв** слова. Для `'code'` нужны `'c'`, `'co'`, `'cod'`, `'code'`. Какие значения k нужно перебрать?",
        2: "Срез `word[:k]` даёт префикс длины k. Перебери k от 1 до `len(word)` включительно.\n\n- [Срезы строк](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nword = data[0]\nreturn [word[:i] for i in range(...)]  # TODO: диапазон от 1 до len(word) включительно\n```",
    },
    90: {
        1: "Суффикс с позиции i — это **слово начиная с i-й буквы до конца**. Для `'code'`: `'code'`, `'ode'`, `'de'`, `'e'`. Какие i перебрать?",
        2: "Срез `word[i:]` даёт суффикс с позиции i. Перебери i от 0 до `len(word) - 1`.\n\n- [Срезы строк](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nword = data[0]\nreturn [word[i:] for i in range(...)]  # TODO: диапазон от 0 до len(word) - 1\n```",
    },
    91: {
        1: "Если общая сумма нечётная — разбить точно **нельзя** (половина будет дробной). Иначе ищи подмножество с суммой, равной половине общей. Это классическая задача о сумме подмножеств.",
        2: "Перебери все подмножества через битовые маски (`2^n` вариантов, ок для маленьких списков). Для каждой маски проверь сумму элементов, чьи биты установлены.\n\n- [Побитовые операции](https://docs.python.org/3/reference/expressions.html#binary-bitwise-operators)",
        3: "```python\ntotal = sum(data)\nif total % 2 != 0:\n    return '❌ Нельзя'\ntarget = total // 2\nn = len(data)\nfor mask in range(1 << n):\n    s = sum(data[i] for i in range(n) if mask & (...))  # TODO: что сдвинуть, чтобы проверить бит i?\n    if s == target:\n        return '...'  # TODO: какой ответ?\nreturn '❌ Нельзя'\n```",
    },
    92: {
        1: "Нужно взять пары: (первый, последний), (второй, предпоследний) и так далее **до середины**. Сколько таких пар для списка длины n? Подумай про индекс «зеркального» элемента.",
        2: "Для i от 0 до `n // 2 - 1`: пара `(data[i], data[n - 1 - i])`. Собирай в список кортежей.\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\nn = len(data)\nreturn [(data[i], data[...]) for i in range(n // 2)]  # TODO: индекс зеркального элемента\n```",
    },
    93: {
        1: "Нужно построить словарь, где ключ — слово, а значение — его длина. Какая функция даёт длину строки? Это можно записать одной строкой через dict comprehension.",
        2: "`len(word)` — длина. Dict comprehension: `{word: len(word) for word in data}`.\n\n- [Словари и comprehensions](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)",
        3: "```python\nreturn {word: ... for word in data}  # TODO: длина слова\n```",
    },
    94: {
        1: "Элемент «больше соседей», если он **больше и левого, и правого**. Первую и последнюю позиции не проверяем (у них нет двух соседей). Перебирай только внутренние элементы.",
        2: "Для i от 1 до `len(data) - 2`: условие `data[i] > data[i - 1] and data[i] > data[i + 1]`. Собирай подходящие в список.\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\nresult = []\nfor i in range(1, len(data) - 1):\n    if data[i] > data[...] and data[i] > data[...]:  # TODO: левый и правый соседи\n        result.append(data[i])\nreturn result\n```",
    },
    95: {
        1: "Для каждого слова возьми **первую и последнюю букву** и соедини их в новую строку. Как получить первый и последний символ строки?",
        2: "`word[0]` — первая буква, `word[-1]` — последняя. Конкатенация: `word[0] + word[-1]`.\n\n- [Индексация строк](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nreturn [word[...] + word[...] for word in data]  # TODO: первая [0] и последняя [-1] буквы\n```",
    },
    96: {
        1: "Идём по списку и оставляем элемент, **только если он отличается от предыдущего добавленного**. С какого элемента начать? Что сравнивать? Пустой список — отдельный случай.",
        2: "Заведи `result = [data[0]]`. Для каждого следующего: добавляй, если `item != result[-1]` (последнему добавленному).\n\n- [Списки и индексация](https://docs.python.org/3/tutorial/datastructures.html#more-on-lists)",
        3: "```python\nif not data:\n    return []\nresult = [data[0]]\nfor item in data[1:]:\n    if item != result[...]:  # TODO: с чем сравнить (последний добавленный)?\n        result.append(item)\nreturn result\n```",
    },
    97: {
        1: "Считай длину **текущей серии** одинаковых подряд идущих элементов. Когда элемент меняется — сбрасывай счётчик в 1. Постоянно запоминай максимум.",
        2: "Храни `cur` (текущая длина серии) и `best` (максимум). Если `data[i] == data[i-1]`: `cur += 1`, иначе `cur = 1`. Обновляй `best = max(best, cur)`.\n\n- [max](https://docs.python.org/3/library/functions.html#max)",
        3: "```python\nif not data:\n    return 0\nbest = cur = 1\nfor i in range(1, len(data)):\n    if data[i] == data[...]:  # TODO: с чем сравнить (предыдущий)?\n        cur += 1\n        best = max(best, cur)\n    else:\n        cur = ...  # TODO: сбросить счётчик\nreturn best\n```",
    },
    98: {
        1: "Попробуй **удалить каждый элемент по очереди** и проверь, стал ли оставшийся список строго возрастающим. Если хоть один вариант сработал — ответ «можно».",
        2: "Вспомогательная функция `is_increasing(lst)`: `all(lst[i] < lst[i+1] for всех i)`. Для каждого i проверь `data[:i] + data[i+1:]` (выкидываем i-й элемент срезами).\n\n- [all](https://docs.python.org/3/library/functions.html#all)\n- [Срезы списков](https://docs.python.org/3/tutorial/introduction.html#lists)",
        3: "```python\ndef is_increasing(lst):\n    return all(lst[i] < lst[i + 1] for i in range(len(lst) - 1))\nfor i in range(len(data)):\n    if is_increasing(data[:i] + data[...]):  # TODO: как выкинуть i-й элемент?\n        return '✅ Можно'\nreturn '❌ Нельзя'\n```",
    },
    99: {
        1: "Нужны подсписки увеличивающейся длины: первый длины 1, второй длины 2 и т.д. Отрезай от `data` куски, **следя за текущей позицией** и увеличивая длину на 1 каждый шаг.",
        2: "`result.append(data[i:i + length])`, затем `i += length`, `length += 1`. Повторяй, пока `i < len(data)`.\n\n- [Срезы списков](https://docs.python.org/3/tutorial/introduction.html#lists)",
        3: "```python\nresult = []\ni = 0\nlength = 1\nwhile i < len(data):\n    result.append(data[...])  # TODO: срез длины length начиная с i\n    i += length\n    length += 1\nreturn result\n```",
    },
    100: {
        1: "Сначала **посчитай, сколько раз встречается каждый элемент**. Потом собери те, у кого счётчик больше 1, без повторов в ответе (и желательно сохраняя порядок первого появления).",
        2: "Словарь счётчиков: `counts[x] = counts.get(x, 0) + 1`. Затем проходи по `data` (чтобы сохранить порядок) и добавляй в результат, если `counts[x] > 1` и `x` ещё не в результате.\n\n- [dict.get](https://docs.python.org/3/library/stdtypes.html#dict.get)",
        3: "```python\ncounts = {}\nfor x in data:\n    counts[x] = counts.get(x, 0) + 1\nresult = []\nfor x in data:\n    if counts[x] > ... and x not in result:  # TODO: условие (> 1) и проверка дубля\n        result.append(x)\nreturn result\n```",
    },
}


def main() -> None:
    Base.metadata.create_all(bind=engine)  # на случай запуска до старта приложения
    db = SessionLocal()
    created = updated = 0
    try:
        for task_id, levels in HINTS_DATA.items():
            for level, content in levels.items():
                row = db.query(Hint).filter(Hint.task_id == task_id, Hint.level == level).first()
                if row is None:
                    db.add(Hint(task_id=task_id, level=level, content=content))
                    created += 1
                else:
                    row.content = content
                    updated += 1
        db.commit()
        total = len(HINTS_DATA) * 3
        print(f"✅ Подсказки загружены: создано {created}, обновлено {updated} (всего {total} = {len(HINTS_DATA)} задач × 3 уровня)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
