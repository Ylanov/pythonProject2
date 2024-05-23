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