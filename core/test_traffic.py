from datetime import timedelta
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import VisitLog
from core.traffic_tracker import (
    determine_path_type,
    get_client_ip,
    get_or_create_visitor_id,
    parse_user_agent,
    should_ignore_request,
)


class TrafficTrackerUnitTests(TestCase):
    def test_parse_googlebot(self):
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        info = parse_user_agent(ua)
        self.assertTrue(info["is_bot"])
        self.assertEqual(info["bot_name"], "Googlebot")
        self.assertEqual(info["device_type"], "Bot")

    def test_parse_bingbot(self):
        ua = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
        info = parse_user_agent(ua)
        self.assertTrue(info["is_bot"])
        self.assertEqual(info["bot_name"], "Bingbot")
        self.assertEqual(info["device_type"], "Bot")

    def test_parse_python_requests_bot(self):
        ua = "python-requests/2.28.1"
        info = parse_user_agent(ua)
        self.assertTrue(info["is_bot"])
        self.assertEqual(info["bot_name"], "Scraper/CLI Tool")

    def test_parse_desktop_chrome_windows(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        info = parse_user_agent(ua)
        self.assertFalse(info["is_bot"])
        self.assertEqual(info["device_type"], "Desktop")
        self.assertEqual(info["browser"], "Google Chrome")
        self.assertEqual(info["os"], "Windows 10/11")

    def test_parse_iphone_safari(self):
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        info = parse_user_agent(ua)
        self.assertFalse(info["is_bot"])
        self.assertEqual(info["device_type"], "Mobile")
        self.assertEqual(info["browser"], "Apple Safari")
        self.assertEqual(info["os"], "iOS (iPhone)")

    def test_determine_path_type(self):
        self.assertEqual(determine_path_type("/dashboard/"), "admin")
        self.assertEqual(determine_path_type("/admin/login/"), "admin")
        self.assertEqual(determine_path_type("/api/v1/products/"), "api")
        self.assertEqual(determine_path_type("/products/"), "storefront")
        self.assertEqual(determine_path_type("/"), "storefront")


class TrafficMiddlewareIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staff_traffic_user",
            password="securePassword123!",
            is_staff=True,
            is_superuser=True,
        )

    def test_guest_visit_is_logged_and_sets_cookie(self):
        response = self.client.get(
            reverse("core:home"),
            HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("rocks_vid", response.cookies)

        log = VisitLog.objects.filter(path=reverse("core:home")).first()
        self.assertIsNotNone(log)
        self.assertFalse(log.is_bot)
        self.assertFalse(log.is_authenticated)
        self.assertIsNone(log.user)
        self.assertEqual(log.device_type, "Desktop")
        self.assertEqual(log.browser, "Google Chrome")

    def test_authenticated_visit_records_user(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(
            reverse("core:home"),
            HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1",
        )
        self.assertEqual(response.status_code, 200)

        log = VisitLog.objects.filter(path=reverse("core:home"), is_authenticated=True).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.staff_user)
        self.assertTrue(log.is_authenticated)
        self.assertFalse(log.is_bot)
        self.assertEqual(log.device_type, "Mobile")

    def test_bot_visit_is_flagged(self):
        response = self.client.get(
            reverse("core:home"),
            HTTP_USER_AGENT="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        )
        self.assertEqual(response.status_code, 200)

        log = VisitLog.objects.filter(is_bot=True).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.is_bot)
        self.assertEqual(log.bot_name, "Googlebot")
        self.assertEqual(log.device_type, "Bot")

    def test_static_assets_are_not_logged(self):
        initial_count = VisitLog.objects.count()
        self.client.get("/static/css/styles.css")
        self.client.get("/health/")
        self.assertEqual(VisitLog.objects.count(), initial_count)


class TrafficControlPanelViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="admin_traffic_tester",
            password="securePassword123!",
            is_staff=True,
            is_superuser=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular_customer",
            password="regularPassword123!",
            is_staff=False,
        )

        # Seed sample visit logs
        now = timezone.now()
        # 1. Registered user visit
        VisitLog.objects.create(
            ip_address="192.168.1.10",
            visitor_id="vid_registered_1",
            user=self.regular_user,
            is_authenticated=True,
            path="/products/",
            status_code=200,
            is_bot=False,
            device_type="Desktop",
            browser="Google Chrome",
            os="Windows 10/11",
            path_type="storefront",
        )
        # 2. Guest visit
        VisitLog.objects.create(
            ip_address="192.168.1.20",
            visitor_id="vid_guest_1",
            user=None,
            is_authenticated=False,
            path="/products/",
            status_code=200,
            is_bot=False,
            device_type="Mobile",
            browser="Apple Safari",
            os="iOS (iPhone)",
            path_type="storefront",
        )
        # 3. Bot visit
        VisitLog.objects.create(
            ip_address="66.249.66.1",
            visitor_id="vid_bot_1",
            user=None,
            is_authenticated=False,
            path="/products/",
            status_code=200,
            is_bot=True,
            bot_name="Googlebot",
            device_type="Bot",
            browser="Googlebot",
            os="Bot / Crawler",
            path_type="storefront",
        )

    def test_anonymous_cannot_access_traffic_dashboard(self):
        response = self.client.get(reverse("controlpanel:traffic_analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/login/", response.url)

    def test_staff_can_view_traffic_analytics(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("controlpanel:traffic_analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "سجل الزيارات والتحليلات")
        self.assertContains(response, "إجمالي المشاهدات")
        self.assertContains(response, "المستخدمون المسجلون")
        self.assertContains(response, "الروبوتات وعناكب البحث")

        # Context metrics
        stats = response.context["stats"]
        self.assertGreaterEqual(stats["total_views"], 3)
        self.assertGreaterEqual(stats["registered_users"], 1)
        self.assertGreaterEqual(stats["guest_visitors"], 1)
        self.assertGreaterEqual(stats["bot_hits"], 1)

    def test_traffic_analytics_user_type_filter(self):
        self.client.force_login(self.staff_user)
        # Filter for bots only
        response = self.client.get(reverse("controlpanel:traffic_analytics") + "?user_type=bot")
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        for item in page_obj:
            self.assertTrue(item.is_bot)

        # Filter for registered only
        response = self.client.get(reverse("controlpanel:traffic_analytics") + "?user_type=registered")
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        for item in page_obj:
            self.assertTrue(item.is_authenticated)

    def test_traffic_export_csv(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("controlpanel:traffic_export_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("التاريخ والوقت", content)
        self.assertIn("Googlebot", content)
        self.assertIn("regular_customer", content)

    def test_traffic_log_detail_json(self):
        self.client.force_login(self.staff_user)
        log = VisitLog.objects.filter(is_bot=True).first()
        response = self.client.get(reverse("controlpanel:traffic_log_detail", args=[log.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], log.pk)
        self.assertEqual(data["bot_name"], "Googlebot")
        self.assertTrue(data["is_bot"])

    def test_dashboard_index_shows_traffic_stats(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("controlpanel:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("traffic_stats", response.context)
        self.assertContains(response, "نشاط الموقع المباشر (اليوم)")
        self.assertContains(response, "مشاهدات اليوم")

