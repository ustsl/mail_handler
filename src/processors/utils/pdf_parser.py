import io
import pypdf


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return ""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        full_text = "".join(page.extract_text() or "" for page in reader.pages)

        return full_text

    except Exception as e:
        print(f"Не удалось извлечь текст из PDF: {e}")
        return ""
