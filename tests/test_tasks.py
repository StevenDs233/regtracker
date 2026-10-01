import pytest

from notices.models import Notice, ScrapeRun, Source
from notices.tasks import run_scrape
from tests.test_scraper import LISTING


@pytest.fixture
def source(db):
    return Source.objects.create(name="Test Regulator", url="https://regulator.ca/", item_selector="ul.notices li a", date_selector=".date")


def test_run_scrape_saves_new_notices_with_tags(source, monkeypatch):
    monkeypatch.setattr("notices.tasks.fetch_html", lambda url: LISTING)
    run = run_scrape(source)

    assert run.status == ScrapeRun.Status.SUCCESS
    assert (run.items_found, run.items_new) == (2, 2)
    notice = Notice.objects.get(url="https://regulator.ca/decisions/2026-41")
    assert "rates" in notice.tags and "decision" in notice.tags


def test_run_scrape_is_idempotent(source, monkeypatch):
    monkeypatch.setattr("notices.tasks.fetch_html", lambda url: LISTING)
    run_scrape(source)
    second = run_scrape(source)

    assert second.items_new == 0
    assert Notice.objects.count() == 2


def test_run_scrape_records_failures(source, monkeypatch):
    def boom(url):
        raise TimeoutError("page took too long")

    monkeypatch.setattr("notices.tasks.fetch_html", boom)
    with pytest.raises(TimeoutError):
        run_scrape(source)

    run = ScrapeRun.objects.get()
    assert run.status == ScrapeRun.Status.FAILED
    assert "page took too long" in run.error
    assert run.finished_at is not None


def test_notice_list_page_filters_by_search(client, source, monkeypatch):
    monkeypatch.setattr("notices.tasks.fetch_html", lambda url: LISTING)
    run_scrape(source)

    response = client.get("/", {"q": "wind"})
    assert response.status_code == 200
    assert b"Wind Farm Interconnection" in response.content
    assert b"General Rate Application" not in response.content
