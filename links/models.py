import uuid
from urllib.parse import urlsplit

from django.conf import settings
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    # Required to support foreign key from Tag -> Link with UUID as the primary key
    # https://github.com/jazzband/django-taggit/issues/679

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class Link(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=1000, default="", blank=True)
    note = models.TextField(default="", blank=True)
    tags = TaggableManager(blank=True, through=UUIDTaggedItem)

    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("edit-link", kwargs={"pk": self.pk})

    def icon(self):
        return f"https://icons.duckduckgo.com/ip3/{self.domain()}.ico"

    def domain(self):
        parts = urlsplit(self.url)
        return parts.netloc

    def as_json(self):
        return {
            "id": str(self.id),
            "url": self.url,
            "note": self.note,
            "tags": [t.name for t in self.tags.all()],
            "added": self.added.isoformat(),
            "updated": self.updated.isoformat(),
            "screenshots": [s.as_json() for s in self.linkscreenshot_set.all()],
        }


class LinkScreenshot(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    link = models.ForeignKey("Link", on_delete=models.CASCADE)
    url = models.URLField(max_length=2000)
    added = models.DateTimeField(auto_now_add=True)

    def as_json(self):
        return {
            "id": str(self.id),
            "url": self.url,
            "added": self.added.isoformat(),
        }


class UserSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    github_pat = models.CharField(
        max_length=200, blank=True, help_text="A Github personal access token with access to your stars"
    )

    feedbin_username = models.CharField(
        max_length=300, blank=True, help_text="Your feedbin username, probably an email address"
    )

    feedbin_password = models.CharField(max_length=300, blank=True, help_text="Your feedbin password")

    hn_username = models.CharField(max_length=40, blank=True, help_text="Your Hacker News username")
