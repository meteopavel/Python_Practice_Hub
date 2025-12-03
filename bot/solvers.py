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
