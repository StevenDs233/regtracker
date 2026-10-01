from django.contrib import admin, messages

from .models import Notice, ScrapeRun, Source
from .tasks import scrape_source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "created_at")
    list_filter = ("is_active",)
    actions = ["scrape_now"]

    @admin.action(description="Scrape selected sources now")
    def scrape_now(self, request, queryset):
        for source in queryset:
            scrape_source.delay(source.id)
        messages.success(request, f"Queued {queryset.count()} scrape job(s).")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published_on", "first_seen_at")
    list_filter = ("source",)
    search_fields = ("title",)


@admin.register(ScrapeRun)
class ScrapeRunAdmin(admin.ModelAdmin):
    list_display = ("source", "status", "items_found", "items_new", "started_at", "finished_at")
    list_filter = ("status", "source")
