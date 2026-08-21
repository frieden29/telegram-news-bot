import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib.request
import urllib.parse
import json
import os
import re
import time


# =========================================================
# Telegram
# =========================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL")


# =========================================================
# Facebook
# =========================================================

FACEBOOK_PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_TOKEN")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")


if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN غير موجود")

if not TELEGRAM_CHANNEL:
    raise ValueError("TELEGRAM_CHANNEL غير موجود")

if not FACEBOOK_PAGE_TOKEN:
    raise ValueError("FACEBOOK_PAGE_TOKEN غير موجود")

if not FACEBOOK_PAGE_ID:
    raise ValueError("FACEBOOK_PAGE_ID غير موجود")


# =========================================================
# ملف الأخبار المنشورة
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PUBLISHED_FILE = os.path.join(
    BASE_DIR,
    "published_top_news.txt"
)


# =========================================================
# كلمات مرتبطة بسوريا
# تستخدم للمصادر العربية والعالمية
# =========================================================

SYRIA_KEYWORDS = [
    "سوريا",
    "سورية",
    "سوري",
    "سوريين",
    "السوري",
    "السورية",
    "السوريين",
    "دمشق",
    "حلب",
    "إدلب",
    "حمص",
    "حماة",
    "درعا",
    "السويداء",
    "اللاذقية",
    "طرطوس",
    "دير الزور",
    "الرقة",
    "الحسكة",
    "القنيطرة"
]


# =========================================================
# المصادر
#
# syria_only = False
#   يأخذ أهم خبر جديد من الموقع
#
# syria_only = True
#   لا يقبل إلا خبرًا متعلقًا بسوريا
# =========================================================

SOURCES = [

    # ========================
    # المصادر السورية
    # ========================

    {
        "name": "حلب اليوم",
        "url": "https://halabtodaytv.net/",
        "domain": "halabtodaytv.net",
        "icon": "🟨",
        "syria_only": False
    },

    {
        "name": "تلفزيون سوريا",
        "url": "https://www.syria.tv/",
        "domain": "syria.tv",
        "icon": "🔵",
        "syria_only": False
    },

    {
        "name": "الإخبارية السورية",
        "url": "https://alikhbariah.com/",
        "domain": "alikhbariah.com",
        "icon": "🇸🇾",
        "syria_only": False
    },

    {
        "name": "سانا",
        "url": "https://sana.sy/",
        "domain": "sana.sy",
        "icon": "🟦",
        "syria_only": False
    },


    # ========================
    # المصادر العربية
    # أخبار سوريا فقط
    # ========================

    {
        "name": "الجزيرة",
        "url": "https://www.aljazeera.net/",
        "domain": "aljazeera.net",
        "icon": "🟠",
        "syria_only": True
    },

    {
        "name": "العربية",
        "url": "https://www.alarabiya.net/",
        "domain": "alarabiya.net",
        "icon": "🔴",
        "syria_only": True
    },


    # ========================
    # المصادر العالمية العربية
    # أخبار سوريا فقط
    # ========================

    {
        "name": "BBC News عربي",
        "url": "https://www.bbc.com/arabic",
        "domain": "bbc.com",
        "icon": "🌍",
        "syria_only": True
    },

    {
        "name": "DW عربية",
        "url": "https://www.dw.com/ar/",
        "domain": "dw.com",
        "icon": "🌐",
        "syria_only": True
    },

    {
        "name": "France 24 عربي",
        "url": "https://www.france24.com/ar/",
        "domain": "france24.com",
        "icon": "🇫🇷",
        "syria_only": True
    },

    {
        "name": "Euronews عربي",
        "url": "https://arabic.euronews.com/",
        "domain": "euronews.com",
        "icon": "🇪🇺",
        "syria_only": True
    },

    {
        "name": "Sky News Arabia",
        "url": "https://www.skynewsarabia.com/",
        "domain": "skynewsarabia.com",
        "icon": "🟥",
        "syria_only": True
    }
]


# =========================================================
# Headers
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.8"
}


# =========================================================
# عناوين غير مرغوبة
# =========================================================

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
    "برامج",
    "الأخبار",
    "سياسة",
    "اقتصاد",
    "رياضة",
    "ثقافة"
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
    "/tag/",
    "/authors/",
    "/author/"
]


# =========================================================
# تنظيف النص
# =========================================================

def clean_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# =========================================================
# تنظيف الرابط
# =========================================================

def clean_link(link):

    if not link:
        return ""

    return link.split("#")[0].strip()


# =========================================================
# التحقق من الدومين
# =========================================================

def same_domain(link, domain):

    try:

        hostname = urlparse(link).hostname or ""

        return (
            hostname == domain
            or hostname.endswith("." + domain)
        )

    except Exception:

        return False


# =========================================================
# هل الخبر متعلق بسوريا؟
# =========================================================

def is_syria_news(title, link=""):

    text = (
        clean_text(title)
        + " "
        + clean_text(link)
    ).lower()

    for keyword in SYRIA_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# =========================================================
# هل الرابط يشبه خبرًا؟
# =========================================================

def looks_like_article(title, link, domain):

    if not title or not link:
        return False

    title = clean_text(title)

    if len(title) < 25:
        return False

    if len(title) > 300:
        return False

    if title in BLOCKED_TITLES:
        return False

    lower_link = link.lower()

    for part in BLOCKED_URL_PARTS:

        if part in lower_link:
            return False

    if not same_domain(
        link,
        domain
    ):
        return False

    parsed = urlparse(link)

    if parsed.path in ("", "/"):
        return False

    return True


# =========================================================
# تحميل الأخبار المنشورة
# =========================================================

def load_published():

    if not os.path.exists(
        PUBLISHED_FILE
    ):
        return set()

    with open(
        PUBLISHED_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return {
            line.strip()
            for line in file
            if line.strip()
        }


# =========================================================
# حفظ الخبر
# =========================================================

def save_published(link):

    with open(
        PUBLISHED_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            link + "\n"
        )


# =========================================================
# استخراج أهم خبر
# =========================================================

def get_top_story(source):

    try:

        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "❌ فشل الاتصال:",
            source["name"]
        )

        print(e)

        return None


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    seen_titles = set()
    seen_links = set()


    for tag in soup.find_all(
        "a",
        href=True
    ):

        title = clean_text(
            tag.get_text(
                " ",
                strip=True
            )
        )


        # بعض المواقع تضع العنوان في aria-label
        if len(title) < 10:

            aria_label = tag.get(
                "aria-label",
                ""
            )

            if aria_label:
                title = clean_text(
                    aria_label
                )


        href = tag.get(
            "href",
            ""
        ).strip()


        if not href:
            continue


        link = urljoin(
            source["url"],
            href
        )

        link = clean_link(
            link
        )


        if not looks_like_article(
            title,
            link,
            source["domain"]
        ):
            continue


        # المصادر العالمية والعربية
        # يجب أن يكون الخبر متعلقاً بسوريا
        if source.get(
            "syria_only",
            False
        ):

            if not is_syria_news(
                title,
                link
            ):
                continue


        normalized_title = (
            title.lower()
        )


        if normalized_title in seen_titles:
            continue


        if link in seen_links:
            continue


        seen_titles.add(
            normalized_title
        )

        seen_links.add(
            link
        )


        return {
            "source": source["name"],
            "title": title,
            "link": link,
            "icon": source["icon"]
        }


    return None


# =========================================================
# شكل الرسالة
# =========================================================

def build_message(story):

    return f"""📰 {story["title"]}

{story["icon"]} المصدر: {story["source"]}

🔗 {story["link"]}
"""


# =========================================================
# Telegram
# =========================================================

def send_to_telegram(story):

    message = build_message(
        story
    )


    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "disable_web_page_preview": False
    }).encode(
        "utf-8"
    )


    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )


    with urllib.request.urlopen(
        url,
        data=data,
        timeout=30
    ) as response:

        result = json.loads(
            response
            .read()
            .decode("utf-8")
        )


    return result.get(
        "ok",
        False
    )


# =========================================================
# Facebook
# =========================================================

def send_to_facebook(story):

    message = build_message(
        story
    )


    url = (
        "https://graph.facebook.com/"
        f"v26.0/{FACEBOOK_PAGE_ID}/feed"
    )


    data = {
        "message": message,
        "access_token": FACEBOOK_PAGE_TOKEN
    }


    response = requests.post(
        url,
        data=data,
        timeout=30
    )


    try:

        result = response.json()

    except Exception:

        print(
            "❌ Facebook response:",
            response.text
        )

        return False


    if (
        response.ok
        and result.get("id")
    ):

        print(
            "✅ Facebook Post ID:",
            result["id"]
        )

        return True


    print(
        "❌ فشل النشر على Facebook"
    )

    print(result)

    return False


# =========================================================
# تشغيل البوت
# =========================================================

print()

print("=" * 70)

print(
    "بوت أخبار سوريا"
)

print("=" * 70)


published = load_published()

total_new = 0


for source in SOURCES:

    print()

    print(
        "🔎 فحص:",
        source["name"]
    )


    story = get_top_story(
        source
    )


    if not story:

        if source.get(
            "syria_only",
            False
        ):

            print(
                "لا يوجد خبر سوري مناسب حالياً."
            )

        else:

            print(
                "❌ لم يتم العثور على خبر."
            )

        continue


    if story["link"] in published:

        print(
            "سبق نشره:",
            story["title"]
        )

        continue


    print(
        "🆕 خبر جديد:"
    )

    print(
        story["title"]
    )


    telegram_ok = False
    facebook_ok = False


    # =========================
    # Telegram
    # =========================

    try:

        telegram_ok = send_to_telegram(
            story
        )

        if telegram_ok:

            print(
                "✅ Telegram SUCCESS"
            )

        else:

            print(
                "❌ Telegram لم يؤكد النشر"
            )


    except Exception as e:

        print(
            "❌ خطأ Telegram:"
        )

        print(e)


    time.sleep(2)


    # =========================
    # Facebook
    # =========================

    try:

        facebook_ok = send_to_facebook(
            story
        )

        if facebook_ok:

            print(
                "✅ Facebook SUCCESS"
            )


    except Exception as e:

        print(
            "❌ خطأ Facebook:"
        )

        print(e)


    # =========================
    # حفظ الخبر
    # =========================

    if telegram_ok and facebook_ok:

        save_published(
            story["link"]
        )

        published.add(
            story["link"]
        )

        total_new += 1

        print(
            "✅ تم حفظ الخبر ضمن سجل المنشورات"
        )


    else:

        print(
            "⚠️ لم يتم حفظ الخبر في سجل المنشورات"
        )

        print(
            "Telegram:",
            telegram_ok
        )

        print(
            "Facebook:",
            facebook_ok
        )


    time.sleep(2)


# =========================================================
# النتيجة النهائية
# =========================================================

print()

print("=" * 70)


if total_new == 0:

    print(
        "لا توجد أخبار جديدة "
        "تم نشرها على المنصتين."
    )

else:

    print(
        "تم نشر",
        total_new,
        "أخبار جديدة "
        "على Telegram وFacebook."
    )


print("=" * 70)