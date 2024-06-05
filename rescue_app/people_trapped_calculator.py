import math
from itertools import zip_longest
from PyQt5.QtWidgets import QMessageBox


def _calculate_people_trapped(rescue, num_fatalities, surviv):
    """Вычисляет количество людей в завале."""
    return [math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i]))
            for i in range(min(len(rescue), len(num_fatalities), len(surviv)))
            if math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i])) >= 0]


def _calculate_total_volume(landslide_height, people_trapped, time):
    """Вычисляет общий объем завала."""
    return [round(1.25 * landslide_height * people_trapped[i], 2)
            for i in range(min(time, len(people_trapped)))]


def _calculate_work_required(total_volume, method_power, tempa, koff_lum):
    """Вычисляет объем работ."""
    return [int(float(volume) * (6.8 if method_power == "Кирпич" else 10.8) * tempa * float(koff))
            for volume, koff in zip(total_volume, koff_lum)]


def _update_final_values(workreq, workload, final):
    """Обновляет значения в списке final."""
    min_length = min(len(workreq), len(workload))
    try:
        new_values = [min(i / w if w != 0 else 0, 1) for w, i in
                      zip_longest(workreq[:min_length], workload[:min_length], fillvalue=0)]
    except ZeroDivisionError:
        QMessageBox.critical(None, "Ошибка", "Произошло деление на ноль. Проверьте входные данные.")
        return

    if final[0]:
        final[0] = [sum(x) for x in zip_longest(final[0], new_values, fillvalue=0)]
    else:
        final[0] = new_values


def PeopleTrapped_func(time, landslide_height, rescue, num_fatalities, surviv, workload, sublists, tempa, line2,
                       method_power, final):
    """
    Функция для расчета количества людей в завале.
    """
    print("time", time)
    print("landslide_height", landslide_height)
    print("rescue", rescue)
    print("num_fatalities", num_fatalities)
    print("surviv", surviv)
    print("workload", workload)
    print("sublists", sublists)
    print("tempa", tempa)
    print("line2", line2)

    ast_time = [str(i % 25) for i in range(int(line2.text() or 0), time + int(line2.text() or 0))]
    print("ast_time", ast_time)
    koff_lum = ['1' if 7 <= int(it) <= 18 else '1.5' for it in ast_time]

    people_trapped = _calculate_people_trapped(rescue, num_fatalities, surviv)

    # Находим количество нулей в начале workload
    leading_zeros = 0
    for value in workload:
        if value == 0:
            leading_zeros += 1
        else:
            break

    # ОБНОВЛЯЕМ PeopleTrapped
    people_trapped = [people_trapped[0]] * leading_zeros + people_trapped[leading_zeros:]
    total_volume = _calculate_total_volume(landslide_height, people_trapped, time)
    workreq = _calculate_work_required(total_volume, method_power, tempa, koff_lum)

    # Добавляем фиктивный элемент в конец workreq
    workreq.append(0)  # Теперь длины workreq и surviv совпадают
    _update_final_values(workreq, workload, final)

    print("workreq", workreq)
    print("Длина PeopleTrapped:", len(people_trapped))
    print("Длина TotVol_m3:", len(total_volume))
    print("Длина workreq:", len(workreq))
    print("Размер final:", len(final))  # Если final - список, то len(final)

    return people_trapped, total_volume, workreq, ast_time, koff_lum