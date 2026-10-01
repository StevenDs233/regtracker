from django.urls import path

from . import views

urlpatterns = [
    path("", views.NoticeListView.as_view(), name="notice_list"),
    path("sources/<int:source_id>/scrape/", views.scrape_now, name="scrape_now"),
]
