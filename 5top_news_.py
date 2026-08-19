import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib.request
import urllib.parse
import json
import os
import re
import time

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN غير موجود")

if not CHANNEL:
    raise ValueError("TELEGRAM_CHANNEL غير موجود")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLISHED_FILE = os.path.join(BASE_DIR, "published_top_news.txt")


SOURCES = [
    {
        "name": "الإخبارية السورية",
        "url": "https://alikhbariah.com/",
        "domain": "alikhbariah.com",
        "icon": "🇸🇾"
    },
    {
        "name": "سانا",
        "url": "https://sana.sy/",
        "domain": "sana.sy",
        "icon": "🟦"
    },
    {
        "name": "حلب اليوم",
        "url": "https://halabtodaytv.net/",
        "domain": "halabtodaytv.net",
        "icon": "🟨"
    },
    {
        "name": "تلفزيون سوريا",
        "url": "https://www.syria.tv/",
        "domain": "syria.tv",
        "icon": "🔵"
    },
    {
        "name": "الجزيرة",
        "url": "https://www.aljazeera.net/",
        "domain": "aljazeera.net",
        "icon": "🟠"
    }
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.8"
}


BLOCKED_TITLES = [
    "الرئيسية",
    "بث مباشر",
    "البث المباشر",
    "من نحن",
    "اتصل بنا",
    "المزيد",
    "اشترك",
    "تسجيل الدخول",
    "فيديو",
    "الصور",
    "بودكاست",
    "برامج"
]


BLOCKED_URL_PARTS = [
    "/live",
    "/video/",
    "/videos/",
    "/program",
    "/programs/",
    "/podcast",
    "/privacy",
    "/about",
    "/contact",
    "/login",
    "/search",
    "/tag/"
]


def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_link(link):
    if not link:
        return ""
    return link.split("#")[0].strip()


def same_domain(link, domain):
    try:
        hostname = urlparse(link).hostname or ""
        return hostname == domain or hostname.endswith("." + domain)
    except Exception:
        return False


def looks_like_article(title, link, domain):
    if not title or not link:
        return False

    title = clean_text(title)

    if len(title) < 25 or len(title) > 260:
        return False

    if title in BLOCKED_TITLES:
        return False

    lower_link = link.lower()

    for part in BLOCKED_URL_PARTS:
        if part in lower_link:
            return False

    if not same_domain(link, domain):
        return False

    parsed = urlparse(link)

    if parsed.path in ("", "/"):
        return False

    return True


def load_published():
    if not os.path.exists(PUBLISHED_FILE):
        return set()

    with open(PUBLISHED_FILE, "r", encoding="utf-8") as file:
        return {
            line.strip()
            for line in file
            if line.strip()
        }


def save_published(link):
    with open(PUBLISHED_FILE, "a", encoding="utf-8") as file:
        file.write(link + "\n")


def get_top_story(source):
    try:
        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=25
        )

        response.raise_for_status()

    except Exception as e:
        print("❌ فشل الاتصال:", source["name"])
        print(e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    seen_titles = set()
    seen_links = set()

    for tag in soup.find_all("a", href=True):

        title = clean_text(
            tag.get_text(" ", strip=True)
        )

        href = tag.get("href", "").strip()

        if not href:
            continue

        link = urljoin(source["url"], href)
        link = clean_link(link)

        if not looks_like_article(
            title,
            link,
            source["domain"]
        ):
            continue

        normalized_title = title.lower()

        if normalized_title in seen_titles:
            continue

        if link in seen_links:
            continue

        seen_titles.add(normalized_title)
        seen_links.add(link)

        return {
            "source": source["name"],
            "title": title,
            "link": link,
            "icon": source["icon"]
        }

    return None


def send_to_telegram(story):

    message = f"""📰 {story["title"]}

{story["icon"]} المصدر: {story["source"]}
🔗 {story["link"]}
"""

    data = urllib.parse.urlencode({
        "chat_id": CHANNEL,
        "text": message,
        "disable_web_page_preview": False
    }).encode("utf-8")

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    with urllib.request.urlopen(
        url,
        data=data,
        timeout=30
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    return result.get("ok", False)


print()
print("=" * 70)
print("بوت أهم الأخبار")
print("=" * 70)

published = load_published()
total_new = 0

for source in SOURCES:

    print()
    print("فحص:", source["name"])

    story = get_top_story(source)

    if not story:
        print("❌ لم يتم العثور على خبر.")
        continue

    if story["link"] in published:
        print("سبق نشره:", story["title"])
        continue

    print("خبر جديد:")
    print(story["title"])

    try:
        if send_to_telegram(story):

            save_published(story["link"])
            published.add(story["link"])
            total_new += 1

            print("SUCCESS - تم النشر")

            time.sleep(2)

        else:
            print("Telegram لم يؤكد النشر.")

    except Exception as e:
        print("خطأ أثناء النشر:")
        print(e)


print()
print("=" * 70)

if total_new == 0:
    print("لا توجد أخبار جديدة للنشر.")
else:
    print("تم نشر", total_new, "أخبار جديدة.")

print("=" * 70)