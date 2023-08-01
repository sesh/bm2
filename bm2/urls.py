"""
URL configuration for bm2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.http import HttpResponse
from django.urls import include, path

from authuser.views import LoginWithTotpView
from links.views import (
    add,
    api_link,
    dashboard,
    delete,
    edit,
    import_feedbin,
    import_github,
    import_hackernews,
    user_settings,
)


def robots(request):
    return HttpResponse("User-Agent: *", headers={"Content-Type": "text/plain; charset=UTF-8"})


def security(request):
    return HttpResponse(
        "Contact: security@brntn.me\nExpires: 2025-01-01T00:00:00.000Z",
        headers={"Content-Type": "text/plain; charset=UTF-8"},
    )


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("add/", add, name="add"),
    path("delete/<uuid:pk>/", delete, name="delete-link"),
    path("edit/<uuid:pk>/", edit, name="edit-link"),
    path("settings/", user_settings, name="user-settings"),
    # "api"
    path("api/<uuid:pk>/", api_link, name="api-link"),
    # importers
    path("import/github/", import_github, name="github-import"),
    path("import/feedbin/", import_feedbin, name="feedbin-import"),
    path("import/hackernews/", import_hackernews, name="hackernews-import"),
    # .well-known
    path("robots.txt", robots),
    path(".well-known/security.txt", security),
    # Django accounts
    path("accounts/login/", LoginWithTotpView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
]

if settings.DEBUG and settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
