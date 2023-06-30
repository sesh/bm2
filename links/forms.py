from django import forms

from .models import Link, UserSettings


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ["url", "title", "note", "tags"]


class UserSettingsForm(forms.ModelForm):
    github_pat = forms.CharField(
        label="Github Personal Access Token",
        strip=False,
        widget=forms.PasswordInput(render_value=True),
        required=False,
    )

    feedbin_password = forms.CharField(
        label="Feedbin password",
        strip=False,
        widget=forms.PasswordInput(render_value=True),
        required=False,
    )

    hn_username = forms.CharField(label="HN username", strip=True, required=False)

    class Meta:
        model = UserSettings
        fields = ["github_pat", "feedbin_username", "feedbin_password", "hn_username"]
