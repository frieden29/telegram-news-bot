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
from email.utils import parsedate_to_datetime


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
# إعدادات عامة
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PUBLISHED_FILE = os.path.join(
    BASE_DIR,
    "published_telegram_news.json"
)

MAX_PUBLISHED_RECORDS = 2500
MAX_CANDIDATES_PER_SOURCE = 20
MAX_POSTS_PER_RUN = 10


# =========================================================
# كلمات مرتبطة بسوريا
# =========================================================

SYRIA_KEYWORDS_AR = [
    "سوريا", "سورية", "سوري", "سوريون", "سوريين",
    "السوري", "السورية", "السوريون", "السوريين",
    "دمشق", "حلب", "إدلب", "ادلب", "حمص", "حماة",
    "درعا", "السويداء", "اللاذقية", "طرطوس",
    "دير الزور", "الرقة", "الحسكة", "القنيطرة",
    "الجولان", "بشار الأسد", "بشار الاسد", "قسد"
]

SYRIA_KEYWORDS_EN = [
    "syria", "syrian", "damascus", "aleppo",
    "idlib", "homs", "hama", "daraa",
    "sweida", "suwayda", "latakia", "tartus",
    "deir ez-zor", "deir al-zor", "raqqa",
    "hasakah", "golan", "bashar assad",
    "bashar al-assad", "sdf"
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
# المصادر العربية عبر RSS
# =========================================================

RSS_ARABIC_SOURCES = [
    {
        "name": "الإخبارية السورية",
        "domain": "alikhbariah.com",
        "icon": "🇸🇾"
    },
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
# المصادر العالمية
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
# HTTP
# =========================================================

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
    "/authors/",
    "/tag/"
]


STOP_WORDS = {
    "في", "من", "إلى", "الى", "على", "عن", "مع",
    "بعد", "قبل", "بين", "هذا", "هذه", "ذلك",
    "تلك", "هو", "هي", "أن", "ان", "ما",
    "حول", "خلال", "وسط", "عبر", "قال", "قالت",
    "يقول", "جديد", "جديدة", "آخر", "اخر",
    "the", "a", "an", "of", "in", "on",
    "to", "for", "and", "with", "after",
    "before", "from", "says", "said"
}


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


def clean_title(text):
    text = clean_text(text)

    prefixes = [
        r"^Read article:\s*",
        r"^Read Article:\s*",
        r"^READ ARTICLE:\s*",
        r"^اقرأ المقال:\s*",
        r"^شاهد:\s*"
    ]

    for pattern in prefixes:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    return clean_text(text)


def normalize_title(text):
    text = clean_title(text).lower()

    text = re.sub(
        r"[^\w\u0600-\u06FF\s]",
        " ",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


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
# فلتر سوريا
# =========================================================

def is_syria_news(text):
    text = clean_text(text).lower()

    if not text:
        return False

    for keyword in SYRIA_KEYWORDS_AR:
        if keyword.lower() in text:
            return True

    for keyword in SYRIA_KEYWORDS_EN:
        pattern = (
            r"(?<![a-z])"
            + re.escape(keyword.lower())
            + r"(?![a-z])"
        )

        if re.search(pattern, text):
            return True

    return False


# =========================================================
# الترجمة
# =========================================================

def translate_to_arabic(title):
    title = clean_title(title)

    if not title:
        return ""

    if has_arabic(title):
        return title

    try:
        translated = GoogleTranslator(
            source="auto",
            target="ar"
        ).translate(title)

        return clean_title(translated)

    except Exception as e:
        print(
            "⚠️ فشلت الترجمة:",
            e
        )

        return ""


# =========================================================
# سجل المنشورات
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


def remember_story(story, records):
    records.append({
        "title": story["title"],
        "link": story["link"],
        "source": story["source"],
        "published_at": int(time.time())
    })

    if len(records) > MAX_PUBLISHED_RECORDS:
        records[:] = records[
            -MAX_PUBLISHED_RECORDS:
        ]

    save_published(records)


# =========================================================
# مقارنة الأخبار
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


def important_words(title):
    title = normalize_title(title)

    words = set()

    for word in title.split():
        if len(word) < 3:
            continue

        if word in STOP_WORDS:
            continue

        words.add(word)

    return words


def event_similarity(title1, title2):
    first = important_words(title1)
    second = important_words(title2)

    if not first or not second:
        return 0

    shared = first.intersection(second)

    if len(shared) < 3:
        return 0

    smaller = min(
        len(first),
        len(second)
    )

    if smaller == 0:
        return 0

    return len(shared) / smaller


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

        if (
            new_link
            and old_link
            and new_link == old_link
        ):
            return True

        if title_similarity(
            new_title,
            old_title
        ) >= 0.84:
            return True

        if event_similarity(
            new_title,
            old_title
        ) >= 0.65:
            return True

    return False


# =========================================================
# المصادر المباشرة
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
    title = clean_title(title)

    if not title or not link:
        return False

    if len(title) < 25:
        return False

    if len(title) > 350:
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


def get_direct_candidates(source):
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

        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    candidates = []
    seen_titles = set()
    seen_links = set()

    for tag in soup.find_all(
        "a",
        href=True
    ):
        title = clean_title(
            tag.get_text(
                " ",
                strip=True
            )
        )

        if len(title) < 10:
            title = clean_title(
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
                title
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

        candidates.append({
            "title": title,
            "link": link,
            "source": source["name"],
            "icon": source["icon"],
            "timestamp": 0
        })

        if (
            len(candidates)
            >= MAX_CANDIDATES_PER_SOURCE
        ):
            break

    return candidates


# =========================================================
# Google News RSS
# =========================================================

def google_news_rss_url(
    domain,
    arabic=False
):
    query = (
        '("Syria" OR "Syrian" OR "Damascus" '
        'OR "Aleppo" OR "سوريا" OR "سورية" '
        'OR "دمشق" OR "حلب") '
        f"site:{domain}"
    )

    encoded = urllib.parse.quote(
        query
    )

    if arabic:
        return (
            "https://news.google.com/rss/search"
            f"?q={encoded}"
            "&hl=ar"
            "&gl=AE"
            "&ceid=AE:ar"
        )

    return (
        "https://news.google.com/rss/search"
        f"?q={encoded}"
        "&hl=en-US"
        "&gl=US"
        "&ceid=US:en"
    )


def parse_rss_date(date_text):
    if not date_text:
        return 0

    try:
        dt = parsedate_to_datetime(
            date_text
        )

        return int(
            dt.timestamp()
        )

    except Exception:
        return 0


def get_rss_candidates(
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

        return []

    soup = BeautifulSoup(
        response.content,
        "xml"
    )

    candidates = []
    seen_titles = set()

    for item in soup.find_all(
        "item"
    )[:MAX_CANDIDATES_PER_SOURCE]:

        title_tag = item.find("title")
        link_tag = item.find("link")
        date_tag = item.find("pubDate")

        if not title_tag or not link_tag:
            continue

        original_title = clean_title(
            title_tag.get_text()
        )

        link = clean_link(
            link_tag.get_text()
        )

        if not is_syria_news(
            original_title
        ):
            continue

        normalized = normalize_title(
            original_title
        )

        if normalized in seen_titles:
            continue

        seen_titles.add(
            normalized
        )

        title = translate_to_arabic(
            original_title
        )

        if not title:
            continue

        timestamp = 0

        if date_tag:
            timestamp = parse_rss_date(
                date_tag.get_text()
            )

        candidates.append({
            "title": title,
            "original_title": original_title,
            "link": link,
            "source": source["name"],
            "icon": source["icon"],
            "timestamp": timestamp
        })

    candidates.sort(
        key=lambda item: item.get(
            "timestamp",
            0
        ),
        reverse=True
    )

    return candidates


# =========================================================
# اختيار أحدث خبر غير منشور
# =========================================================

def choose_new_story(
    candidates,
    published
):
    duplicate_count = 0

    for story in candidates:
        if was_published(
            story,
            published
        ):
            duplicate_count += 1
            continue

        return (
            story,
            duplicate_count
        )

    return (
        None,
        duplicate_count
    )


# =========================================================
# Telegram
# الرابط يظهر فقط باسم "مصدر الخبر"
# =========================================================

def build_message(story):
    title = html.escape(
        clean_title(story["title"])
    )

    source = html.escape(
        story["source"]
    )

    link = html.escape(
        story["link"],
        quote=True
    )

    return f"""📰 {title}

{story["icon"]} المصدر: {source}

🔗 <a href="{link}">مصدر الخبر</a>"""


def send_to_telegram(story):
    message = build_message(
        story
    )

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
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
# النشر
# =========================================================

def publish_story(
    story,
    published
):
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
            "❌ خطأ Telegram:"
        )

        print(e)

    return False


# =========================================================
# تقرير المصدر
# =========================================================

def process_source(
    source,
    candidates,
    published
):
    print(
        "📥 نتائج صالحة:",
        len(candidates)
    )

    if not candidates:
        print(
            "لا يوجد خبر سوري مناسب حالياً."
        )

        return False

    story, duplicates = choose_new_story(
        candidates,
        published
    )

    print(
        "🔁 منشورة سابقاً أو متشابهة:",
        duplicates
    )

    if not story:
        print(
            "⏭️ لا يوجد خبر جديد في هذا المصدر."
        )

        return False

    print(
        "🆕 أحدث خبر جديد:"
    )

    print(
        story["title"]
    )

    return publish_story(
        story,
        published
    )


# =========================================================
# التشغيل
# =========================================================

print()
print("=" * 70)
print("بوت أخبار سوريا - 22 مصدراً")
print("=" * 70)

published = load_published()

print(
    "📚 سجل منع التكرار يحتوي على:",
    len(published),
    "خبراً"
)

total_new = 0


# المصادر المباشرة
for source in DIRECT_SOURCES:

    if total_new >= MAX_POSTS_PER_RUN:
        break

    print()
    print(
        "🔎 فحص مباشر:",
        source["name"]
    )

    candidates = get_direct_candidates(
        source
    )

    if process_source(
        source,
        candidates,
        published
    ):
        total_new += 1

    time.sleep(1)


# RSS العربي
for source in RSS_ARABIC_SOURCES:

    if total_new >= MAX_POSTS_PER_RUN:
        break

    print()
    print(
        "📰 فحص RSS عربي:",
        source["name"]
    )

    candidates = get_rss_candidates(
        source,
        arabic=True
    )

    if process_source(
        source,
        candidates,
        published
    ):
        total_new += 1

    time.sleep(1)


# المصادر العالمية
for source in GLOBAL_SOURCES:

    if total_new >= MAX_POSTS_PER_RUN:
        break

    print()
    print(
        "🌍 فحص عالمي:",
        source["name"]
    )

    candidates = get_rss_candidates(
        source,
        arabic=False
    )

    if process_source(
        source,
        candidates,
        published
    ):
        total_new += 1

    time.sleep(1)


# النهاية
print()
print("=" * 70)

print(
    "📚 حجم سجل منع التكرار الآن:",
    len(published)
)

if total_new == 0:
    print(
        "لا توجد أخبار سورية جديدة للنشر."
    )

else:
    print(
        "✅ تم نشر",
        total_new,
        "أخبار سورية جديدة."
    )

print("=" * 70)
