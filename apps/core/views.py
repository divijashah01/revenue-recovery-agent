from django.shortcuts import render

APP_NAME = "Recoup"


def home_view(request):
    return render(request, "core/home.html", {"app_name": APP_NAME})