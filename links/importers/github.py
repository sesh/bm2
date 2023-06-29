import thttp

from links.models import Link, UserSettings


def import_stars(user, request=None):
    settings = UserSettings.objects.get(user=user)

    if not settings.github_pat:
        return 0

    url = "https://api.github.com/user/starred"
    response = thttp.request(
        url, headers={"Authorization": f"token {settings.github_pat}", "Accept": "application/vnd.github.v3.star+json"}
    )

    count_added = 0
    for star_json in response.json:
        link, created = Link.objects.get_or_create(url=star_json["repo"]["html_url"], user=user)

        if created:
            count_added += 1
            link.title = star_json["repo"]["full_name"] or star_json["repo"]["name"]
            link.note = star_json["repo"]["description"]

            link.tags.add("github-starred", *star_json["repo"].get("topics", []))
            link.added = star_json["starred_at"]
            link.save()

    return count_added
