from typing import Iterable, Sequence

import zip_extractor


ZIP_MAX_COMPRESSED_BYTES = 10 * 1024 * 1024


def extract_files_from_zip(
    file_bytes: bytes,
    allowed_extensions: Iterable[str],
    password: str = "",
    pin_length: int | None = None,
) -> list[tuple[str, bytes]]:
    """
    Возвращает список файлов с подходящими расширениями из ZIP
    с учётом пароля или набора паролей.
    """
    if len(file_bytes) > ZIP_MAX_COMPRESSED_BYTES:
        print("ZIP-файл превышает лимит 10 МБ, пропускаем вложение.")
        return []

    lowered_exts: Sequence[str] = tuple(ext.lower() for ext in allowed_extensions)

    def _safe_extract(fn, *args) -> list[tuple[str, bytes]]:
        try:
            return fn(*args) or []
        except Exception as e:
            print(f"Ошибка распаковки ZIP: {e}")
            return []

    if pin_length is not None:
        return _safe_extract(
            zip_extractor.extract_with_number_passes,
            file_bytes,
            lowered_exts,
            pin_length,
        )

    if password:
        return _safe_extract(
            zip_extractor.extract_with_pass, file_bytes, lowered_exts, password
        )

    return _safe_extract(zip_extractor.extract, file_bytes, lowered_exts)
