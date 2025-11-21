import io
import zipfile
import zlib
from typing import Iterable, Sequence


ZIP_MAX_COMPRESSED_BYTES = 5 * 1024 * 1024
ZIP_MAX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024


def extract_first_file_from_zip(
    file_bytes: bytes,
    allowed_extensions: Iterable[str],
    password: str = "",
    password_candidates: Iterable[str] | None = None,
) -> tuple[str, bytes] | None:
    """
    Безопасно извлекает первый файл с подходящим расширением из архива.
    """
    if len(file_bytes) > ZIP_MAX_COMPRESSED_BYTES:
        print("ZIP-файл превышает лимит 5 МБ, пропускаем вложение.")
        return None

    attempts: Sequence[str]
    if password_candidates is not None:
        attempts = [str(p or "") for p in password_candidates]
    else:
        attempts = [password or ""]

    lowered_exts = tuple(ext.lower() for ext in allowed_extensions)
    total_uncompressed = 0

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                total_uncompressed += info.file_size
                if total_uncompressed > ZIP_MAX_UNCOMPRESSED_BYTES:
                    print(
                        "Объём распаковки превышает безопасный лимит, прекращаем чтение."
                    )
                    return None
                if info.filename.lower().endswith(lowered_exts):
                    for pwd in attempts:
                        try:
                            read_kwargs = {}
                            if pwd:
                                read_kwargs["pwd"] = pwd.encode()
                            data = archive.read(info, **read_kwargs)
                            return info.filename, data
                        except RuntimeError as e:
                            error_msg = str(e).lower()
                            if "password" not in error_msg:
                                print(
                                    f"Ошибка чтения файла '{info.filename}' из ZIP: {e}"
                                )
                            continue
                        except zlib.error as e:
                            print(
                                f"Ошибка распаковки файла '{info.filename}' (вероятно, неверный пароль): {e}"
                            )
                            continue
                    print(
                        f"Подходящий пароль для '{info.filename}' не найден, файл пропущен."
                    )
    except zipfile.BadZipFile as e:
        print(f"Некорректный ZIP-файл: {e}")
    return None


def _extract_first_spreadsheet_from_zip(
    file_bytes: bytes, password: str = "rgs"
) -> tuple[str, bytes] | None:
    """
    Обёртка для обратной совместимости с обработчиками,
    извлекающая первую таблицу из архива.
    """
    return extract_first_file_from_zip(
        file_bytes=file_bytes,
        allowed_extensions=(".xls", ".xlsx"),
        password=password,
    )
