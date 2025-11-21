import pandas as pd


def universal_search_table_func(dataframe, fio_syn, polis_syn):
    """
    Ищет строку заголовков, где встречаются указанные слова fio_syn и polis_syn,
    затем извлекает пары (ФИО, Полис) из строк ниже.
    """
    if dataframe is None or dataframe.empty:
        return []

    fio_names = [fio_syn] if isinstance(fio_syn, str) else fio_syn
    polis_names = [polis_syn] if isinstance(polis_syn, str) else polis_syn
    fio_names_lower = [name.lower() for name in fio_names]
    polis_names_lower = [name.lower() for name in polis_names]

    header_row_index = -1
    fio_col_index = -1
    polis_col_index = -1
    patients_data = []

    # --- поиск строки заголовков ---
    for i, row in dataframe.iterrows():
        row_values = [str(v).strip() for v in row.values if pd.notna(v)]
        if not row_values:
            continue

        has_fio = any(name in row_values for name in fio_names)
        has_polis = any(name in row_values for name in polis_names)

        if has_fio and has_polis:
            header_row_index = i
            header_list = [str(v).strip() for v in list(dataframe.iloc[i])]
            for name in fio_names:
                if name in header_list:
                    fio_col_index = header_list.index(name)
                    break
            for name in polis_names:
                if name in header_list:
                    polis_col_index = header_list.index(name)
                    break
            break

    if header_row_index == -1:
        return []

    # --- извлечение строк ниже заголовков ---
    for i in range(header_row_index + 1, len(dataframe)):
        row_data = dataframe.iloc[i]
        fio_val = (
            row_data.iloc[fio_col_index] if fio_col_index < len(row_data) else None
        )
        polis_val = (
            row_data.iloc[polis_col_index] if polis_col_index < len(row_data) else None
        )

        if pd.notna(fio_val) and pd.notna(polis_val):
            fio_text = str(fio_val).strip()
            polis_text = str(polis_val).strip()
            fio_lower = fio_text.lower()
            polis_lower = polis_text.lower()

            if (
                not fio_text
                or not polis_text
                or fio_lower == "nan"
                or polis_lower == "nan"
            ):
                continue

            # если строка повторяет заголовок, пропускаем её
            if fio_lower in fio_names_lower and polis_lower in polis_names_lower:
                continue

            patients_data.append(
                {"patient_name": fio_text, "insurance_policy_number": polis_text}
            )

    return patients_data


def universal_search_table_func_v2(dataframe, name_parts_headers, polis_syn):
    """
    Ищет строку заголовков, содержащую все перечисленные столбцы для ФИО и полис.
    Собирает ФИО из нескольких столбцов в одну строку.

    :param name_parts_headers: список заголовков (или списков синонимов) для частей имени.
                               Пример: ['Фамилия', 'Имя', 'Отчество']
    :param polis_syn: строка или список синонимов для поиска столбца полиса.
    """
    if dataframe is None or dataframe.empty:
        return []

    # Нормализация входных данных в списки
    parts_to_search = (
        name_parts_headers
        if isinstance(name_parts_headers, list)
        else [name_parts_headers]
    )
    polis_names = [polis_syn] if isinstance(polis_syn, str) else polis_syn

    header_row_index = -1
    name_col_indices = []  # Будет хранить индексы [idx_фамилия, idx_имя, idx_отчество]
    polis_col_index = -1
    patients_data = []

    # --- 1. Поиск строки заголовков ---
    for i, row in dataframe.iterrows():
        # Получаем чистые значения строки
        row_values = [str(v).strip() for v in row.values if pd.notna(v)]
        if not row_values:
            continue

        # Проверяем наличие полиса
        has_polis = any(name in row_values for name in polis_names)
        if not has_polis:
            continue

        # Проверяем наличие ВСЕХ частей имени (Фамилия, Имя и т.д.)
        current_indices = []
        header_list = [str(v).strip() for v in list(dataframe.iloc[i])]
        all_parts_found = True

        for part in parts_to_search:
            # part может быть строкой "Фамилия" или списком синонимов ["Фамилия", "Last Name"]
            syns = [part] if isinstance(part, str) else part

            found_index = -1
            for s in syns:
                if s in header_list:
                    found_index = header_list.index(s)
                    break

            if found_index != -1:
                current_indices.append(found_index)
            else:
                all_parts_found = False
                break

        if all_parts_found:
            header_row_index = i
            name_col_indices = current_indices
            # Находим индекс полиса
            for name in polis_names:
                if name in header_list:
                    polis_col_index = header_list.index(name)
                    break
            break

    if header_row_index == -1:
        return []

    # --- 2. Извлечение и склейка данных ---
    for i in range(header_row_index + 1, len(dataframe)):
        row_data = dataframe.iloc[i]

        # Извлекаем полис
        polis_val = (
            row_data.iloc[polis_col_index] if polis_col_index < len(row_data) else None
        )
        polis_text = str(polis_val).strip() if pd.notna(polis_val) else ""

        if not polis_text or polis_text.lower() == "nan":
            continue

        # Извлекаем и склеиваем части имени
        full_name_parts = []
        for col_idx in name_col_indices:
            if col_idx < len(row_data):
                val = row_data.iloc[col_idx]
                if pd.notna(val):
                    txt = str(val).strip()
                    if txt and txt.lower() != "nan":
                        full_name_parts.append(txt)

        full_name = " ".join(full_name_parts)

        if full_name:
            patients_data.append(
                {"patient_name": full_name, "insurance_policy_number": polis_text}
            )

    return patients_data
