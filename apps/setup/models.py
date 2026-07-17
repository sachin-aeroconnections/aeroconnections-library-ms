from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class SetupConfig(models.Model):
    setup_completed = models.BooleanField(default=False)
    setup_pin = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Setup Configuration"
        verbose_name_plural = "Setup Configuration"

    def __str__(self):
        return f"Setup Config (Completed: {self.setup_completed})"

    @classmethod
    def is_configured(cls):
        return cls.objects.filter(pk=1, setup_completed=True).exists()

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def has_users(cls):
        return User.objects.exists()
