import thttp

from links.importers import MissingCredentialException
from links.models import Link, UserSettings


def import_favourites(user, request=None):
    settings = UserSettings.objects.get(user=user)

    if not settings.hn_username:
        raise MissingCredentialException()

    url = f"https://osnhvzckcf.execute-api.ap-southeast-2.amazonaws.com/api/users/{settings.hn_username}"
    response = thttp.request(url)

    count_added = 0

    if response.json:
        for favourite in response.json.get("links", []):
            link, created = Link.objects.get_or_create(url=favourite["url"], user=user)

            if created:
                count_added += 1
                link.title = favourite["title"]

            link.tags.add("hn-fav")
            link.save()

    return count_added
