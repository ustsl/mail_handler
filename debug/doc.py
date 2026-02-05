from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.processors.insurance_rules.akbars_insurance_rule import (
    akbars_insurance_rule,
)
from src.processors.insurance_rules.renins_pult_insurance_rule import (
    renins_pult_insurance_rule,
)
from src.processors.insurance_rules.renins_insurance_rule import renins_insurance_rule
from src.processors.insurance_rules.luchi_insurance_rule import luchi_insurance_rule


def _print_form_data(form_data: Any) -> None:
    for type_options, _, value in getattr(form_data, "_fields", []):
        name = type_options.get("name")
        if name == "patients_info_json":
            print(value)
            return
    print("patients_info_json not found")


def main() -> int:
    doc_path = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("test.doc")
    )
    if not doc_path.exists():
        print(f"File not found: {doc_path}", file=sys.stderr)
        return 1

    doc_bytes = doc_path.read_bytes()

    form_data = luchi_insurance_rule(
        content=None,
        subject="test",
        sender="debug@example.local",
        attachments=[(doc_path.name, doc_bytes)],
    )
    _print_form_data(form_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
