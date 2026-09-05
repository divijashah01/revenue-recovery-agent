from django.shortcuts import render

APP_NAME = "Vasooli"  # placeholder — rename freely, used everywhere via context


def home_view(request):
    return render(request, "core/home.html", {"app_name": APP_NAME})