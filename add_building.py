import math
import ui  # Импорт ui.py для доступа к классу BuildingData

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
    sum_esh, cumulativeWork = 0, [0]
    for i, esh in enumerate(group_esh):
        sum_esh += esh
        if sum_esh <= group_cnt:
            cumulativeWork.append(cumulativeWork[-1] + (group_min[i] * 7) / 2)
        elif sum_esh - esh <= group_cnt:
            cumulativeWork.append((group_cnt * 7) / 2)
            break
    cumulativeWorks.append(cumulativeWork[1:])

    for group_index, group_cnt in enumerate(group_cnt_list[1:], start=1):
        cumulativeWork = [(free_group[group_index - 1] * 7) / 2]
        for i, esh in enumerate(group_esh):
            if sum(group_esh) <= group_cnt:
                next_value = sum(group_esh) * 7 / 2
                cumulativeWork[0] = max((free_group[group_index - 1] * 7) / 2, next_value)
            elif sum(group_esh) - esh >= group_cnt:
                next_value = group_cnt * 7 / 2
                cumulativeWork[0] = max((free_group[group_index - 1] * 7) / 2, next_value)
                break
        cumulativeWorks.append(cumulativeWork)

    for index, cumulativeWork in enumerate(cumulativeWorks):
        workload = [0] * time
        intensity_ranges = [
            (int(time_esh_1), int(time_esh_2), cumulativeWork[0] if len(cumulativeWork) > 0 else 0),
            (int(time_esh_2), int(time_esh_3), cumulativeWork[1] if len(cumulativeWork) > 1 else 0),
            (int(time_esh_3), time, cumulativeWork[2] if len(cumulativeWork) > 2 else 0)
        ]
        for start, end, intensity in intensity_ranges:
            for time_stamp in range(start, end):
                workload[time_stamp] = intensity
        while workload and workload[-1] == 0:
            workload.pop()
        if len(cumulativeWork) < 3 and len(workload) < number_surv:
            if workload:
                workload.extend([workload[-1]] * (number_surv - len(workload)))
            else:
                initial_value = 0
                workload.extend([initial_value] * number_surv)
        workloads.append(workload)

    for i in accumulate(workloads[-1]):
        if number_surv != 0:
            value = min(round(i / ((float(debris_volume) * 6.8) / number_surv)), number_surv)
        else:
            value = 0
        rescue.append(value)
        if value >= number_surv:
            break
    print("Кол-во групп с эшелонов", group_esh)
    print(" Необходимое кол-во групп исходя из площади", group_cnt_list)
    print("список свободных групп", free_group)
    return workloads[-1], rescue, group_esh, group_min, cumulativeWorks, landslide_height, sublists


def PeopleTrapped_func(time, landslide_height, rescue, num_fatalities, surviv, workload, sublists, tempa):
    def find_tab_index(tab_widget, name):
        """Поиск вкладки по имени."""
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i) == name:
                return i
        return -1
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