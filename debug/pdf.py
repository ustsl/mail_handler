import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.processors.insurance_rules.kaplife_insurance_rule import kaplife_insurance_rule
from src.processors.insurance_rules.vsk_insurance_rule import (
    vsk_insurance_rule,
)
from src.processors.insurance_rules.renhealth_insurance_rule import (
    renhealth_insurance_rule,
)
from src.processors.insurance_rules.sogaz_insurance_rule import sogaz_insurance_rule
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.insurance_rules.luchi_insurance_rule import luchi_insurance_rule


def _print_form_data(form_data: Any) -> None:
    for type_options, _, value in getattr(form_data, "_fields", []):
        name = type_options.get("name")
        if name == "patients_info_json":
            payload = value
            print(payload)
            try:
                decoded = json.loads(payload)
                print("Итог по правилу:", len(decoded), "записей")
            except Exception as exc:
                print("Не удалось посчитать записи:", exc)
            return
    print("patients_info_json not found")


def main() -> None:
    pdf_path = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("test.PDF")
    )
    file_bytes = pdf_path.read_bytes()
    pdf_text = extract_text_from_pdf(file_bytes)

    print(pdf_text)

    form_data = luchi_insurance_rule(
        content=None,
        subject="test",
        sender="debug@example.local",
        attachments=[(pdf_path.name, file_bytes)],
    )
    _print_form_data(form_data)


if __name__ == "__main__":
    main()
