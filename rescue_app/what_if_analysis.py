# rescue_app/what_if_analysis.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QCheckBox, QSpinBox, QComboBox, QDialogButtonBox, QWidget)
from PyQt5.QtCore import Qt
import logging

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
        """Создает группы элементов управления для настройки параметров сценариев."""
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
                spin_box.setValue(int(multiplier))  # Используем множитель для установки значения
                spin_box.setEnabled(False)
                checkbox.stateChanged.connect(lambda state, sb=spin_box: sb.setEnabled(state == Qt.Checked))
                hbox.addWidget(spin_box)
                self.scenario_widgets[param_name]["spin_boxes"].append(spin_box)

            # Добавляем QLabel с описанием сценария
            description_label = QLabel(f"  -  Изменить {param_label} на {self.format_multiplier(multiplier)}")
            hbox.addWidget(description_label)
            parameters_layout.addLayout(hbox)

        self.parameters_groupbox.setLayout(parameters_layout)

    def get_scenarios(self):
        """Возвращает список сценариев на основе выбранных параметров."""
        scenarios = [
            {"label": "Базовый сценарий"}
        ]

        for param_name, widgets in self.scenario_widgets.items():
            if widgets["checkbox"].isChecked():
                multipliers = [spin_box.value() for spin_box in widgets["spin_boxes"]]
                for multiplier in multipliers:
                    new_scenario = {
                        "label": f"Изменение {param_name} на {self.format_multiplier(multiplier)}"
                    }
                    new_scenario[param_name] = self.original_values[param_name] * self.format_multiplier(multiplier)
                    scenarios.append(new_scenario)

        return scenarios

    def get_criterion(self):
        """Возвращает выбранный критерий для анализа."""
        criterion_text = self.criterion_combobox.currentText()
        if criterion_text == "Максимум спасённых":
            return "rescue"
        elif criterion_text == "Минимум пострадавших":
            return "num_fatalities"
        elif criterion_text == "Минимум времени":
            return "time_total"
        else:
            logging.warning("Неизвестный критерий, возвращаем 'workload'")
            return "workload"  # Явное возвращение значения по умолчанию

    def format_multiplier(self, multiplier):
        """Форматирует множитель для отображения в описании."""
        return multiplier * 0.1 if isinstance(multiplier, float) else multiplier



