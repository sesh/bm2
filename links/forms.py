from django import forms

from .models import Link, UserSettings


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ["url", "title", "note", "tags"]


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ["github_pat", "feedbin_username", "feedbin_password"]
