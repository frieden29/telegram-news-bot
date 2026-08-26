import os
import re
import json
import time
import html
import requests
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from deep_translator import GoogleTranslator
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv


# =========================================================
# Telegram
# =========================================================
load_dotenv()

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

MAX_PUBLISHED_RECORDS = 3000

# عدد الأخبار التي نفحصها من كل مصدر
MAX_ITEMS_PER_SOURCE = 100

# أقصى عدد أخبار ينشرها البوت في تشغيل واحد
MAX_POSTS_PER_RUN = 10

REQUEST_TIMEOUT = 30


# =========================================================
# كلمات تدل على ارتباط الخبر بسوريا
# =========================================================

SYRIA_KEYWORDS_AR = [
    "سوريا",
    "سورية",
    "سوري",
    "سوريون",
    "سوريين",
    "السوري",
    "السورية",
    "السوريون",
    "السوريين",
    "دمشق",
    "حلب",
    "إدلب",
    "ادلب",
    "حمص",
    "حماة",
    "درعا",
    "السويداء",
    "اللاذقية",
    "طرطوس",
    "دير الزور",
    "الرقة",
    "الحسكة",
    "القنيطرة",
    "الجولان",
    "بشار الأسد",
    "بشار الاسد",
    "قسد"
]

SYRIA_KEYWORDS_EN = [
    "syria",
    "syrian",
    "damascus",
    "aleppo",
    "idlib",
    "homs",
    "hama",
    "daraa",
    "sweida",
    "suwayda",
    "latakia",
    "tartus",
    "deir ez-zor",
    "deir al-zor",
    "raqqa",
    "hasakah",
    "golan",
    "bashar assad",
    "bashar al-assad",
    "sdf"
]


# =========================================================
# المصادر العربية ذات RSS مباشر
#
# الرابط الذي يصل Telegram سيكون رابط المقال الأصلي
# وليس Google News.
# =========================================================

ARABIC_RSS_SOURCES = [

    {
        "name": "BBC News عربي",
        "rss": "https://feeds.bbci.co.uk/arabic/rss.xml",
        "icon": "🌍",
        "language": "ar"
    },

    {
        "name": "Sky News Arabia",
        "rss": "https://www.skynewsarabia.com/rss",
        "icon": "🟥",
        "language": "ar"
    },

    {
        "name": "الجزيرة",
        "rss": "https://www.aljazeera.net/aljazeerarss/alarabic.xml",
        "icon": "🟠",
        "language": "ar"
    },

    {
        "name": "سانا",
        "rss": "https://sana.sy/?feed=rss2",
        "icon": "🟦",
        "language": "ar"
    },

    {
        "name": "الإخبارية السورية",
        "rss": "https://alikhbariah.com/feed/",
        "icon": "🇸🇾",
        "language": "ar"
    },

    {
        "name": "حلب اليوم",
        "rss": "https://halabtodaytv.net/feed/",
        "icon": "🟨",
        "language": "ar"
    },

    {
        "name": "تلفزيون سوريا",
        "rss": "https://www.syria.tv/rss",
        "icon": "🔵",
        "language": "ar"
    },

    {
        "name": "DW عربية",
        "rss": "https://rss.dw.com/xml/rss-ar-all",
        "icon": "🇩🇪",
        "language": "ar"
    },

    {
        "name": "France 24 عربي",
        "rss": "https://www.france24.com/ar/rss",
        "icon": "🇫🇷",
        "language": "ar"
    },

    {
        "name": "Euronews عربي",
        "rss": "https://arabic.euronews.com/rss?level=vertical&name=news",
        "icon": "🇪🇺",
        "language": "ar"
    }
]


# =========================================================
# المصادر الأجنبية ذات RSS مباشر
#
# العنوان يترجم للعربية،
# لكن رابط "مصدر الخبر" يفتح المقال الأصلي.
# =========================================================

GLOBAL_RSS_SOURCES = [

    {
        "name": "The Jerusalem Post",
        "rss": "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
        "icon": "🇮🇱",
        "language": "en"
    },

    {
        "name": "يديعوت أحرونوت - Ynet",
        "rss": "https://www.ynetnews.com/Integration/StoryRss3082.xml",
        "icon": "🇮🇱",
        "language": "en"
    },

    {
        "name": "CGTN",
        "rss": "https://www.cgtn.com/subscribe/rss/section/world.xml",
        "icon": "🇨🇳",
        "language": "en"
    },

    {
        "name": "China Daily",
        "rss": "https://www.chinadaily.com.cn/rss/world_rss.xml",
        "icon": "🇨🇳",
        "language": "en"
    },

    {
        "name": "Times of India",
        "rss": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "icon": "🇮🇳",
        "language": "en"
    },

    {
        "name": "BBC News",
        "rss": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "icon": "🇬🇧",
        "language": "en"
    },

    # سنجرب RSS المباشر أولاً.
    # إذا فشل، ينتقل البوت تلقائياً إلى Google News.
    {
        "name": "DW",
        "rss": "https://rss.dw.com/xml/rss-en-world",
        "domain": "dw.com",
        "icon": "🇩🇪",
        "language": "en",
        "google_fallback": True
    },

    {
        "name": "France 24",
        "rss": "https://www.france24.com/en/rss",
        "domain": "france24.com",
        "icon": "🇫🇷",
        "language": "en",
        "google_fallback": True
    }
]


# =========================================================
# مصادر Google News الاحتياطية
#
# هذه المصادر لم نجد لها RSS مباشر صالحاً أثناء الاختبار.
# =========================================================

GOOGLE_ONLY_SOURCES = [

    {
        "name": "العربية",
        "domain": "alarabiya.net",
        "icon": "🔴",
        "language": "ar"
    },

    {
        "name": "The Times of Israel",
        "domain": "timesofisrael.com",
        "icon": "🇮🇱",
        "language": "en"
    },

    {
        "name": "Associated Press",
        "domain": "apnews.com",
        "icon": "🇺🇸",
        "language": "en"
    },

    {
        "name": "Reuters",
        "domain": "reuters.com",
        "icon": "🌍",
        "language": "en"
    }
]


# =========================================================
# HTTP Headers
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
# كلمات عامة لا تساعد كثيراً في مقارنة الأخبار
# =========================================================

STOP_WORDS = {
    "في", "من", "إلى", "الى", "على", "عن", "مع",
    "بعد", "قبل", "بين", "هذا", "هذه", "ذلك",
    "تلك", "هو", "هي", "أن", "ان", "ما",
    "حول", "خلال", "وسط", "عبر", "قال", "قالت",
    "يقول", "جديد", "جديدة", "آخر", "اخر",

    "the", "a", "an", "of", "in", "on", "to",
    "for", "and", "with", "after", "before",
    "from", "says", "said"
}


# =========================================================
# تنظيف النص
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def clean_title(title):

    title = clean_text(title)

    prefixes = [
        r"^Read article:\s*",
        r"^Read Article:\s*",
        r"^READ ARTICLE:\s*",
        r"^اقرأ المقال:\s*",
        r"^شاهد:\s*"
    ]

    for pattern in prefixes:

        title = re.sub(
            pattern,
            "",
            title,
            flags=re.IGNORECASE
        )

    return clean_text(title)


def normalize_title(title):

    title = clean_title(title).lower()

    title = re.sub(
        r"[^\w\u0600-\u06FF\s]",
        " ",
        title
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def has_arabic(text):

    return bool(
        re.search(
            r"[\u0600-\u06FF]",
            text or ""
        )
    )


def clean_link(link):

    if not link:
        return ""

    link = clean_text(link)

    # إزالة tracking من BBC وبعض المصادر
    if "?" in link:

        base, query = link.split(
            "?",
            1
        )

        # Google News يحتاج query الخاص به أحياناً،
        # أما روابط الأخبار الأصلية فنزيل tracking منها.
        if "news.google.com" not in base:
            link = base

    return link.strip()


# =========================================================
# هل الخبر متعلق بسوريا؟
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
# الترجمة إلى العربية
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

        return clean_title(
            translated
        )

    except Exception as e:

        print(
            "⚠️ فشلت الترجمة:",
            e
        )

        return ""


# =========================================================
# قراءة التاريخ من RSS
# =========================================================

def parse_date(date_text):

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


# =========================================================
# سجل الأخبار المنشورة
# =========================================================

def load_published():

    if not os.path.exists(
        PUBLISHED_FILE
    ):
        return []

    try:

        with open(
            PUBLISHED_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(
                data,
                list
            ):
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


def remember_story(
    story,
    published
):

    published.append({
        "title": story["title"],
        "link": story["link"],
        "source": story["source"],
        "published_at": int(
            time.time()
        )
    })

    if (
        len(published)
        > MAX_PUBLISHED_RECORDS
    ):

        published[:] = published[
            -MAX_PUBLISHED_RECORDS:
        ]

    save_published(
        published
    )


# =========================================================
# منع التكرار
# =========================================================

def title_similarity(
    first,
    second
):

    first = normalize_title(
        first
    )

    second = normalize_title(
        second
    )

    if not first or not second:
        return 0

    return SequenceMatcher(
        None,
        first,
        second
    ).ratio()


def important_words(title):

    title = normalize_title(
        title
    )

    words = set()

    for word in title.split():

        if len(word) < 3:
            continue

        if word in STOP_WORDS:
            continue

        words.add(word)

    return words


def event_similarity(
    first,
    second
):

    words1 = important_words(
        first
    )

    words2 = important_words(
        second
    )

    if not words1 or not words2:
        return 0

    shared = words1.intersection(
        words2
    )

    # كلمة أو كلمتان مشتركتان لا تكفي
    if len(shared) < 3:
        return 0

    smaller = min(
        len(words1),
        len(words2)
    )

    if not smaller:
        return 0

    return (
        len(shared)
        / smaller
    )


def was_published(
    story,
    published
):

    new_link = clean_link(
        story.get(
            "link",
            ""
        )
    )

    new_title = story.get(
        "title",
        ""
    )

    for old in published:

        old_link = clean_link(
            old.get(
                "link",
                ""
            )
        )

        old_title = old.get(
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

        # عنوان شديد التشابه
        if (
            title_similarity(
                new_title,
                old_title
            )
            >= 0.86
        ):

            return True

        # نفس الحدث تقريباً
        if (
            event_similarity(
                new_title,
                old_title
            )
            >= 0.70
        ):

            return True

    return False


# =========================================================
# قراءة RSS أو Atom
# =========================================================

def extract_feed_items(
    response_content
):

    soup = BeautifulSoup(
        response_content,
        "xml"
    )

    items = soup.find_all(
        "item"
    )

    if items:
        return items

    return soup.find_all(
        "entry"
    )


# =========================================================
# قراءة رابط item
# =========================================================

def extract_item_link(item):

    link_tag = item.find(
        "link"
    )

    if not link_tag:
        return ""

    # RSS
    text_link = link_tag.get_text(
        strip=True
    )

    if text_link:
        return clean_link(
            text_link
        )

    # Atom
    href = link_tag.get(
        "href",
        ""
    )

    return clean_link(
        href
    )


# =========================================================
# الحصول على تاريخ item
# =========================================================

def extract_item_date(item):

    for name in [
        "pubDate",
        "published",
        "updated"
    ]:

        tag = item.find(name)

        if tag:

            return parse_date(
                tag.get_text(
                    strip=True
                )
            )

    return 0


# =========================================================
# استخراج مختصر الخبر من RSS
# =========================================================

def extract_item_summary(item):

    summary = ""

    for name in [
        "description",
        "summary",
        "content",
        "content:encoded"
    ]:

        tag = item.find(name)

        if tag:
            summary = tag.get_text(
                " ",
                strip=True
            )
            break

    if not summary:
        return ""

    # إزالة HTML إن وجد داخل الوصف
    summary = BeautifulSoup(
        summary,
        "html.parser"
    ).get_text(
        " ",
        strip=True
    )

    summary = clean_text(
        summary
    )

    # منع الوصف الطويل جداً
    if len(summary) > 450:

        summary = summary[:450]

        # نحاول عدم قطع آخر كلمة
        if " " in summary:
            summary = summary.rsplit(
                " ",
                1
            )[0]

        summary += "..."

    return summary


# =========================================================
# RSS مباشر
# =========================================================

def get_rss_candidates(
    source
):

    try:

        response = requests.get(
            source["rss"],
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "❌ فشل RSS:",
            source["name"]
        )

        print(e)

        return []


    items = extract_feed_items(
        response.content
    )


    print(
        "📥 إجمالي RSS:",
        len(items)
    )


    candidates = []

    seen_titles = set()
    seen_links = set()


    for item in items[
        :MAX_ITEMS_PER_SOURCE
    ]:

        title_tag = item.find(
            "title"
        )

        if not title_tag:
            continue


        original_title = clean_title(
            title_tag.get_text(
                " ",
                strip=True
            )
        )


        link = extract_item_link(
            item
        )


        if (
            not original_title
            or not link
        ):
            continue


        # مهم:
        # العنوان نفسه يجب أن يشير إلى سوريا
        if not is_syria_news(
            original_title
        ):
            continue


        normalized = normalize_title(
            original_title
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


        if source.get(
            "language"
        ) == "ar":

            arabic_title = (
                original_title
            )

        else:

            arabic_title = (
                translate_to_arabic(
                    original_title
                )
            )


        if not arabic_title:
            continue


        summary = extract_item_summary(
            item
        )

        if summary:

            if source.get(
                "language"
            ) != "ar":

                try:

                    summary = GoogleTranslator(
                        source="auto",
                        target="ar"
                    ).translate(
                        summary
                    )

                    summary = clean_text(
                        summary
                    )

                except Exception as e:

                    print(
                        "⚠️ فشلت ترجمة مختصر الخبر:",
                        e
                    )

                    summary = ""


        candidates.append({
            "title": arabic_title,
            "original_title": original_title,
            "summary": summary,
            "link": link,
            "source": source["name"],
            "icon": source["icon"],
            "timestamp": extract_item_date(
                item
            ),
            "direct_link": True
        })


    candidates.sort(
        key=lambda story: story.get(
            "timestamp",
            0
        ),
        reverse=True
    )


    print(
        "🇸🇾 أخبار سوريا المطابقة:",
        len(candidates)
    )


    return candidates


# =========================================================
# Google News
# =========================================================

def google_news_url(
    domain,
    arabic=False
):

    query = (
        '("Syria" OR "Syrian" '
        'OR "Damascus" OR "Aleppo" '
        'OR "سوريا" OR "سورية" '
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


def get_google_candidates(
    source
):

    rss_url = google_news_url(
        source["domain"],
        arabic=(
            source.get(
                "language"
            ) == "ar"
        )
    )


    try:

        response = requests.get(
            rss_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "❌ فشل Google News:",
            source["name"]
        )

        print(e)

        return []


    items = extract_feed_items(
        response.content
    )

    candidates = []

    seen_titles = set()


    for item in items[
        :MAX_ITEMS_PER_SOURCE
    ]:

        title_tag = item.find(
            "title"
        )

        if not title_tag:
            continue


        original_title = clean_title(
            title_tag.get_text(
                " ",
                strip=True
            )
        )

        link = extract_item_link(
            item
        )


        if (
            not original_title
            or not link
        ):
            continue


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


        if source.get(
            "language"
        ) == "ar":

            arabic_title = (
                original_title
            )

        else:

            arabic_title = (
                translate_to_arabic(
                    original_title
                )
            )


        if not arabic_title:
            continue


        candidates.append({
            "title": arabic_title,
            "original_title": original_title,
            "link": link,
            "source": source["name"],
            "icon": source["icon"],
            "timestamp": extract_item_date(
                item
            ),
            "direct_link": False
        })


    candidates.sort(
        key=lambda story: story.get(
            "timestamp",
            0
        ),
        reverse=True
    )


    return candidates


# =========================================================
# RSS مع fallback تلقائي
# =========================================================

def get_source_candidates(
    source
):

    candidates = []

    if source.get("rss"):

        candidates = (
            get_rss_candidates(
                source
            )
        )


    if (
        not candidates
        and source.get(
            "google_fallback"
        )
        and source.get(
            "domain"
        )
    ):

        print(
            "↪️ تجربة Google News كبديل..."
        )

        candidates = (
            get_google_candidates(
                source
            )
        )


    return candidates


# =========================================================
# اختيار أحدث خبر لم يُنشر
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
#
# المستخدم يرى فقط "مصدر الخبر"
# ولا يرى الرابط الطويل.
# =========================================================

def build_message(story):

    title = html.escape(
        clean_title(
            story["title"]
        )
    )

    source = html.escape(
        story["source"]
    )

    link = html.escape(
        story["link"],
        quote=True
    )

    summary = clean_text(
        story.get(
            "summary",
            ""
        )
    )

    if summary:

        summary = html.escape(
            summary
        )

        return f"""📰 <b>{title}</b>

📝 <b>مختصر الخبر:</b>
{summary}

{story["icon"]} المصدر: {source}

🔗 <a href="{link}">مصدر الخبر</a>"""


    return f"""📰 <b>{title}</b>

{story["icon"]} المصدر: {source}

🔗 <a href="{link}">مصدر الخبر</a>"""


def send_to_telegram(
    story
):

    message = build_message(
        story
    )


    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
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
# نشر الخبر
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


            if story.get(
                "direct_link"
            ):

                print(
                    "🔗 رابط المصدر: مباشر ✅"
                )

            else:

                print(
                    "🔗 رابط المصدر: Google News ⚠️"
                )


            # الحفظ مباشرة بعد نجاح Telegram
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
# معالجة مصدر واحد
# =========================================================

def process_source(
    source,
    candidates,
    published
):

    print(
        "📋 الأخبار السورية المرشحة:",
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
        "🔁 تم تجاوز:",
        duplicates,
        "خبر منشور أو مشابه"
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
print("=" * 75)
print("بوت أخبار سوريا - 22 مصدراً")
print("=" * 75)


published = load_published()


print(
    "📚 سجل منع التكرار:",
    len(published),
    "خبراً"
)


total_new = 0


# =========================================================
# 1. المصادر العربية RSS
# =========================================================

for source in ARABIC_RSS_SOURCES:

    if total_new >= MAX_POSTS_PER_RUN:
        break


    print()
    print("=" * 75)
    print(
        "🇸🇾/🌍 مصدر عربي:",
        source["name"]
    )
    print("=" * 75)


    candidates = (
        get_source_candidates(
            source
        )
    )


    if process_source(
        source,
        candidates,
        published
    ):

        total_new += 1


    time.sleep(1)


# =========================================================
# 2. المصادر الأجنبية RSS
# =========================================================

for source in GLOBAL_RSS_SOURCES:

    if total_new >= MAX_POSTS_PER_RUN:
        break


    print()
    print("=" * 75)
    print(
        "🌍 مصدر عالمي:",
        source["name"]
    )
    print("=" * 75)


    candidates = (
        get_source_candidates(
            source
        )
    )


    if process_source(
        source,
        candidates,
        published
    ):

        total_new += 1


    time.sleep(1)


# =========================================================
# 3. مصادر Google News الاحتياطية
# =========================================================

for source in GOOGLE_ONLY_SOURCES:

    if total_new >= MAX_POSTS_PER_RUN:
        break


    print()
    print("=" * 75)
    print(
        "🛰️ مصدر احتياطي:",
        source["name"]
    )
    print("=" * 75)


    candidates = (
        get_google_candidates(
            source
        )
    )


    if process_source(
        source,
        candidates,
        published
    ):

        total_new += 1


    time.sleep(1)


# =========================================================
# النهاية
# =========================================================

print()
print("=" * 75)

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


print("=" * 75)

