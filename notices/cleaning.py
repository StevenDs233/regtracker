"""Pure functions for turning messy scraped text into clean, structured data."""
import re
from datetime import date
from urllib.parse import urldefrag, urljoin

from dateutil import parser as date_parser

TAG_KEYWORDS = {
    "rates": ["rate", "tariff", "pricing", "fuel adjustment"],
    "hearing": ["hearing", "intervenor", "oral argument"],
    "decision": ["decision", "order", "ruling"],
    "application": ["application", "filing", "submission"],
    "consultation": ["consultation", "comment", "engagement"],
    "renewables": ["solar", "wind", "renewable", "net metering"],
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_date(text: str) -> date | None:
    """Parse dates such as 'Sept 3, 2026', '2026-09-03', or 'Posted: 03/09/2026'."""
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return None
    cleaned = re.sub(r"^(posted|published|updated|date)\s*:?\s*", "", cleaned, flags=re.I)
    cleaned = cleaned.replace("Sept ", "Sep ")
    try:
        return date_parser.parse(cleaned, fuzzy=False, dayfirst=False).date()
    except (ValueError, OverflowError):
        return None


def absolute_url(href: str, base_url: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    url, _fragment = urldefrag(urljoin(base_url, href))
    return url if url.startswith(("http://", "https://")) else None


def tag_title(title: str) -> list[str]:
    lowered = title.lower()
    return sorted(tag for tag, words in TAG_KEYWORDS.items() if any(w in lowered for w in words))
