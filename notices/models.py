from django.db import models


class Source(models.Model):
    """A regulator web page that lists notices, decisions, or hearings."""

    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500, unique=True)
    item_selector = models.CharField(
        max_length=200,
        blank=True,
        help_text="CSS selector for each notice link. Leave blank to collect all meaningful links on the page.",
    )
    date_selector = models.CharField(
        max_length=200,
        blank=True,
        help_text="CSS selector, relative to each item's container, for the published date.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Notice(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="notices")
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    published_on = models.DateField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_on", "-first_seen_at"]
        indexes = [models.Index(fields=["source", "-first_seen_at"])]

    def __str__(self):
        return self.title


class ScrapeRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="runs")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    items_found = models.PositiveIntegerField(default=0)
    items_new = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
