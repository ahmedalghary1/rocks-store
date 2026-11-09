import re
import secrets
from urllib.parse import urlparse
from django.conf import settings

# Pre-compiled regular expressions for bot detection
BOT_PATTERNS = [
    ("Googlebot", re.compile(r"googlebot|google-inspectiontool|storebot-google|mediapartners-google|adsbot-google|feedfetcher-google", re.I)),
    ("Bingbot", re.compile(r"bingbot|bingpreview|msnbot|adidxbot", re.I)),
    ("YandexBot", re.compile(r"yandexbot|yandeximages|yandexaccessibilitybot|yandexmobilebot", re.I)),
    ("DuckDuckBot", re.compile(r"duckduckbot", re.I)),
    ("Baiduspider", re.compile(r"baiduspider", re.I)),
    ("Applebot", re.compile(r"applebot", re.I)),
    ("AhrefsBot", re.compile(r"ahrefsbot|ahrefssiteaudit", re.I)),
    ("SemrushBot", re.compile(r"semrushbot|splitbee", re.I)),
    ("PetalBot", re.compile(r"petalbot", re.I)),
    ("DotBot", re.compile(r"dotbot|rogerbot", re.I)),
    ("ByteSpider", re.compile(r"bytespider", re.I)),
    ("FacebookBot", re.compile(r"facebookexternalhit|facebot|meta-externalagent", re.I)),
    ("Twitterbot", re.compile(r"twitterbot", re.I)),
    ("WhatsApp", re.compile(r"whatsapp", re.I)),
    ("TelegramBot", re.compile(r"telegrambot", re.I)),
    ("LinkedInBot", re.compile(r"linkedinbot", re.I)),
    ("Pinterestbot", re.compile(r"pinterestbot", re.I)),
    ("Slackbot", re.compile(r"slackbot", re.I)),
    ("Discordbot", re.compile(r"discordbot", re.I)),
    ("Amazonbot", re.compile(r"amazonbot", re.I)),
    ("UptimeRobot", re.compile(r"uptimerobot", re.I)),
    ("Pingdom", re.compile(r"pingdom", re.I)),
    ("GTmetrix", re.compile(r"gtmetrix", re.I)),
    ("Lighthouse", re.compile(r"chrome-lighthouse", re.I)),
    ("Scraper/CLI Tool", re.compile(r"python-requests|aiohttp|httpx|curl/|wget|urllib|postmanruntime|scrapy|headlesschrome|phantomjs", re.I)),
    ("Generic Crawler", re.compile(r"bot|crawler|spider|crawl|slurp|fetch|robot|scan|checker|archiver|scraper", re.I)),
]

IGNORED_EXTENSIONS = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".map", ".mp4", ".webm",
)

IGNORED_PATH_PREFIXES = (
    "/static/",
    "/media/",
)

IGNORED_EXACT_PATHS = {
    "/health/",
    "/favicon.ico",
}


def parse_user_agent(user_agent: str) -> dict:
    """
    Parses User-Agent string to detect bots, browser, OS, and device type
    without requiring third-party dependencies.
    """
    ua = (user_agent or "").strip()
    if not ua:
        return {
            "is_bot": False,
            "bot_name": "",
            "device_type": "Unknown",
            "browser": "Unknown",
            "browser_version": "",
            "os": "Unknown",
        }

    # 1. Detect Bots & Crawlers
    for bot_name, pattern in BOT_PATTERNS:
        if pattern.search(ua):
            return {
                "is_bot": True,
                "bot_name": bot_name,
                "device_type": "Bot",
                "browser": bot_name,
                "browser_version": "",
                "os": "Bot / Crawler",
            }

    # 2. Detect Operating System
    os_name = "Unknown"
    if "Windows NT 10.0" in ua or "Windows NT 11.0" in ua:
        os_name = "Windows 10/11"
    elif "Windows NT 6.3" in ua:
        os_name = "Windows 8.1"
    elif "Windows NT 6.1" in ua:
        os_name = "Windows 7"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "iPhone" in ua:
        os_name = "iOS (iPhone)"
    elif "iPad" in ua:
        os_name = "iPadOS"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        os_name = "macOS"
    elif "Android" in ua:
        os_name = "Android"
    elif "Linux" in ua:
        os_name = "Linux"
    elif "CrOS" in ua:
        os_name = "Chrome OS"

    # 3. Detect Device Type
    device_type = "Desktop"
    if re.search(r"iPad|Tablet|PlayBook|Silk", ua, re.I) or ("Android" in ua and "Mobile" not in ua):
        device_type = "Tablet"
    elif re.search(r"iPhone|iPod|Android.*Mobile|webOS|BlackBerry|IEMobile|Opera Mini", ua, re.I):
        device_type = "Mobile"

    # 4. Detect Browser
    browser = "Other"
    browser_version = ""

    if "Edg/" in ua or "Edge/" in ua or "EdgA/" in ua:
        browser = "Microsoft Edge"
        m = re.search(r"(?:Edg|Edge|EdgA)/([\d.]+)", ua)
        if m:
            browser_version = m.group(1).split(".")[0]
    elif "SamsungBrowser/" in ua:
        browser = "Samsung Internet"
        m = re.search(r"SamsungBrowser/([\d.]+)", ua)
        if m:
            browser_version = m.group(1).split(".")[0]
    elif "OPR/" in ua or "Opera/" in ua:
        browser = "Opera"
        m = re.search(r"(?:OPR|Opera)/([\d.]+)", ua)
        if m:
            browser_version = m.group(1).split(".")[0]
    elif "Chrome/" in ua or "CriOS/" in ua:
        browser = "Google Chrome"
        m = re.search(r"(?:Chrome|CriOS)/([\d.]+)", ua)
        if m:
            browser_version = m.group(1).split(".")[0]
    elif "Firefox/" in ua or "FxiOS/" in ua:
        browser = "Mozilla Firefox"
        m = re.search(r"(?:Firefox|FxiOS)/([\d.]+)", ua)
        if m:
            browser_version = m.group(1).split(".")[0]
    elif "Safari/" in ua:
        browser = "Apple Safari"
        m = re.search(r"Version/([\d.]+)", ua)
        if m:
            browser_version = m.group(1).split(".")[0]

    return {
        "is_bot": False,
        "bot_name": "",
        "device_type": device_type,
        "browser": browser,
        "browser_version": browser_version,
        "os": os_name,
    }


def get_client_ip(request) -> str:
    """Safely extracts visitor IP address, respecting trusted reverse proxy settings."""
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            if ip:
                return ip
        real_ip = request.META.get("HTTP_X_REAL_IP")
        if real_ip:
            return real_ip.strip()
    return request.META.get("REMOTE_ADDR") or "127.0.0.1"


def get_or_create_visitor_id(request) -> tuple[str, bool]:
    """
    Retrieves the unique visitor token from cookie or returns a new one.
    Returns (visitor_id, is_new).
    """
    cookie_id = request.COOKIES.get("rocks_vid")
    if cookie_id and 16 <= len(cookie_id) <= 64 and re.match(r"^[a-zA-Z0-9_-]+$", cookie_id):
        return cookie_id, False
    return secrets.token_hex(16), True


def should_ignore_request(request) -> bool:
    """Returns True if request should be skipped from visitor logs (assets, health checks, etc.)."""
    path = request.path_info or request.path
    if path in IGNORED_EXACT_PATHS:
        return True
    for prefix in IGNORED_PATH_PREFIXES:
        if path.startswith(prefix):
            return True
    lower_path = path.lower()
    for ext in IGNORED_EXTENSIONS:
        if lower_path.endswith(ext):
            return True
    return False


def determine_path_type(path: str) -> str:
    """Categorizes the request path for easier filtering."""
    if path.startswith(("/dashboard/", "/admin/")):
        return "admin"
    if path.startswith("/api/"):
        return "api"
    return "storefront"

