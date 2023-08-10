import json
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from links.forms import LinkForm, UserSettingsForm
from links.importers import MissingCredentialException, feedbin, github, hackernews
from links.models import Link, LinkScreenshot, UserSettings
from links.ssrf import uri_is_safe


def build_absolute_uri_with_added_params(request, *, params={}):
    url = request.build_absolute_uri()
    parts = urlsplit(url)
    query = parse_qs(parts.query)

    for k, v in params.items():
        query[k] = v

    url = urlunsplit([parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment])
    return url


@login_required
def dashboard(request):
    links = Link.objects.filter(user=request.user)

    # filtering
    if "domain" in request.GET:
        domain = request.GET["domain"]
        links = links.filter(Q(url__startswith=f"https://{domain}") | Q(url__startswith=f"http://{domain}"))

    if "date" in request.GET:
        d = request.GET["date"]
        links = links.filter(added__date=d)

    if "tag" in request.GET:
        tag = request.GET["tag"]
        links = links.filter(tags__slug__iexact=tag)

    if "q" in request.GET:
        query = request.GET["q"]
        links = links.filter(
            Q(url__icontains=query) | Q(title__icontains=query) | Q(tags__slug__iexact=query)
        ).distinct()

    if "limit" in request.GET:
        limit = int(request.GET["limit"])
        limit = min([limit, 100])
    else:
        limit = 100

    if "random" in request.GET:
        links = links.order_by("?")

    # pagination
    paginator = Paginator(links, limit)

    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1

    current_page = paginator.page(page)
    next_url, prev_url = None, None

    if current_page.has_next():
        next_url = build_absolute_uri_with_added_params(request, params={"page": page + 1})

    if current_page.has_previous():
        prev_url = build_absolute_uri_with_added_params(request, params={"page": page - 1})

    links = current_page.object_list.prefetch_related("tags").prefetch_related("linkscreenshot_set")

    if "json" in request.GET:
        data = {
            "data": [link.as_json() for link in links],
            "next": next_url,
            "prev": prev_url,
        }
        return JsonResponse(data)

    return render(
        request,
        "links.html",
        {
            "links": links,
            "next": next_url,
            "prev": prev_url,
        },
    )


@login_required
def add(request):
    url = request.GET.get("url")

    if url:
        existing_links = Link.objects.filter(url=url, user=request.user)
        if existing_links:
            return redirect(existing_links[0])

    if request.method == "POST":
        form = LinkForm(request.POST)

        if form.is_valid():
            link = form.save()
            link.user = request.user
            link.save()

            messages.info(request, "Bookmark added")
            return redirect("/")
    else:
        if url:
            form = LinkForm(request.GET)
        else:
            form = LinkForm()

    return render(request, "add.html", {"form": form})


@login_required
def edit(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)

    if request.method == "POST":
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.info(request, "Bookmark saved successfully")
            return redirect("/")
    else:
        form = LinkForm(instance=link)

    return render(request, "edit.html", {"form": form})


def screenshot(request, pk):
    # login not required for the screenshots
    # but don't display the other screenshots for this URL unless the user is authenticated
    screenshot = get_object_or_404(LinkScreenshot, pk=pk)
    if request.user == screenshot.link.user:
        link = screenshot.link
    else:
        link = None

    return render(request, "screenshot.html", {"screenshot": screenshot, "link": link})


@login_required
def delete(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)

    if request.method == "POST":
        link.delete()
        return redirect("/")

    return render(request, "delete.html", {"link": link})


@login_required
def user_settings(request):
    user_settings_obj, created = UserSettings.objects.get_or_create(user=request.user)
    if created:
        user_settings_obj.save()

    if request.method == "POST":
        form = UserSettingsForm(request.POST, instance=user_settings_obj)
        if form.is_valid():
            form.save()
            messages.info(request, "Settings saved successfully")
            return redirect("/settings/")
    else:
        form = UserSettingsForm(instance=user_settings_obj)

    return render(request, "settings.html", {"form": form})


@login_required
def import_github(request):
    if request.method == "POST":
        try:
            count = github.import_stars(request.user, request)
        except (UserSettings.DoesNotExist, MissingCredentialException):
            messages.warning(request, "Please add your Github token in settings")
            return redirect("/")

        if count >= 0:
            messages.info(request, f"Imported {count} stars from Github")

    return redirect("/")


@login_required
def import_feedbin(request):
    if request.method == "POST":
        try:
            count = feedbin.import_stars(request.user, request)
        except (UserSettings.DoesNotExist, MissingCredentialException):
            messages.warning(request, "Please add your Feedbin credentials in settings")
            return redirect("/")

        if count >= 0:
            messages.info(request, f"Imported {count} starred entries from Feedbin")

    return redirect("/")


@login_required
def import_hackernews(request):
    if request.method == "POST":
        try:
            count = hackernews.import_favourites(request.user, request)
        except (UserSettings.DoesNotExist, MissingCredentialException):
            messages.warning(request, "Please add your Hacker News username in settings")
            return redirect("/")

        if count >= 0:
            messages.info(request, f"Imported {count} favourites from Hacker News")

    return redirect("/")


@login_required
@csrf_exempt
def api_link(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)

    if request.method == "POST":
        try:
            request_body = json.loads(request.body)
        except Exception as e:
            return JsonResponse(
                {"errors": [{"code": "bad_request", "message": "Failed to parse JSON body", "exception": str(e)}]},
                status=400,
            )

        if "screenshot_url" in request_body:
            url = request_body["screenshot_url"]
            if uri_is_safe(url):
                screenshot, created = LinkScreenshot.objects.get_or_create(link=link, url=url)

                if created:
                    return JsonResponse({"data": link.as_json(), "messages": ["screeshot added"]}, status=201)
                else:
                    return JsonResponse({"data": link.as_json(), "messages": ["screeshot already exists"]})

        return JsonResponse(
            {"errors": [{"code": "bad_request", "message": "Invalid body or unsupported action"}]}, status=400
        )

    else:
        return JsonResponse({"data": link.as_json()})
