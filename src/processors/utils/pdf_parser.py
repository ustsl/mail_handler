import pdf_text


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return ""
    try:
        return pdf_text.extract_text(pdf_bytes)
    except Exception:
        return ""
