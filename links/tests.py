import secrets
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

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
