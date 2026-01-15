import sys
from pathlib import Path
from typing import Any


from src.processors.insurance_rules.sovcom_insurance_rule import (
    sovcom_insurance_rule,
)


def _print_form_data(form_data: Any) -> None:
    for type_options, _, value in getattr(form_data, "_fields", []):
        name = type_options.get("name")
        if name == "patients_info_json":
            print(value)
            return
    print("patients_info_json not found")


def main() -> None:
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test.PDF")
    pdf_bytes = pdf_path.read_bytes()

    form_data = sovcom_insurance_rule(
        content=None,
        subject="test",
        sender="debug@example.local",
        attachments=[(pdf_path.name, pdf_bytes)],
    )
    _print_form_data(form_data)


if __name__ == "__main__":
    main()
