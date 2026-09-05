from functools import wraps
from django.shortcuts import redirect


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = getattr(request.user, "profile", None)
        if not profile or profile.role != "admin":
            return redirect("agent-queue")
        return view_func(request, *args, **kwargs)
    return wrapped


def agent_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        profile = getattr(request.user, "profile", None)
        if not profile or profile.role != "agent":
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    return wrapped