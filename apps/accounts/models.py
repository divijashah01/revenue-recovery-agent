from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("agent", "Recovery Agent"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="admin")

    def __str__(self):
        return f"{self.user.username} ({self.role})"