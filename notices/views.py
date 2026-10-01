from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from .cleaning import TAG_KEYWORDS
from .models import Notice, ScrapeRun, Source
from .tasks import scrape_source


class NoticeListView(ListView):
    model = Notice
    template_name = "notices/notice_list.html"
    context_object_name = "notices"
    paginate_by = 25

    def get_queryset(self):
        qs = Notice.objects.select_related("source")
        query = self.request.GET.get("q", "").strip()
        source_id = self.request.GET.get("source")
        tag = self.request.GET.get("tag")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(source__name__icontains=query))
        if source_id:
            qs = qs.filter(source_id=source_id)
        if tag:
            qs = qs.filter(tags__contains=tag) if self._json_contains_supported() else qs.filter(tags__icontains=tag)
        return qs

    def _json_contains_supported(self):
        from django.db import connection
        return connection.vendor == "postgresql"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sources"] = Source.objects.filter(is_active=True)
        ctx["tags"] = sorted(TAG_KEYWORDS)
        ctx["recent_runs"] = ScrapeRun.objects.select_related("source")[:6]
        ctx["filters"] = self.request.GET
        return ctx


@require_POST
def scrape_now(request, source_id):
    source = get_object_or_404(Source, pk=source_id, is_active=True)
    scrape_source.delay(source.id)
    messages.success(request, f"Checking {source.name} for new notices.")
    return redirect("notice_list")
