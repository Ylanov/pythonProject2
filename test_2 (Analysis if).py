import random
import sys
from itertools import zip_longest, accumulate
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QLineEdit, QGridLayout, QHeaderView, QTabWidget, QWidget, QTableWidget,
                             QTableWidgetItem, QMessageBox, QFileDialog, QScrollArea)
from PyQt5.QtCore import Qt, QSettings
import pyqtgraph as pg
import numpy as np
import pandas as pd
import csv
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from reportlab.pdfgen import canvas
import math

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QCheckBox, QSpinBox, QComboBox, QDialogButtonBox)


class WhatIfDialog(QDialog):
    def __init__(self, original_values, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Анализ \"что если\"")

        self.original_values = original_values
        self.scenario_widgets = {}  # Словарь для хранения виджетов сценариев

        # UI элементы для выбора параметров
        self.create_parameter_groupboxes()

        # UI элементы для выбора критерия
        self.criterion_combobox = QComboBox()
        self.criterion_combobox.addItems(["Максимум спасённых", "Минимум пострадавших", "Минимум времени"])
        criterion_layout = QHBoxLayout()
        criterion_layout.addWidget(QLabel("Критерий:"))
        criterion_layout.addWidget(self.criterion_combobox)

        # Кнопки OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.parameters_groupbox)
        main_layout.addLayout(criterion_layout)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def create_parameter_groupboxes(self):
        self.parameters_groupbox = QGroupBox("Параметры сценариев")
        parameters_layout = QVBoxLayout()

        parameter_definitions = {
            "stage_1_time": ("Время прибытия 1-го эшелона (час)", [1, 2, 5]),
            "stage_2_time": ("Время прибытия 2-го эшелона (час)", [1, 2, 5]),
            "stage_3_time": ("Время прибытия 3-го эшелона (час)", [1, 2, 5]),
            "stage_1_count": ("Число спасателей 1-го эшелона (чел)", [0.5, 2]),
            "stage_2_count": ("Число спасателей 2-го эшелона (чел)", [0.5, 2]),
            "stage_3_count": ("Число спасателей 3-го эшелона (чел)", [0.5, 2])
        }

        for param_name, (param_label, multipliers) in parameter_definitions.items():
            checkbox = QCheckBox(param_label)
            self.scenario_widgets[param_name] = {
                "checkbox": checkbox,
                "spin_boxes": []
            }

            hbox = QHBoxLayout()
            hbox.addWidget(checkbox)

            for multiplier in multipliers:
                spin_box = QSpinBox()
                spin_box.setRange(-10, 10)
                # Исправление: просто используем multiplier
                spin_box.setValue(int(multiplier))
                spin_box.setEnabled(False)
                checkbox.stateChanged.connect(lambda state, sb=spin_box: sb.setEnabled(state == Qt.Checked))
                hbox.addWidget(spin_box)
                self.scenario_widgets[param_name]["spin_boxes"].append(spin_box)

            parameters_layout.addLayout(hbox)

        self.parameters_groupbox.setLayout(parameters_layout)

    def get_scenarios(self):
        scenarios = [
            {"label": "Базовый сценарий"}  # Базовый сценарий без изменений
        ]

        for param_name, widgets in self.scenario_widgets.items():
            if widgets["checkbox"].isChecked():
                for spin_box in widgets["spin_boxes"]:
                    # Создаем новый сценарий с измененным параметром
                    new_scenario = {
                        "label": f"Изменение {param_name} на {spin_box.value() * 0.1 if isinstance(spin_box.value(), float) else spin_box.value()}"}
                    new_scenario[param_name] = self.original_values[param_name] * (
                        spin_box.value() * 0.1 if isinstance(spin_box.value(), float) else spin_box.value())
                    scenarios.append(new_scenario)

        return scenarios

    def get_criterion(self):
        criterion_text = self.criterion_combobox.currentText()
        if criterion_text == "Максимум спасённых":
            return "rescue"  # Ключ для доступа к данным о спасённых
        elif criterion_text == "Минимум пострадавших":
            return "num_fatalities"  # Ключ для доступа к данным о пострадавших
        elif criterion_text == "Минимум времени":
            return "time_total"  # Ключ для доступа к данным о времени операции
        else:
            return None
class BuildingData:
    def __init__(self, height, length, width, debris_volume, method_name, method_power):
        self.height = height
        self.length = length
        self.width = width
        self.debris_volume = debris_volume
        self.method_name = method_name
        self.method_power = method_power


buildings = []
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
    }
}


def create_label(text, tooltip=None):
    label = QLabel(text)
    if tooltip:
        label.setToolTip(tooltip)
    return label


def create_line_edit(tooltip=None):
    line_edit = QLineEdit()
    if tooltip:
        line_edit.setToolTip(tooltip)
    return line_edit


def create_combobox(items, tooltip=None):
    combobox = QComboBox()
    combobox.addItems(items)
    if tooltip:
        combobox.setToolTip(tooltip)
    return combobox


def get_time_range_result(data):
    time_ranges = {
        (0, 7): 1,
        (8, 9): 0.6,
        (10, 18): 0.7,
        (19, 20): 0.65,
        (21, 23): 0.9
    }
    return 1 if data == 24 else next((value for (start, end), value in time_ranges.items() if start <= data <= end), 0)


def calculate_data(height, width, length, k, framework_building, method_name, desruction_full, method_power, surviv,
                   time, esh_1, esh_2, esh_3, time_esh_1, time_esh_2, time_esh_3, number_surv, num_fatalities, tempa):
    try:
        (workload, rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists) = (
            WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3,
                          time_esh_1,
                          time_esh_2, time_esh_3, width, length, number_surv))

        print("Результат WorkLoad_func:")
        print(f"  workload: {workload}")
        print(f"  rescue: {rescue}")
        print(f"  group_esh: {group_esh}")
        print(f"  group_min: {group_min}")
        print(f"  cumulativeWorks: {cumulativeWorks}")
        print(f"  landslide_height: {landslide_height}")
        print(f"  sublists: {sublists}")

        PeopleTrapped, TotVol_m3, workreq, ast_time, koff_lum = PeopleTrapped_func(time, landslide_height, surviv,
                                                                                   num_fatalities, rescue, workload,
                                                                                   sublists, tempa)

        print("Результат PeopleTrapped_func:")
        print(f"  PeopleTrapped: {PeopleTrapped}")
        print(f"  TotVol_m3: {TotVol_m3}")
        print(f"  workreq: {workreq}")
        print(f"  ast_time: {ast_time}")
        print(f"  koff_lum: {koff_lum}")

        average, group_cnt_sort = dist_func(workreq, surviv)
        update_table(average)
        return workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum
    except ZeroDivisionError:
        QMessageBox.critical(window, "Ошибка", "Произошло деление на ноль. Проверьте входные данные.")
    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")


def WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3, time_esh_1,
                  time_esh_2, time_esh_3, width, length, number_surv):
    landslide_height = round((height * framework_building) / (100 + (height * k)), 2)
    debris_volume = float(round(1.25 * landslide_height * number_surv, 2))
    buildings.append([height, length, width, debris_volume, method_name, method_power])
    cumulativeWorks, sublists, current_sublist, workloads, rescue = [], [], [], [], []
    for area_value in [width * length]:
        group_cnt, i = 0, 1
        while (i * 3.2 * 7) / 2 < area_value:
            group_cnt += 1
            i += 1
        group_cnt = group_cnt
        group_cnt_list.append(group_cnt)
    area.append(width * length)
    print(area)
    # Заполнение списка group_esh
    group_esh = [round(value / 7) for value in [esh_1, esh_2, esh_3]]
    group_min = [min(round(e / 7), group_esh[index]) for index, e in enumerate([esh_1, esh_2, esh_3][:len(group_esh)])]
    free_group = [group_esh[0] - group_cnt_list[0]]
    cnt_index, esh_index, cnt_esh_index, sum_group_esh = 1, 1, 0, sum(group_esh)
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

    sum_esh, cumulativeWork = 0, [0]  # Начальное значение для кумулятивной суммы первого здания

    for i, esh in enumerate(group_esh):
        sum_esh += esh
        if sum_esh <= group_cnt:
            cumulativeWork.append(cumulativeWork[-1] + (group_min[i] * 7) / 2)
        elif sum_esh - esh <= group_cnt:
            cumulativeWork.append((group_cnt * 7) / 2)
            break

    cumulativeWorks.append(cumulativeWork[1:])  # Исключаем изначальный ноль

    # Начинаем с индекса 1
    for group_index, group_cnt in enumerate(group_cnt_list[1:], start=1):  # Начинаем с индекса 1
        # Вычисляем начальное значение из free_group
        initial_value = (free_group[group_index - 1] * 7) / 2
        cumulativeWork = [initial_value]

        for i, esh in enumerate(group_esh):
            if sum(group_esh) <= group_cnt:
                next_value = sum(group_esh) * 7 / 2
                cumulativeWork[0] = max(initial_value, next_value)
                print(f"Сработала стадия {i + 4}")
                break
            elif sum(group_esh) - esh >= group_cnt:
                next_value = group_cnt * 7 / 2
                cumulativeWork[0] = max(initial_value, next_value)
                print(f"Сработала стадия {i + 4}")
                break

        cumulativeWorks.append(cumulativeWork)  # Добавление результатов в список

    for work in cumulativeWorks:
        print(work)

    for index, cumulativeWork in enumerate(cumulativeWorks):
        # Инициализация рабочей нагрузки нулями для текущего списка
        workload = [0] * time  # Создает список с 'time' количеством нулей
        # Создание intensity_ranges для текущего списка
        intensity_ranges = [
            (int(time_esh_1), int(time_esh_2), cumulativeWork[0] if len(cumulativeWork) > 0 else 0),
            (int(time_esh_2), int(time_esh_3), cumulativeWork[1] if len(cumulativeWork) > 1 else 0),
            (int(time_esh_3), time, cumulativeWork[2] if len(cumulativeWork) > 2 else 0)
        ]

        # Обновление workload для каждого диапазона в intensity_ranges
        for start, end, intensity in intensity_ranges:
            for time_stamp in range(start, end):
                workload[time_stamp] = intensity
        # Обрезать список с конца, удаляя нули
        while workload and workload[-1] == 0:
            workload.pop()
            # Если в cumulativeWork меньше трех значений, продолжаем последнее значение до number_surv
        if len(cumulativeWork) < 3 and len(workload) < number_surv:
            if workload:
                workload.extend([workload[-1]] * (number_surv - len(workload)))
            else:
                # Если список workload пустой, нужно инициализировать его некоторым значением
                # Это значение зависит от вашей бизнес-логики
                initial_value = 0
                workload.extend([initial_value] * number_surv)
        # Добавление обработанного списка workload в итоговый список workloads
        workloads.append(workload)
    # Вычисляем значения для списка rescue и останавливаемся, когда достигаем number_surv
    for i in accumulate(workloads[-1]):
        if number_surv != 0:
            value = min(round(i / ((float(debris_volume) * 6.8) / number_surv)), number_surv)
        else:
            # Обработка случая, когда number_surv равно нулю
            # Например, можно присвоить переменной value некоторое значение по умолчанию
            value = 0
        rescue.append(value)
        if value >= number_surv:
            break

    print("Кол-во групп с эшелонов", group_esh)
    print(" Необходимое кол-во групп исходя из площади", group_cnt_list)
    print("список свободных групп", free_group)
    return workloads[-1], rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists


def PeopleTrapped_func(time, landslide_height, rescue, num_fatalities, surviv, workload, sublists, tempa):
    ast_time = [str(i % 25) for i in range(int(line2.text() or 0), time + 1)]
    koff_lum = ['1' if 7 <= int(it) <= 18 else '1.5' for it in ast_time]
    PeopleTrapped = [math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i]))
                     for i in range(min(len(rescue), len(num_fatalities), len(surviv)))
                     if math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i])) >= 0]
    TotVol_m3 = [round(1.25 * landslide_height * PeopleTrapped[i], 2) for i in
                 range(min(time, len(PeopleTrapped)))]
    workreq = [int(float(TotVol_m3[i]) * 6.8 * tempa * float(koff_lum[i])) for i in range(len(TotVol_m3))]
    print("workreq", workreq)
    min_length = min(len(workreq), len(workload))
    # Проверяем, существует ли список и является ли первый элемент списка списком
    if not final or not isinstance(final[0], list):
        final.append([])

    # Вычисляем новые значения, которые должны быть добавлены или суммированы
        # Вычисляем новые значения, которые должны быть добавлены или суммированы
    try:
        new_values = [min(i / w if w != 0 else 0, 1) for w, i in
                      zip_longest(workreq[:min_length], workload[:min_length], fillvalue=0)]
    except ZeroDivisionError:
        QMessageBox.critical(window, "Ошибка", "Произошло деление на ноль. Проверьте входные данные.")
        return None, None, None, None, None  # Возвращаем None для всех значений

    # Если final[0] уже содержит значения, суммируем их с новыми значениями
    if final[0]:
        # Суммируем значения, если оба списка содержат элементы на данной позиции
        final[0] = [sum(x) for x in zip_longest(final[0], new_values, fillvalue=0)]
    else:
        # Если final[0] пуст, просто присваиваем ему новые значения
        final[0] = new_values

        # Создание холстов для графиков
        pw1 = pg.PlotWidget(title="Трудозатраты")
        pw1.addLegend()
        pw1.setLabel('left', 'Трудозатраты, чел., час')
        pw1.setLabel('bottom', 'Время, час')
        pw1.showGrid(x=True, y=True)

        pw2 = pg.PlotWidget(title="Значения показателя эффективности")
        pw2.addLegend()
        pw2.setLabel('left', 'Трудозатраты, чел., час')
        pw2.setLabel('bottom', 'Время, час')
        pw2.showGrid(x=True, y=True)

        # Добавление графиков
        pw1.plot(workreq, pen='b', name='Необходимые трудозатраты')
        pw1.plot(workload, pen='r', name='Задействованные трудозатраты')

        for i, sublist in enumerate(final):
            pw2.plot(sublist, pen=(i, len(final)), name=f"Здание {i + 1}")

        # Добавление графиков в layout
        grid_layout1.addWidget(pw1, 2, 0)
        grid_layout1.addWidget(pw2, 2, 1)

        # Находим индекс вкладки "Итог"
    tab_index = find_tab_index(tabWidget, "Итог")
    if tab_index == -1:
        new_tab = QWidget()
        table_widget = QTableWidget()
        new_tab.setLayout(QVBoxLayout())
        new_tab.layout().addWidget(table_widget)
        tab_index = tabWidget.addTab(new_tab, "Итог")
    else:
        table_widget = tabWidget.widget(tab_index).findChild(QTableWidget)

    tabWidget.setCurrentIndex(tab_index)

    # Настройка столбцов таблицы, если только что создали вкладку
    if table_widget.columnCount() == 0:
        table_widget.setColumnCount(5)
        table_widget.setHorizontalHeaderLabels(
            ["Здания", "Группы", "Комментарий", "Время проведения работ", "Кол-во спасенных"])

    # Подготовка данных для вставки в таблицу
    table_widget.setRowCount(len(sublists))
    table_widget.clearContents()

    for index, work in enumerate(sublists):
        comment = "Необходимо {} групп".format(abs(work[-1])) if work and work[-1] < 0 else (
            "В запасе {} групп, Завершено".format(work[-1])) if work else ""
        table_widget.setItem(index, 0, QTableWidgetItem(str(index + 1)))
        table_widget.setItem(index, 1, QTableWidgetItem(str(work)))
        table_widget.setItem(index, 2, QTableWidgetItem(comment))
        column_3.append(str(len(TotVol_m3)))
        column_4.append(str(rescue[len(TotVol_m3) - 1]))
    for index, value in enumerate(column_3):
        table_widget.setItem(index, 3, QTableWidgetItem(value))
    for index, value in enumerate(column_4):
        table_widget.setItem(index, 4, QTableWidgetItem(value))
    if len(sublists) > 1:
        previous_row_index = len(sublists) - 2  # Индекс предыдущей строки
        table_widget.item(previous_row_index, 2).setText("Завершено")
    table_widget.resizeColumnsToContents()

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


def update_table(average):
    # Сначала отключим обновление виджета, чтобы избежать лишних перерисовок
    table_min.setSortingEnabled(False), table_min.blockSignals(True), table_min.setUpdatesEnabled(False)
    # Сортировка данных
    combined_data = sorted(zip(buildings, average), key=lambda x: (x[1], x[0][3]), reverse=True)
    table_min.setRowCount(len(combined_data))

    # Заполнение таблицы данными
    for row, (building, dist) in enumerate(combined_data):
        table_min.setItem(row, 0, QTableWidgetItem(f"Здание №{row + 1}"))
        for column, data in enumerate(building):
            item_data = str(round(data, 2)) if isinstance(data, (int, float)) else str(data)
            table_min.setItem(row, column + 1, QTableWidgetItem(item_data))
        table_min.setItem(row, len(building) + 1, QTableWidgetItem(str(round(dist, 2))))

    # Включаем обновление виджета после внесения изменений
    table_min.setSortingEnabled(True), table_min.blockSignals(False), table_min.setUpdatesEnabled(True)
    table_min.viewport().update()



def clear_input_fields(*input_fields):
    for field in input_fields:
        if hasattr(field, 'clear') and callable(getattr(field, 'clear')):
            field.clear()


def add_building(scenario=None):
    # Применяем изменения из scenario, если он передан
    if scenario:
        for key, value in scenario.items():
            if key != 'label' and isinstance(value, (int, float, str)):
                locals()[key] = value  # Изменяем локальные переменные

    dimensions = [float(height_line.text()), float(length_line.text()), float(width_line.text())]
    time = int(line_edit_1.text())
    stage_values = [float(line_stage_1.text()), float(line_stage_2.text()),
                    float(line_stage_3.text()),
                    float(line_stage_4.text()), float(line_stage_5.text()), float(line_stage_6.text())]
    table_max.setRowCount(time)

    survivor_args = subject_methods["survivors"].get(subject_combo.currentText())
    building_args = subject_methods["buildings"].get(building_combo.currentText())
    disaster_intensity = subject_methods["intensity"].get(values_combo.currentText())
    tempa_args = subject_methods["tempa"].get(tempa_combo.currentText())

    number_surv = round(math.ceil((get_time_range_result(int(line2.text() or 0)) * int(label3.text() or 0)) * 0.4))
    surviv = [str(round((-0.16 * math.log1p(i) + 0.9107) * number_surv)) for i in range(time + 1)]
    surviv.insert(0, str(number_surv))
    num_fatalities = [0] + [str(math.floor(float(surviv[i]) - float(surviv[i + 1]))) for i in range(len(surviv) - 1)]

    if building_args:
        print("Входные данные для calculate_data:")
        print(f"  height: {dimensions[0]}")
        print(f"  width: {dimensions[2]}")
        print(f"  length: {dimensions[1]}")
        print(f"  k: {disaster_intensity}")
        print(f"  framework_building: {building_args[0]}")
        print(f"  method_name: {survivor_args[1]}")
        print(f"  desruction_full: {survivor_args[0]}")
        print(f"  method_power: {building_args[1]}")
        print(f"  surviv: {surviv}")
        print(f"  time: {time}")
        print(f"  esh_1: {stage_values[0]}")
        print(f"  esh_2: {stage_values[1]}")
        print(f"  esh_3: {stage_values[2]}")
        print(f"  time_esh_1: {stage_values[3]}")
        print(f"  time_esh_2: {stage_values[4]}")
        print(f"  time_esh_3: {stage_values[5]}")
        print(f"  number_surv: {number_surv}")
        print(f"  num_fatalities: {num_fatalities}")
        print(f"  tempa: {tempa_args}")

        calculation_result = calculate_data(height=dimensions[0], width=dimensions[2], length=dimensions[1],
                                            k=disaster_intensity, framework_building=building_args[0],
                                            method_name=survivor_args[1],
                                            desruction_full=survivor_args[0], method_power=building_args[1],
                                            surviv=surviv,
                                            time=time, esh_1=stage_values[0], esh_2=stage_values[1],
                                            esh_3=stage_values[2],
                                            time_esh_1=stage_values[3], time_esh_2=stage_values[4],
                                            time_esh_3=stage_values[5],
                                            number_surv=number_surv, num_fatalities=num_fatalities,
                                            tempa=tempa_args)

        if calculation_result is None:
            print("calculate_data вернула None")
        else:
            (workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum) = calculation_result
            print("calculate_data вернула результат")

        # Проверяем результат вычислений
        if calculation_result is not None:
            (workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum) = calculation_result

            table_max.clearContents()
            table_max.setRowCount(len(TotVol_m3))

            for row_index, values in enumerate(zip(TotVol_m3, PeopleTrapped, surviv, rescue,
                                                   num_fatalities, workload, ast_time, koff_lum, workreq)):
                set_table_items(table_max, row_index, values)

            new_tab = QWidget()
            new_table_widget = copy_table(table_max)
            new_tab.setLayout(QVBoxLayout())
            new_tab.layout().addWidget(new_table_widget)
            tab_index = tabWidget.addTab(new_tab, f"Здание {tabWidget.count()}")
            tabWidget.setCurrentIndex(tab_index)

            # Возвращаем все 9 значений
            return workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum, num_fatalities, surviv

        else:
            # Выводим сообщение об ошибке
            QMessageBox.warning(window, "Ошибка", "Не удалось рассчитать данные для здания. Проверьте входные параметры.")
            return None, None, None, None, None, None, None, None, None


def randomize(line_edits, ranges):
    for line_edit, number_range in zip(line_edits, custom_ranges):
        random_number = random.randint(number_range[0], number_range[1])
        line_edit.setText(str(random_number))


def set_table_items(table, row_index, values):
    for column_index, value in enumerate(values):
        table.setItem(row_index, column_index, QTableWidgetItem(str(value)))


def copy_table(source):
    target = QTableWidget(source.rowCount(), source.columnCount())
    target.setHorizontalHeaderLabels([
        source.horizontalHeader().model().headerData(i, Qt.Horizontal)
        for i in range(source.columnCount())
    ])
    for row in range(source.rowCount()):
        for column in range(source.columnCount()):
            if item := source.item(row, column):
                target.setItem(row, column, item.clone())
    return target


def find_tab_index(tab_widget, name):
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == name:
            return i
    return -1


def hbox(*widgets):
    layout = QHBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def validate_input():
    try:
        height = float(height_line.text())
        length = float(length_line.text())
        width = float(width_line.text())
        time = int(line_edit_1.text())
        time_esh_1 = int(line_stage_4.text())
        time_esh_2 = int(line_stage_5.text())
        time_esh_3 = int(line_stage_6.text())
        people_count = int(label3.text())

        if height <= 0:
            raise ValueError("Высота здания должна быть положительным числом.")
        if length <= 0:
            raise ValueError("Длина здания должна быть положительным числом.")
        if width <= 0:
            raise ValueError("Ширина здания должна быть положительным числом.")
        if time <= 0:
            raise ValueError("Общее время проведения операции должно быть положительным числом.")
        if people_count <= 0:
            raise ValueError("Количество людей в здании должно быть положительным числом.")
        if not (1 <= time_esh_1 <= 24):
            raise ValueError("Время прибытия первого эшелона должно быть в пределах от 1 до 24 часов.")
        if not (1 <= time_esh_2 <= 24):
            raise ValueError("Время прибытия второго эшелона должно быть в пределах от 1 до 24 часов.")
        if not (1 <= time_esh_3 <= 24):
            raise ValueError("Время прибытия третьего эшелона должно быть в пределах от 1 до 24 часов.")

        return True
    except ValueError as e:
        QMessageBox.warning(window, "Ошибка валидации", str(e))
        print("validate_input вернула False")
        return False
    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")
        return False


def export_to_csv():
    try:
        file_path, _ = QFileDialog.getSaveFileName(window, "Экспорт в CSV", "", "CSV files (*.csv)")
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Записываем заголовки столбцов
                writer.writerow([table_min.horizontalHeaderItem(i).text() for i in range(table_min.columnCount())])
                # Записываем данные из таблицы
                for row in range(table_min.rowCount()):
                    row_data = []
                    for col in range(table_min.columnCount()):
                        item = table_min.item(row, col)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    writer.writerow(row_data)
            QMessageBox.information(window, "Успех", "Данные успешно экспортированы в CSV файл.")

    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")


def export_to_excel():
    try:
        file_path, _ = QFileDialog.getSaveFileName(window, "Экспорт в Excel", "", "Excel files (*.xlsx)")
        if file_path:
            # Создаем DataFrame из данных таблицы
            df = pd.DataFrame(
                [[table_min.item(row, col).text() for col in range(table_min.columnCount())] for row in
                 range(table_min.rowCount())],
                columns=[table_min.horizontalHeaderItem(i).text() for i in range(table_min.columnCount())]
            )

            # Сохраняем DataFrame в Excel файл
            wb = openpyxl.Workbook()
            ws = wb.active
            for r in dataframe_to_rows(df, index=False, header=True):
                ws.append(r)
            wb.save(file_path)
            QMessageBox.information(window, "Успех", "Данные успешно экспортированы в Excel файл.")

    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")


def export_to_pdf():
    try:
        file_path, _ = QFileDialog.getSaveFileName(window, "Экспорт в PDF", "", "PDF files (*.pdf)")
        if file_path:
            c = canvas.Canvas(file_path)
            c.drawString(100, 750, "Данные из таблицы:")

            # Устанавливаем начальные координаты
            x = 100
            y = 700

            # Вычисляем ширину столбцов
            col_widths = [table_min.columnWidth(i) / 5 for i in range(table_min.columnCount())]

            # Записываем данные из таблицы
            for row in range(table_min.rowCount()):
                for col in range(table_min.columnCount()):
                    item = table_min.item(row, col)
                    if item is not None:
                        c.drawString(x, y, item.text())
                    x += col_widths[col]
                x = 100
                y -= 20

            c.save()
            QMessageBox.information(window, "Успех", "Данные успешно экспортированы в PDF файл.")

    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")


def save_project():
    try:
        file_path, _ = QFileDialog.getSaveFileName(window, "Сохранить проект", "", "JSON files (*.json)")
        if file_path:
            settings = QSettings(file_path, QSettings.IniFormat)
            # Сохраняем данные зданий
            settings.beginWriteArray("Buildings")
            for i, building in enumerate(buildings):
                settings.setArrayIndex(i)
                settings.setValue("height", building.height)
                settings.setValue("length", building.length)
                settings.setValue("width", building.width)
                settings.setValue("debris_volume", building.debris_volume)
                settings.setValue("method_name", building.method_name)
                settings.setValue("method_power", building.method_power)
            settings.endArray()
            # Сохраняем другие параметры проекта
            # ...
            QMessageBox.information(window, "Успех", "Проект успешно сохранен.")
    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")


def load_project():
    try:
        file_path, _ = QFileDialog.getOpenFileName(window, "Загрузить проект", "", "JSON files (*.json)")
        if file_path:
            settings = QSettings(file_path, QSettings.IniFormat)
            # Загружаем данные зданий
            size = settings.beginReadArray("Buildings")
            buildings.clear()
            for i in range(size):
                settings.setArrayIndex(i)
                buildings.append(BuildingData(
                    settings.value("height"),
                    settings.value("length"),
                    settings.value("width"),
                    settings.value("debris_volume"),
                    settings.value("method_name"),
                    settings.value("method_power")
                ))
            settings.endArray()
            # Загружаем другие параметры проекта
            # ...
            update_table([0] * len(buildings))  # Обновляем таблицу после загрузки данных
            QMessageBox.information(window, "Успех", "Проект успешно загружен.")
    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")


# --------------------- Функция анализа "что если" -------------------------

def analyze_what_if():
    """
    Функция, реализующая анализ "что если".
    """

    # 1. Получаем значения параметров из GUI и сохраняем их
    original_values = {
        'height': float(height_line.text()),
        'length': float(length_line.text()),
        'width': float(width_line.text()),
        'time_total': int(line_edit_1.text()),
        'people_count': int(label3.text()),
        'stage_1_count': int(line_stage_1.text()),
        'stage_2_count': int(line_stage_2.text()),
        'stage_3_count': int(line_stage_3.text()),
        'stage_1_time': float(line_stage_4.text()),
        'stage_2_time': float(line_stage_5.text()),
        'stage_3_time': float(line_stage_6.text()),
        'building_type': building_combo.currentText(),
        'destruction_level': subject_combo.currentText(),
        'tempa': tempa_combo.currentText()
    }
    print('список', original_values)
    # 2. Диалог для выбора сценариев и критерия
    dialog = WhatIfDialog(original_values)
    if dialog.exec_() == QDialog.Accepted:
        scenarios = dialog.get_scenarios()
        criterion = dialog.get_criterion()
    # Словарь для сопоставления ключей с виджетами
    widgets = {
        'height': height_line,
        'length': length_line,
        'width': width_line,
        'time_total': line_edit_1,
        'people_count': label3,
        'stage_1_count': line_stage_1,
        'stage_2_count': line_stage_2,
        'stage_3_count': line_stage_3,
        'stage_1_time': line_stage_4,
        'stage_2_time': line_stage_5,
        'stage_3_time': line_stage_6,
        'building_type': building_combo,
        'destruction_level': subject_combo,
        'tempa': tempa_combo
    }
    # 2. Определяем сценарии для анализа
    scenarios = [
        {"label": "Базовый сценарий"},
        {"label": "Первый эшелон опоздал на 1 час", "stage_1_time": min(original_values['stage_1_time'] + 1, 24)},
        {"label": "Первый эшелон опоздал на 2 часа", "stage_2_time": min(original_values['stage_2_time'] + 2, 24)},
        {"label": "Первый эшелон опоздал на 5 часов", "stage_3_time": min(original_values['stage_3_time'] + 5, 24)},
        {"label": "Удвоенное число спасателей",
         "stage_1_count": min(original_values['stage_1_count'] * 2, 360),
         "stage_2_count": min(original_values['stage_2_count'] * 2, 360),
         "stage_3_count": min(original_values['stage_3_count'] * 2, 360)},
        {"label": "Уменьшенное число спасателей",
         "stage_1_count": max(original_values['stage_1_count'] // 2, 40),
         "stage_2_count": max(original_values['stage_2_count'] // 2, 40),
         "stage_3_count": max(original_values['stage_3_count'] // 2, 40)}
    ]

    # 3. Создаем новую вкладку для результатов анализа
    analysis_tab = QWidget()
    analysis_layout = QVBoxLayout()
    analysis_tab.setLayout(analysis_layout)
    tabWidget.addTab(analysis_tab, "Анализ \"что если\"")

    # 4. Создаем ScrollArea и размещаем её на вкладке
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    analysis_layout.addWidget(scroll_area)

    # 5. Создаем виджет для размещения контента анализа внутри ScrollArea
    scroll_content = QWidget()
    scroll_content_layout = QVBoxLayout()
    scroll_content.setLayout(scroll_content_layout)
    scroll_area.setWidget(scroll_content)

    # 6. Цикл по всем сценариям
    for scenario_index, scenario in enumerate(scenarios):
        # Создаем QLabel для названия сценария
        scenario_label = QLabel(scenario["label"])
        # Добавляем QLabel в layout контента
        scroll_content_layout.addWidget(scenario_label)

        print(f"Сценарий: {scenario['label']}")  # Выводим название сценария
        for key, value in scenario.items():
            if key != 'label' and isinstance(value, (int, float, str)):
                print(f"  {key}: {value} (тип: {type(value)})")  # Выводим значения и их типы
                widget = widgets[key]
                widget.setText(str(value))  # Устанавливаем значения в виджеты

        QApplication.processEvents()  # Обновляем GUI
        # Вызываем функцию add_building с параметром scenario
        workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum, num_fatalities, surviv = add_building(
            scenario=scenario)

        # Проверяем, были ли получены результаты
        if workload is not None:
            # Создаем таблицу для вывода результатов
            results_table = QTableWidget(len(TotVol_m3), 9)
            results_table.setHorizontalHeaderLabels(
                ['Объём завала, м3', 'В завале, чел', 'Выжившие, чел', 'Спасённые, чел',
                 'Пострадавшие, чел', 'Workload', 'Время', 'Освещение', 'Трудозатраты'])
            results_table.horizontalHeader().setDefaultSectionSize(130)
            results_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            # Заполняем таблицу результатами
            for row_index, values in enumerate(zip(TotVol_m3, PeopleTrapped, surviv, rescue,
                                                   num_fatalities, workload, ast_time, koff_lum, workreq)):
                set_table_items(results_table, row_index, values)

            # Добавляем таблицу результатов на вкладку анализа
            scroll_content_layout.addWidget(results_table)
        else:
            # Выводим сообщение об ошибке
            error_label = QLabel("Ошибка: неверные входные данные")
            scroll_content_layout.addWidget(error_label)

        # Убираем изменение GUI после расчета, чтобы не влияло на следующий сценарий
        for key, value in scenario.items():
            if key != 'label' and isinstance(value, (int, float, str)):
                widget = widgets[key]  # Получаем виджет из словаря
                widget.setText(str(original_values[key]))  # Возвращаем исходное значение


app = QApplication(sys.argv)

app.setStyle("Fusion")  # Устанавливаем стиль Fusion

window = QMainWindow()
window.setGeometry(0, 0, 1920, 1080)

# --------------------- Стили CSS ------------------------

style_sheet = """
QGroupBox {
    font-size: 14px;
    margin-top: 5px; 
    padding: 5px;    
}
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
    min-width: 80px;
    max-width: 100px;
    height: 25px;
}
QComboBox {
    min-width: 100px;
}
QGridLayout {
    spacing: 5px; 
}
"""

building_combo = create_combobox(["Кирпич", "Панель"],
                                "Тип здания: влияет на расчет объема завалов.")
subject_combo = create_combobox(["Слабая", "Средняя", "Сильная", "Полная"],
                              "Степень разрушений: влияет на вероятность выживания людей.")
values_combo = create_combobox(["землетрясение", "взрыв вне здания", "взрыв внутри здания"],
                             "Тип чрезвычайной ситуации: влияет на расчет интенсивности.")
tempa_combo = create_combobox(['свыше +25', 'от 0 до +25', 'от -10 до 0', 'от -20 до -10', 'ниже -20'],
                            "Температура воздуха: влияет на трудозатраты.")

labels = [create_label(text, tooltip) for text, tooltip in [
    ('Условия', None),
    ('Высота', "Высота здания в метрах."),
    ('Длина', "Длина здания в метрах."),
    ('Ширина', "Ширина здания в метрах."),
    ('кол-во часов', "Общее время проведения спасательной операции."),
    ('1-эшелон', "Количество спасателей в первом эшелоне."),
    ('2-эшелон', "Количество спасателей во втором эшелоне."),
    ('3-эшелон', "Количество спасателей в третьем эшелоне."),
    ('Время', "Время прибытия первого эшелона (в часах)."),
    ('Время', "Время прибытия второго эшелона (в часах)."),
    ('Время', "Время прибытия третьего эшелона (в часах)."),
    ('Данные о количестве людей из АПК "Безопасный город":', None),
    ('Данные о степени разрушений зданий:', None),
    ('Астрономическое время:', None)
]]
(QLabel5, height_label, length_label, width_label, Line_label_1, stage_label_1, stage_label_2, stage_label_3,
 stage_label_4, stage_label_5, stage_label_6, label1, label2, label4) = labels

line_edits = [create_line_edit(tooltip) for tooltip in [
    "Высота здания в метрах.",
    "Длина здания в метрах.",
    "Ширина здания в метрах.",
    "Общее время проведения спасательной операции.",
    "Астрономическое время начала спасательной операции.",
    "Количество людей в здании.",
    "Количество спасателей в первом эшелоне.",
    "Количество спасателей во втором эшелоне.",
    "Количество спасателей в третьем эшелоне.",
    "Время прибытия первого эшелона (в часах).",
    "Время прибытия второго эшелона (в часах).",
    "Время прибытия третьего эшелона (в часах)."
]]
(height_line, length_line, width_line, line_edit_1, line2, label3, line_stage_1, line_stage_2, line_stage_3,
 line_stage_4, line_stage_5, line_stage_6) = line_edits

table_min = QTableWidget(1, 8)
table_min.setHorizontalHeaderLabels(
    ['№', 'Выс., м', 'Длина, м', 'Шир., м', 'Объём, м3', "Тип", "Разрушение", 'Приоритет'])
table_min.horizontalHeader().setDefaultSectionSize(150)
table_min.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
table_min.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
table_min.resize(800, 600)
tabWidget = QTabWidget()
tabWidget.setFocus()
table_max = QTableWidget(0, 9)
table_max.setHorizontalHeaderLabels(['Объём завала, м3', 'В завале, чел', 'Выжившие, чел', 'Спасённые, чел',
                                     'Пострадавшие, чел', 'Workload', 'Время', 'Освещение', 'Трудозатраты'])
table_max.horizontalHeader().setDefaultSectionSize(130)
table_max.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
button = QPushButton('Добавить здание')
button_2 = QPushButton('Заполнить')
button.clicked.connect(add_building)
custom_ranges = [(4, 60), (10, 50), (10, 50), (120, 120), (1, 24), (100, 600), (70, 150), (70, 150), (70, 180),
                 (1, 2),
                 (3, 7), (8, 15)]
button_2.clicked.connect(lambda: randomize(line_edits, custom_ranges))

# --------------------- UI layout -------------------------

widget_left = QWidget()
widget_right = QWidget()
central_widget = QWidget()

grid_layout = QGridLayout(widget_left)
grid_layout1 = QGridLayout(widget_right)

widget_right.setFixedWidth(1400)
main_layout = QHBoxLayout()

# --- Добавляем QScrollArea для widget_left ---
scroll_area = QScrollArea()
scroll_area.setWidgetResizable(True)
scroll_area.setWidget(widget_left)
main_layout.addWidget(scroll_area)  # Добавляем scroll_area в main_layout

main_layout.addWidget(widget_right)

# --- Building Input Group ---
building_input_group = QGroupBox("Параметры здания")
building_input_layout = QGridLayout()

building_input_layout.addLayout(hbox(height_label, height_line, Line_label_1, line_edit_1), 0, 0)
building_input_layout.addLayout(hbox(length_label, length_line, width_label, width_line), 1, 0)
building_input_group.setLayout(building_input_layout)

# --- Conditions Group ---
conditions_group = QGroupBox("Условия")
conditions_layout = QGridLayout()
conditions_layout.addLayout(hbox(QLabel5, building_combo, values_combo, tempa_combo), 0, 0)
conditions_layout.addLayout(hbox(label1, label3), 1, 0)
conditions_layout.addLayout(hbox(label2, subject_combo), 2, 0)
conditions_layout.addLayout(hbox(label4, line2), 3, 0)
conditions_group.setLayout(conditions_layout)

# --- Echelons Group ---
echelons_group = QGroupBox("Эшелоны")
echelons_layout = QGridLayout()
echelons_layout.addLayout(hbox(stage_label_1, line_stage_1, stage_label_4, line_stage_4), 0, 0)
echelons_layout.addLayout(hbox(stage_label_2, line_stage_2, stage_label_5, line_stage_5), 1, 0)
echelons_layout.addLayout(hbox(stage_label_3, line_stage_3, stage_label_6, line_stage_6), 2, 0)
echelons_group.setLayout(echelons_layout)

# --- Buttons Group ---
buttons_group = QGroupBox("")
buttons_layout = QHBoxLayout()
buttons_layout.addWidget(button)
buttons_layout.addWidget(button_2)
buttons_group.setLayout(buttons_layout)

# --- Export Group ---
export_group = QGroupBox("Экспорт данных")
export_layout = QHBoxLayout()
export_csv_button = QPushButton("CSV")
export_csv_button.clicked.connect(export_to_csv)
export_excel_button = QPushButton("Excel")
export_excel_button.clicked.connect(export_to_excel)
export_pdf_button = QPushButton("PDF")
export_pdf_button.clicked.connect(export_to_pdf)
export_layout.addWidget(export_csv_button)
export_layout.addWidget(export_excel_button)
export_layout.addWidget(export_pdf_button)
export_group.setLayout(export_layout)

# --- Project Group ---
project_group = QGroupBox("Проект")
project_layout = QHBoxLayout()
save_button = QPushButton("Сохранить")
save_button.clicked.connect(save_project)
load_button = QPushButton("Загрузить")
load_button.clicked.connect(load_project)
project_layout.addWidget(save_button)
project_layout.addWidget(load_button)
project_group.setLayout(project_layout)

# --- What-If Analysis Group ---
what_if_group = QGroupBox("Анализ \"что если\"")
what_if_layout = QVBoxLayout()
analyze_button = QPushButton("Проанализировать")
# Вызов функции
analyze_button.clicked.connect(analyze_what_if)  # Без аргументов
what_if_layout.addWidget(analyze_button)
what_if_group.setLayout(what_if_layout)

# Adding groups to main layouts
grid_layout.addWidget(building_input_group, 0, 0)
grid_layout.addWidget(conditions_group, 1, 0)
grid_layout.addWidget(echelons_group, 2, 0)
grid_layout.addWidget(buttons_group, 3, 0)
grid_layout.addWidget(table_min, 4, 0)
grid_layout.addWidget(export_group, 5, 0)
grid_layout.addWidget(project_group, 6, 0)
grid_layout.addWidget(what_if_group, 7, 0)
grid_layout1.addWidget(tabWidget, 0, 0, 1, 2)

central_widget.setLayout(main_layout)
window.setCentralWidget(central_widget)

window.show()
sys.exit(app.exec_())
