import secrets
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from thttp import Response

from authuser.models import User
from links.models import Link, UserSettings


class LinkModelTestCase(TestCase):
    def test_str_returns_title(self):
        link = Link.objects.create(url="https://example.org", title="Example Site")
        self.assertEqual("Example Site", str(link))

    def test_icon_uses_ddg_service(self):
        link = Link.objects.create(url="https://example.org")
        self.assertEqual("https://icons.duckduckgo.com/ip3/example.org.ico", link.icon())


class DashboardTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="tester@example.org")

    def test_dashboard_limits_links(self):
        self.client.force_login(self.user)

        for _ in range(1000):
            Link.objects.create(user=self.user, url=f"https://example.org/{secrets.token_hex()}")

        response = self.client.get("/")
        self.assertEqual(100, len(response.context["links"]))

    def test_dashboard_only_shows_users_bookmarks(self):
        self.client.force_login(self.user)
        second_user = User.objects.create(email="test2@example.org")

        for _ in range(10):
            Link.objects.create(user=self.user, url=f"https://example.org/{secrets.token_hex()}")
            Link.objects.create(user=second_user, url=f"https://example.org/{secrets.token_hex()}")

        response = self.client.get("/")
        self.assertEqual(10, len(response.context["links"]))

    def test_dashboard_filtering_by_domain(self):
        self.client.force_login(self.user)

        for _ in range(10):
            Link.objects.create(user=self.user, url=f"https://example.org/{secrets.token_hex()}")
            Link.objects.create(user=self.user, url=f"https://example.com/{secrets.token_hex()}")

        response = self.client.get("/?domain=example.com")
        self.assertEqual(10, len(response.context["links"]))

    def test_dashboard_filtering_by_domain_with_mixed_scheme(self):
        self.client.force_login(self.user)

        for _ in range(10):
            Link.objects.create(user=self.user, url=f"https://example.org/{secrets.token_hex()}")
            Link.objects.create(user=self.user, url=f"http://example.com/{secrets.token_hex()}")
            Link.objects.create(user=self.user, url=f"https://example.com/{secrets.token_hex()}")

        response = self.client.get("/?domain=example.com")
        self.assertEqual(20, len(response.context["links"]))

    def test_dashboard_filtering_by_date(self):
        self.client.force_login(self.user)

        for i in range(10):
            d = timezone.now() - timedelta(days=i)
            for _ in range(5):
                link = Link.objects.create(user=self.user, url=f"https://example.org/{secrets.token_hex()}")
                link.added = d
                link.save()

        yesterday = timezone.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

        response = self.client.get(f"/?date={date_str}")
        self.assertEqual(5, len(response.context["links"]))

    def test_dashboard_filtering_by_tag(self):
        self.client.force_login(self.user)

        for i in range(10):
            link = Link.objects.create(user=self.user, url=f"https://example.org/{secrets.token_hex()}")
            link.tags.add("a")

            link = Link.objects.create(user=self.user, url=f"https://example.org/{secrets.token_hex()}")
            link.tags.add("b")

        response = self.client.get("/?tag=a")
        self.assertEqual(10, len(response.context["links"]))

    def test_pagination_returns_first_page_if_invalid_page(self):
        self.client.force_login(self.user)

        for x in range(1000):
            Link.objects.create(user=self.user, url=f"https://example.org/{x}")

        response = self.client.get("/?page=asodas")
        self.assertEqual("https://example.org/999", response.context["links"][0].url)

    def test_pagination_next_and_previous_urls(self):
        self.client.force_login(self.user)

        for x in range(1000):
            Link.objects.create(user=self.user, url=f"https://example.org/{x}")

        response = self.client.get("/?page=4")
        self.assertEqual("http://testserver/?page=3", response.context["prev"])
        self.assertEqual("http://testserver/?page=5", response.context["next"])

        response = self.client.get("/")
        self.assertEqual(None, response.context["prev"])
        self.assertEqual("http://testserver/?page=2", response.context["next"])

        response = self.client.get("/?page=10")
        self.assertEqual("http://testserver/?page=9", response.context["prev"])
        self.assertEqual(None, response.context["next"])

        response = self.client.get("/?page=3&domain=example.org")
        self.assertEqual("http://testserver/?page=2&domain=example.org", response.context["prev"])

    def test_limit_restricts_number_of_links(self):
        self.client.force_login(self.user)

        for x in range(1000):
            Link.objects.create(user=self.user, url=f"https://example.org/{x}")

        response = self.client.get("/?limit=10")
        self.assertEqual(10, len(response.context["links"]))

    def test_random_param_shuffles_links(self):
        self.client.force_login(self.user)

        for x in range(1000):
            link = Link.objects.create(user=self.user, url=f"https://example.org/{x}")

        response = self.client.get("/")
        self.assertEqual(link.pk, response.context["links"][0].pk)

        # there's a 1/1000 chance this will fail let's do it 10 times
        for _ in range(10):
            response = self.client.get("/?random=1")

            # if the first link isn't the last one created that means
            # the shuffle has worked: exit the test
            if link.pk != response.context["links"][0].pk:
                return

        self.assertTrue(False)

    def test_search(self):
        self.client.force_login(self.user)

        Link.objects.create(user=self.user, url="https://example.org/", title="example")
        Link.objects.create(user=self.user, url="https://waxy.org/wordle", title="Fun little game")
        Link.objects.create(user=self.user, url="https://games.nytimes.com", title="Crosswords & Wordles")
        link = Link.objects.create(user=self.user, url="https://puzzleanswers.com", title="")
        link.tags.add("wordle")
        link.save()

        response = self.client.get("/?q=wordle")
        self.assertEqual(3, len(response.context["links"]))


class AddLinkTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="tester@example.org")
        self.client.force_login(self.user)

    def test_add_form_when_logged_in(self):
        response = self.client.get("/add/")
        self.assertEqual(200, response.status_code)

    def test_prefills_url_if_provided_as_url_param(self):
        response = self.client.get("/add/?url=https://google.com")
        self.assertTrue('value="https://google.com"' in response.content.decode())

    def test_add_link_to_url_that_already_exists_redirects(self):
        link = Link.objects.create(user=self.user, url="https://example.org")
        response = self.client.get("/add/?url=https://example.org")
        self.assertEqual(link.get_absolute_url(), response.url)

    def test_add_link_by_submitting_form(self):
        response = self.client.post("/add/", {"url": "https://example.org/added"})
        self.assertEqual("/", response.url)

        links = Link.objects.filter(url__exact="https://example.org/added")
        self.assertEqual(1, len(links))

    def test_add_link_fails_if_url_missing(self):
        response = self.client.post("/add/", {"notes": "Just a note, eh?"})
        self.assertTrue(response.context["form"].has_error("url"))


class EditLinkTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="tester@example.org")
        self.client.force_login(self.user)

    def test_can_update_link(self):
        link = Link.objects.create(user=self.user, title="Test Title", url="https://example.com")
        response = self.client.post(
            f"/edit/{link.pk}/", {"title": "This is the updated title", "url": "https://example.com"}
        )

        # returns redirect
        self.assertEqual(302, response.status_code)

        link = Link.objects.get(pk=link.pk)
        self.assertEqual("This is the updated title", link.title)

    def test_edit_form_is_prefilled_with_instance(self):
        link = Link.objects.create(user=self.user, title="Test Title", url="https://example.com")
        response = self.client.get(f"/edit/{link.pk}/")

        self.assertInHTML(
            '<input type="text" name="title" value="Test Title" maxlength="1000" id="id_title">',
            response.content.decode(),
        )


class SettingsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="tester@example.org")
        self.client.force_login(self.user)

    def test_loading_settings_creates_settings_object_if_missing(self):
        self.assertEqual(0, UserSettings.objects.filter(user=self.user).count())
        self.client.get("/settings/")
        self.assertEqual(1, UserSettings.objects.filter(user=self.user).count())

    def test_updating_settings_saves_new_value(self):
        user_settings = UserSettings.objects.create(user=self.user, github_pat="BBB")
        self.client.post("/settings/", {"github_pat": "AAA"})

        user_settings = UserSettings.objects.get(user=self.user)
        self.assertEqual("AAA", user_settings.github_pat)


class ImporterTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="tester@example.org")
        self.client.force_login(self.user)

    def test_imports_fail_with_missing_settings(self):
        for url in ["/import/github/", "/import/feedbin/", "/import/hackernews/"]:
            response = self.client.post(url, follow=True)
            messages = list(response.context["messages"])
            self.assertTrue("in settings" in messages[0].message)

    def test_imports_fail_with_missing_credential(self):
        UserSettings.objects.create(user=self.user)

        for url in ["/import/github/", "/import/feedbin/", "/import/hackernews/"]:
            response = self.client.post(url, follow=True)
            messages = list(response.context["messages"])
            self.assertTrue("in settings" in messages[0].message)

    def test_import_github_stars(self):
        UserSettings.objects.create(user=self.user, github_pat="AAA")

        mocked_response = Response(
            None,
            None,
            [
                {
                    "repo": {
                        "html_url": "https://github.com/sesh/thttp",
                        "full_name": "sesh/thttp",
                        "description": "A tiny http library with a mocked response!",
                        "topics": ["test", "http", "mocking"],
                    },
                    "starred_at": "2023-06-29T23:39:35Z",
                }
            ],
            200,
            None,
            {},
            None,
        )

        with mock.patch("links.importers.github.thttp.request", return_value=mocked_response):
            self.client.post("/import/github/")
            self.assertEqual(1, Link.objects.filter(user=self.user).count())
            self.assertEqual("https://github.com/sesh/thttp", Link.objects.filter(user=self.user)[0].url)

    def test_import_feedbin_entries(self):
        UserSettings.objects.create(user=self.user, feedbin_username="aaa", feedbin_password="aaa")  # nosec

        first_mocked_response = Response(None, None, ["123456"], 200, None, {}, None)
        second_mocked_response = Response(
            None,
            None,
            [{"url": "https://example.org", "title": "Official example", "created_at": "2023-06-29T23:39:35Z"}],
            200,
            None,
            {},
            None,
        )

        with mock.patch(
            "links.importers.feedbin.thttp.request", side_effect=[first_mocked_response, second_mocked_response]
        ):
            self.client.post("/import/feedbin/")
            self.assertEqual(1, Link.objects.filter(user=self.user).count())
            self.assertEqual("https://example.org", Link.objects.filter(user=self.user)[0].url)

    def test_import_feedbin_uses_summary_if_no_title(self):
        UserSettings.objects.create(user=self.user, feedbin_username="aaa", feedbin_password="aaa")  # nosec

        first_mocked_response = Response(None, None, ["123456"], 200, None, {}, None)
        second_mocked_response = Response(
            None,
            None,
            [
                {
                    "url": "https://example.net",
                    "title": "",
                    "summary": "This is a summary of the post",
                    "created_at": "2023-06-29T23:39:35Z",
                },
                {
                    "url": "https://example.org",
                    "title": "",
                    "summary": "Magni pariatur omnis ducimus atque tenetur. "
                    "Unde culpa inventore ipsam et. Unde ipsam sed assumenda officiis. "
                    "Asperiores qui aut consequuntur ullam sunt vero ea enim.",
                    "created_at": "2023-06-29T23:39:35Z",
                },
            ],
            200,
            None,
            {},
            None,
        )

        with mock.patch(
            "links.importers.feedbin.thttp.request", side_effect=[first_mocked_response, second_mocked_response]
        ):
            self.client.post("/import/feedbin/")
            self.assertEqual(2, Link.objects.filter(user=self.user).count())
            self.assertEqual("This is a summary of the post.", Link.objects.filter(user=self.user)[0].title)
            self.assertEqual(
                "Magni pariatur omnis ducimus atque tenetur. "
                "Unde culpa inventore ipsam et. Unde ipsam sed assumenda officiis.",
                Link.objects.filter(user=self.user)[1].title,
            )

    def test_import_hackernews_favoutires(self):
        UserSettings.objects.create(user=self.user, hn_username="brntn")

        mocked_response = Response(
            None, None, {"links": [{"url": "https://example.org", "title": "ICAAN Example Site"}]}, 200, None, {}, None
        )

        with mock.patch("links.importers.hackernews.thttp.request", side_effect=[mocked_response]):
            self.client.post("/import/hackernews/")
            self.assertEqual(1, Link.objects.filter(user=self.user).count())
            self.assertEqual("ICAAN Example Site", Link.objects.filter(user=self.user)[0].title)


class WellKnownTestCase(TestCase):
    def test_robots(self):
        response = self.client.get("/robots.txt")
        self.assertEqual("text/plain; charset=UTF-8", response.headers["content-type"])

    def test_security(self):
        response = self.client.get("/.well-known/security.txt")
        self.assertTrue("security@brntn.me" in response.content.decode())


class DeleteLinkTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="tester@example.org")
        self.client.force_login(self.user)

    def test_deletes_link(self):
        link = Link.objects.create(url="https://example.org", user=self.user)
        self.client.post(f"/delete/{link.pk}/")
        self.assertEqual(0, Link.objects.count())

    def test_delete_link_fails_if_wrong_user(self):
        link = Link.objects.create(url="https://example.org")  # no user
        response = self.client.post(f"/delete/{link.pk}/")

        self.assertEqual(404, response.status_code)
        self.assertEqual(1, Link.objects.count())
