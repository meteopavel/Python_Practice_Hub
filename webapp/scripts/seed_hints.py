# -*- coding: utf-8 -*-
"""Одноразовая загрузка курированных подсказок для заданий 0, 81..100 и 101..120.

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
        1: "Что такое «сумма цифр»? Для числа 123 это 1+2+3 = 6. Для 99 это 9+9 = 18.\nНужно для каждого числа в списке посчитать такую сумму и выбрать то число,\nу которого она самая большая.\n\nЧтобы достать цифры из числа — преврати его в строку через `str()`:\n`str(123)` даёт `'123'`. По этой строке можно пройти циклом `for`, и каждую\nцифру превратить обратно в число через `int()`. Если число отрицательное —\nсначала возьми модуль `abs()`, чтобы минус не мешал.",
        2: "Вот как посчитать сумму цифр числа n (например, 123):\n\n```\ns = 0\nfor d in str(abs(n)):   # идём по '1','2','3'; abs — чтобы минус не мешал\n    s = s + int(d)       # 0+1=1, потом 1+2=3, потом 3+3=6\n```\n\nПройдись так по каждому числу из `data`, запоминай лучшее число и его сумму,\nобновляй когда нашёл больше.\n\n- [str и int](https://docs.python.org/3/library/functions.html#func-str)\n- [abs](https://docs.python.org/3/library/functions.html#abs)",
        3: "```python\nbest = data[0]\nbest_sum = 0\nfor d in str(abs(best)):\n    best_sum = best_sum + int(d)\nfor num in data[1:]:\n    s = 0\n    for d in str(abs(num)):\n        s = s + int(d)\n    if s > ...:   # TODO: с чем сравнить сумму этого числа?\n        best_sum = s\n        best = num\nreturn best\n```",
    },
    87: {
        1: "Чётное число делится на 2 без остатка: 2, 4, 6, 8, 10... Нечётное — нет:\n1, 3, 5, 7, 9...\n\nНужно посчитать отдельно, сколько в списке чётных и сколько нечётных, и\nпроверить, равны ли эти количества. В примере `[1, 2, 3, 4]` чётных два (2,\n4) и нечётных два (1, 3) — поровну, ответ `✅ Одинаково`.\n\nЧётность проверяют через остаток от деления на 2: если остаток 0 — число\nчётное.",
        2: "Остаток от деления в Python — это `%`. Чётность числа x проверяют так:\n`x % 2 == 0` (для чётных это верно).\n\nПосчитай чётные обычным циклом:\n\n```\neven = 0\nfor x in data:\n    if x % 2 == 0:   # условие чётности\n        even = even + 1\n```\n\nНечётных будет `len(data) - even` (всего минус чётные). Сравни `even` и\n`odd` и верни строку точно как в примере: `✅ Одинаково` или\n`❌ Не одинаково`.\n\n- [Арифметика и %](https://docs.python.org/3/tutorial/introduction.html#numbers)",
        3: "```python\neven = 0\nfor x in data:\n    if x % 2 == 0:\n        even = even + 1\nodd = len(data) - even\nif even == odd:\n    return '✅ Одинаково'\nelse:\n    return ...   # TODO: какую строку вернуть, если поровну НЕ получается?\n```",
    },
    88: {
        1: "Остаток от деления на 3 бывает только трёх видов: 0, 1 или 2.\nНапример: 3 → 0, 4 → 1, 5 → 2, 6 → 0, 7 → 1.\n\nНужно каждое число из списка положить в одну из трёх групп по этому остатку.\nОтвет — это словарь (dict), где ключ — остаток (0, 1 или 2), а значение —\nсписок чисел с этим остатком. Для `[1, 2, 3, 4, 5, 6, 7]` ответ:\n`{0: [3, 6], 1: [1, 4, 7], 2: [2, 5]}`.\n\nСловарь — это коробка, в которой по ключу лежит значение. У нас значением\nбудет список, в который мы добавляем числа.",
        2: "Остаток от деления — это `%`: `num % 3` даёт 0, 1 или 2.\n\nЧтобы положить число в нужную группу, сначала проверь, есть ли уже такой\nключ в словаре. Если нет — создай пустой список. Потом добавь число:\n\n```\nresult = {}\nfor num in data:\n    key = num % 3\n    if key not in result:        # такого ключа ещё не было\n        result[key] = []         # создаём пустой список для этой группы\n    result[key].append(num)      # добавляем число в его группу\n```\n\nТак вместо `result.setdefault(key, [])` используется обычная проверка `if\nkey not in result`.\n\n- [Словари](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)",
        3: "```python\nresult = {}\nfor num in data:\n    key = num % 3\n    if key not in result:\n        result[key] = []\n    result[key].append(...)   # TODO: какое число добавляем в группу?\nreturn result\n```",
    },
    89: {
        1: "Префикс — это начало слова. Для `'code'` префиксы такие:\n\n- длины 1 → `'c'`\n- длины 2 → `'co'`\n- длины 3 → `'cod'`\n- длины 4 → `'code'` (всё слово)\n\nНужно собрать все префиксы слова из `data[0]` в один список. Перебери\nдлины от 1 до длины слова включительно.",
        2: "Срез `word[:k]` даёт первые k букв слова:\n\n```\nword = 'code'\nword[:1]   # 'c'\nword[:2]   # 'co'\nword[:3]   # 'cod'\nword[:4]   # 'code'\n```\n\nСобери все префиксы в список обычным циклом:\n\n```\nresult = []\nfor k in range(1, len(word) + 1):   # k = 1, 2, 3, 4 для 'code'\n    result.append(word[:k])\n```\n\n`range(1, len(word) + 1)` даёт числа от 1 до длины слова включительно\n(правый конец у `range` не включается, поэтому `+ 1`).\n\n- [Срезы строк](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nword = data[0]\nresult = []\nfor k in range(1, len(word) + 1):\n    result.append(word[...])   # TODO: какой срез даёт первые k букв?\nreturn result\n```",
    },
    90: {
        1: "Суффикс — это конец слова. Для `'code'` суффиксы такие:\n\n- с позиции 0 → `'code'` (всё слово)\n- с позиции 1 → `'ode'`\n- с позиции 2 → `'de'`\n- с позиции 3 → `'e'`\n\nНужно собрать все суффиксы слова из `data[0]` в один список. Перебери\nпозиции от 0 до длины слова минус 1.",
        2: "Срез `word[i:]` даёт часть слова, начиная с позиции i и до конца:\n\n```\nword = 'code'\nword[0:]   # 'code'\nword[1:]   # 'ode'\nword[2:]   # 'de'\nword[3:]   # 'e'\n```\n\nСобери все суффиксы в список обычным циклом:\n\n```\nresult = []\nfor i in range(len(word)):   # i = 0, 1, 2, 3 для 'code'\n    result.append(word[i:])\n```\n\n`range(len(word))` даёт позиции от 0 до длины слова минус 1.\n\n- [Срезы строк](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nword = data[0]\nresult = []\nfor i in range(len(word)):\n    result.append(word[...])   # TODO: какой срез даёт слово с позиции i до конца?\nreturn result\n```",
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
    101: {
        1: "Максимум — самый большой элемент списка, минимум — самый маленький, а их разница называется **размахом**. Для `[3, 7, 1]`: максимум — 7, минимум — 1, размах 7 - 1 = 6.\n\nИ то и другое можно найти одним проходом: до цикла возьми первый элемент и как «текущий максимум», и как «текущий минимум», а в цикле обновляй их, если встретил число побольше или поменьше. В конце верни разницу.",
        2: "Так ищут максимум и минимум одновременно:\n\n```\nmax_value = data[0]\nmin_value = data[0]\nfor num in data:\n    if num > max_value:   # нашли число побольше\n        max_value = num\n    if num < min_value:   # нашли число поменьше\n        min_value = num\n```\n\nСтартовать надо именно с `data[0]`, а не с нуля: для списка из отрицательных чисел «нулевой» максимум оказался бы неверным.\n\n- [Цикл for](https://docs.python.org/3/tutorial/controlflow.html#for-statements)",
        3: "```python\nmax_value = data[0]\nmin_value = data[0]\nfor num in data:\n    if num > max_value:\n        max_value = num\n    if num < min_value:\n        min_value = ...   # TODO: какое число запоминаем, если оно поменьше?\nreturn max_value - ...   # TODO: что вычитаем из максимума?\n```",
    },
    102: {
        1: "Положительное число — это число строго больше нуля. Ноль не положительное и не отрицательное: 5 — положительное, 0 — нет, -3 — отрицательное.\n\nПройди по списку циклом и посчитай, сколько чисел больше нуля. Заведи счётчик, равный 0, и увеличивай его на 1 для каждого подходящего числа.\n\nВ примере `[-2, 5, 0, 3, -1, 7]` подходят 5, 3 и 7 — итого 3.",
        2: "Счётчик — обычная переменная, которую наращивают в цикле:\n\n```\ncount = 0\nfor num in data:\n    if num > 0:      # строго больше нуля — ноль не считается\n        count = count + 1\n```\n\nПосле цикла верни `count`.\n\n- [Цикл for](https://docs.python.org/3/tutorial/controlflow.html#for-statements)",
        3: "```python\ncount = 0\nfor num in data:\n    if num > ...:   # TODO: какое условие у положительного числа?\n        count += 1\nreturn count\n```",
    },
    103: {
        1: "Отрицательное число — меньше нуля: -1, -3, -5. Ноль и положительные числа остаются как есть.\n\nСобери **новый список**: идём по исходному и для каждого числа решаем — если оно отрицательное, кладём в новый список 0, иначе кладём само число.\n\nВ примере `[-1, 2, -3, 0, 5]` получается `[0, 2, 0, 0, 5]`: -1 и -3 заменились на нули, а 2, 0 и 5 прошли без изменений.",
        2: "Собирай результат в новый список, исходный не меняй:\n\n```\nresult = []\nfor num in data:\n    if num < 0:\n        result.append(0)     # отрицательное заменяем нулём\n    else:\n        result.append(num)   # всё остальное проходит как есть\n```\n\n- [append](https://docs.python.org/3/tutorial/datastructures.html#more-on-lists)",
        3: "```python\nresult = []\nfor num in data:\n    if num < 0:\n        result.append(...)\n    else:\n        result.append(num)\nreturn result\n```",
    },
    104: {
        1: "Индекс — это номер места элемента, и счёт идёт с нуля: в списке `[4, 9, 2]` у четвёрки индекс 0, у девятки — 1, у двойки — 2.\n\nНужен индекс самого большого элемента. Если максимум встречается несколько раз — берём первое вхождение (самый левый из них). В примере `[4, 9, 2, 9, 7]` максимум — 9, впервые он стоит на индексе 1, значит ответ 1.\n\nЗаведи переменную «индекс лучшего», начни с 0 и в цикле по индексам обновляй её, когда встретишь элемент больше текущего лучшего.",
        2: "Проходи по индексам от 1 и сравнивай элемент с текущим лучшим:\n\n```\nbest_index = 0\nfor i in range(1, len(data)):\n    if data[i] > data[best_index]:   # строго больше: равные не сбивают индекс\n        best_index = i\n```\n\nСравнение именно строгое (`>`), поэтому при равных максимумах остаётся первое вхождение.\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\nbest_index = 0\nfor i in range(1, len(data)):\n    if data[i] > data[...]:   # TODO: с каким элементом сравниваем?\n        best_index = i\nreturn best_index\n```",
    },
    105: {
        1: "Чётное число делится на 2 без остатка: 2, 4, 6, 8... Нечётное — с остатком: 1, 3, 5, 7...\n\n«Все ли чётные» значит, что в списке не должно быть ни одного нечётного. Проверять удобно наоборот: как только встретили нечётное — сразу ответ «нет», не досматривая список до конца. Если цикл прошёл до конца и нечётных не нашлось — «да».\n\nВ примере `[2, 3, 8]` тройка нечётная, поэтому ответ — «❌ Есть нечётные».",
        2: "Чётность проверяют через остаток от деления: `num % 2 == 0` — чётное, `num % 2 != 0` — нечётное. Стратегия «выйти сразу при нарушении»:\n\n```\nfor num in data:\n    if num % 2 != 0:          # нечётное — условие нарушено\n        return '❌ Есть нечётные'\n# цикл прошёл без нарушений\nreturn '✅ Все чётные'\n```\n\nПустой список пройдёт без нарушений — ответ «да». Верни строки точно как в примере.\n\n- [Арифметика и %](https://docs.python.org/3/tutorial/introduction.html#numbers)",
        3: "```python\nfor num in data:\n    if num % 2 != ...:   # TODO: какой остаток даёт нечётное число при делении на 2?\n        return '❌ Есть нечётные'\nreturn ...   # TODO: какая строка, если нечётных не нашлось?\n```",
    },
    106: {
        1: "Список лежит в `data[0]`, а искомое число — в `data[1]`. Нужно посчитать, сколько элементов списка равны этому числу. В примере `[1, 2, 2, 3, 2]` и число 2: двойка встречается 3 раза, ответ — 3.\n\nМетод `.count()` запрещён условием, но он и не нужен: пройди по списку циклом со счётчиком и прибавляй 1 каждый раз, когда элемент равен заданному числу.",
        2: "Обычный счётчик в цикле вместо `.count()`:\n\n```\ncount = 0\nfor num in data[0]:\n    if num == data[1]:    # элемент равен заданному числу\n        count = count + 1\n```\n\n- [Цикл for](https://docs.python.org/3/tutorial/controlflow.html#for-statements)",
        3: "```python\ncount = 0\nfor num in data[0]:\n    if num == ...:   # TODO: с чем сравнить каждый элемент?\n        count += 1\nreturn count\n```",
    },
    107: {
        1: "Список лежит в `data[0]`, а число, которое прибавляем, — в `data[1]`. К каждому числу списка надо прибавить одно и то же число. В примере `[1, 2, 3]` и 10: 1+10=11, 2+10=12, 3+10=13, получается `[11, 12, 13]`.\n\nЗаведи пустой список результата, пройди по всем числам и добавляй в него суммы.",
        2: "```\nresult = []\nfor num in data[0]:\n    result.append(num + data[1])\n```\n\n- [append](https://docs.python.org/3/tutorial/datastructures.html#more-on-lists)",
        3: "```python\nresult = []\nfor num in data[0]:\n    result.append(num + ...)   # TODO: что прибавляем к каждому числу?\nreturn result\n```",
    },
    108: {
        1: "Индекс — номер места элемента, счёт с нуля. В списке `[5, 1, 7, 2, 9]`: у пятёрки индекс 0, у единицы — 1, у семёрки — 2, у двойки — 3, у девятки — 4.\n\nНужны элементы на чётных индексах: 0, 2, 4 — то есть числа 5, 7 и 9. Их сумма 5 + 7 + 9 = 21. Внимание: чётными должны быть **индексы**, а не сами числа!\n\nИди по индексам 0, 2, 4, ... циклом и складывай элементы на этих местах в аккумулятор.",
        2: "`range(0, len(data), 2)` даёт числа 0, 2, 4, ... — то есть каждое второе:\n\n```\nresult = 0\nfor i in range(0, len(data), 2):   # i = 0, 2, 4, ...\n    result += data[i]\n```\n\nТретий аргумент `range` — это шаг.\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\nresult = 0\nfor i in range(0, len(data), ...):   # TODO: какой шаг у чётных индексов?\n    result += data[...]\nreturn result\n```",
    },
    109: {
        1: "Двузначное число состоит из двух цифр, то есть лежит от 10 до 99 включительно. Однозначные (0-9) и трёхзначные (100 и больше) не подходят.\n\nВ примере `[5, 23, 100, 47, 8]` двузначные — это 23 и 47, их сумма 70.\n\nПроверка «число от 10 до 99» записывается двойным неравенством `10 <= num <= 99`. Заведи аккумулятор и прибавляй туда только подходящие числа.",
        2: "Двойное сравнение в Python работает напрямую:\n\n```\nresult = 0\nfor num in data:\n    if 10 <= num <= 99:    # одновременно и >= 10, и <= 99\n        result += num\n```\n\n- [Арифметика и сравнения](https://docs.python.org/3/tutorial/introduction.html#numbers)",
        3: "```python\nresult = 0\nfor num in data:\n    if ... <= num <= ...:   # TODO: какие границы у двузначного числа?\n        result += num\nreturn result\n```",
    },
    110: {
        1: "Индекс — номер места элемента, счёт с нуля. Здесь надо посчитать, у скольких элементов **значение совпадает с их индексом**.\n\nРазберём `[0, 3, 2, 7, 4]`:\n\n- индекс 0, значение 0 — совпало\n- индекс 1, значение 3 — нет\n- индекс 2, значение 2 — совпало\n- индекс 3, значение 7 — нет\n- индекс 4, значение 4 — совпало\n\nИтого 3 совпадения. Иди по индексам циклом и считай совпадения счётчиком.",
        2: "```\ncount = 0\nfor i in range(len(data)):\n    if data[i] == i:     # значение равно своему месту\n        count = count + 1\n```\n\n- [range и len](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\ncount = 0\nfor i in range(len(data)):\n    if data[i] == ...:   # TODO: с чем сравнить элемент?\n        count += 1\nreturn count\n```",
    },
    111: {
        1: "Каждое слово надо записать с заглавной первой буквой: 'cat' → 'Cat'. Остальные буквы не меняются.\n\nУ строк есть готовый метод `.capitalize()` — он возвращает копию слова с заглавной первой буквой: `'cat'.capitalize()` даёт `'Cat'`. Пройди по словам циклом и собери преобразованные слова в новый список.",
        2: "```\nresult = []\nfor word in data:\n    result.append(word.capitalize())\n```\n\n- [Строковые методы](https://docs.python.org/3/library/stdtypes.html#string-methods)",
        3: "```python\nresult = []\nfor word in data:\n    result.append(word....())   # TODO: какой метод делает первую букву заглавной?\nreturn result\n```",
    },
    112: {
        1: "Надо склеить все слова в одну строку, поставив между ними по одному пробелу: `['Hello', 'world']` → 'Hello world'. Обрати внимание: пробел нужен **между** словами, а не в конце — в 'Hello world' на конце пробела нет.\n\nЗаведи пустую строку-аккумулятор и дописывай в неё слова по одному; перед каждым словом, кроме первого, добавь пробел.",
        2: "Строка — тоже аккумулятор, её наращивают через `+=`:\n\n```\nresult = ''\nfor word in data:\n    if result != '':     # слово не первое — нужен разделитель\n        result += ' '\n    result += word\n```\n\n(Готовый метод `' '.join(data)` сделал бы то же самое, но ручная склейка понятнее.)\n\n- [Строки](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nresult = ''\nfor word in data:\n    if result != '':\n        result += ...   # TODO: какой разделитель добавить перед очередным словом?\n    result += word\nreturn result\n```",
    },
    113: {
        1: "Надо сложить длины всех слов. В примере `['cat', 'dog', 'bird']`: 3 + 3 + 4 = 10.\n\nДлину строки даёт функция `len()`: `len('cat')` — это 3. Заведи аккумулятор, равный 0, и прибавляй к нему длину каждого слова в цикле.",
        2: "```\nresult = 0\nfor word in data:\n    result += len(word)\n```\n\n- [len](https://docs.python.org/3/library/functions.html#len)",
        3: "```python\nresult = 0\nfor word in data:\n    result += ...(...)   # TODO: как получить длину слова?\nreturn result\n```",
    },
    114: {
        1: "Гласные буквы — это a, e, i, o, u (заглавные тоже считаются: слово 'Ice' начинается с гласной). Согласные — все остальные буквы.\n\nПервая буква слова — это `word[0]`. У 'apple' это 'a', гласная → ответ «✅ Начинается с гласной». У 'dog' — 'd', согласная → «❌ Начинается с согласной».\n\nСлово лежит в `data[0]`. Чтобы заглавная буква не сбила проверку, приведи её к нижнему регистру методом `.lower()`.",
        2: "```\nword = data[0]\nfirst = word[0].lower()    # 'I'.lower() → 'i': регистр больше не мешает\nif first in 'aeiou':\n    return '✅ Начинается с гласной'\nelse:\n    return '❌ Начинается с согласной'\n```\n\nОператор `in` для строк проверяет, входит ли буква в строку-перечисление.\n\n- [Строковые методы](https://docs.python.org/3/library/stdtypes.html#string-methods)",
        3: "```python\nword = data[0]\nfirst = word[0].lower()\nif first in ...:   # TODO: какая строка-перечисление гласных?\n    return '✅ Начинается с гласной'\nreturn '❌ Начинается с согласной'\n```",
    },
    115: {
        1: "Каждую букву слова надо повторить два раза: 'cat' → 'ccaatt' (c → cc, a → aa, t → tt).\n\nСтроку удобно собирать постепенно: заведи пустую строку и в цикле по буквам дописывай каждую букву дважды. Дописывание — это сцепление: `result += letter` добавляет букву в конец строки.\n\nСлово лежит в `data[0]`. По строке можно пройтись циклом `for` напрямую — так же, как по списку.",
        2: "```\nword = data[0]\nresult = ''\nfor letter in word:\n    result = result + letter + letter   # каждая буква дважды подряд\n```\n\n- [Строки](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\nword = data[0]\nresult = ''\nfor letter in word:\n    result += letter + ...   # TODO: что дописать второй раз?\nreturn result\n```",
    },
    116: {
        1: "Ответ — это словарь (dict): «коробка», в которой по ключу лежит значение. Здесь ключ — буква, значение — сколько раз она встречается в слове. Для 'banana': b — 1 раз, a — 3 раза, n — 2 раза, получается `{'b': 1, 'a': 3, 'n': 2}`.\n\nИди по буквам слова циклом и веди словарь-счётчик: если буквы в словаре ещё нет — заведи для неё счётчик 0, а потом увеличь его на 1.",
        2: "```\nword = data[0]\nresult = {}\nfor letter in word:\n    if letter not in result:   # буква встретилась впервые\n        result[letter] = 0\n    result[letter] = result[letter] + 1\n```\n\nЗапись `letter not in result` проверяет, есть ли уже такой ключ в словаре.\n\n- [Словари](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)",
        3: "```python\nword = data[0]\nresult = {}\nfor letter in word:\n    if letter not in result:\n        result[letter] = ...   # TODO: с какого счётчика начать новую букву?\n    result[letter] += 1\nreturn result\n```",
    },
    117: {
        1: "Палиндром — слово, которое одинаково читается в обе стороны: 'radar' наоборот тоже 'radar', а 'cat' наоборот — 'tac', значит не палиндром.\n\nПроще всего развернуть строку срезом с шагом -1: `word[::-1]`. Слово — палиндром, если оно равно своему развороту.\n\nПройди по всем словам, проверь каждое и посчитай подходящие счётчиком. В примере `['radar', 'cat', 'level', 'dog']` палиндромы — radar и level, ответ 2.",
        2: "```\ncount = 0\nfor word in data:\n    if word == word[::-1]:   # слово равно своему развороту\n        count = count + 1\n```\n\n`word[::-1]` — это слово задом наперёд (срез с отрицательным шагом).\n\n- [Срезы строк](https://docs.python.org/3/tutorial/introduction.html#strings)",
        3: "```python\ncount = 0\nfor word in data:\n    if word == word[...]:   # TODO: какой срез разворачивает строку?\n        count += 1\nreturn count\n```",
    },
    118: {
        1: "Каждое число превращается в его «знак»:\n\n- положительное (больше 0) → 1\n- отрицательное (меньше 0) → -1\n- ровно ноль → 0\n\nНапример, `[-5, 3, 0]` → `[-1, 1, 0]`.\n\nСобери новый список: в цикле выбирай одну из трёх веток через `if` / `elif` / `else` и добавляй в результат нужное число.",
        2: "```\nresult = []\nfor num in data:\n    if num > 0:\n        result.append(1)\n    elif num < 0:\n        result.append(-1)\n    else:\n        result.append(0)    # сюда попадает только ноль\n```\n\n- [if / elif / else](https://docs.python.org/3/tutorial/controlflow.html#if-statements)",
        3: "```python\nresult = []\nfor num in data:\n    if num > 0:\n        result.append(1)\n    elif num < 0:\n        result.append(...)   # TODO: что ставим вместо отрицательного числа?\n    else:\n        result.append(...)   # TODO: что ставим вместо нуля?\nreturn result\n```",
    },
    119: {
        1: "Складываем числа, стоящие на одинаковых местах: первые с первыми, вторые со вторыми и так далее. Для `[1, 2, 3]` и `[10, 20, 30]`: 1+10=11, 2+20=22, 3+30=33, ответ `[11, 22, 33]`.\n\nПервый список лежит в `data[0]`, второй — в `data[1]`. Длины у них одинаковые, поэтому удобно идти по индексам и складывать элементы с одним и тем же индексом.",
        2: "```\nresult = []\nfor i in range(len(data[0])):\n    result.append(data[0][i] + data[1][i])   # пара с одинаковым индексом\n```\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\nresult = []\nfor i in range(len(data[0])):\n    result.append(data[0][i] + data[...][i])   # TODO: из какого списка берём второе слагаемое?\nreturn result\n```",
    },
    120: {
        1: "Смотрим на пары соседей: (1-й элемент, 2-й), (2-й, 3-й) и так далее. Пара засчитывается, если второй элемент пары **больше** первого.\n\nВ примере `[1, 3, 2, 5, 4]` пары такие: 1→3 (больше, +1), 3→2 (нет), 2→5 (больше, +1), 5→4 (нет). Итого 2.\n\nИди по индексам от 1 до конца: у каждого элемента сравнивай его с предыдущим и считай случаи «больше» счётчиком.",
        2: "```\ncount = 0\nfor i in range(1, len(data)):   # начинаем со второго — у него есть предыдущий\n    if data[i] > data[i - 1]:\n        count = count + 1\n```\n\n`data[i - 1]` — это сосед слева (предыдущий элемент).\n\n- [range](https://docs.python.org/3/library/stdtypes.html#ranges)",
        3: "```python\ncount = 0\nfor i in range(1, len(data)):\n    if data[i] > data[...]:   # TODO: с каким соседом сравниваем?\n        count += 1\nreturn count\n```",
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
