from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QHBoxLayout, QComboBox,
                             QLabel, QLineEdit, QGridLayout, QHeaderView, QTabWidget, QWidget, QTableWidget, QVBoxLayout,
                             QTableWidgetItem)
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import random
from PyQt5 import QtCore
import math
from itertools import zip_longest, accumulate
import numpy as np

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


def create_label(text):
    return QLabel(text)


def create_line_edit():
    return QLineEdit()


def create_combobox(items):
    combobox = QComboBox()
    combobox.addItems(items)
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
    (workload, rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists) = (
        WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3, time_esh_1,
                      time_esh_2, time_esh_3, width, length, number_surv))

    PeopleTrapped, TotVol_m3, workreq, ast_time, koff_lum = PeopleTrapped_func(time, landslide_height, surviv,
                                                                               num_fatalities, rescue, workload,
                                                                               sublists, tempa)
    average, group_cnt_sort = dist_func(workreq, surviv)
    update_table(average)
    return workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum


def WorkLoad_func(height, k, framework_building, method_name, method_power, time, esh_1, esh_2, esh_3, time_esh_1,
                  time_esh_2, time_esh_3, width, length, number_surv):
    landslide_height = (height * framework_building) / (100 + (height * k))
    debris_volume = 1.25 * landslide_height * number_surv
    buildings.append(BuildingData(height, length, width, debris_volume, method_name, method_power))

    area_value = width * length
    group_cnt = int(np.ceil((2 * area_value) / (3.2 * 7)))
    group_cnt_list.append(group_cnt)
    area.append(area_value)

    group_esh = np.round(np.array([esh_1, esh_2, esh_3]) / 7).astype(int)
    group_min = np.minimum(np.round(np.array([esh_1, esh_2, esh_3]) / 7), group_esh).astype(int)

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
            (int(time_esh_1), int(time_esh_2), cumulativeWork[0] if len(cumulativeWork) > 0 else 0),
            (int(time_esh_2), int(time_esh_3), cumulativeWork[1] if len(cumulativeWork) > 1 else 0),
            (int(time_esh_3), time, cumulativeWork[2] if len(cumulativeWork) > 2 else 0)
        ]
        for start, end, intensity in intensity_ranges:
            workload[start:end] = intensity

        if len(cumulativeWork) < 3 and len(workload) < number_surv:
            workload = np.concatenate((workload, np.full(number_surv - len(workload), workload[-1] if workload.size > 0 else 0)))

        workloads.append(workload)

    rescue = []
    for i in np.cumsum(workloads[-1]):
        value = min(round(i / ((debris_volume * 6.8) / number_surv)), number_surv) if number_surv != 0 else 0
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
    workreq = [int(float(TotVol_m3[i]) * 6.8 * float(koff_lum[i]) * float(tempa)) for i in range(len(TotVol_m3))]
    min_length = min(len(workreq), len(workload))
    print(min_length, workreq, workload)
    # Проверяем, существует ли список и является ли первый элемент списка списком
    if not final or not isinstance(final[0], list):
        final.append([])

    # Вычисляем новые значения, которые должны быть добавлены или суммированы
    new_values = [min(i / w if w != 0 else 0, 1) for w, i in
                  zip_longest(workreq[:min_length], workload[:min_length], fillvalue=0)]

    # Если final[0] уже содержит значения, суммируем их с новыми значениями
    if final[0]:
        # Суммируем значения, если оба списка содержат элементы на данной позиции
        final[0] = [sum(x) for x in zip_longest(final[0], new_values, fillvalue=0)]
    else:
        # Если final[0] пуст, просто присваиваем ему новые значения
        final[0] = new_values
    # Создание холстов для графиков
    plt.style.use('ggplot')

    # Создание фигур и осей для каждого графика
    fig1, ax1 = plt.subplots(figsize=(1, 5), dpi=100)
    fig2, ax2 = plt.subplots(figsize=(1, 5), dpi=100)

    # Создание FigureCanvas для каждого графика
    canvas1 = FigureCanvas(fig1)
    canvas2 = FigureCanvas(fig2)

    # Настройка линий и текста для графика 1
    ax1.plot(workreq, label='Необходимые трудозатраты', color='blue')
    if workload is not None:
        ax1.plot(workload, label='Задействованные трудозатраты', color='orange', linestyle='dashed')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # Настройка линий и текста для графика 2
    for sublist in final:
        ax2.plot(sublist, color='blue')
    ax2.set(xlabel='Время, час', ylabel='Трудозатраты, чел., час', title='Значения показателя эффективности')
    ax2.grid(True)

    # Отображение графиков
    canvas1.draw()
    canvas2.draw()

    # Добавление графиков в layout
    grid_layout1.addWidget(canvas1, 2, 0)
    grid_layout1.addWidget(canvas2, 2, 1)

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

    # Create lists to store the value

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

    # Включаем обновление виджета после внесения изменений
    table_min.setSortingEnabled(True), table_min.blockSignals(False), table_min.setUpdatesEnabled(True)
    table_min.viewport().update()


def clear_input_fields(*input_fields):
    for field in input_fields:
        if hasattr(field, 'clear') and callable(getattr(field, 'clear')):
            field.clear()


def add_building():
    dimensions = [float(height_line.text() or 0), float(length_line.text() or 0), float(width_line.text() or 0)]
    # Разбор входных данных и расчет результатов
    time = int(line_edit_1.text() or 0)
    stage_values = [float(line_stage_1.text() or 0), float(line_stage_2.text() or 0),
                    float(line_stage_3.text() or 0),
                    float(line_stage_4.text() or 0), float(line_stage_5.text() or 0), float(line_stage_6.text() or 0)]
    table_max.setRowCount(time)

    # Получение и вызов методов
    survivor_args = subject_methods["survivors"].get(subject_combo.currentText())
    building_args = subject_methods["buildings"].get(building_combo.currentText())
    disaster_intensity = subject_methods["intensity"].get(values_combo.currentText(), 0)
    tempa_args = subject_methods["tempa"].get(tempa_combo.currentText())
    # Извлечение числового значения из survivor_args
    survival_probability, _ = subject_methods["survivors"].get(subject_combo.currentText(), (0.5, None))

    number_surv = round(
        math.ceil((get_time_range_result(int(line2.text() or 0)) * int(label3.text() or 0)) * survival_probability)
    )
    surviv = [str(round((-0.16 * math.log1p(i) + 0.9107) * number_surv)) for i in range(time + 1)]
    surviv.insert(0, str(number_surv))
    num_fatalities = [0] + [str(math.floor(float(surviv[i]) - float(surviv[i + 1]))) for i in range(len(surviv) - 1)]
    clear_input_fields(
        height_line, length_line, width_line, label3)

    if building_args:
        (workload, PeopleTrapped, TotVol_m3, workreq, rescue, ast_time, koff_lum) = (
            calculate_data(*dimensions, disaster_intensity, *building_args, *survivor_args, surviv, time, *stage_values,
                           number_surv, num_fatalities, tempa_args))

        # Очистка содержимого таблицы и установка количества строк
        table_max.clearContents()
        table_max.setRowCount(len(TotVol_m3))
        # Заполнение таблицы данными
        for row_index, values in enumerate(zip(TotVol_m3, PeopleTrapped, surviv, rescue,
                                               num_fatalities, workload, ast_time, koff_lum, workreq)):
            set_table_items(table_max, row_index, values)

        # Создание новой вкладки и копирование данных в нее
        new_tab = QWidget()
        new_table_widget = copy_table(table_max)
        new_tab.setLayout(QVBoxLayout())
        new_tab.layout().addWidget(new_table_widget)
        # Добавление вкладки в QTabWidget
        tab_index = tabWidget.addTab(new_tab, f"Здание {tabWidget.count()}")
        tabWidget.setCurrentIndex(tab_index)


def randomize(line_edits, ranges):
    for line_edit, number_range in zip(line_edits, ranges):
        random_number = random.randint(number_range[0], number_range[1])
        line_edit.setText(str(random_number))


def set_table_items(table, row_index, values):
    # Заполнение строки таблицы значениями
    for column_index, value in enumerate(values):
        table.setItem(row_index, column_index, QTableWidgetItem(str(value)))


def copy_table(source):
    target = QTableWidget(source.rowCount(), source.columnCount())
    target.setHorizontalHeaderLabels([
        source.horizontalHeader().model().headerData(i, QtCore.Qt.Horizontal)
        for i in range(source.columnCount())
    ])
    for row in range(source.rowCount()):
        for column in range(source.columnCount()):
            if item := source.item(row, column):
                target.setItem(row, column, item.clone())
    return target


def find_tab_index(tab_widget, name):
    """Поиск вкладки по имени."""
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == name:
            return i
    return -1


def hbox(*widgets):
    layout = QHBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


app = QApplication([])
window = QMainWindow()
window.setGeometry(0, 0, 1920, 1080)

building_combo = create_combobox(["Кирпич", "Панель"])
subject_combo = create_combobox(["Слабая", "Средняя", "Сильная", "Полная"])
values_combo = create_combobox(["землетрясение", "взрыв вне здания", "взрыв внутри здания"])
tempa_combo = create_combobox(['свыше +25', 'от 0 до +25', 'от -10 до 0', 'от -20 до -10', 'ниже -20'])

labels = [create_label(text) for text in [
    'Условия', 'Высота', 'Длина', 'Ширина',
    'кол-во часов', '1-эшелон', '2-эшелон', '3-эшелон',
    'Время', 'Время', 'Время',
    'Данные о количестве людей из АПК "Безопасный город:',
    'Данные о степени разрушений зданий:',
    'Астрономическое время:'
]]
(QLabel5, height_label, length_label, width_label, Line_label_1, stage_label_1, stage_label_2, stage_label_3,
 stage_label_4, stage_label_5, stage_label_6, label1, label2, label4) = labels

line_edits = [create_line_edit() for _ in range(12)]
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

widget_left, widget_right, central_widget = [QWidget() for _ in range(3)]
grid_layout, grid_layout1 = QGridLayout(widget_left), QGridLayout(widget_right)
widget_right.setFixedWidth(1400)
main_layout = QHBoxLayout()
main_layout.addWidget(widget_left)
main_layout.addWidget(widget_right)

height_layout = hbox(height_label, height_line, Line_label_1, line_edit_1)
length_layout = hbox(length_label, length_line, width_label, width_line)
stage_1 = hbox(stage_label_1, line_stage_1, stage_label_4, line_stage_4)
stage_2 = hbox(stage_label_2, line_stage_2, stage_label_5, line_stage_5)
stage_3 = hbox(stage_label_3, line_stage_3, stage_label_6, line_stage_6)
combo_layout = hbox(QLabel5, building_combo, values_combo, tempa_combo)
Label1 = hbox(label1, label3)
Label2 = hbox(label2, subject_combo)
Label4 = hbox(label4, line2)
Button = hbox(button, button_2)
table_widget = hbox(table_min)
grid_layout.addLayout(height_layout, 0, 0), grid_layout.addLayout(length_layout, 1, 0)
grid_layout.addLayout(combo_layout, 2, 0), grid_layout.addLayout(Label1, 3, 0)
grid_layout.addLayout(Label2, 4, 0), grid_layout.addLayout(Label4, 5, 0)
grid_layout.addLayout(stage_1, 6, 0), grid_layout.addLayout(stage_2, 7, 0)
grid_layout.addLayout(stage_3, 8, 0), grid_layout.addLayout(Button, 9, 0)
grid_layout.addLayout(table_widget, 10, 0)
grid_layout1.addWidget(tabWidget, 0, 0, 1, 2)
central_widget.setLayout(main_layout)  # Use main_layout here
window.setCentralWidget(central_widget)

window.show()
app.exec_()