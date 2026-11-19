"""Эталонные решения всех заданий: solve_task_N(data) → эталонный ответ,
get_solver(task_num) — диспетчер. Это генерируемый банк данных, а не API —
докстринги на каждой solve_task_* не нужны (их 121+)."""
import sys


def get_solver(task_num):
    func_name = f'solve_task_{task_num}'
    return getattr(sys.modules[__name__], func_name, None)


def solve_task_1(data):
    result = []
    for item in data:
        if item not in result:
            result.append(item)
    return result


def solve_task_2(data):
    result = 0
    for x in data:
        if x % 2 == 0:
            result += x
    return result


def solve_task_3(data):
    result = data
    for i in range(len(result) // 2):
        result[i], result[-i-1] = result[-i-1], result[i]
    return result


def solve_task_4(data):
    result = data[0]
    for num in data:
        if num > result:
            result = num
    return result


def solve_task_5(data):
    result = []
    print(data)
    for sublist in data:
        for item in sublist:
            if item not in result:
                result.append(item)
    return result


def solve_task_6(data):
    for i in range(len(data) - 1):
        if data[i] > data[i + 1]:
            return '❌ Список не сортирован'
    return '✅ Список сортирован'


def solve_task_7(data):
    index = data[1] if data[1] <= len(data[0]) else len(data[0])
    data[0].insert(index, data[1])
    return data[0]


def solve_task_8(data):
    min_value = min(data)
    data.remove(min_value)
    return data


def solve_task_9(data):
    result = []
    for i in range(len(data)):
        if i == 0:
            result.append(data[1])
        elif i == len(data) - 1:
            result.append(data[len(data) - 2])
        else:
            result.append(data[i - 1] + data[i + 1])
    return result


def solve_task_10(data):
    zero = []
    non_zero = []
    for num in data:
        if num == 0:
            zero.append(num)
        else:
            non_zero.append(num)
    return non_zero + zero


def solve_task_11(data):
    result = []
    for i in range(len(data[0])):
        result.append((data[0][i], data[1][i]))
    return result


def solve_task_12(data):
    fruits = {}
    for item in data:
        fruits[item] = fruits.get(item, 0) + 1
    max_fruits = max(fruits.keys(), key=lambda fruit: fruits[fruit])
    return max_fruits


def solve_task_13(data):
    chunks = []
    for i in range(0, len(data[0]), data[1]):
        chunks.append(data[0][i:i + data[1]])
    return chunks


def solve_task_14(data):
    lst_set = set(data)
    if len(lst_set) != len(data):
        return "✅ Повторы есть"
    return "❌ Повторов нет"


def solve_task_15(data):
    return sum(data) / len(data)


def solve_task_16(data):
    min_value = data[0]
    for num in data:
        if num < min_value:
            min_value = num
    min_value_index = data.index(min_value)
    data.pop(min_value_index)
    return data


def solve_task_17(data):
    if data[1] > len(data[0]):
        data[1] %= len(data[0])
    return data[0][-data[1]:] + data[0][:-data[1]]


def solve_task_18(data):
    return len(set(data))


def solve_task_19(data):
    text_lst = list(data[0])
    if text_lst == text_lst[::-1]:
        return '✅ Слово палиндром'
    return '❌ Слово не палиндром'


def solve_task_20(data):
    result = []
    for i in range(len(data[0]) - 1):
        for j in range(i + 1, len(data[0])):
            if data[0][i] + data[0][j] == data[1]:
                result.append((data[0][i], data[0][j]))
    return result


def solve_task_21(data):
    result = {}
    for word in data:
        key = len(word)
        if key not in result:
            result[key] = []
        result[key].append(word)
    return result


def solve_task_22(data):
    combined = [x for item in data for x in item]
    unique = set(combined)
    result = list(unique)
    result.sort()
    return result


def solve_task_23(data):
    num_set = set(data)
    cur_len = 0
    max_len = 0
    values_max_lens = {}
    for num in num_set:
        for n in data:
            if n == num:
                cur_len += 1
                max_len = max(max_len, cur_len)
            else:
                cur_len = 0
        values_max_lens[num] = max_len
        max_len = 0
    max_key = max(values_max_lens, key=values_max_lens.get)
    max_key_value = values_max_lens[max_key]
    return [max_key] * max_key_value


def solve_task_24(data):
    frequency = {}
    for num in data:
        frequency[num] = frequency.get(num, 0) + 1
    for num in data:
        if frequency[num] == 1:
            return num


def solve_task_25(data):
    frequency = {}
    for letter in data:
        frequency[letter] = frequency.get(letter, 0) + 1
    sorted_letters = sorted(data, key=lambda x: frequency[x])
    return sorted_letters


def solve_task_26(data):
    n = len(data)
    if n <= 2:
        result = len(set(data)) == n
    else:
        result = all((data[i - 1] < data[i] > data[i + 1]) or (data[i - 1] > data[i] < data[i + 1])
                     for i in range(1, n - 1))
    return "✅ Список пилообразный" if result else "❌ Список не пилообразный"


def solve_task_27(data):
    even = [x for x in data if x % 2 == 0]
    odd = [x for x in data if x % 2 != 0]
    return even + odd


def solve_task_28(data):
    return min(data[0], key=lambda num: abs(num - data[1]))


def solve_task_29(data):
    pairs = []
    for i in range(len(data[0])):
        for j in range(i + 1, len(data[0])):
            if abs(data[0][i] - data[0][j]) == data[1]:
                pairs.append((data[0][i], data[0][j]))
    return pairs


def solve_task_30(data):
    result = {}
    for word in data:
        first_letter = word[0]
        if first_letter not in result:
            result[first_letter] = []
        result[first_letter].append(word)
    return result


def solve_task_31(data):
    result = []
    for num in data:
        if num % 2 == 0:
            result.append(num)
    return result


def solve_task_32(data):
    for x in data:
        if x < 0:
            return '❌ Есть отрицательные'
        return '✅ Все положительные'


def solve_task_33(data):
    if len(data) == 0:
        return 'Список не должен быть пустым'
    lengths = []
    for item in data:
        lengths.append(len(item))
    max_length = max(lengths)
    for item in data:
        if len(item) == max_length:
            return item


def solve_task_34(data):
    for i in range(len(data)):
        data[i] = data[i] ** 2
    return data


def solve_task_35(data):
    result = []
    idx = [0, 1] if len(data[0]) >= len(data[1]) else [1, 0]
    for i in range(max(len(data[0]), len(data[1]))):
        if i < len(data[idx[0]]):
            result.append(data[idx[0]][i])
        if i < len (data[idx[1]]):
            result.append(data[idx[1]][i])
    return result


def solve_task_36(data):
    vowels = ['a', 'e', 'i', 'o', 'u']
    result = []
    for letter in data:
        if letter in vowels:
            result.append(letter)
    return result


def solve_task_37(data):
    for num in range(data-1, 1, -1):
        if data % num == 0:
            return '❌ Не простое число'
    return '✅ Простое число'


def solve_task_38(data):
    result = data
    result.sort()
    return result


def solve_task_39(data):
    result = []
    def inner_sum(obj):
        for item in obj:
            if type(item) is int:
                result.append(item)
            else:
                inner_sum(item)
    inner_sum(data)
    return sum(result)


def solve_task_40(data):
    result = []
    for num in data:
        if num >=0:
            result.append(num)
    return result


def solve_task_41(data):
    vowels = ['a','e','i','o','u']
    result = [letter for letter in data[0] if letter not in vowels]
    return result


def solve_task_42(data):
    sorted_data_0, sorted_data_1 = sorted(data[0]), sorted(data[1])
    return '✅ Анаграммы' if sorted_data_0 == sorted_data_1 else '❌ Не анаграммы'


def solve_task_43(data):
    factorial = 1
    for i in range(1,data[0] +  1):
        factorial *= i
    return factorial


def solve_task_44(data):
    vowels = ['a','e','i','o','u']
    result = data[0]
    for vowel in vowels:
        result = result.replace(vowel,'*')
    return result


def solve_task_45(data):
    data[0] = abs(data[0])
    data[1] = abs(data[1])
    for max_delim in range(min(data), 0, -1):
        if data[0] % max_delim == 0 and data[1] % max_delim == 0:
            return max_delim
    return None


def solve_task_46(data):
    if data[0].isdigit():
        return '✅ Только цифры'
    return '❌ Содержит нецифровые символы'


def solve_task_47(data):
    data[0] = abs(data[0])
    data[1] = abs(data[1])
    max_delim = max(data)
    while True:
        if max_delim % data[0] == 0 and max_delim % data[1] == 0:
            return max_delim
        max_delim += 1


def solve_task_48(data):
    words = data.split()
    return len(words)


def solve_task_49(data):
    def remove_duplicates_preserve_order(lst):
        seen = set()
        result = []
        for item in lst:
            if isinstance(item, list):
                cleaned_item = remove_duplicates_preserve_order(item)
                result.append(cleaned_item)
            else:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
        return result
    return remove_duplicates_preserve_order(data)


def solve_task_50(data):
    return '✅ Симметричный' if data == data[::-1] else '❌ Не симметричный'


def solve_task_51(data):
    for word in data:
        if word != word.capitalize():
            return '✗ Не все'
    return '☑️ Все'


def solve_task_52(data):
    result = 1
    for num in data:
        if num > 0:
            result *= num
    return result


def solve_task_53(data):
    result = []
    len1 = len(data[0])
    len2 = len(data[1])
    min_len = min(len1, len2)
    max_len = max(len1, len2)
    for i in range(min_len):
        result.append(data[0][i])
        result.append(data[1][i])
    for i in range(min_len, max_len):
        result.append(data[0][i]) if len(data[0]) > len(data[1]) else result.append(data[1][i])
    return result


def solve_task_54(data):
    result = []
    for num in data:
        result.append(abs(num))
    return result


def solve_task_55(data):
    for i in range(len(data) - 1):
        if data[i] >= data[i + 1]:
            return '❌ Не строго возрастает'
    return '✅ Строго возрастает'


def solve_task_56(data):
    sorted_data = sorted(data, reverse=True)
    return sorted_data[1]


def solve_task_57(data):
    data_set = set(data)
    data_set_list = list(data_set)
    sorted_data_set_list = sorted(data_set_list)
    result = {}
    for item in sorted_data_set_list:
        result[item] = data.count(item)
    return result


def solve_task_58(data):
    result = []
    min_item = min(data)
    max_item = max(data)
    for item in data:
        if item == min_item:
            result.append(max_item)
        elif item == max_item:
            result.append(min_item)
        else:
            result.append(item)
    return result


def solve_task_59(data):
    return [item for item in data if not data.count(item) > 1]


def solve_task_60(data):
    result = []
    for item in data[0]:
        if item not in result and item in data[1]:
            result.append(item)
    return result


def solve_task_61(data):
    result = [[], []]
    for i in range(len(data)):
        result[0].append(data[i]) if i % 2 == 0 else result[1].append(data[i])
    return result


def solve_task_62(data):
    for item in data:
        if data.count(item) > 1:
            return item
    return None


def solve_task_63(data):
    result = []
    for i in range(len(data)):
        if i == 0:
            result.append(data[i])
        else:
            result.append(data[i] - data[i - 1])
    return result


def solve_task_64(data):
    word1_list = list(data[0])
    for ch in data[1]:
        if ch in word1_list:
            word1_list.remove(ch)
        else:
            return False
    return True


def solve_task_65(data):
    vowels = 'aeiouAEIOU'
    result = []
    for word in data:
        count = 0
        for char in word:
            if char in vowels:
                count += 1
        result.append(count)
    return result


def solve_task_66(data):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join([letter for letter in data[0] if letter.lower() in alphabet])


def solve_task_67(data):
    return [num for num in data[0] if num % data[1] == 0]


def solve_task_68(data):
    return ', '.join([str(item) for item in data])


def solve_task_69(data):
    s = data[0]
    return [s[i:i + 2] for i in range(0, len(s), 2)]


def solve_task_70(data):
    result = []
    for item in data:
        item_sum = 0
        for num in str(item):
            item_sum += int(num)
        result.append(item_sum)
    return result


def solve_task_71(data):
    for i in range(len(data) - 1):
        if ((data[i] % 2 == 0 and data[i + 1] % 2 != 0)
            or (data[i + 1] % 2 == 0 and data[i] % 2 != 0)):
            continue
        else:
            return '❌ Не чередуются'
    return '✅ Чередуются'


def solve_task_72(data):
    return [i for i in range(len(data[0])) if data[0][i] == data[1]][-1]


def solve_task_73(data):
    result = [data[-1]]
    for i in range(len(data) - 1):
        result.append(data[i])
    return result


def solve_task_74(data):
    return [item * 2 if item < data[1] else item for item in data[0]]


def solve_task_75(data):
    result = data[0]
    for word in data:
        if len(word) < len(result):
            result = word
    return result


def solve_task_76(data):
    for letter in data[0]:
        if data[0].count(letter) > 1:
            return '✅ Есть'
    return '❌ Нет'


def solve_task_77(data):
    result, dublicates = [], []
    for item in data:
        if data.count(item) > 1 and item not in dublicates:
            dublicates.append(item)
            result.append(item)
        elif data.count(item) == 1:
            result.append(item)
        else:
            result.append('dup')
    return result


def solve_task_78(data):
    data.sort(key=lambda x: len(x))
    if len(data) % 2 == 0:
        start = int(len(data) / 2)
    else:
        start = int(len(data) / 2) + 1
    return data[start:]


def solve_task_79(data):
    if not data:
        return []
    result = []
    current = data[0]
    count = 1
    for item in data[1:]:
        if item == current:
            count += 1
        else:
            result.append((current, count))
            current = item
            count = 1
    result.append((current, count))
    return result


def solve_task_80(data):
    result = []
    for item, count in data:
        result.extend([item] * count)
    return result


def solve_task_81(data):
    return [(data[i], data[i + 1]) for i in range(len(data) - 1)]


def solve_task_82(data):
    if len(data) < 2:
        return '✅ Да'
    diff = data[1] - data[0]
    for i in range(1, len(data)):
        if data[i] - data[i - 1] != diff:
            return '❌ Нет'
    return '✅ Да'


def solve_task_83(data):
    vowels = 'aeiouAEIOU'
    best_word = data[0]
    best_count = sum(1 for ch in data[0] if ch in vowels)
    for word in data[1:]:
        count = sum(1 for ch in word if ch in vowels)
        if count > best_count:
            best_count = count
            best_word = word
    return best_word


def solve_task_84(data):
    return [item for i, item in enumerate(data) if i % 2 == 0]


def solve_task_85(data):
    return [word[::-1] for word in data]


def solve_task_86(data):
    def digit_sum(n):
        return sum(int(d) for d in str(abs(n)))
    best = data[0]
    best_sum = digit_sum(data[0])
    for num in data[1:]:
        s = digit_sum(num)
        if s > best_sum:
            best_sum = s
            best = num
    return best


def solve_task_87(data):
    even = sum(1 for x in data if x % 2 == 0)
    odd = len(data) - even
    return '✅ Одинаково' if even == odd else '❌ Не одинаково'


def solve_task_88(data):
    result = {}
    for num in data:
        key = num % 3
        result.setdefault(key, []).append(num)
    return result


def solve_task_89(data):
    word = data[0]
    return [word[:i] for i in range(1, len(word) + 1)]


def solve_task_90(data):
    word = data[0]
    return [word[i:] for i in range(len(word))]


def solve_task_91(data):
    total = sum(data)
    if total % 2 != 0:
        return '❌ Нельзя'
    target = total // 2
    n = len(data)
    for mask in range(1 << n):
        s = sum(data[i] for i in range(n) if mask & (1 << i))
        if s == target:
            return '✅ Можно'
    return '❌ Нельзя'


def solve_task_92(data):
    n = len(data)
    return [(data[i], data[n - 1 - i]) for i in range(n // 2)]


def solve_task_93(data):
    return {word: len(word) for word in data}


def solve_task_94(data):
    result = []
    for i in range(1, len(data) - 1):
        if data[i] > data[i - 1] and data[i] > data[i + 1]:
            result.append(data[i])
    return result


def solve_task_95(data):
    return [word[0] + word[-1] for word in data]


def solve_task_96(data):
    if not data:
        return []
    result = [data[0]]
    for item in data[1:]:
        if item != result[-1]:
            result.append(item)
    return result


def solve_task_97(data):
    if not data:
        return 0
    best = cur = 1
    for i in range(1, len(data)):
        if data[i] == data[i - 1]:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def solve_task_98(data):
    def is_increasing(lst):
        return all(lst[i] < lst[i + 1] for i in range(len(lst) - 1))
    for i in range(len(data)):
        if is_increasing(data[:i] + data[i + 1:]):
            return '✅ Можно'
    return '❌ Нельзя'


def solve_task_99(data):
    result = []
    i = 0
    length = 1
    while i < len(data):
        result.append(data[i:i + length])
        i += length
        length += 1
    return result


def solve_task_100(data):
    counts = {}
    for x in data:
        counts[x] = counts.get(x, 0) + 1
    result = []
    for x in data:
        if counts[x] > 1 and x not in result:
            result.append(x)
    return result


def solve_task_101(data):
    max_value = data[0]
    min_value = data[0]
    for num in data:
        if num > max_value:
            max_value = num
        if num < min_value:
            min_value = num
    return max_value - min_value


def solve_task_102(data):
    count = 0
    for num in data:
        if num > 0:
            count += 1
    return count


def solve_task_103(data):
    result = []
    for num in data:
        if num < 0:
            result.append(0)
        else:
            result.append(num)
    return result


def solve_task_104(data):
    best_index = 0
    for i in range(1, len(data)):
        if data[i] > data[best_index]:
            best_index = i
    return best_index


def solve_task_105(data):
    for num in data:
        if num % 2 != 0:
            return '❌ Есть нечётные'
    return '✅ Все чётные'


def solve_task_106(data):
    count = 0
    for num in data[0]:
        if num == data[1]:
            count += 1
    return count


def solve_task_107(data):
    result = []
    for num in data[0]:
        result.append(num + data[1])
    return result


def solve_task_108(data):
    result = 0
    for i in range(0, len(data), 2):
        result += data[i]
    return result


def solve_task_109(data):
    result = 0
    for num in data:
        if 10 <= num <= 99:
            result += num
    return result


def solve_task_110(data):
    count = 0
    for i in range(len(data)):
        if data[i] == i:
            count += 1
    return count


def solve_task_111(data):
    result = []
    for word in data:
        result.append(word.capitalize())
    return result


def solve_task_112(data):
    result = ''
    for word in data:
        if result != '':
            result += ' '
        result += word
    return result


def solve_task_113(data):
    result = 0
    for word in data:
        result += len(word)
    return result


def solve_task_114(data):
    word = data[0]
    if word[0].lower() in 'aeiou':
        return '✅ Начинается с гласной'
    return '❌ Начинается с согласной'


def solve_task_115(data):
    word = data[0]
    result = ''
    for letter in word:
        result += letter + letter
    return result


def solve_task_116(data):
    word = data[0]
    result = {}
    for letter in word:
        if letter not in result:
            result[letter] = 0
        result[letter] += 1
    return result


def solve_task_117(data):
    count = 0
    for word in data:
        if word == word[::-1]:
            count += 1
    return count


def solve_task_118(data):
    result = []
    for num in data:
        if num > 0:
            result.append(1)
        elif num < 0:
            result.append(-1)
        else:
            result.append(0)
    return result


def solve_task_119(data):
    result = []
    for i in range(len(data[0])):
        result.append(data[0][i] + data[1][i])
    return result


def solve_task_120(data):
    count = 0
    for i in range(1, len(data)):
        if data[i] > data[i - 1]:
            count += 1
    return count


def solve_task_121(data):
    a = data[0]
    b = data[1]
    result = []
    i = 0
    j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    while i < len(a):
        result.append(a[i])
        i += 1
    while j < len(b):
        result.append(b[j])
        j += 1
    return result


def solve_task_122(data):
    result = []
    for item in data[0]:
        if item not in data[1] and item not in result:
            result.append(item)
    return result


def solve_task_123(data):
    return sorted(data, key=len)


def solve_task_124(data):
    return sorted(data, key=lambda num: num % 10)


def solve_task_125(data):
    best_pair = (data[0], data[1])
    best_sum = data[0] + data[1]
    for i in range(1, len(data) - 1):
        cur_sum = data[i] + data[i + 1]
        if cur_sum > best_sum:
            best_sum = cur_sum
            best_pair = (data[i], data[i + 1])
    return best_pair


def solve_task_126(data):
    result = 0
    for num in data:
        if num < 0:
            return result
        result += num
    return result


def solve_task_127(data):
    result = list(data[0])
    for i in range(len(result)):
        if result[i] > data[1]:
            result.insert(i, data[1])
            return result
    result.append(data[1])
    return result


def solve_task_128(data):
    count = 0
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] > data[j]:
                count += 1
    return count


def solve_task_129(data):
    lst = data[0]
    k = data[1]
    best = 0
    for i in range(k):
        best += lst[i]
    cur = best
    for i in range(k, len(lst)):
        cur = cur + lst[i] - lst[i - k]
        if cur > best:
            best = cur
    return best


def solve_task_130(data):
    s = sorted(data)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def solve_task_131(data):
    for i in range(0, len(data) - 1, 2):
        data[i], data[i + 1] = data[i + 1], data[i]
    return data


def solve_task_132(data):
    result = []
    total = 0
    for num in data:
        total += num
        result.append(total)
    return result


def solve_task_133(data):
    n = data[0]
    if n == 0:
        return '0'
    result = ''
    while n > 0:
        result = str(n % 2) + result
        n = n // 2
    return result


def solve_task_134(data):
    n = len(data) + 1
    expected = n * (n + 1) // 2
    return expected - sum(data)


def solve_task_135(data):
    word = data[0]
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    result = ''
    for ch in word:
        index = alphabet.index(ch)
        result += alphabet[(index + 1) % 26]
    return result


def solve_task_136(data):
    words = data[0].split()
    result = []
    for i in range(len(words) - 1, -1, -1):
        result.append(words[i])
    return ' '.join(result)


def solve_task_137(data):
    words = data[0].split()
    result = ''
    for word in words:
        result += word[0]
    return result


def solve_task_138(data):
    d = data[0]
    best_key = None
    best_value = None
    for key in d:
        if best_value is None or d[key] > best_value:
            best_value = d[key]
            best_key = key
    return best_key


def solve_task_139(data):
    result = dict(data[0])
    for key in data[1]:
        if key in result:
            result[key] = result[key] + data[1][key]
        else:
            result[key] = data[1][key]
    return result


def solve_task_140(data):
    digits = str(data[0])
    left = int(digits[0]) + int(digits[1]) + int(digits[2])
    right = int(digits[3]) + int(digits[4]) + int(digits[5])
    if left == right:
        return '✅ Счастливый'
    return '❌ Несчастливый'


def solve_task_141(data):
    result = []
    for num in data:
        if num % 15 == 0:
            result.append('fizzbuzz')
        elif num % 3 == 0:
            result.append('fizz')
        elif num % 5 == 0:
            result.append('buzz')
        else:
            result.append(str(num))
    return result


def solve_task_142(data):
    amount = data[0]
    count = 0
    for coin in [10, 5, 2, 1]:
        count += amount // coin
        amount = amount % coin
    return count


def solve_task_143(data):
    total = 0
    for digit in str(data[0]):
        total += int(digit)
    if total % 3 == 0:
        return '✅ Делится'
    return '❌ Не делится'


def solve_task_144(data):
    word = data[0]
    count = 0
    for i in range(len(word) - 1):
        if word[i] == word[i + 1]:
            count += 1
    return count


def solve_task_145(data):
    max_so_far = data[0]
    count = 1
    for num in data[1:]:
        if num > max_so_far:
            max_so_far = num
            count += 1
    return count


def solve_task_146(data):
    first = data.index(0)
    last = len(data) - 1
    while data[last] != 0:
        last -= 1
    total = 0
    for num in data[first + 1:last]:
        total += num
    return total


def solve_task_147(data):
    result = []
    for num in data:
        count = 0
        for d in range(1, num + 1):
            if num % d == 0:
                count += 1
        result.append(count)
    return result


def solve_task_148(data):
    seconds = data[0]
    hours = seconds // 3600
    seconds = seconds % 3600
    minutes = seconds // 60
    seconds = seconds % 60
    return str(hours) + ':' + str(minutes) + ':' + str(seconds)


def solve_task_149(data):
    total = 0
    for num in data:
        digits = str(num)
        if digits[0] < digits[-1]:
            total += num
    return total


def solve_task_150(data):
    packed = data[0]
    result = ''
    for i in range(0, len(packed), 2):
        letter = packed[i]
        count = int(packed[i + 1])
        result = result + letter * count
    return result


def solve_task_151(data):
    prefix = data[0]
    for word in data[1:]:
        i = 0
        while i < len(prefix) and i < len(word) and prefix[i] == word[i]:
            i += 1
        prefix = prefix[:i]
    return prefix


def solve_task_152(data):
    word = data[0]
    if len(word) <= 2:
        return word
    return word[0] + str(len(word) - 2) + word[-1]


def solve_task_153(data):
    result = ''
    for ch in data[0]:
        if ch.isupper():
            result += ch.lower()
        else:
            result += ch.upper()
    return result


def solve_task_154(data):
    letters = ''
    for ch in data[0]:
        if ch != ' ':
            letters += ch
    if letters == letters[::-1]:
        return '✅ Палиндром'
    return '❌ Не палиндром'


def solve_task_155(data):
    counts = {}
    for x in data[0]:
        counts[x] = counts.get(x, 0) + 1
    result = []
    for x in data[0]:
        if counts[x] == data[1] and x not in result:
            result.append(x)
    return result


def solve_task_156(data):
    result = [0]
    for i in range(1, len(data)):
        if data[i] != data[i - 1]:
            result.append(i)
    return result


def solve_task_157(data):
    seen = []
    result = []
    for x in data:
        if x in seen:
            return result
        seen.append(x)
        result.append(x)
    return result


def solve_task_158(data):
    keys = []
    groups = []
    for word in data:
        key = ''.join(sorted(word))
        if key in keys:
            index = keys.index(key)
            groups[index].append(word)
        else:
            keys.append(key)
            groups.append([word])
    return groups


def solve_task_159(data):
    result = []
    for ch in sorted(data[0]):
        if ch in data[1] and ch not in result:
            result.append(ch)
    return result


def solve_task_160(data):
    result = []
    for x in data[0]:
        if x in data[1] and x in data[2] and x not in result:
            result.append(x)
    return result


def solve_task_161(data):
    result = []
    for row in data:
        total = 0
        for num in row:
            total += num
        result.append(total)
    return result


def solve_task_162(data):
    result = []
    for j in range(len(data[0])):
        column = []
        for i in range(len(data)):
            column.append(data[i][j])
        result.append(column)
    return result


def solve_task_163(data):
    balance = 0
    for ch in data[0]:
        if ch == '(':
            balance += 1
        if ch == ')':
            balance -= 1
        if balance < 0:
            return '❌ Несбалансированы'
    if balance == 0:
        return '✅ Сбалансированы'
    return '❌ Несбалансированы'


def solve_task_164(data):
    word = data[0]
    result = ''
    current = word[0]
    count = 1
    for ch in word[1:]:
        if ch == current:
            count += 1
        else:
            result = result + current + str(count)
            current = ch
            count = 1
    result = result + current + str(count)
    return result


def solve_task_165(data):
    result = ''
    for word in data[0].split():
        if word[0].isupper():
            result += word[0]
    return result


def solve_task_166(data):
    digits = sorted(data, reverse=True)
    result = ''
    for d in digits:
        result += str(d)
    return int(result)


def solve_task_167(data):
    total = 0
    for ch in data[0]:
        total += ord(ch)
    return total


def solve_task_168(data):
    result = 1
    for _ in range(data[1]):
        result = result * data[0]
    return result


def solve_task_169(data):
    n = data[0]
    if n == 0:
        return 0
    a = 0
    b = 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


def solve_task_170(data):
    total = 0
    for num in range(1, data[0] + 1):
        if num % 3 != 0 and num % 5 != 0:
            total += num
    return total


def solve_task_171(data):
    n = data[0]
    count = 0
    while n > 1:
        n = n // 2
        count += 1
    return count


def solve_task_172(data):
    number = 0
    for ch in data[0]:
        number = number * 2 + int(ch)
    return number


def solve_task_173(data):
    n = data[0]
    total = 0
    for digit in str(n):
        total += int(digit) ** 3
    if total == n:
        return '✅ Число Армстронга'
    return '❌ Не число Армстронга'


def solve_task_174(data):
    a = data[0][0]
    op = data[0][1]
    b = data[0][2]
    if op == '+':
        return a + b
    if op == '-':
        return a - b
    if op == '*':
        return a * b
    return a / b


def solve_task_175(data):
    result = []
    for ch in sorted(data[0]):
        if ch not in result:
            result.append(ch)
    return result


def solve_task_176(data):
    password = data[0]
    if len(password) < 8:
        return '❌ Не подходит'
    has_upper = False
    has_digit = False
    for ch in password:
        if ch.isupper():
            has_upper = True
        if ch.isdigit():
            has_digit = True
    if has_upper and has_digit:
        return '✅ Подходит'
    return '❌ Не подходит'


def solve_task_177(data):
    result = ''
    for ch in data[0]:
        if ch.isdigit():
            result += ch
    return result


def solve_task_178(data):
    result = '#'
    for word in data[0].split():
        result += word.capitalize()
    return result


def solve_task_179(data):
    email = data[0]
    at_index = email.index('@')
    name = email[:at_index]
    domain = email[at_index:]
    return name[0] + '*' * (len(name) - 1) + domain


def solve_task_180(data):
    total = 0
    for part in data[0].split(','):
        total += int(part)
    return total


def solve_task_181(data):
    parts = data[0].split('.')
    if len(parts) != 4:
        return '❌ Некорректный'
    for part in parts:
        if not part.isdigit():
            return '❌ Некорректный'
        if int(part) > 255:
            return '❌ Некорректный'
    return '✅ Корректный'


def solve_task_182(data):
    word = data[0]
    counts = {}
    for ch in word:
        counts[ch] = counts.get(ch, 0) + 1
    for ch in word:
        if counts[ch] == 1:
            return ch
    return ''


def solve_task_183(data):
    def vowel_count(word):
        vowels = 'aeiou'
        count = 0
        for ch in word:
            if ch in vowels:
                count += 1
        return count
    return sorted(data, key=vowel_count)


def solve_task_184(data):
    scores = {'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2, 'h': 4,
              'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1, 'o': 1, 'p': 3,
              'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
              'y': 4, 'z': 10}
    total = 0
    for ch in data[0]:
        total += scores[ch]
    return total


def solve_task_185(data):
    morse = {'a': '.-', 'b': '-...', 'c': '-.-.', 'd': '-..', 'e': '.',
             'f': '..-.', 'g': '--.', 'h': '....', 'i': '..', 'j': '.---',
             'k': '-.-', 'l': '.-..', 'm': '--', 'n': '-.', 'o': '---',
             'p': '.--.', 'q': '--.-', 'r': '.-.', 's': '...', 't': '-',
             'u': '..-', 'v': '...-', 'w': '.--', 'x': '-..-', 'y': '-.--',
             'z': '--..'}
    codes = []
    for ch in data[0]:
        codes.append(morse[ch])
    return ' '.join(codes)


def solve_task_186(data):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    codes = []
    for ch in data[0]:
        codes.append(str(alphabet.index(ch) + 1))
    return ' '.join(codes)


def solve_task_187(data):
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    i = 0
    roman = data[0]
    while i < len(roman):
        if i + 1 < len(roman) and values[roman[i]] < values[roman[i + 1]]:
            total += values[roman[i + 1]] - values[roman[i]]
            i += 2
        else:
            total += values[roman[i]]
            i += 1
    return total


def solve_task_188(data):
    year = data[0]
    if year % 400 == 0:
        return '✅ Високосный'
    if year % 100 == 0:
        return '❌ Обычный'
    if year % 4 == 0:
        return '✅ Високосный'
    return '❌ Обычный'


def solve_task_189(data):
    price = data[0]
    discount = data[1]
    return price - price * discount / 100


def solve_task_190(data):
    seconds = data[0]
    hours = seconds // 3600
    seconds = seconds % 3600
    minutes = seconds // 60
    seconds = seconds % 60
    return str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)


def solve_task_191(data):
    n = data[0]
    result = []
    divisor = 2
    while n > 1:
        while n % divisor == 0:
            result.append(divisor)
            n = n // divisor
        divisor += 1
    return result


def solve_task_192(data):
    min_price = data[0]
    best = 0
    for price in data[1:]:
        if price - min_price > best:
            best = price - min_price
        if price < min_price:
            min_price = price
    return best


def solve_task_193(data):
    intervals = sorted(data, key=lambda pair: pair[0])
    result = []
    for start, end in intervals:
        if result and start <= result[-1][1]:
            if end > result[-1][1]:
                result[-1][1] = end
        else:
            result.append([start, end])
    return result


def solve_task_194(data):
    text = data[0]
    pattern = data[1]
    count = 0
    for i in range(len(text) - len(pattern) + 1):
        if text[i:i + len(pattern)] == pattern:
            count += 1
    return count


def solve_task_195(data):
    old = data[0]
    new = data[1]
    added = []
    for x in new:
        if x not in old and x not in added:
            added.append(x)
    removed = []
    for x in old:
        if x not in new and x not in removed:
            removed.append(x)
    return [added, removed]


def solve_task_196(data):
    result = []
    second = list(data[1])
    for x in data[0]:
        if x in second:
            result.append(x)
            second.remove(x)
    return result


def solve_task_197(data):
    counts = {}
    for word in data[0].split():
        counts[word] = counts.get(word, 0) + 1
    return counts


def solve_task_198(data):
    total = 0
    for i in range(len(data)):
        total += data[i][i]
    return total


def solve_task_199(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data[i])):
            if data[i][j] == 0:
                result.append((i, j))
    return result


def solve_task_200(data):
    result = list(data[0])
    while len(result) < data[1]:
        result.append(0)
    return result


def solve_task_0(data):
    result = 0
    for x in data:
        result += x
    return result
