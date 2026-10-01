# RegTracker

RegTracker watches Canadian utility regulators for new notices, decisions, and hearings, so an analyst does not have to check each regulator's website by hand.

Every six hours a Celery task opens each regulator page in headless Chromium with Playwright, parses the listing with BeautifulSoup, cleans titles, dates, and links, tags each notice by topic (rates, hearings, decisions, renewables), and stores only new notices in PostgreSQL. A Django page lets you search and filter notices and see the result of every scrape run.

## How it works

```
Celery beat (every 6h)
  -> scrape_all_sources          queues one job per active regulator
     -> scrape_source(id)        retries up to 3 times with backoff
        -> fetch_html            Playwright renders JavaScript-built pages
        -> parse_listing         BeautifulSoup extracts title, URL, date
        -> cleaning              whitespace, date formats, absolute URLs, topic tags
        -> Notice (PostgreSQL)   unique URL makes repeat runs idempotent
        -> ScrapeRun             records found, new, status, and errors
Django views                     search and filter notices, trigger a check
Django admin                     manage regulators and CSS selectors
```

Fetching and parsing are separate on purpose: parsing is a pure function, so it is tested against saved HTML without a browser or network.

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

docker compose up -d                 # PostgreSQL and Redis
cp .env.example .env && export $(cat .env | xargs)

python manage.py migrate
python manage.py seed_sources
python manage.py createsuperuser
python manage.py runserver
```

In two more terminals (with the same environment variables):

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Open http://localhost:8000 and click a "Check ... now" button, or use the admin action on Sources.

Without `POSTGRES_DB` set, the app falls back to SQLite, which is enough for a quick look.

## Adding a regulator

In the admin, add a Source with the listing page URL. Leave the selectors blank to collect every meaningful link on the page, or inspect the page and set `item_selector` (for example `ul.news li a`) and `date_selector` (for example `.date`) for cleaner results.

## Tests

```bash
pytest
```

The suite covers date parsing across formats, URL cleaning, topic tagging, listing parsing with and without selectors, idempotent re-runs, failure recording, and the search view.

## Tech

Python 3.12, Django 5.2, Celery 5.4 with Redis, Playwright, BeautifulSoup, PostgreSQL, pytest, Fomantic UI.
