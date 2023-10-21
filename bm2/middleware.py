"""
This is free and unencumbered software released into the public domain.

https://github.com/sesh/django-middleware
"""

import logging

from django.conf import settings
from django.contrib.auth import login, logout
from django.utils import timezone

from authuser.models import ApiKey

logger = logging.getLogger("django")


def login_with_api_key(get_response):
    def middleware(request):
        authorization_header = request.META.get("HTTP_AUTHORIZATION")
        api_key = authorization_header.replace("Bearer", "").strip() if authorization_header else None

        if api_key:
            try:
                api_key_obj = ApiKey.objects.get(key=api_key, expires__gt=timezone.now())
            except ApiKey.DoesNotExist:
                api_key_obj = None

            if api_key_obj:
                login(request, api_key_obj.user)
                response = get_response(request)
                logout(request)
                return response

        return get_response(request)

    return middleware


def set_remote_addr(get_response):
    def middleware(request):
        request.META["REMOTE_ADDR"] = request.META.get("HTTP_X_REAL_IP", request.META["REMOTE_ADDR"])
        response = get_response(request)
        return response

    return middleware


def permissions_policy(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["Permissions-Policy"] = "interest-cohort=(),microphone=(),camera=(),autoplay=()"
        return response

    return middleware


def referrer_policy(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["Referrer-Policy"] = "same-origin"  # using no-referrer breaks CSRF
        return response

    return middleware


def csp(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "img-src 'self' https://icons.duckduckgo.com https://media.brntn.me; "
            "child-src 'self'; form-action 'self'"
        )

        if settings.DEBUG and settings.ENABLE_DEBUG_TOOLBAR:
            response.headers["Content-Security-Policy"] += "; connect-src 'self'"
        return response

    return middleware


def xss_protect(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return middleware


def expect_ct(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["Expect-CT"] = "enforce, max-age=30m"
        return response

    return middleware


def cache(get_response):
    def middleware(request):
        response = get_response(request)
        if request.method in ["GET", "HEAD"] and "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "max-age=10"
        return response

    return middleware


def corp_coop_coep(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        # response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        return response

    return middleware


def dns_prefetch(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["X-DNS-Prefetch-Control"] = "off"
        return response

    return middleware
