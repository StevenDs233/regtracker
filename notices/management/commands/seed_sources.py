from django.core.management.base import BaseCommand

from notices.models import Source

SOURCES = [
    ("Nova Scotia Utility and Review Board", "https://nsuarb.novascotia.ca/"),
    ("Nova Scotia Government News", "https://news.novascotia.ca/en"),
]


class Command(BaseCommand):
    help = "Create starter regulator sources (generic link mode; tune selectors in the admin)."

    def handle(self, *args, **options):
        for name, url in SOURCES:
            _, created = Source.objects.get_or_create(url=url, defaults={"name": name})
            self.stdout.write(f"{'Created' if created else 'Exists'}: {name}")
