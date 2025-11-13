import json
from typing import Any, Dict, List

from aiohttp import FormData


def finalize_and_add_patients_json(
    form_data: FormData, patients_data: List[Dict[str, Any]]
) -> None:
    """
    Преобразует список данных о пациентах в JSON и добавляет в FormData.

    Если список пуст, создается JSON-строка с одной пустой записью.

    Args:
        form_data: Объект FormData для добавления поля.
        patients_data: Список словарей с данными пациентов.
    """
    if patients_data:
        print(
            f"Всего извлечено {len(patients_data)} записей о пациентах. Добавляем в JSON."
        )
        patients_json_string = json.dumps(patients_data, ensure_ascii=False)
    else:
        # Если пациенты не найдены, создаем JSON с пустой записью
        patients_json_string = json.dumps(
            [{"patient_name": "", "insurance_policy_number": ""}], ensure_ascii=False
        )

    form_data.add_field("patients_info_json", patients_json_string)
