from datetime import date

from notices.scraper import parse_listing

LISTING = """
<html><body>
  <nav><a href="/about">About the regulator and its board members</a></nav>
  <ul class="notices">
    <li><a href="/decisions/2026-41">Decision on General Rate Application 2027</a><span class="date">Sept 3, 2026</span></li>
    <li><a href="/hearings/88">Notice of Public Hearing: Wind Farm Interconnection</a><span class="date">2026-08-28</span></li>
    <li><a href="/decisions/2026-41">Decision on General Rate Application 2027</a><span class="date">Sept 3, 2026</span></li>
    <li><a href="/x">Short</a></li>
  </ul>
</body></html>
"""


def test_parse_listing_with_selectors_extracts_titles_urls_and_dates():
    items = parse_listing(LISTING, "https://regulator.ca/", "ul.notices li a", ".date")
    assert [i["url"] for i in items] == ["https://regulator.ca/decisions/2026-41", "https://regulator.ca/hearings/88"]
    assert items[0]["published_on"] == date(2026, 9, 3)
    assert items[1]["title"] == "Notice of Public Hearing: Wind Farm Interconnection"


def test_parse_listing_generic_mode_skips_nav_short_and_duplicate_links():
    items = parse_listing(LISTING, "https://regulator.ca/")
    titles = [i["title"] for i in items]
    assert "About the regulator and its board members" not in titles
    assert "Short" not in titles
    assert len(items) == 2
