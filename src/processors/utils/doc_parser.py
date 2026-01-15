import shutil
import subprocess
import tempfile


def extract_text_from_doc(doc_bytes: bytes) -> str:
    if not doc_bytes:
        return ""

    catdoc_path = shutil.which("catdoc")
    if not catdoc_path:
        return ""

    try:
        # catdoc only accepts file paths, so use a short-lived temp file.
        with tempfile.NamedTemporaryFile(suffix=".doc") as tmp:
            tmp.write(doc_bytes)
            tmp.flush()

            result = subprocess.run(
                [catdoc_path, tmp.name],
                capture_output=True,
                check=False,
            )
    except Exception:
        return ""

    if result.returncode != 0 and not result.stdout:
        return ""

    text = result.stdout.decode("utf-8", errors="replace")
    if "\uFFFD" in text:
        alt = result.stdout.decode("cp1251", errors="replace")
        if alt.count("\uFFFD") < text.count("\uFFFD"):
            text = alt
    return text
