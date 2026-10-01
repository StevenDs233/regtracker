"""Fetching (Playwright) is kept separate from parsing (BeautifulSoup) so parsing is easy to test."""
import logging

from bs4 import BeautifulSoup

from .cleaning import absolute_url, normalize_whitespace, parse_date

logger = logging.getLogger(__name__)

MIN_TITLE_LENGTH = 15


def fetch_html(url: str, timeout_ms: int = 30_000) -> str:
    """Render the page in headless Chromium so JavaScript-built listings are included."""
    from playwright.sync_api import sync_playwright  # imported lazily so tests don't need a browser

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent="RegTracker/1.0 (research project)")
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            return page.content()
        finally:
            browser.close()


def parse_listing(html: str, base_url: str, item_selector: str = "", date_selector: str = "") -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    links = soup.select(item_selector) if item_selector else soup.find_all("a", href=True)

    items, seen = [], set()
    for link in links:
        anchor = link if link.name == "a" else link.find("a", href=True)
        if anchor is None:
            continue
        title = normalize_whitespace(anchor.get_text(" "))
        url = absolute_url(anchor.get("href"), base_url)
        if not url or len(title) < MIN_TITLE_LENGTH or url in seen:
            continue
        seen.add(url)

        published_on = None
        if date_selector:
            container = link.find_parent(["li", "tr", "article", "div"]) or link
            date_el = container.select_one(date_selector)
            published_on = parse_date(date_el.get_text(" ")) if date_el else None

        items.append({"title": title[:500], "url": url, "published_on": published_on})

    logger.info("Parsed %d items from %s", len(items), base_url)
    return items
