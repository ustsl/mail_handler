from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from striprtf.striprtf import rtf_to_text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.processors.insurance_rules.alfa_insurance_rule import (
    alfa_insurance_rule,
)


def _print_form_data(form_data: Any) -> None:
    for type_options, _, value in getattr(form_data, "_fields", []):
        name = type_options.get("name")
        if name == "patients_info_json":
            payload = value
            print(payload)
            try:
                decoded = json.loads(payload)
                print("Итог по правилу alfa:", len(decoded), "записей")
            except Exception as exc:
                print("Не удалось посчитать записи:", exc)
            return
    print("patients_info_json not found")


def _render_rtf(file_bytes: bytes) -> str:
    try:
        decoded = file_bytes.decode("cp1251")
    except UnicodeDecodeError:
        decoded = file_bytes.decode("utf-8", errors="ignore")
    try:
        return rtf_to_text(decoded)
    except Exception:
        return decoded


def main() -> None:
    rtf_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).with_name("test.rtf")
    )
    file_bytes = rtf_path.read_bytes()
    print(_render_rtf(file_bytes))

    form_data = alfa_insurance_rule(
        content=None,
        subject="test",
        sender="debug@example.local",
        attachments=[(rtf_path.name, file_bytes)],
    )
    _print_form_data(form_data)


if __name__ == "__main__":
    main()
