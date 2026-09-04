from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:token>/", views.portal_view, name="portal-view"),
    path("<uuid:token>/opt-out/", views.opt_out_view, name="portal-opt-out"),
]