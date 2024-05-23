from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QHBoxLayout, QComboBox,
                             QLabel, QLineEdit, QGridLayout, QHeaderView, QTabWidget)
import random
from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout)
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import QtCore
import math
import add_building  # Импорт файла с расчетами

def add_building():
    def get_method(dictionary, key, default=None):
        return dictionary.get(key, default)

    # Инициализация размеров один раз, напрямую с помощью генератора списка
    dimensions = [float(height_line.text() or 0), float(length_line.text() or 0), float(width_line.text() or 0)]
    # Разбор входных данных и расчет результатов
    time = int(line_edit_1.text() or 0)
    stage_values = [float(line_stage_1.text() or 0), float(line_stage_2.text() or 0), float(line_stage_3.text() or 0),
                    float(line_stage_4.text() or 0), float(line_stage_5.text() or 0), float(line_stage_6.text() or 0)]
    table_max.setRowCount(time)

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


buildings, num_surv, Kq, group_cnt_list, area, final, column_3, column_4 = [], [], [], [], [], [], [], []
app = QApplication([])
window = QMainWindow()
window.setGeometry(0, 0, 1920, 1080)
building_combo, subject_combo, values_combo, tempa_combo = [QComboBox() for _ in range(4)]
building_combo.addItems(["Кирпич", "Панель"])
subject_combo.addItems(["Слабая", "Средняя", "Сильная", "Полная"])
values_combo.addItems(["землетрясение", "взрыв вне здания", "взрыв внутри здания"])
tempa_combo.addItems(['свыше +25', 'от 0 до +25', 'от -10 до 0', 'от -20 до -10', 'ниже -20'])

def create_label(text):
    label = QLabel(text)
    return label


# Функция для создания QLineEdit
def create_line_edit():
    line_edit = QLineEdit()
    return line_edit


# Создание меток
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


def randomize(line_edits, ranges):
    for line_edit, number_range in zip(line_edits, ranges):
        random_number = random.randint(number_range[0], number_range[1])
        line_edit.setText(str(random_number))


custom_ranges = [(4, 60), (10, 50), (10, 50), (120, 120), (1, 24), (100, 600), (70, 150), (70, 150), (70, 180), (1, 2),
                 (3, 7), (8, 15)]

# Создание полей ввода
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
button_2.clicked.connect(lambda: randomize(line_edits, custom_ranges))

widget_left, widget_right, central_widget = [QWidget() for _ in range(3)]
grid_layout, grid_layout1 = QGridLayout(widget_left), QGridLayout(widget_right)
widget_right.setFixedWidth(1400)
main_layout = QHBoxLayout()
main_layout.addWidget(widget_left)
main_layout.addWidget(widget_right)


def hbox(*widgets):
    layout = QHBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


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