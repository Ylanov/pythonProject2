# rescue_app/gui.py
import math
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QGridLayout, QHeaderView, QTabWidget, QWidget, QTableWidget,
                             QTableWidgetItem, QMessageBox, QLabel, QComboBox, QVBoxLayout,
                             QDialog, QGroupBox, QHBoxLayout, QFrame, QSizePolicy, QScrollArea, QSplitter,
                             QDesktopWidget, QToolBar, QSpacerItem)
from PyQt5.QtCore import Qt

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from building_data import calculate_data, subject_methods, get_time_range_result
from what_if_analysis import WhatIfDialog
from utils import create_label, create_line_edit, create_combobox, hbox, copy_table


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowTitle("Анализ ЧС")
        # --- Инициализация settings_visible ---
        self.settings_visible = True
        # --- Объявление self.widget_left ---
        self.widget_left = QWidget()
        self.widget_right = QWidget()  # Добавляем объявление
        # --- Объявление self.grid_layout ---
        self.grid_layout = QGridLayout(
            self.widget_left
        )  # Добавляем объявление
        self.grid_layout1 = QGridLayout(
            self.widget_right
        )  # Добавляем объявление

        self.left_panel_width = 0  # Инициализируем
        self.right_panel_width = 0  # Инициализируем
        self.splitter = None

        self.initUI()

    def initUI(self):
        # --------------------- Стили CSS ------------------------
        self.setStyleSheet("Fusion")

        # --------------------- Создание виджетов ------------------------
        self.building_combo = create_combobox(
            ["Кирпич", "Панель"],
            "Тип здания: влияет на расчет объема завалов.",
        )
        self.subject_combo = create_combobox(
            ["Слабая", "Средняя", "Сильная", "Полная"],
            "Степень разрушений: влияет на вероятность выживания людей.",
        )
        self.values_combo = create_combobox(
            ["землетрясение", "взрыв вне здания", "взрыв внутри здания"],
            "Тип чрезвычайной ситуации: влияет на расчет интенсивности.",
        )
        self.tempa_combo = create_combobox(
            ['свыше +25', 'от 0 до +25', 'от -10 до 0', 'от -20 до -10', 'ниже -20'],
            "Температура воздуха: влияет на трудозатраты.",
        )

        self.labels = [
            create_label(text, tooltip)
            for text, tooltip in [
                ("Условия", None),
                ("Высота", "Высота здания в метрах."),
                ("Длина", "Длина здания в метрах."),
                ("Ширина", "Ширина здания в метрах."),
                ("кол-во часов", "Общее время проведения спасательной операции."),
                ("1-эшелон", "Количество спасателей в первом эшелоне."),
                ("2-эшелон", "Количество спасателей во втором эшелоне."),
                ("3-эшелон", "Количество спасателей в третьем эшелоне."),
                ("Время", "Время прибытия первого эшелона (в часах)."),
                ("Время", "Время прибытия второго эшелона (в часах)."),
                ("Время", "Время прибытия третьего эшелона (в часах)."),
                (
                    "Данные о количестве людей из АПК \"Безопасный город\":",
                    None,
                ),
                ("Данные о степени разрушений зданий:", None),
                ("Астрономическое время:", None),
            ]
        ]
        (
            self.QLabel5,
            self.height_label,
            self.length_label,
            self.width_label,
            self.Line_label_1,
            self.stage_label_1,
            self.stage_label_2,
            self.stage_label_3,
            self.stage_label_4,
            self.stage_label_5,
            self.stage_label_6,
            self.label1,
            self.label2,
            self.label4,
        ) = self.labels

        self.line_edits = [
            create_line_edit(tooltip)
            for tooltip in [
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
                "Время прибытия третьего эшелона (в часах).",
            ]
        ]
        (
            self.height_line,
            self.length_line,
            self.width_line,
            self.line_edit_1,
            self.line2,
            self.label3,
            self.line_stage_1,
            self.line_stage_2,
            self.line_stage_3,
            self.line_stage_4,
            self.line_stage_5,
            self.line_stage_6,
        ) = self.line_edits

        # Создаем QComboBox для выбора количества смен
        self.shift_combo = QComboBox()
        self.shift_combo.addItems(["1 смена", "2 смены", "3 смены", "4 смены"])
        self.shift_combo.setToolTip("Количество смен: влияет на расчет необходимого количества групп спасателей.")

        self.table_min = QTableWidget(1, 8)
        self.table_min.setHorizontalHeaderLabels(
            [
                "№",
                "Выс., м",
                "Длина, м",
                "Шир., м",
                "Объём, м3",
                "Тип",
                "Разрушение",
                "Приоритет",
            ]
        )
        self.table_min.horizontalHeader().setDefaultSectionSize(150)
        self.table_min.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.table_min.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.table_min.resize(800, 600)
        self.tabWidget = QTabWidget()
        self.tabWidget.setFocus()
        self.table_max = QTableWidget(0, 9)
        self.table_max.setHorizontalHeaderLabels(
            [
                "Объём завала, м3",
                "В завале, чел",
                "Выжившие, чел",
                "Спасённые, чел",
                "Пострадавшие, чел",
                "Workload",
                "Время",
                "Освещение",
                "Трудозатраты",
            ]
        )
        self.table_max.horizontalHeader().setDefaultSectionSize(130)
        self.table_max.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.button = QPushButton("Добавить здание")
        self.button_2 = QPushButton("Заполнить")
        self.button.clicked.connect(self.add_building)
        custom_ranges = [
            (4, 60),
            (10, 50),
            (10, 50),
            (120, 120),
            (1, 24),
            (100, 600),
            (70, 150),
            (70, 150),
            (70, 180),
            (1, 2),
            (3, 7),
            (8, 15),
        ]
        self.button_2.clicked.connect(
            lambda: self.randomize(self.line_edits, custom_ranges)
        )

        # --------------------- UI layout -------------------------

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        # --- Создаем QToolBar ---
        toolbar = QToolBar("Настройки")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # --- Вычисляем ширину для левой и правой панелей ---
        screen_width = QDesktopWidget().screenGeometry().width()
        self.left_panel_width = (
            screen_width // 4
        )  # Сохраняем как атрибут
        right_panel_width = screen_width - self.left_panel_width

        # --- Левая панель с кнопкой ---
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel_layout = QVBoxLayout(left_panel)

        # --- Добавляем кнопку в QToolBar ---
        self.toggle_settings_button = QPushButton("⚙️ Настройки")
        self.toggle_settings_button.setFixedSize(110, 30)
        self.toggle_settings_button.setStyleSheet(
            """
                    QPushButton {
                        background-color: #f0f0f0;
                        border: none;
                        border-radius: 10px; 
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                    QPushButton:checked {
                        background-color: #a0a0a0;
                    }
                """
        )
        self.toggle_settings_button.setCheckable(True)
        self.toggle_settings_button.clicked.connect(self.toggle_settings)
        toolbar.addWidget(self.toggle_settings_button)

        # --- Фрейм для настроек ---
        self.settings_frame = QFrame()
        self.settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_layout = QVBoxLayout(self.settings_frame)
        settings_layout.addWidget(self.widget_left)
        left_panel_layout.addWidget(self.settings_frame)

        # --- Правая панель с таблицей ---
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.addWidget(self.tabWidget)
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- QSplitter для разделения левой и правой панелей ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.widget_right)
        self.splitter.setSizes([self.left_panel_width, right_panel_width])
        self.splitter.setStretchFactor(1, 2)

        main_layout.addWidget(self.splitter)

        # --- Добавляем widget_left (содержащий все настройки) в settings_layout ---
        settings_layout.addWidget(self.widget_left)
        left_panel_layout.addWidget(self.settings_frame)

        # --- Добавляем left_panel и widget_right в main_layout ---
        self.widget_right.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )

        # --- Линия разделения ---
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # --- Building Input Group ---
        building_input_group = QGroupBox("Параметры здания")
        building_input_layout = QGridLayout()
        building_input_layout.addLayout(
            hbox(
                self.height_label,
                self.height_line,
                self.Line_label_1,
                self.line_edit_1,
            ),
            0,
            0,
        )
        building_input_layout.addLayout(
            hbox(
                self.length_label,
                self.length_line,
                self.width_label,
                self.width_line,
            ),
            1,
            0,
        )
        building_input_group.setLayout(building_input_layout)

        # --- Conditions Group ---
        conditions_group = QGroupBox("Условия")
        conditions_layout = QGridLayout()
        conditions_layout.addLayout(
            hbox(
                self.QLabel5,
                self.building_combo,
                self.values_combo,
                self.tempa_combo,
            ),
            0,
            0,
        )
        conditions_layout.addLayout(
            hbox(self.label1, self.label3), 1, 0
        )
        conditions_layout.addLayout(
            hbox(self.label2, self.subject_combo), 2, 0
        )
        conditions_layout.addLayout(hbox(self.label4, self.line2), 3, 0)
        conditions_group.setLayout(conditions_layout)

        # --- Echelons Group ---
        echelons_group = QGroupBox("Эшелоны")
        echelons_layout = QGridLayout()
        echelons_layout.addLayout(
            hbox(
                self.stage_label_1,
                self.line_stage_1,
                self.stage_label_4,
                self.line_stage_4,
            ),
            0,
            0,
        )
        echelons_layout.addLayout(
            hbox(
                self.stage_label_2,
                self.line_stage_2,
                self.stage_label_5,
                self.line_stage_5,
            ),
            1,
            0,
        )
        echelons_layout.addLayout(
            hbox(
                self.stage_label_3,
                self.line_stage_3,
                self.stage_label_6,
                self.line_stage_6,
            ),
            2,
            0,
        )
        echelons_group.setLayout(echelons_layout)

        # --- Buttons Group ---
        buttons_group = QGroupBox("")
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.button)
        buttons_layout.addWidget(self.button_2)
        buttons_group.setLayout(buttons_layout)

        # --- Export Group ---
        export_group = QGroupBox("Экспорт данных")
        export_layout = QHBoxLayout()
        export_csv_button = QPushButton("CSV")
        export_csv_button.clicked.connect(lambda: self.export_to_csv(self.table_min))  # Используем lambda
        export_excel_button = QPushButton("Excel")
        export_excel_button.clicked.connect(lambda: self.export_to_excel(self.table_min))  # Используем lambda
        export_pdf_button = QPushButton("PDF")
        export_pdf_button.clicked.connect(lambda: self.export_to_pdf(self.table_min))  # Используем lambda
        export_layout.addWidget(export_csv_button)
        export_layout.addWidget(export_excel_button)
        export_layout.addWidget(export_pdf_button)
        export_group.setLayout(export_layout)

        # --- Project Group ---
        project_group = QGroupBox("Проект")
        project_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(lambda: self.save_project())
        load_button = QPushButton("Загрузить")
        load_button.clicked.connect(lambda: self.load_project())
        project_layout.addWidget(save_button)
        project_layout.addWidget(load_button)
        project_group.setLayout(project_layout)

        # --- What-If Analysis Group ---
        what_if_group = QGroupBox("Анализ \"что если\"")
        what_if_layout = QVBoxLayout()
        analyze_button = QPushButton("Проанализировать")
        # Вызов функции
        analyze_button.clicked.connect(
            self.analyze_what_if
        )  # Без аргументов
        what_if_layout.addWidget(analyze_button)
        what_if_group.setLayout(what_if_layout)

        # --- Добавление групп в grid_layout ---
        self.grid_layout.addWidget(building_input_group, 0, 0)
        self.grid_layout.addWidget(conditions_group, 1, 0)
        self.grid_layout.addWidget(echelons_group, 2, 0)
        self.grid_layout.addWidget(buttons_group, 3, 0)
        self.grid_layout.addWidget(self.table_min, 4, 0)
        # Добавляем shift_combo в layout
        conditions_layout.addLayout(
            hbox(create_label("Количество смен:"), self.shift_combo),
            4, 0  # Номер строки и столбца в вашем layout
        )
        self.grid_layout.addWidget(export_group, 5, 0)
        self.grid_layout.addWidget(project_group, 6, 0)
        self.grid_layout.addWidget(what_if_group, 7, 0)
        self.grid_layout1.addWidget(self.tabWidget, 0, 0, 1, 2)

        self.setCentralWidget(central_widget)

    # Функция для скрытия/показа настроек
    def toggle_settings(self):
        self.settings_visible = not self.settings_visible

        if self.settings_visible:
            self.toggle_settings_button.setText("⚙️ Настройки")
            self.settings_frame.show()  # Показываем settings_frame
            # Восстанавливаем левую панель, корректируя правую
            self.splitter.setSizes(
                [
                    self.left_panel_width,
                    self.splitter.width() - self.left_panel_width,
                ]
            )
        else:
            self.toggle_settings_button.setText("⚙️ Настройки")
            self.settings_frame.hide()  # Скрываем settings_frame
            self.splitter.setSizes([0, self.splitter.width()])

    # Функция для добавления здания
    def add_building(self, scenario=None):
        # Применяем изменения из scenario, если он передан
        if scenario:
            for key, value in scenario.items():
                if key != "label" and isinstance(
                    value, (int, float, str)
                ):
                    setattr(self, key, value)
        dimensions = [
            float(self.height_line.text()),
            float(self.length_line.text()),
            float(self.width_line.text()),
        ]
        time = int(self.line_edit_1.text())
        # Получаем количество смен из QComboBox
        num_shifts = int(self.shift_combo.currentText().split()[0])  # Извлекаем число из строки
        stage_values = [
            float(self.line_stage_1.text()),
            float(self.line_stage_2.text()),
            float(self.line_stage_3.text()),
            float(self.line_stage_4.text()),
            float(self.line_stage_5.text()),
            float(self.line_stage_6.text()),
        ]
        self.table_max.setRowCount(time)

        survivor_args = subject_methods["survivors"].get(
            self.subject_combo.currentText()
        )
        building_args = subject_methods["buildings"].get(
            self.building_combo.currentText()
        )
        disaster_intensity = subject_methods["intensity"].get(
            self.values_combo.currentText()
        )
        tempa_args = subject_methods["tempa"].get(
            self.tempa_combo.currentText()
        )
        num_shifts = subject_methods["shift"].get(
            self.shift_combo.currentText()
        )

        number_surv = round(
            math.ceil(
                (
                    get_time_range_result(int(self.line2.text() or 0))
                    * int(self.label3.text() or 0)
                )
                * 0.4
            )
        )
        surviv = [
            str(round((-0.16 * math.log1p(i) + 0.9107) * number_surv))
            for i in range(time + 1)
        ]
        surviv.insert(0, str(number_surv))
        num_fatalities = [0] + [
            str(math.floor(float(surviv[i]) - float(surviv[i + 1])))
            for i in range(len(surviv) - 1)
        ]

        if building_args:
            calculation_result = calculate_data(
                height=dimensions[0],
                width=dimensions[2],
                length=dimensions[1],
                k=disaster_intensity,
                framework_building=building_args[0],
                method_name=survivor_args[1],
                desruction_full=survivor_args[0],
                method_power=building_args[1],
                surviv=surviv,
                time=time,
                esh_1=stage_values[0],
                esh_2=stage_values[1],
                esh_3=stage_values[2],
                time_esh_1=stage_values[3],
                time_esh_2=stage_values[4],
                time_esh_3=stage_values[5],
                number_surv=number_surv,
                num_fatalities=num_fatalities,
                tempa=tempa_args,
                line2=self.line2,
                num_shifts=num_shifts,
            )

            if calculation_result is not None:
                (
                    workload,
                    PeopleTrapped,
                    TotVol_m3,
                    workreq,
                    rescue,
                    ast_time,
                    koff_lum,
                    average,
                    time
                ) = calculation_result

                self.table_max.clearContents()
                self.table_max.setRowCount(len(TotVol_m3))
                self.update_table(average)

                for row_index, values in enumerate(
                    zip(
                        TotVol_m3,
                        PeopleTrapped,
                        surviv,
                        rescue,
                        num_fatalities,
                        workload,
                        ast_time,
                        koff_lum,
                        workreq,
                    )
                ):
                    self.set_table_items(self.table_max, row_index, values)
                    print("TotVol_m3: ", TotVol_m3)
                    print("PeopleTrapped: ", PeopleTrapped)
                    print("surviv: ", surviv)
                    print("rescue: ", rescue)
                    print("num_fatalities: ", num_fatalities)
                    print("workload: ", workload)
                    print("ast_time: ", ast_time)
                    print("koff_lum: ", koff_lum)
                    print("workreq: ", workreq)

                new_tab = QWidget()
                new_table_widget = copy_table(self.table_max)
                new_tab.setLayout(QVBoxLayout())
                new_tab.layout().addWidget(new_table_widget)
                tab_index = self.tabWidget.addTab(
                    new_tab, f"Здание {self.tabWidget.count()}"
                )
                self.tabWidget.setCurrentIndex(tab_index)

                return (
                    workload,
                    PeopleTrapped,
                    TotVol_m3,
                    workreq,
                    rescue,
                    ast_time,
                    koff_lum,
                    num_fatalities,
                    surviv,
                    time
                )

            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось рассчитать данные для здания. Проверьте входные параметры.",
                )
                return None, None, None, None, None, None, None, None, None

    def analyze_what_if(self):
        """
        Функция, реализующая анализ "что если".
        """
        # 1. Сохраняем значения в self.original_values
        self.original_values = {
            "height": float(self.height_line.text()),
            "length": float(self.length_line.text()),
            "width": float(self.width_line.text()),
            "time_total": int(self.line_edit_1.text()),
            "people_count": int(self.label3.text()),
            "stage_1_count": int(self.line_stage_1.text()),
            "stage_2_count": int(self.line_stage_2.text()),
            "stage_3_count": int(self.line_stage_3.text()),
            "stage_1_time": float(self.line_stage_4.text()),
            "stage_2_time": float(self.line_stage_5.text()),
            "stage_3_time": float(self.line_stage_6.text()),
            "building_type": self.building_combo.currentText(),
            "destruction_level": self.subject_combo.currentText(),
            "tempa": self.tempa_combo.currentText(),
        }

        # 2. Диалог для выбора сценариев и критерия
        dialog = WhatIfDialog(self.original_values)
        if dialog.exec_() == QDialog.Accepted:
            scenarios = dialog.get_scenarios()
            criterion = dialog.get_criterion()
        # Словарь для сопоставления ключей с виджетами
        widgets = {
            "height": self.height_line,
            "length": self.length_line,
            "width": self.width_line,
            "time_total": self.line_edit_1,
            "people_count": self.label3,
            "stage_1_count": self.line_stage_1,
            "stage_2_count": self.line_stage_2,
            "stage_3_count": self.line_stage_3,
            "stage_1_time": self.line_stage_4,
            "stage_2_time": self.line_stage_5,
            "stage_3_time": self.line_stage_6,
            "building_type": self.building_combo,
            "destruction_level": self.subject_combo,
            "tempa": self.tempa_combo,
        }
        # 2. Определяем сценарии для анализа
        scenarios = [
            {"label": "Базовый сценарий"},
            {
                "label": "Первый эшелон опоздал на 1 час",
                "stage_1_time": min(
                    self.original_values["stage_1_time"] + 1, 24
                ),
            },
            {
                "label": "Первый эшелон опоздал на 2 часа",
                "stage_2_time": min(
                    self.original_values["stage_2_time"] + 2, 24
                ),
            },
            {
                "label": "Первый эшелон опоздал на 5 часов",
                "stage_3_time": min(
                    self.original_values["stage_3_time"] + 5, 24
                ),
            },
            {
                "label": "Удвоенное число спасателей",
                "stage_1_count": min(
                    self.original_values["stage_1_count"] * 2, 500
                ),
                "stage_2_count": min(
                    self.original_values["stage_2_count"] * 2, 500
                ),
                "stage_3_count": min(
                    self.original_values["stage_3_count"] * 2, 500
                ),
            },
            {
                "label": "Уменьшенное число спасателей",
                "stage_1_count": max(
                    self.original_values["stage_1_count"] // 2, 50
                ),
                "stage_2_count": max(
                    self.original_values["stage_2_count"] // 2, 30
                ),
                "stage_3_count": max(
                    self.original_values["stage_3_count"] // 2, 70
                ),
            },
        ]

        # 3. Создаем новую вкладку для результатов анализа
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout()
        analysis_tab.setLayout(analysis_layout)
        self.tabWidget.addTab(analysis_tab, "Анализ \"что если\"")

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
        results = []  # Список для хранения результатов каждого сценария
        for scenario_index, scenario in enumerate(scenarios):
            # Создаем QLabel для названия сценария
            scenario_label = QLabel(scenario["label"])
            # Добавляем QLabel в layout контента
            scroll_content_layout.addWidget(scenario_label)

            print(
                f"Сценарий: {scenario['label']}"
            )  # Выводим название сценария
            for key, value in scenario.items():
                if key != "label" and isinstance(
                        value, (int, float, str)
                ):
                    print(
                        f"  {key}: {value} (тип: {type(value)})"
                    )  # Выводим значения и их типы
                    widget = widgets[key]
                    widget.setText(
                        str(value)
                    )  # Устанавливаем значения в виджеты

            QApplication.processEvents()  # Обновляем GUI
            # Вызываем функцию add_building с параметром scenario
            (
                workload,
                PeopleTrapped,
                TotVol_m3,
                workreq,
                rescue,
                ast_time,
                koff_lum,
                num_fatalities,
                surviv,
                time  # Добавляем time здесь
            ) = self.add_building(scenario=scenario)

            # Проверяем, были ли получены результаты
            if workload is not None:
                # Создаем таблицу для вывода результатов
                results_table = QTableWidget(len(TotVol_m3), 9)
                results_table.setHorizontalHeaderLabels(
                    [
                        "Объём завала, м3",
                        "В завале, чел",
                        "Выжившие, чел",
                        "Спасённые, чел",
                        "Пострадавшие, чел",
                        "Workload",
                        "Время",
                        "Освещение",
                        "Трудозатраты",
                    ]
                )
                results_table.horizontalHeader().setDefaultSectionSize(130)
                results_table.verticalHeader().setSectionResizeMode(
                    QHeaderView.ResizeToContents
                )

                # Заполняем таблицу результатами
                for row_index, values in enumerate(
                        zip(
                            TotVol_m3,
                            PeopleTrapped,
                            surviv,
                            rescue,
                            num_fatalities,
                            workload,
                            ast_time,
                            koff_lum,
                            workreq,
                        )
                ):
                    self.set_table_items(
                        results_table, row_index, values
                    )

                # Добавляем таблицу результатов на вкладку анализа
                scroll_content_layout.addWidget(results_table)

                # Сохраняем результаты сценария в список
                results.append(
                    {
                        "scenario": scenario["label"],
                        "TotVol_m3": TotVol_m3,
                        "PeopleTrapped": PeopleTrapped,
                        "surviv": surviv,
                        "rescue": rescue,
                        "num_fatalities": num_fatalities,
                        "workload": workload,
                        "ast_time": ast_time,
                        "koff_lum": koff_lum,
                        "workreq": workreq,
                        "time_total": time  # Добавьте time_total здесь
                    }
                )
            else:
                # Выводим сообщение об ошибке
                error_label = QLabel("Ошибка: неверные входные данные")
                scroll_content_layout.addWidget(error_label)

            # Убираем изменение GUI после расчета, чтобы не влияло на следующий сценарий
            for key, value in scenario.items():
                if key != "label" and isinstance(
                        value, (int, float, str)
                ):
                    widget = widgets[
                        key
                    ]  # Получаем виджет из словаря
                    widget.setText(
                        str(self.original_values[key])
                    )  # Возвращаем исходное значение

        # 7. Создание всплывающего окна с графиком и описанием
        self.show_analysis_report(results, self.original_values)

    def show_analysis_report(self, results, original_values):
        """
        Функция для отображения всплывающего окна с отчетом анализа.
        """
        report_dialog = QDialog(self)
        report_dialog.setWindowTitle("Отчет анализа \"что если\"")
        report_dialog.setMinimumSize(800, 600)  # Установите минимальный размер

        # Основной layout
        main_layout = QVBoxLayout()
        report_dialog.setLayout(main_layout)

        # ScrollArea для всего контента
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Виджет для контента внутри ScrollArea
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        # === Секция с описанием исходного сценария ===
        original_scenario_frame = QFrame()
        original_scenario_frame.setFrameShape(QFrame.StyledPanel)
        original_scenario_layout = QVBoxLayout(original_scenario_frame)
        scroll_layout.addWidget(original_scenario_frame)

        original_scenario_label = QLabel("<h2>Исходный сценарий:</h2>")
        original_scenario_label.setAlignment(Qt.AlignLeft)  # Выравнивание по левому краю
        original_scenario_layout.addWidget(original_scenario_label)

        # Форматируем описание с использованием HTML для отступов и пробелов
        original_scenario_description = f"""<p>
               - Высота здания: <b>{original_values['height']:.2f} м</b><br>
               - Длина здания: <b>{original_values['length']:.2f} м</b><br>
               - Ширина здания: <b>{original_values['width']:.2f} м</b><br>
               - Тип здания: <b>{original_values['building_type']}</b><br>
               - Степень разрушений: <b>{original_values['destruction_level']}</b><br>
               - Число людей в здании: <b>{original_values['people_count']}</b><br>
            <br>
               - Время прибытия 1-го эшелона: <b>{original_values['stage_1_time']} часов</b><br>
               - Время прибытия 2-го эшелона: <b>{original_values['stage_2_time']} часов</b><br>
               - Время прибытия 3-го эшелона: <b>{original_values['stage_3_time']} часов</b><br>
            <br>
               - Число спасателей в 1-м эшелоне: <b>{original_values['stage_1_count']} человек</b><br>
               - Число спасателей во 2-м эшелоне: <b>{original_values['stage_2_count']} человек</b><br>
               - Число спасателей в 3-м эшелоне: <b>{original_values['stage_3_count']} человек</b><br>
        </p>"""

        original_scenario_description_label = QLabel(original_scenario_description)
        original_scenario_description_label.setWordWrap(True)  # Разрешаем перенос слов
        original_scenario_layout.addWidget(original_scenario_description_label)

        # === Цикл по результатам анализа ===
        for result in results:
            # === Фрейм для каждого сценария ===
            scenario_frame = QFrame()
            scenario_frame.setFrameShape(QFrame.StyledPanel)
            scenario_layout = QVBoxLayout(scenario_frame)
            scroll_layout.addWidget(scenario_frame)

            scenario_label = QLabel(f"<h2>Сценарий: {result['scenario']}</h2>")
            scenario_label.setAlignment(Qt.AlignLeft)
            scenario_layout.addWidget(scenario_label)

            # Форматируем вывод данных
            scenario_data = f"""<p>
                   - Число спасенных: <b>{result['rescue'][-1]}</b><br>
                   - Число пострадавших: <b>{sum(int(x) for x in result['num_fatalities'])}</b><br>
                   - Время работ: <b>{len(result['workreq'])} часов</b><br>
                   - Workload: <b>{max(result['workload']):.2f} чел*час</b><br>  # Изменено
            </p>"""

            scenario_data_label = QLabel(scenario_data)
            scenario_data_label.setWordWrap(True)
            scenario_layout.addWidget(scenario_data_label)

        # === Секция с графиком ===
        graph_frame = QFrame()
        graph_frame.setFrameShape(QFrame.StyledPanel)
        graph_layout = QVBoxLayout(graph_frame)
        scroll_layout.addWidget(graph_frame)

        figure, ax = plt.subplots()

        for i, result in enumerate(results):
            # Приводим ast_time к числам
            ast_time = [int(t) for t in result['ast_time']]

            # Проверка на соответствие длин
            if len(ast_time) != len(result['workload']):
                print("Ошибка: Длины массивов ast_time и workload не совпадают!")
                print("Длина ast_time:", len(ast_time))
                print("Длина workload:", len(result['workload']))
                # Обрезаем workload по длине ast_time
                result['workload'] = result['workload'][:len(ast_time)]

                print("workload обрезан:", len(result['workload']))  # Добавьте эту строку для проверки
                continue
            # Построение графика
            sns.lineplot(x=ast_time, y=result['workload'], label=result['scenario'], ax=ax)

        ax.set_xlabel("Время", fontsize=12)  # Увеличиваем размер шрифта
        ax.set_ylabel("Workload", fontsize=12)
        ax.legend()
        plt.tight_layout()  # Автоматически подбираем отступы

        canvas = FigureCanvas(figure)
        graph_layout.addWidget(canvas)

        # Добавляем отступ внизу
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        scroll_layout.addItem(spacer)

        # Отображение диалогового окна
        report_dialog.exec_()

    def update_table(self, average):
        # Исправленный метод update_table
        self.table_min.setSortingEnabled(False)  # Отключаем сортировку
        self.table_min.blockSignals(True)  # Блокируем сигналы

        # Сортировка данных
        from building_data import buildings
        combined_data = sorted(zip(buildings, average), key=lambda x: (x[1], x[0].debris_volume), reverse=True)
        self.table_min.setRowCount(len(combined_data))

        # Заполнение таблицы данными
        for row, (building, dist) in enumerate(combined_data):
            self.table_min.setItem(row, 0, QTableWidgetItem(f"Здание №{row + 1}"))
            self.table_min.setItem(row, 1, QTableWidgetItem(str(building.height)))
            self.table_min.setItem(row, 2, QTableWidgetItem(str(building.length)))
            self.table_min.setItem(row, 3, QTableWidgetItem(str(building.width)))
            self.table_min.setItem(row, 4, QTableWidgetItem(str(round(building.debris_volume, 2))))
            self.table_min.setItem(row, 5, QTableWidgetItem(str(building.method_name)))
            self.table_min.setItem(row, 6, QTableWidgetItem(str(building.method_power)))
            self.table_min.setItem(row, 7, QTableWidgetItem(str(round(dist, 2))))

        self.table_min.blockSignals(False)  # Разблокируем сигналы
        self.table_min.setSortingEnabled(True)  # Включаем сортировку обратно
        self.table_min.viewport().update()  # Обновляем отображение таблицы

    def randomize(self, line_edits, custom_ranges):
        for line_edit, number_range in zip(line_edits, custom_ranges):
            random_number = random.randint(number_range[0], number_range[1])
            line_edit.setText(str(random_number))

    def set_table_items(self, table, row_index, values):
        for column_index, value in enumerate(values):
            table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
