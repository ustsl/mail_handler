from __future__ import annotations

from typing import Any

from aiohttp import FormData

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json


def finalize_and_chunk_patients(
    form_data: FormData,
    patients_data: list[dict[str, Any]],
    *,
    chunk_size: int = 200,
    repeat_files: bool = False,
) -> FormData | list[FormData]:
    """
    Split only `patients_info_json` into multiple requests (<= chunk_size rows per request).

    Flow:
    - Caller builds `form_data` with all common fields (sender/subject/message/files/...)
    - Caller extracts `patients_data` from attachments
    - This helper clones the base FormData N times and injects `patients_info_json` per chunk

    Notes:
    - Attachments are NOT split.
    - By default files are sent only in the first request (`repeat_files=False`) so we
      don't re-upload the same XLS/PDF multiple times. If the receiving API expects the
      file on every request, set `repeat_files=True`.
    - Returns a single FormData when `patients_data` fits into one request, otherwise a list.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    base_fields: list[tuple[dict[str, Any], dict[str, Any], Any]] = []
    for type_options, headers, value in getattr(form_data, "_fields", []):
        if type_options.get("name") == "patients_info_json":
            continue
        base_fields.append((type_options, headers, value))

    if len(patients_data) <= chunk_size:
        finalize_and_add_patients_json(form_data, patients_data)
        return form_data

    chunks: list[FormData] = []
    for start in range(0, len(patients_data), chunk_size):
        chunk_form = FormData()
        for type_options, _headers, value in base_fields:
            name = type_options.get("name")
            if not name:
                continue
            if not repeat_files and name == "files" and start != 0:
                continue
            chunk_form.add_field(
                name,
                value,
                filename=type_options.get("filename"),
                content_type=type_options.get("content_type"),
            )

        finalize_and_add_patients_json(chunk_form, patients_data[start : start + chunk_size])
        chunks.append(chunk_form)

    return chunks
