import random
import sys
from itertools import zip_longest
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QHBoxLayout, QComboBox,
                             QLabel, QLineEdit, QGridLayout, QHeaderView, QTabWidget, QWidget, QTableWidget,
                             QVBoxLayout,
                             QTableWidgetItem, QMessageBox, QFileDialog, QGroupBox, QToolTip, QScrollArea, QSpinBox)
from PyQt5.QtCore import Qt, QSettings
import pyqtgraph as pg
import numpy as np
import pandas as pd
import csv
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from reportlab.pdfgen import canvas
import math


class Building:
    def __init__(self, height, length, width, method_name, method_power):
        self.height = height
        self.length = length
        self.width = width
        self.method_name = method_name
        self.method_power = method_power
        self.debris_volume = self.calculate_debris_volume()

    def calculate_debris_volume(self):
        # Здесь будет логика расчёта объёма завала
        # ...
        return self.height * self.length * self.width  # Пример: объём как прямоугольный параллелепипед


class Scenario:
    def __init__(self, label, **kwargs):
        self.label = label
        # Используем kwargs, чтобы динамически добавлять параметры сценария
        for key, value in kwargs.items():
            setattr(self, key, value)


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


def calculate_data(building, disaster_intensity, workload_arg, workload_name, survivor_prob, survivor_name, surviv, time, stage_values,
                    number_surv, num_fatalities, tempa, building_args):  # Добавь building_args здесь
    try:
        workload, rescue, _, _, _, landslide_height, sublists = WorkLoad_func(
            building, disaster_intensity, (building_args[0], building_args[1]), time, stage_values)
        PeopleTrapped, TotVol_m3, workreq, ast_time, koff_lum = PeopleTrapped_func(
            time, landslide_height, surviv, num_fatalities, rescue, workload, sublists, tempa
        )
        average, group_cnt_sort = dist_func(workreq, surviv)
        update_table(average)
        return workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum
    except ZeroDivisionError:
        QMessageBox.critical(window, "Ошибка", "Произошло деление на ноль. Проверьте входные данные.")
        return None, None, None, None, None, None, None
    except Exception as e:
        QMessageBox.critical(window, "Ошибка", f"Произошла ошибка: {str(e)}")
        return None, None, None, None, None, None, None


def WorkLoad_func(building, disaster_intensity, workload_args, time, stage_values):
    landslide_height = (building.height * workload_args[0]) / (100 + (building.height * disaster_intensity))
    debris_volume = 1.25 * landslide_height * int(label3.text())
    buildings.append(Building(building.height, building.length, building.width, workload_args[1], workload_args[0]))

    area_value = building.width * building.length
    group_cnt = int(np.ceil((2 * area_value) / (3.2 * 7)))
    group_cnt_list.append(group_cnt)
    area.append(area_value)

    group_esh = np.round(np.array(stage_values[:3]) / 7).astype(int)
    group_min = np.minimum(np.round(np.array(stage_values[:3]) / 7), group_esh).astype(int)

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

    workloads = []
    for index, cumulativeWork in enumerate(cumulativeWorks):
        workload = np.zeros(time)
        intensity_ranges = [
            (int(stage_values[3]), int(stage_values[4]), cumulativeWork[0] if len(cumulativeWork) > 0 else 0),
            (int(stage_values[4]), int(stage_values[5]), cumulativeWork[1] if len(cumulativeWork) > 1 else 0),
            (int(stage_values[5]), time, cumulativeWork[2] if len(cumulativeWork) > 2 else 0)
        ]
        for start, end, intensity in intensity_ranges:
            workload[start:end] = intensity

        if len(cumulativeWork) < 3 and len(workload) < int(label3.text()):
            workload = np.concatenate(
                (workload, np.full(int(label3.text()) - len(workload), workload[-1] if workload.size > 0 else 0)))

        workloads.append(workload)

    rescue = []
    for i in np.cumsum(workloads[-1]):
        value = min(round(i / ((debris_volume * 6.8) / int(label3.text()))), int(label3.text())) if int(
            label3.text()) != 0 else 0
        rescue.append(value)
        if value >= int(label3.text()):
            break

    print("Кол-во групп с эшелонов", group_esh)
    print(" Необходимое кол-во групп исходя из площади", group_cnt_list)
    print("список свободных групп", free_group)
    return workloads[-1], rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists


def PeopleTrapped_func(time, landslide_height, surviv, num_fatalities, rescue, workload, sublists, tempa):
    ast_time = [str(i % 25) for i in range(int(line2.text() or 0), time + 1)]
    koff_lum = ['1' if 7 <= int(it) <= 18 else '1.5' for it in ast_time]
    PeopleTrapped = [math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i]))
                     for i in range(min(len(rescue), len(num_fatalities), len(surviv)))
                     if math.ceil(float(rescue[i]) - float(num_fatalities[i]) - float(surviv[i])) >= 0]
    TotVol_m3 = [round(1.25 * landslide_height * PeopleTrapped[i], 2) for i in
                 range(min(time, len(PeopleTrapped)))]
    workreq = [int(float(TotVol_m3[i]) * 6.8 * float(koff_lum[i]) * float(tempa)) for i in range(len(TotVol_m3))]
    min_length = min(len(workreq), len(workload))
    print(min_length, workreq, workload)
    # Проверяем, существует ли список и является ли первый элемент списка списком
    if not final or not isinstance(final[0], list):
        final.append([])

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
        graphs_layout.addWidget(pw1)  # Добавляем графики на вкладку "Графики"
        graphs_layout.addWidget(pw2)

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
    table_min.setSortingEnabled(False)
    table_min.blockSignals(True)
    table_min.setUpdatesEnabled(False)
    # Сортировка данных
    combined_data = sorted(zip(buildings, average), key=lambda x: (x[1], x[0].debris_volume), reverse=True)
    table_min.setRowCount(len(combined_data))

    # Заполнение таблицы данными
    for row, (building, dist) in enumerate(combined_data):
        table_min.setItem(row, 0, QTableWidgetItem(f"Здание №{row + 1}"))
        table_min.setItem(row, 1, QTableWidgetItem(str(building.height)))
        table_min.setItem(row, 2, QTableWidgetItem(str(building.length)))
        table_min.setItem(row, 3, QTableWidgetItem(str(building.width)))
        table_min.setItem(row, 4, QTableWidgetItem(str(round(building.debris_volume, 2))))
        table_min.setItem(row, 5, QTableWidgetItem(str(building.method_name)))
        table_min.setItem(row, 6, QTableWidgetItem(str(building.method_power)))
        table_min.setItem(row, 7, QTableWidgetItem(str(round(dist, 2))))

    table_min.setSortingEnabled(True)
    table_min.blockSignals(False)
    table_min.setUpdatesEnabled(True)
    table_min.viewport().update()


def clear_input_fields(*input_fields):
    for field in input_fields:
        if hasattr(field, 'clear') and callable(getattr(field, 'clear')):
            field.clear()


def add_building(scenario=None):
    if not validate_input():
        return

    if scenario:
        height_line.setText(str(scenario.height))
        length_line.setText(str(scenario.length))
        width_line.setText(str(scenario.width))
        line_edit_1.setText(str(scenario.time_total))
        label3.setText(str(scenario.people_count))
        line_stage_1.setText(str(scenario.stage_1_count))
        line_stage_2.setText(str(scenario.stage_2_count))
        line_stage_3.setText(str(scenario.stage_3_count))
        line_stage_4.setText(str(scenario.stage_1_time))
        line_stage_5.setText(str(scenario.stage_2_time))
        line_stage_6.setText(str(scenario.stage_3_time))
        building_combo.setCurrentText(scenario.building_type)
        subject_combo.setCurrentText(scenario.destruction_level)
        tempa_combo.setCurrentText(scenario.tempa)

    building = Building(float(height_line.text()), float(length_line.text()), float(width_line.text()),
                        building_combo.currentText(), subject_combo.currentText())
    time = int(line_edit_1.text())
    stage_values = [float(line_stage_1.text()), float(line_stage_2.text()),
                    float(line_stage_3.text()),
                    float(line_stage_4.text()), float(line_stage_5.text()), float(line_stage_6.text())]
    table_max.setRowCount(time)

    survivor_args = subject_methods["survivors"].get(subject_combo.currentText())
    building_args = subject_methods["buildings"].get(building_combo.currentText())
    disaster_intensity = subject_methods["intensity"].get(values_combo.currentText())
    tempa_args = subject_methods["tempa"].get(tempa_combo.currentText())
    survival_probability, _ = subject_methods["survivors"].get(subject_combo.currentText(), (0.5, None))

    number_surv = round(
        math.ceil((get_time_range_result(int(line2.text()))) * int(label3.text())) * survival_probability
    )
    surviv = [str(round((-0.16 * math.log1p(i) + 0.9107) * number_surv)) for i in range(time + 1)]
    surviv.insert(0, str(number_surv))
    num_fatalities = [0] + [str(math.floor(float(surviv[i]) - float(surviv[i + 1]))) for i in
                            range(len(surviv) - 1)]

    if building_args:
        (workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum) = (
            calculate_data(building, disaster_intensity, building_args[0], building_args[1], survivor_args[0],
                           survivor_args[1], surviv, time, stage_values,
                           number_surv, num_fatalities, tempa_args, building_args))  # Добавь building_args здесь

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
                buildings.append(Building(
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
# --- Функция для анализа с заданными параметрами ---


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
        Scenario("Базовый сценарий", **original_values),
        Scenario("Первый эшелон опоздал на 1 час",
                 **{k: v if k != 'stage_1_time' else min(v + 1, 24) for k, v in original_values.items()}),
        Scenario("Второй эшелон опоздал на 2 часа",
                 **{k: v if k != 'stage_2_time' else min(v + 2, 24) for k, v in original_values.items()}),
        Scenario("Третий эшелон опоздал на 5 часов",
                 **{k: v if k != 'stage_3_time' else min(v + 5, 24) for k, v in original_values.items()}),
        Scenario("Удвоенное число спасателей",
                 **{k: v if k not in ['stage_1_count', 'stage_2_count', 'stage_3_count'] else min(v * 2,
                                                                                                  360 if k == 'stage_1_count' else 200 if k == 'stage_2_count' else 360)
                    for k, v in original_values.items()}),
        Scenario("Уменьшенное число спасателей",
                 **{k: v if k not in ['stage_1_count', 'stage_2_count', 'stage_3_count'] else max(v // 2,
                                                                                                  50 if k == 'stage_1_count' else 30 if k == 'stage_2_count' else 70)
                    for k, v in original_values.items()})
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
        scenario_label = QLabel(scenario.label)
        scroll_content_layout.addWidget(scenario_label)

        # Вызываем функцию add_building с параметром scenario
        results = add_building(scenario=scenario)

        # Проверяем, были ли получены результаты
        if results is not None:
            workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum, num_fatalities, surviv = results
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


app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Приложение для анализа ЧС")
window.setGeometry(0, 0, 1600, 800)

# --- Создание элементов интерфейса ---
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

# --- Основной layout ---
central_widget = QWidget()
main_layout = QHBoxLayout(central_widget)
window.setCentralWidget(central_widget)

# --- Вкладки ---
tab_widget = QTabWidget(central_widget)
main_layout.addWidget(tab_widget)

# --- Вкладка "Параметры" ---
parameters_tab = QWidget()
parameters_layout = QVBoxLayout(parameters_tab)
tab_widget.addTab(parameters_tab, "Параметры")

# --- Группы элементов на вкладке "Параметры" ---
building_group = QGroupBox("Параметры здания")
building_layout = QGridLayout(building_group)
building_layout.addWidget(height_label, 0, 0)
building_layout.addWidget(height_line, 0, 1)
building_layout.addWidget(Line_label_1, 0, 2)
building_layout.addWidget(line_edit_1, 0, 3)

building_layout.addWidget(length_label, 1, 0)
building_layout.addWidget(length_line, 1, 1)
building_layout.addWidget(width_label, 1, 2)
building_layout.addWidget(width_line, 1, 3)
parameters_layout.addWidget(building_group)

conditions_group = QGroupBox("Условия")
conditions_layout = QGridLayout(conditions_group)
conditions_layout.addWidget(QLabel5, 0, 0)
conditions_layout.addWidget(building_combo, 0, 1)
conditions_layout.addWidget(values_combo, 0, 2)
conditions_layout.addWidget(tempa_combo, 0, 3)

conditions_layout.addWidget(label1, 1, 0)
conditions_layout.addWidget(label3, 1, 1)

conditions_layout.addWidget(label2, 2, 0)
conditions_layout.addWidget(subject_combo, 2, 1)

conditions_layout.addWidget(label4, 3, 0)
conditions_layout.addWidget(line2, 3, 1)
parameters_layout.addWidget(conditions_group)

echelons_group = QGroupBox("Эшелоны")
echelons_layout = QGridLayout(echelons_group)
echelons_layout.addWidget(stage_label_1, 0, 0)
echelons_layout.addWidget(line_stage_1, 0, 1)
echelons_layout.addWidget(stage_label_4, 0, 2)
echelons_layout.addWidget(line_stage_4, 0, 3)

echelons_layout.addWidget(stage_label_2, 1, 0)
echelons_layout.addWidget(line_stage_2, 1, 1)
echelons_layout.addWidget(stage_label_5, 1, 2)
echelons_layout.addWidget(line_stage_5, 1, 3)

echelons_layout.addWidget(stage_label_3, 2, 0)
echelons_layout.addWidget(line_stage_3, 2, 1)
echelons_layout.addWidget(stage_label_6, 2, 2)
echelons_layout.addWidget(line_stage_6, 2, 3)
parameters_layout.addWidget(echelons_group)

# --- Кнопки на вкладке "Параметры" ---
buttons_layout = QHBoxLayout()
parameters_layout.addLayout(buttons_layout)
buttons_layout.addWidget(button)
buttons_layout.addWidget(button_2)

# --- Вкладка "Результаты" ---
results_tab = QWidget()
results_layout = QVBoxLayout(results_tab)
tab_widget.addTab(results_tab, "Результаты")
results_layout.addWidget(table_max)

# --- Вкладка "Приоритет" ---
priority_tab = QWidget()
priority_layout = QVBoxLayout(priority_tab)
tab_widget.addTab(priority_tab, "Приоритет")
priority_layout.addWidget(table_min)

# --- Вкладка "Графики" ---
graphs_tab = QWidget()
graphs_layout = QVBoxLayout(graphs_tab)
tab_widget.addTab(graphs_tab, "Графики")
# ... (добавьте графики pyqtgraph)

# --- Вкладка "Анализ" ---
analysis_tab = QWidget()
analysis_layout = QVBoxLayout(analysis_tab)
tab_widget.addTab(analysis_tab, "Анализ")

# --- Группа "Параметры сценария" ---
scenario_group = QGroupBox("Параметры сценария")
scenario_layout = QGridLayout(scenario_group)
analysis_layout.addWidget(scenario_group)

# --- Элементы управления для изменения параметров ---
stage_1_time_label = QLabel("Время прибытия 1-го эшелона:")
stage_1_time_spinbox = QSpinBox()
stage_1_time_spinbox.setRange(1, 24)
scenario_layout.addWidget(stage_1_time_label, 0, 0)
scenario_layout.addWidget(stage_1_time_spinbox, 0, 1)

stage_2_time_label = QLabel("Время прибытия 2-го эшелона:")
stage_2_time_spinbox = QSpinBox()
stage_2_time_spinbox.setRange(1, 24)
scenario_layout.addWidget(stage_2_time_label, 1, 0)
scenario_layout.addWidget(stage_2_time_spinbox, 1, 1)

stage_3_time_label = QLabel("Время прибытия 3-го эшелона:")
stage_3_time_spinbox = QSpinBox()
stage_3_time_spinbox.setRange(1, 24)
scenario_layout.addWidget(stage_3_time_label, 2, 0)
scenario_layout.addWidget(stage_3_time_spinbox, 2, 1)

stage_1_count_label = QLabel("Количество спасателей 1-го эшелона:")
stage_1_count_spinbox = QSpinBox()
stage_1_count_spinbox.setRange(1, 360)
scenario_layout.addWidget(stage_1_count_label, 3, 0)
scenario_layout.addWidget(stage_1_count_spinbox, 3, 1)

stage_2_count_label = QLabel("Количество спасателей 2-го эшелона:")
stage_2_count_spinbox = QSpinBox()
stage_2_count_spinbox.setRange(1, 200)
scenario_layout.addWidget(stage_2_count_label, 4, 0)
scenario_layout.addWidget(stage_2_count_spinbox, 4, 1)

stage_3_count_label = QLabel("Количество спасателей 3-го эшелона:")
stage_3_count_spinbox = QSpinBox()
stage_3_count_spinbox.setRange(1, 360)
scenario_layout.addWidget(stage_3_count_label, 5, 0)
scenario_layout.addWidget(stage_3_count_spinbox, 5, 1)

# --- Кнопка "Запустить анализ" ---
analyze_button = QPushButton("Запустить анализ")
analyze_button.clicked.connect(analyze_what_if)
analysis_layout.addWidget(analyze_button)

# --- Текстовое поле для вывода результатов ---
results_label = QLabel("")
analysis_layout.addWidget(results_label)

# --- Стили CSS ---
app.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                background-color: #f8f8f8;
            }

            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }

            QLineEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }

            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #0056b3;
            }

            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }

            QHeaderView::section {
                background-color: #eee;
                border: 1px solid #ddd;
                padding: 5px;
            }

            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f8f8f8;
            }

            QTabWidget::tab-bar {
                alignment: center;
            }

            QTabBar::tab {
                background-color: #eee;
                border: 1px solid #ddd;
                border-bottom-color: #ccc;
                padding: 8px 15px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }

            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
        """)

# --- Запуск приложения ---
window.show()
sys.exit(app.exec_())