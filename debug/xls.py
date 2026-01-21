from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.processors.insurance_rules.sogaz_insurance_rule import (
    sogaz_insurance_rule,
)


def _print_form_data(form_data: Any) -> None:
    def _extract_patients_json(fd: Any) -> str | None:
        for type_options, _, value in getattr(fd, "_fields", []):
            if type_options.get("name") == "patients_info_json":
                return str(value)
        return None

    out_dir = Path(__file__).parent

    if isinstance(form_data, list):
        for index, chunk in enumerate(form_data, start=1):
            payload = _extract_patients_json(chunk)
            if payload is None:
                print(f"[chunk {index}] patients_info_json not found")
                continue
            print(payload)
            try:
                (out_dir / f"patients_info_debug.part{index}.txt").write_text(payload)
            except Exception as exc:  # pragma: no cover - manual debug helper
                print(f"Failed to save patients info: {exc}", file=sys.stderr)
        return

    output_path = out_dir / "patients_info_debug.txt"
    payload = _extract_patients_json(form_data)
    if payload is None:
        print("patients_info_json not found")
        return

    print(payload)
    try:
        output_path.write_text(payload)
    except Exception as exc:  # pragma: no cover - manual debug helper
        print(f"Failed to save patients info: {exc}", file=sys.stderr)


def main() -> int:
    xls_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).with_name("test.xls")
    )
    if not xls_path.exists():
        print(f"File not found: {xls_path}", file=sys.stderr)
        return 1

    xls_bytes = xls_path.read_bytes()

    form_data = sogaz_insurance_rule(
        content=None,
        subject="test",
        sender="debug@example.local",
        attachments=[(xls_path.name, xls_bytes)],
    )
    _print_form_data(form_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
