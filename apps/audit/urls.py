from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("batch/", views.batch_list_view, name="batch-list"),
    path("event/<int:event_id>/", views.event_detail_view, name="event-detail"),
]