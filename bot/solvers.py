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
