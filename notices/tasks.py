import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .cleaning import tag_title
from .models import Notice, ScrapeRun, Source
from .scraper import fetch_html, parse_listing

logger = logging.getLogger(__name__)


def run_scrape(source: Source) -> ScrapeRun:
    """Scrape one source and record the outcome. Safe to run repeatedly: existing URLs are skipped."""
    run = ScrapeRun.objects.create(source=source)
    try:
        html = fetch_html(source.url)
        items = parse_listing(html, source.url, source.item_selector, source.date_selector)

        existing = set(Notice.objects.filter(url__in=[i["url"] for i in items]).values_list("url", flat=True))
        new_notices = [
            Notice(source=source, title=i["title"], url=i["url"], published_on=i["published_on"], tags=tag_title(i["title"]))
            for i in items
            if i["url"] not in existing
        ]
        with transaction.atomic():
            Notice.objects.bulk_create(new_notices, ignore_conflicts=True)

        run.status = ScrapeRun.Status.SUCCESS
        run.items_found = len(items)
        run.items_new = len(new_notices)
    except Exception as exc:
        logger.exception("Scrape failed for %s", source.url)
        run.status = ScrapeRun.Status.FAILED
        run.error = f"{type(exc).__name__}: {exc}"[:2000]
        raise
    finally:
        run.finished_at = timezone.now()
        run.save()
    return run


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, max_retries=3)
def scrape_source(self, source_id: int) -> dict:
    source = Source.objects.get(pk=source_id, is_active=True)
    run = run_scrape(source)
    return {"source": source.name, "found": run.items_found, "new": run.items_new}


@shared_task
def scrape_all_sources() -> int:
    ids = list(Source.objects.filter(is_active=True).values_list("id", flat=True))
    for source_id in ids:
        scrape_source.delay(source_id)
    return len(ids)
