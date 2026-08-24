import os
import re
import json
import time
import html
import requests
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher
from deep_translator import GoogleTranslator


# =========================================================
# Telegram
# =========================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN غير موجود")

if not TELEGRAM_CHANNEL:
    raise ValueError("TELEGRAM_CHANNEL غير موجود")


# =========================================================
# سجل الأخبار المنشورة
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PUBLISHED_FILE = os.path.join(
    BASE_DIR,
    "published_telegram_news.json"
)


# =========================================================
# كلمات مرتبطة بسوريا
# =========================================================

SYRIA_KEYWORDS_AR = [
    "سوريا", "سورية", "سوري", "سوريين",
    "السوري", "السورية", "السوريين",
    "دمشق", "حلب", "إدلب", "حمص", "حماة",
    "درعا", "السويداء", "اللاذقية", "طرطوس",
    "دير الزور", "الرقة", "الحسكة",
    "القنيطرة", "الجولان"
]

SYRIA_KEYWORDS_EN = [
    "syria", "syrian", "damascus", "aleppo",
    "idlib", "homs", "hama", "daraa",
    "sweida", "suwayda", "latakia", "tartus",
    "deir ez-zor", "deir al-zor",
    "raqqa", "hasakah", "golan"
]


# =========================================================
# المصادر المباشرة
# =========================================================

DIRECT_SOURCES = [
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
    {
        "name": "الجزيرة",
        "url": "https://www.aljazeera.net/",
        "domain": "aljazeera.net",
        "icon": "🟠",
        "syria_only": True
    },
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
        "icon": "🇩🇪",
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
# مصادر عربية عبر Google News RSS
# لأنها أعطت 403 أو لم تُظهر خبراً مناسباً مباشرة
# =========================================================

RSS_ARABIC_SOURCES = [
    {
        "name": "العربية",
        "domain": "alarabiya.net",
        "icon": "🔴"
    },
    {
        "name": "France 24 عربي",
        "domain": "france24.com",
        "icon": "🇫🇷"
    },
    {
        "name": "Euronews عربي",
        "domain": "arabic.euronews.com",
        "icon": "🇪🇺"
    }
]


# =========================================================
# 11 مصادر عالمية
# =========================================================

GLOBAL_SOURCES = [
    {
        "name": "The Times of Israel",
        "domain": "timesofisrael.com",
        "icon": "🇮🇱"
    },
    {
        "name": "The Jerusalem Post",
        "domain": "jpost.com",
        "icon": "🇮🇱"
    },
    {
        "name": "يديعوت أحرونوت - Ynet",
        "domain": "ynetnews.com",
        "icon": "🇮🇱"
    },
    {
        "name": "CGTN",
        "domain": "cgtn.com",
        "icon": "🇨🇳"
    },
    {
        "name": "China Daily",
        "domain": "chinadaily.com.cn",
        "icon": "🇨🇳"
    },
    {
        "name": "Times of India",
        "domain": "timesofindia.indiatimes.com",
        "icon": "🇮🇳"
    },
    {
        "name": "DW",
        "domain": "dw.com",
        "icon": "🇩🇪"
    },
    {
        "name": "France 24",
        "domain": "france24.com",
        "icon": "🇫🇷"
    },
    {
        "name": "BBC News",
        "domain": "bbc.com",
        "icon": "🇬🇧"
    },
    {
        "name": "Associated Press",
        "domain": "apnews.com",
        "icon": "🇺🇸"
    },
    {
        "name": "Reuters",
        "domain": "reuters.com",
        "icon": "🌍"
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
# استبعاد العناصر غير الإخبارية
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
    "تجاوز إلى المحتوى الرئيسي"
]

BLOCKED_URL_PARTS = [
    "/live",
    "/privacy",
    "/about",
    "/contact",
    "/login",
    "/search",
    "/author/",
    "/authors/"
]


# =========================================================
# أدوات النص
# =========================================================

def clean_text(text):
    if not text:
        return ""

    text = html.unescape(text)

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def normalize_title(text):
    text = clean_text(text).lower()

    text = re.sub(
        r"[^\w\u0600-\u06FF\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def clean_link(link):
    if not link:
        return ""

    return link.split("#")[0].strip()


def has_arabic(text):
    return bool(
        re.search(
            r"[\u0600-\u06FF]",
            text or ""
        )
    )


# =========================================================
# هل الخبر متعلق بسوريا؟
# =========================================================

def is_syria_news(text):
    text = clean_text(text).lower()

    for keyword in SYRIA_KEYWORDS_AR:
        if keyword.lower() in text:
            return True

    for keyword in SYRIA_KEYWORDS_EN:
        if keyword.lower() in text:
            return True

    return False


# =========================================================
# ترجمة للعربية
# =========================================================

def translate_to_arabic(title):
    title = clean_text(title)

    if not title:
        return ""

    if has_arabic(title):
        return title

    try:
        translated = GoogleTranslator(
            source="auto",
            target="ar"
        ).translate(title)

        return clean_text(translated)

    except Exception as e:
        print("⚠️ فشلت الترجمة:", e)
        return ""


# =========================================================
# سجل الأخبار
# =========================================================

def load_published():
    if not os.path.exists(PUBLISHED_FILE):
        return []

    try:
        with open(
            PUBLISHED_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

            if isinstance(data, list):
                return data

    except Exception as e:
        print(
            "⚠️ تعذر قراءة سجل الأخبار:",
            e
        )

    return []


def save_published(records):
    with open(
        PUBLISHED_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# منع التكرار
# =========================================================

def title_similarity(title1, title2):
    first = normalize_title(title1)
    second = normalize_title(title2)

    if not first or not second:
        return 0

    return SequenceMatcher(
        None,
        first,
        second
    ).ratio()


def was_published(story, records):
    new_link = clean_link(
        story.get("link", "")
    )

    new_title = story.get(
        "title",
        ""
    )

    for record in records:
        old_link = clean_link(
            record.get("link", "")
        )

        old_title = record.get(
            "title",
            ""
        )

        # نفس الرابط
        if (
            new_link
            and old_link
            and new_link == old_link
        ):
            return True

        # نفس الخبر تقريباً
        similarity = title_similarity(
            new_title,
            old_title
        )

        if similarity >= 0.82:
            print(
                "🔁 خبر مشابه منشور سابقاً:",
                old_title
            )
            return True

    return False


def remember_story(story, records):
    records.append({
        "title": story["title"],
        "link": story["link"],
        "source": story["source"],
        "published_at": int(time.time())
    })

    if len(records) > 1500:
        records[:] = records[-1500:]

    save_published(records)


# =========================================================
# التحقق من الرابط
# =========================================================

def same_domain(link, domain):
    try:
        hostname = (
            urlparse(link).hostname
            or ""
        )

        return (
            hostname == domain
            or hostname.endswith(
                "." + domain
            )
        )

    except Exception:
        return False


def looks_like_article(
    title,
    link,
    domain
):
    title = clean_text(title)

    if not title or not link:
        return False

    if len(title) < 25:
        return False

    if len(title) > 320:
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
# استخراج خبر مباشر
# =========================================================

def get_direct_story(source):
    try:
        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=25
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

        if len(title) < 10:
            title = clean_text(
                tag.get(
                    "aria-label",
                    ""
                )
            )

        href = tag.get(
            "href",
            ""
        ).strip()

        if not href:
            continue

        link = clean_link(
            urljoin(
                source["url"],
                href
            )
        )

        if not looks_like_article(
            title,
            link,
            source["domain"]
        ):
            continue

        if source.get(
            "syria_only",
            False
        ):
            if not is_syria_news(
                title + " " + link
            ):
                continue

        normalized = normalize_title(
            title
        )

        if normalized in seen_titles:
            continue

        if link in seen_links:
            continue

        seen_titles.add(
            normalized
        )
        seen_links.add(
            link
        )

        return {
            "title": title,
            "link": link,
            "source": source["name"],
            "icon": source["icon"]
        }

    return None


# =========================================================
# Google News RSS
# =========================================================

def google_news_rss_url(
    domain,
    arabic=False
):
    query = (
        "(Syria OR Syrian OR Damascus OR Aleppo "
        "OR سوريا OR سورية OR سوري OR دمشق) "
        f"site:{domain}"
    )

    encoded_query = urllib.parse.quote(
        query
    )

    if arabic:
        return (
            "https://news.google.com/rss/search"
            f"?q={encoded_query}"
            "&hl=ar"
            "&gl=AE"
            "&ceid=AE:ar"
        )

    return (
        "https://news.google.com/rss/search"
        f"?q={encoded_query}"
        "&hl=en-US"
        "&gl=US"
        "&ceid=US:en"
    )


# =========================================================
# استخراج خبر عبر RSS
# =========================================================

def get_rss_story(
    source,
    arabic=False
):
    rss_url = google_news_rss_url(
        source["domain"],
        arabic=arabic
    )

    try:
        response = requests.get(
            rss_url,
            headers=HEADERS,
            timeout=25
        )

        response.raise_for_status()

    except Exception as e:
        print(
            "❌ فشل RSS:",
            source["name"]
        )
        print(e)
        return None


    soup = BeautifulSoup(
        response.content,
        "xml"
    )

    items = soup.find_all("item")


    for item in items[:20]:
        title_tag = item.find("title")
        link_tag = item.find("link")

        if not title_tag or not link_tag:
            continue

        original_title = clean_text(
            title_tag.get_text()
        )

        link = clean_link(
            link_tag.get_text()
        )

        original_title = re.sub(
            r"\s+-\s+[^-]+$",
            "",
            original_title
        ).strip()

        if not is_syria_news(
            original_title
        ):
            continue

        title = translate_to_arabic(
            original_title
        )

        if not title:
            continue

        return {
            "title": title,
            "original_title": original_title,
            "link": link,
            "source": source["name"],
            "icon": source["icon"]
        }

    return None


# =========================================================
# Telegram
# =========================================================

def build_message(story):
    return f"""📰 {story["title"]}

{story["icon"]} المصدر: {story["source"]}

🔗 {story["link"]}
"""


def send_to_telegram(story):
    message = build_message(
        story
    )

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "disable_web_page_preview": False
    }).encode("utf-8")

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
# نشر خبر واحد مع منع التكرار
# =========================================================

def publish_story(
    story,
    published
):
    if not story:
        return False

    if was_published(
        story,
        published
    ):
        print(
            "⏭️ لن يتم إعادة نشره."
        )
        return False

    print(
        "🆕 خبر جديد:"
    )
    print(
        story["title"]
    )

    try:
        if send_to_telegram(
            story
        ):
            print(
                "✅ تم النشر على Telegram"
            )

            remember_story(
                story,
                published
            )

            return True

        print(
            "❌ Telegram لم يؤكد النشر"
        )

    except Exception as e:
        print(
            "❌ خطأ Telegram:",
            e
        )

    return False


# =========================================================
# التشغيل
# =========================================================

print()
print("=" * 70)
print("بوت أخبار سوريا - 22 مصدراً")
print("=" * 70)

published = load_published()
total_new = 0


# المصادر المباشرة
for source in DIRECT_SOURCES:
    print()
    print(
        "🔎 فحص مباشر:",
        source["name"]
    )

    story = get_direct_story(
        source
    )

    if not story:
        print(
            "لا يوجد خبر مناسب حالياً."
        )
        continue

    if publish_story(
        story,
        published
    ):
        total_new += 1

    time.sleep(2)


# المصادر العربية عبر RSS
for source in RSS_ARABIC_SOURCES:
    print()
    print(
        "📰 فحص RSS عربي:",
        source["name"]
    )

    story = get_rss_story(
        source,
        arabic=True
    )

    if not story:
        print(
            "لا يوجد خبر سوري مناسب حالياً."
        )
        continue

    if publish_story(
        story,
        published
    ):
        total_new += 1

    time.sleep(2)


# المصادر العالمية
for source in GLOBAL_SOURCES:
    print()
    print(
        "🌍 فحص عالمي:",
        source["name"]
    )

    story = get_rss_story(
        source,
        arabic=False
    )

    if not story:
        print(
            "لا يوجد خبر سوري مناسب حالياً."
        )
        continue

    if publish_story(
        story,
        published
    ):
        total_new += 1

    time.sleep(2)


print()
print("=" * 70)

if total_new == 0:
    print(
        "لا توجد أخبار سورية جديدة للنشر."
    )
else:
    print(
        "تم نشر",
        total_new,
        "أخبار سورية جديدة."
    )

print("=" * 70)
