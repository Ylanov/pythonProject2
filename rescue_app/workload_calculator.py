import numpy as np
from PyQt5.QtWidgets import QMessageBox


def calculate_landslide_height(height, k, framework_building):
    """
    Функция для расчета высоты завала.
    """
    landslide_height = (height * framework_building) / (100 + (height * k))
    return landslide_height


def calculate_debris_volume(landslide_height, number_surv):
    """
    Функция для расчета объема завала.
    """
    debris_volume = 1.25 * landslide_height * number_surv
    return debris_volume


def calculate_group_count(num_shifts, width, length):
    """
    Функция для расчета необходимого количества групп.
    """
    area_value = width * length
    group_cnt = int(np.ceil((num_shifts * area_value) / (3.2 * 7)))
    return group_cnt


def calculate_group_distribution(group_esh, group_cnt_list):
    """
    Функция для расчета распределения групп по эшелонам.
    """
    free_group = [group_esh[0] - group_cnt_list[0]]
    cnt_index, esh_index, cnt_esh_index, sum_group_esh = 1, 1, 0, np.sum(group_esh)

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
    return free_group, sublists


def calculate_workload(time, group_esh, group_min, free_group, group_cnt_list,
                       time_esh_1, time_esh_2, time_esh_3, number_surv):
    """
    Функция для расчета трудозатрат.
    """
    # Словарь для хранения workload для каждого события
    event_workloads = {}

    # Цикл по событиям (по прибытию каждого эшелона)
    for event_index in range(len(group_esh)):
        # Ключ для идентификации события
        event_key = (time_esh_1, time_esh_2, time_esh_3)

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
        return current_workload, cumulativeWorks


def calculate_rescue(workload, debris_volume, number_surv):
    """
    Функция для расчета количества спасенных.
    """
    rescue = []
    for i in np.cumsum(workload):
        value = min(round(i / ((debris_volume * 6.8) / number_surv)),
                    number_surv) if number_surv != 0 else 0
        rescue.append(value)
        if value >= number_surv:
            break
    return rescue


def WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3, time_esh_1,
                  time_esh_2, time_esh_3, width, length, number_surv, num_shifts):
    """
    Основная функция для расчета трудозатрат и других параметров.
    """
    dimensions = [height, length, width]
    if number_surv <= 0 or any(v <= 0 for v in dimensions):
        QMessageBox.warning(None, "Ошибка", "Некорректные параметры здания или число выживших.")
        return None, None, None, None, None, None, None

    landslide_height = calculate_landslide_height(height, k, framework_building)
    debris_volume = calculate_debris_volume(landslide_height, number_surv)
    group_cnt = calculate_group_count(num_shifts, width, length)
    group_esh = np.round(np.array([esh_1, esh_2, esh_3]) / 7).astype(int)
    group_min = np.minimum(np.round(np.array([esh_1, esh_2, esh_3]) / 7), group_esh).astype(int)
    free_group, sublists = calculate_group_distribution(group_esh, [group_cnt])
    workload, cumulativeWorks = calculate_workload(time, group_esh, group_min, free_group, [group_cnt],
                                                   time_esh_1, time_esh_2, time_esh_3, number_surv)
    rescue = calculate_rescue(workload, debris_volume, number_surv)

    return workload, rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists