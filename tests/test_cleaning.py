from datetime import date

import pytest

from notices.cleaning import absolute_url, normalize_whitespace, parse_date, tag_title


def test_normalize_whitespace_collapses_newlines_and_tabs():
    assert normalize_whitespace("  Rate\n\t application  filed ") == "Rate application filed"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Sept 3, 2026", date(2026, 9, 3)),
        ("2026-09-03", date(2026, 9, 3)),
        ("Posted: September 3, 2026", date(2026, 9, 3)),
        ("not a date", None),
        ("", None),
    ],
)
def test_parse_date_handles_common_formats(raw, expected):
    assert parse_date(raw) == expected


def test_absolute_url_resolves_relative_links_and_drops_fragments():
    assert absolute_url("/decisions/123#top", "https://example.ca/news/") == "https://example.ca/decisions/123"


@pytest.mark.parametrize("href", ["mailto:a@b.ca", "javascript:void(0)", "#section", ""])
def test_absolute_url_rejects_non_page_links(href):
    assert absolute_url(href, "https://example.ca/") is None


def test_tag_title_detects_multiple_topics():
    assert tag_title("Board decision on 2027 rate application") == ["application", "decision", "rates"]
