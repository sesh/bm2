import thttp

from links.importers import ExpiredCredentialException, MissingCredentialException
from links.models import Link, UserSettings


def short_text(text):
    parts = text.split(".")

    result = ""

    for p in parts:
        result += p + "."
        if len(result) > 80:
            return result

    return result


def import_stars(user, request=None):
    settings = UserSettings.objects.get(user=user)

    if not (settings.feedbin_username and settings.feedbin_password):
        raise MissingCredentialException()

    response = thttp.request(
        "https://api.feedbin.com/v2/starred_entries.json",
        basic_auth=(settings.feedbin_username, settings.feedbin_password),
    )

    if response.status != 200:
        raise ExpiredCredentialException()

    if len(response.json) > 0:
        entries = thttp.request(
            "https://api.feedbin.com/v2/entries.json",
            basic_auth=(settings.feedbin_username, settings.feedbin_password),
            params={"ids": ",".join([str(x) for x in response.json[-100:]])},
        )

        count_added = 0
        for feedbin_link in entries.json:
            link, created = Link.objects.get_or_create(url=feedbin_link["url"], user=request.user)

            if created:
                count_added += 1
                link.title = feedbin_link["title"] or short_text(feedbin_link.get("summary", "")) or "No title"
                link.added = feedbin_link["created_at"]
                link.tags.add("feedbin-starred")
                link.save()

        return count_added
