# Agent guidance for insurance letters

## `patients_info_json` schema
When insurance rules (Sogaz, Sovcom, Ingos and others) build `patients_info_json`, ensure each entry contains:

- `patient_name` — full name string for the insured person (First Middle Last or Last First Middle depending on source).
- `insurance_policy_number` — policy identifier pulled from the letter.
- `date_from` (optional) — ISO date (`YYYY-MM-DD`) for the beginning of the guarantee or coverage period when available.
- `date_to` (optional) — ISO date for the end of the guarantee or coverage period when available.

Fields should be omitted rather than empty if there is no value.

## Handling large tables
Rules are only allowed to chunk patient data (JSON arrays) after attachments are parsed. The XLS/XLSX/PDF files must be attached whole, even when the resulting patient payload spans multiple requests.

## Debug helpers
Reusable debug scripts under `debug/` (e.g. custom helpers for XLS or PDF) must:

- Add the project root to `sys.path` so the `src` package is loadable.
- Default to the file shipped in `debug/` (like `test.xls` or `test.PDF`) when no argument is passed.
- Keep the same output path structure (e.g. `patients_info_debug.txt`) so tests can compare easily.

## Utility references
- `src/processors/utils/date_helpers.py`: centralizes Russian-date parsing (ISO normalization + range extraction) so every rule requiring `date_from`/`date_to` can reuse the helpers instead of duplicating `_RUSSIAN_MONTHS` tables.
