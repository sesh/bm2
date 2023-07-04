import base64
import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.utils import timezone


class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the provided email and password.
        """
        if not email:
            raise ValueError("The given email address must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    User model that uses email addresses instead of usernames, and
    name instead of first / last name fields.

    All other fields from the Django auth.User model are kept to
    ensure maximum compatibility with the built in management
    commands.
    """

    email = models.EmailField(blank=True, default="", unique=True)
    name = models.CharField(max_length=200, blank=True, default="")

    totp_secret = models.CharField(max_length=200, blank=True, default="")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name or self.email.split("@")[0]

    def totp_url(self):
        secret = base64.b32encode(self.totp_secret.encode()).decode()
        return f"otpauth://totp/{self.email}?secret={secret.rstrip('=')}&issuer=bm2&algorithm=SHA1&digits=6&period=30"


def generate_api_key():
    return "bm2_" + secrets.token_urlsafe()


def expiry_time():
    return timezone.now() + timedelta(days=30)


class ApiKey(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    key = models.CharField(max_length=200, default=generate_api_key, unique=True)
    expires = models.DateTimeField(default=expiry_time)
    created = models.DateTimeField(auto_now_add=True)
