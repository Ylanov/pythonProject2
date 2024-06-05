from PyQt5.QtWidgets import QMessageBox
from workload_calculator import WorkLoad_func  # Импортируем функцию из файла
from people_trapped_calculator import PeopleTrapped_func

buildings = []  # Список для хранения объектов BuildingData
num_surv = []
Kq = []
group_cnt_list = []
area = []
final = [[]]
column_3 = []
column_4 = []
# В начале файла building_data.py
calculation_cache = {}
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
    # Создаем ключ для кеша из параметров функции
    cache_key = (height, width, length, k, framework_building, method_name, desruction_full, method_power,
                 tuple(surviv), time, esh_1, esh_2, esh_3, time_esh_1, time_esh_2, time_esh_3, number_surv,
                 tuple(num_fatalities), tempa, line2.text() if line2 else None, num_shifts)

    # Проверяем, есть ли результат в кеше
    if cache_key in calculation_cache:
        return calculation_cache[cache_key]

    try:
        (workload, rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists) = (
            WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3,
                          time_esh_1,
                          time_esh_2, time_esh_3, width, length, number_surv, num_shifts))

        PeopleTrapped, TotVol_m3, workreq, ast_time, koff_lum = PeopleTrapped_func(
            time, landslide_height, surviv, num_fatalities, rescue, workload,
            sublists, tempa, line2, method_power, final  # Передаем final как аргумент
        )

        average, group_cnt_sort = dist_func(workreq, surviv)

        # update_table(average)  # Удаляем эту строку, так как она относится к GUI
        # Выводим длины массивов для проверки
        print(f"ast_time: {len(ast_time)}, workload: {len(workload)}")
        # Сохраняем результат в кеше
        calculation_cache[cache_key] = (
        workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum, average, time)
        return workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum, average, time
    except ZeroDivisionError:
        QMessageBox.critical(None, "Ошибка", "Произошло деление на ноль. Проверьте входные данные.")
    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Произошла ошибка: {str(e)}")


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