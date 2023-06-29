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
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from links.views import add, dashboard, edit, import_feedbin, import_github, settings


def robots(request):
    return HttpResponse("User-Agent: *", headers={"Content-Type": "text/plain; charset=UTF-8"})


def security(request):
    return HttpResponse(
        "Contact: <your-email>\nExpires: 2025-01-01T00:00:00.000Z",
        headers={"Content-Type": "text/plain; charset=UTF-8"},
    )


def trigger_error(request):
    pass


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("add/", add, name="add"),
    path("edit/<uuid:pk>/", edit, name="edit-link"),
    path("settings/", settings, name="user-settings"),
    # importers
    path("import/github/", import_github, name="github-import"),
    path("import/feedbin/", import_feedbin, name="feedbin-import"),
    # .well-known
    path("robots.txt", robots),
    path(".well-known/security.txt", security),
    path(".well-known/500", trigger_error),
    path("admin/", admin.site.urls),
    # Django accounts
    path("accounts/", include("django.contrib.auth.urls")),
]
