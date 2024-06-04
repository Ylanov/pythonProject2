from PyQt5.QtWidgets import QLabel, QLineEdit, QComboBox, QHBoxLayout, QTableWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import csv
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from reportlab.pdfgen import canvas
import pandas as pd
from PyQt5.QtCore import QSettings
from building_data import BuildingData

def create_label(text, tooltip=None):
    """Создает QLabel с указанным текстом и всплывающей подсказкой."""
    label = QLabel(text)
    if tooltip:
        label.setToolTip(tooltip)
    return label


def create_line_edit(tooltip=None):
    """Создает QLineEdit со всплывающей подсказкой."""
    line_edit = QLineEdit()
    if tooltip:
        line_edit.setToolTip(tooltip)
    return line_edit


def create_combobox(items, tooltip=None):
    """Создает QComboBox с заданными элементами и всплывающей подсказкой."""
    combobox = QComboBox()
    combobox.addItems(items)
    if tooltip:
        combobox.setToolTip(tooltip)
    return combobox


def hbox(*widgets):
    """Создает QHBoxLayout и добавляет в него переданные виджеты."""
    layout = QHBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def copy_table(source):
    """Создает копию QTableWidget."""
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
    """Ищет вкладку с заданным именем и возвращает ее индекс."""
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == name:
            return i
    return -1

def export_to_csv(table_min):
    try:
        file_path, _ = QFileDialog.getSaveFileName(None, "Экспорт в CSV", "", "CSV files (*.csv)")  # Убираем self
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Записываем заголовки столбцов
                writer.writerow(
                    [table_min.horizontalHeaderItem(i).text() for i in range(table_min.columnCount())])
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
            QMessageBox.information("Успех", "Данные успешно экспортированы в CSV файл.")

    except Exception as e:
        QMessageBox.critical("Ошибка", f"Произошла ошибка: {str(e)}")


def export_to_excel(table_min):
    try:
        file_path, _ = QFileDialog.getSaveFileName("Экспорт в Excel", "", "Excel files (*.xlsx)")
        if file_path:
            # Создаем DataFrame из данных таблицы
            df = pd.DataFrame(
                [[table_min.item(row, col).text() for col in range(table_min.columnCount())] for row in
                 range(table_min.rowCount())],
                columns=[table_min.horizontalHeaderItem(i).text() for i in
                         range(table_min.columnCount())]
            )

            # Сохраняем DataFrame в Excel файл
            wb = openpyxl.Workbook()
            ws = wb.active
            for r in dataframe_to_rows(df, index=False, header=True):
                ws.append(r)
            wb.save(file_path)
            QMessageBox.information("Успех", "Данные успешно экспортированы в Excel файл.")

    except Exception as e:
        QMessageBox.critical("Ошибка", f"Произошла ошибка: {str(e)}")


def export_to_pdf(table_min):
    try:
        file_path, _ = QFileDialog.getSaveFileName("Экспорт в PDF", "", "PDF files (*.pdf)")
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
            QMessageBox.information(None,"Успех", "Данные успешно экспортированы в PDF файл.")

    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Произошла ошибка: {str(e)}")


def save_project(buildings, file_path=None):
    try:
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(None, "Сохранить проект", "", "JSON files (*.json)")
        if file_path:
            settings = QSettings(file_path, QSettings.IniFormat)
            from building_data import buildings
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
            QMessageBox.information(None,"Успех", "Проект успешно сохранен.")
    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Произошла ошибка: {str(e)}")


def load_project(file_path=None):
    try:
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(None, "Загрузить проект", "", "JSON files (*.json)")
        if file_path:
            settings = QSettings(file_path, QSettings.IniFormat)
            from building_data import buildings  # Импортируем buildings здесь
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
            msg_box = QMessageBox()  # Создаем объект QMessageBox
            msg_box.information(None, "Успех", "Проект успешно загружен.")
            return buildings  # Возвращаем buildings
    except Exception as e:
        msg_box = QMessageBox()  # Создаем объект QMessageBox
        msg_box.critical(None, "Ошибка", f"Произошла ошибка: {str(e)}")