from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    role = forms.ChoiceField(choices=[("admin", "Admin"), ("agent", "Recovery Agent")])

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "role"]