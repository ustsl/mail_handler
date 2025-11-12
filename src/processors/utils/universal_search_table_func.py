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
