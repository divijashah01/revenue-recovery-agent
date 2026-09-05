from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignupForm
from .models import Profile


def _redirect_by_role(user):
    if user.is_superuser:
        return redirect("dashboard")
    profile = getattr(user, "profile", None)
    if profile and profile.role == "agent":
        return redirect("agent-queue")
    return redirect("dashboard")


def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role=form.cleaned_data["role"])
            login(request, user)
            return _redirect_by_role(user)
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return _redirect_by_role(request.user)
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("home")