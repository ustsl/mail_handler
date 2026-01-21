from __future__ import annotations

from datetime import datetime
import re

_RUSSIAN_MONTHS = {
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12",
}


def normalize_date(value: str) -> str | None:
    """Return an ISO date (YYYY-MM-DD) after parsing Russian date formats."""

    text = value.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    tokens = re.split(r"[\s,]+", text.lower())
    if len(tokens) >= 3 and tokens[0].isdigit():
        day = tokens[0]
        month = tokens[1]
        year = tokens[2]
        month_num = _RUSSIAN_MONTHS.get(month)
        if month_num and year.isdigit():
            return f"{int(year):04d}-{month_num}-{int(day):02d}"

    return None


def extract_date_range(
    text: str, pattern: str, flags: int = 0
) -> tuple[str | None, str | None]:
    """Find the first two capture groups that look like date endpoints."""

    match = re.search(pattern, text, flags=flags)
    if not match:
        return None, None

    start = None
    end = None
    if match.lastindex and match.lastindex >= 1:
        start = normalize_date(match.group(1))
    if match.lastindex and match.lastindex >= 2:
        end = normalize_date(match.group(2))

    return start, end
