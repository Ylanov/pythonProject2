import math


import numpy as np
from itertools import zip_longest
from PyQt5.QtWidgets import QMessageBox

buildings = []  # Список для хранения объектов BuildingData
num_surv = []
Kq = []
group_cnt_list = []
area = []
final = [[]]
column_3 = []
column_4 = []

subject_methods = {
    "survivors": {
        "Полная": (0.6, "Полная"),
        "Сильная": (0.49, "Сильная"),
        "Средняя": (0.09, "Средняя"),
        "Слабая": (1, "Слабая")
    },
    "buildings": {
        "Кирпич": (36, "Кирпич"),
        "Панель": (42, "Панель")
    },
    "intensity": {
        "землетрясение": 0.5,
        "взрыв вне здания": 2,
        "взрыв внутри здания": 2.5
    },
    'tempa': {
        'свыше +25': 1.5,
        'от 0 до +25': 1,
        'от -10 до 0': 1.3,
        'от -20 до -10': 1.4,
        'ниже -20': 1.6
    },
    'shift': {
        '1 смена': 1,
        '2 смены': 2,
        '3 смены': 3,
        '4 смены': 4,
    }
}


class BuildingData:
    """
    Класс для хранения данных о здании.
    """
    def __init__(self, height, length, width, debris_volume, method_name, method_power):
        self.height = height
        self.length = length
        self.width = width
        self.debris_volume = debris_volume
        self.method_name = method_name
        self.method_power = method_power
        print(self.debris_volume)
        print(self.method_power)
        print(self.method_name)


def calculate_data(height, width, length, k, framework_building, method_name, desruction_full, method_power, surviv,
                   time, esh_1, esh_2, esh_3, time_esh_1, time_esh_2, time_esh_3, number_surv, num_fatalities, tempa,
                   line2, num_shifts):
    """
    Функция для расчета данных о здании.
    """
    print('num_shifts', num_shifts)
    print('num_fatalities', num_fatalities)
    print('tempa', tempa)
    print('line2', line2)


    try:
        (workload, rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists) = (
            WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3,
                          time_esh_1,
                          time_esh_2, time_esh_3, width, length, number_surv, num_shifts))



        PeopleTrapped, TotVol_m3, workreq, ast_time, koff_lum = PeopleTrapped_func(time, landslide_height, surviv,
                                                                                   num_fatalities, rescue, workload,
                                                                                   sublists, tempa, line2, method_power)

        average, group_cnt_sort = dist_func(workreq, surviv)

        # update_table(average)  # Удаляем эту строку, так как она относится к GUI
        # Выводим длины массивов для проверки
        print(f"ast_time: {len(ast_time)}, workload: {len(workload)}")
        return workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum, average, time
    except ZeroDivisionError:
        QMessageBox.critical(None, "Ошибка", "Произошло деление на ноль. Проверьте входные данные.")
    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Произошла ошибка: {str(e)}")

def WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3, time_esh_1,
                  time_esh_2, time_esh_3, width, length, number_surv, num_shifts):
    """
    Функция для расчета трудозатрат.
    """
    dimensions = [height, length, width]
    print("Значения в WorkLoad_func:")
    print(f"  height: {height}")
    print(f"  length: {length}")
    print(f"  width: {width}")
    print(f"  k: {k}")
    print(f"  framework_building: {framework_building}")
    print(f"  method_name: {method_name}")
    print(f"  method_power: {method_power}")
    print(f"  time: {time}")
    print(f"  esh_1: {esh_1}")
    print(f"  esh_2: {esh_2}")
    print(f"  esh_3: {esh_3}")
    print(f"  time_esh_1: {time_esh_1}")
    print(f"  time_esh_2: {time_esh_2}")
    print(f"  time_esh_3: {time_esh_3}")
    print(f"  number_surv: {number_surv}")
    print(f"  num_shifts: {num_shifts}")

    landslide_height = (height * framework_building) / (100 + (height * k))
    debris_volume = 1.25 * landslide_height * number_surv
    buildings.append(BuildingData(height, length, width, debris_volume, method_name, method_power))

    area_value = width * length
    # Используем num_shifts в расчете group_cnt
    group_cnt = int(np.ceil((num_shifts * area_value) / (3.2 * 7)))
    group_cnt_list.append(group_cnt)
    area.append(area_value)

    group_esh = np.round(np.array([esh_1, esh_2, esh_3]) / 7).astype(int)
    group_min = np.minimum(np.round(np.array([esh_1, esh_2, esh_3]) / 7), group_esh).astype(int)

    free_group = [group_esh[0] - group_cnt_list[0]]
    cnt_index, esh_index, cnt_esh_index, sum_group_esh = 1, 1, 0, np.sum(group_esh)
    if number_surv <= 0 or debris_volume <= 0 or any(v <= 0 for v in dimensions):
        QMessageBox.warning(None, "Ошибка", "Некорректные параметры здания или число выживших.")
        return None, None, None, None, None, None, None

    while cnt_index < len(group_cnt_list):
        last_value = free_group[-1]
        if last_value < 0:
            if esh_index < len(group_esh):
                free_group.append(last_value + group_esh[esh_index])
                esh_index += 1
            elif sum_group_esh > group_cnt_list[cnt_esh_index]:
                free_group.append(last_value + group_cnt_list[cnt_esh_index])
            else:
                free_group.append(last_value + sum_group_esh)
            cnt_esh_index = (cnt_esh_index + 1) % len(group_cnt_list)
        else:
            free_group.append(last_value - group_cnt_list[cnt_index])
            cnt_index += 1

    if free_group[-1] < 0:
        cnt_index = 1

    sublists = []
    current_sublist = []
    for value in free_group:
        if value >= 0:
            current_sublist.append(value)
            sublists.append(current_sublist)
            current_sublist = []
        else:
            current_sublist.append(value)
    if current_sublist:
        sublists.append(current_sublist)

    free_group = [num for num in free_group if num >= 0][:len(group_cnt_list)]

    # Словарь для хранения workload для каждого события
    event_workloads = {}

    # Цикл по событиям (по прибытию каждого эшелона)
    for event_index in range(len(group_esh)):
        # Ключ для идентификации события
        event_key = (esh_1, esh_2, esh_3, time_esh_1, time_esh_2, time_esh_3)

        # Проверяем, был ли workload уже рассчитан для этого события
        if event_key not in event_workloads:
            cumulativeWorks = []
            for group_index, group_cnt in enumerate(group_cnt_list):
                cumulativeWork = [(free_group[group_index - 1] * 7) / 2 if group_index > 0 else 0]
                sum_esh = 0
                for i, esh in enumerate(group_esh):
                    sum_esh += esh
                    if sum_esh <= group_cnt:
                        cumulativeWork.append(cumulativeWork[-1] + (group_min[i] * 7) / 2)
                    elif sum_esh - esh <= group_cnt:
                        cumulativeWork.append((group_cnt * 7) / 2)
                        break
                cumulativeWorks.append(cumulativeWork[1:])

            # Расчет workload для текущего события
            workload = np.zeros(time)
            intensity_ranges = [
                (int(time_esh_1), int(time_esh_2),
                 cumulativeWorks[0][0] if len(cumulativeWorks) > 0 and len(
                     cumulativeWorks[0]) > 0 else 0),
                (int(time_esh_2), int(time_esh_3),
                 cumulativeWorks[0][1] if len(cumulativeWorks) > 0 and len(
                     cumulativeWorks[0]) > 1 else 0),
                (int(time_esh_3), time,
                 cumulativeWorks[0][2] if len(cumulativeWorks) > 0 and len(
                     cumulativeWorks[0]) > 2 else 0)
            ]
            for start, end, intensity in intensity_ranges:
                workload[start:end] = intensity

            if len(cumulativeWorks[0]) < 3 and len(workload) < number_surv:
                workload = np.concatenate((workload, np.full(number_surv - len(workload),
                                                           workload[-1] if workload.size > 0 else 0)))

            event_workloads[event_key] = workload

        # Используйте workload из словаря для текущего события
        current_workload = event_workloads[event_key]

        # Расчет rescue
    rescue = []
    for i in np.cumsum(current_workload):
        value = min(round(i / ((debris_volume * 6.8) / number_surv)),
                    number_surv) if number_surv != 0 else 0
        rescue.append(value)
        if value >= number_surv:
            break

    print("Длина workloads[-1]:", len(current_workload))
    print("Длина rescue:", len(rescue))
    print("Кол-во групп с эшелонов", group_esh)
    print(" Необходимое кол-во групп исходя из площади", group_cnt_list)
    print("список свободных групп", free_group)

    # Возвращаем workload для последнего события
    return current_workload, rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists


def PeopleTrapped_func(time, landslide_height, rescue, num_fatalities, surviv, workload, sublists, tempa, line2,
                       method_power):
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
    PeopleTrapped = [math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i]))
                     for i in range(min(len(rescue), len(num_fatalities), len(surviv)))
                     if math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i])) >= 0]

    # Находим количество нулей в начале workload
    leading_zeros = 0
    for value in workload:
        if value == 0:
            leading_zeros += 1
        else:
            break

    # ОБНОВЛЯЕМ PeopleTrapped
    PeopleTrapped_1 = [PeopleTrapped[0]] * leading_zeros + PeopleTrapped[leading_zeros:]

    TotVol_m3 = [round(1.25 * landslide_height * PeopleTrapped_1[i], 2) for i in
                 range(min(time, len(PeopleTrapped)))]

    # Изменение расчета workreq
    workreq = [
        int(float(TotVol_m3[i]) * (6.8 if method_power == "Кирпич" else 10.8) * tempa * float(koff_lum[i]))
        for i in range(len(TotVol_m3))]

    # Добавляем фиктивный элемент в конец workreq
    workreq.append(0)  # Теперь длины workreq и surviv совпадают

    print("workreq", workreq)
    min_length = min(len(workreq), len(workload))
    # Проверяем, существует ли список и является ли первый элемент списка списком
    if not final or not isinstance(final[0], list):
        final.append([])

    try:
        new_values = [min(i / w if w != 0 else 0, 1) for w, i in
                      zip_longest(workreq[:min_length], workload[:min_length], fillvalue=0)]
    except ZeroDivisionError:
        QMessageBox.critical(None, "Ошибка", "Произошло деление на ноль. Проверьте входные данные.")
        return None, None, None, None, None

    if final[0]:
        final[0] = [sum(x) for x in zip_longest(final[0], new_values, fillvalue=0)]
    else:
        final[0] = new_values
    print("Длина PeopleTrapped:", len(PeopleTrapped))
    print("Длина TotVol_m3:", len(TotVol_m3))
    print("Длина workreq:", len(workreq))
    print("Размер final:", len(final))  # Если final - список, то len(final)
    return PeopleTrapped, TotVol_m3, workreq, ast_time, koff_lum


def dist_func(workreq, surviv):
    # Делим первое число списка на количество выживших и добавляем в список
    Kq.append(7 / workreq[0])
    Nu = [Kq[i] / sum(Kq) for i in range(len(Kq))]
    num_surv.append(int(surviv[0]))
    weights = [num_surv[i] / sum(num_surv) for i in range(len(num_surv))]
    # Вычисление нового average
    average = [weights[i] * Nu[i] for i in range(len(weights))]
    group_cnt_average = [(group_cnt_list[i], average[i]) for i in range(len(group_cnt_list))]
    # Затем сортируем значения в group_cnt_with_average и извлекаем отсортированные значения group_cnt
    group_cnt_sort = [value for value, _ in sorted(group_cnt_average, key=lambda x: x[1], reverse=True)]
    print(average)
    return average, group_cnt_sort


def get_time_range_result(data):
    """
    Функция для получения результата в зависимости от времени.
    """
    time_ranges = {
        (0, 7): 1,
        (8, 9): 0.6,
        (10, 18): 0.7,
        (19, 20): 0.65,
        (21, 23): 0.9
    }
    return 1 if data == 24 else next((value for (start, end), value in time_ranges.items() if start <= data <= end), 0)