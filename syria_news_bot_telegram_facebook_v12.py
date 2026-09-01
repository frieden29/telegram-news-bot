# -*- coding: utf-8 -*-
'''
بوت أخبار سوريا - Telegram + Facebook + تطبيق نبض سوريا - v12

هذه النسخة مبنية فوق v10 الموجود في نفس المجلد، وتضيف:
1) news.json للتطبيق.
2) التاريخ والوقت الحقيقيين للخبر.
3) استخراج صورة الخبر من RSS عند توفرها.
4) محاولة استخراج og:image / twitter:image من صفحة المصدر.
5) حفظ image + timestamp + time في news.json.
6) استمرار Telegram وFacebook حتى إذا فشل استخراج الصورة.

يجب أن يبقى الملف التالي بجانب هذا الملف:
    syria_news_bot_telegram_facebook_v10.py
'''

from pathlib import Path


BASE_DIR_V12 = Path(__file__).resolve().parent
V10_FILE = BASE_DIR_V12 / "syria_news_bot_telegram_facebook_v10.py"

if not V10_FILE.exists():
    raise FileNotFoundError(
        "لم يتم العثور على syria_news_bot_telegram_facebook_v10.py "
        "بجانب ملف v12."
    )

source = V10_FILE.read_text(encoding="utf-8")


# =========================================================
# 1) إضافة timedelta لاستخدام توقيت سوريا UTC+3
# =========================================================

old_datetime_import = "from datetime import datetime, timezone"
new_datetime_import = "from datetime import datetime, timezone, timedelta"

if old_datetime_import not in source:
    raise RuntimeError(
        "تعذر العثور على سطر استيراد datetime داخل v10."
    )

source = source.replace(
    old_datetime_import,
    new_datetime_import,
    1
)


# =========================================================
# 2) إضافة إعدادات news.json
# =========================================================

old_settings = '''PUBLISHED_FILE = os.path.join(
    BASE_DIR,
    "published_telegram_news.json"
)

MAX_PUBLISHED_RECORDS = 3000'''

new_settings = '''PUBLISHED_FILE = os.path.join(
    BASE_DIR,
    "published_telegram_news.json"
)

# ملف الأخبار الذي يقرأه تطبيق نبض سوريا
NEWS_FILE = os.path.join(
    BASE_DIR,
    "news.json"
)

# أقصى عدد أخبار نحتفظ به داخل التطبيق
MAX_APP_NEWS = 100

MAX_PUBLISHED_RECORDS = 3000'''

if old_settings not in source:
    raise RuntimeError(
        "تعذر العثور على قسم PUBLISHED_FILE داخل v10. "
        "ربما تم تعديل ملف v10."
    )

source = source.replace(
    old_settings,
    new_settings,
    1
)


# =========================================================
# 3) إضافة أدوات الصورة + التاريخ + news.json
# =========================================================

marker_before_remember = '''def remember_story(
    story,
    published
):'''

v12_functions = r'''
# =========================================================
# أدوات v12: الصور + التاريخ والوقت + تطبيق نبض سوريا
# =========================================================

def normalize_image_url(
    image_url,
    base_url=""
):

    image_url = clean_text(
        image_url
    )

    if not image_url:
        return ""

    if image_url.startswith("//"):
        image_url = "https:" + image_url

    elif base_url:
        image_url = urllib.parse.urljoin(
            base_url,
            image_url
        )

    if not image_url.startswith(
        ("http://", "https://")
    ):
        return ""

    return image_url.strip()


def extract_item_image(
    item,
    article_link=""
):

    for tag in item.find_all(True):

        tag_name = str(
            tag.name or ""
        ).lower()

        image_url = tag.get(
            "url",
            ""
        )

        media_type = clean_text(
            tag.get(
                "type",
                ""
            )
        ).lower()

        medium = clean_text(
            tag.get(
                "medium",
                ""
            )
        ).lower()

        is_image_tag = (
            tag_name in {
                "thumbnail",
                "media:thumbnail",
                "enclosure"
            }
            or medium == "image"
            or media_type.startswith("image/")
        )

        if image_url and is_image_tag:

            image_url = normalize_image_url(
                image_url,
                article_link
            )

            if image_url:
                return image_url


    for name in [
        "description",
        "summary",
        "content",
        "content:encoded",
        "encoded"
    ]:

        tag = item.find(name)

        if not tag:
            continue

        try:
            raw_html = tag.decode_contents()
        except Exception:
            raw_html = str(tag)

        html_soup = BeautifulSoup(
            raw_html,
            "html.parser"
        )

        img = html_soup.find(
            "img"
        )

        if not img:
            continue

        possible_src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
            or img.get("data-original")
            or ""
        )

        image_url = normalize_image_url(
            possible_src,
            article_link
        )

        if image_url:
            return image_url


    return ""


def extract_page_image(
    page_url
):

    page_url = clean_link(
        page_url
    )

    if not page_url:
        return ""

    if "news.google.com" in page_url:
        return ""

    try:

        response = requests.get(
            page_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        checks = [
            (
                "meta",
                {"property": "og:image"},
                "content"
            ),
            (
                "meta",
                {"property": "og:image:url"},
                "content"
            ),
            (
                "meta",
                {"name": "twitter:image"},
                "content"
            ),
            (
                "meta",
                {"name": "twitter:image:src"},
                "content"
            ),
            (
                "link",
                {"rel": "image_src"},
                "href"
            )
        ]

        for (
            tag_name,
            attrs,
            value_attribute
        ) in checks:

            tag = soup.find(
                tag_name,
                attrs=attrs
            )

            if not tag:
                continue

            image_url = normalize_image_url(
                tag.get(
                    value_attribute,
                    ""
                ),
                response.url
            )

            if image_url:
                return image_url


    except Exception as e:

        print(
            "⚠️ تعذر استخراج صورة صفحة الخبر:",
            e
        )


    return ""


def format_story_time(
    timestamp
):

    if not timestamp:
        return ""

    try:

        timestamp = int(
            timestamp
        )

        syria_timezone = timezone(
            timedelta(hours=3)
        )

        dt = datetime.fromtimestamp(
            timestamp,
            timezone.utc
        ).astimezone(
            syria_timezone
        )

        return dt.strftime(
            "%d/%m/%Y - %H:%M"
        )

    except Exception:

        return ""


def save_story_for_app(
    story
):

    app_news = []

    if os.path.exists(
        NEWS_FILE
    ):

        try:

            with open(
                NEWS_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

                if isinstance(
                    data,
                    list
                ):
                    app_news = data

        except Exception as e:

            print(
                "⚠️ تعذر قراءة news.json:",
                e
            )


    title = clean_title(
        story.get(
            "title",
            ""
        )
    )

    description = clean_text(
        story.get(
            "summary",
            ""
        )
    )

    source_name = clean_text(
        story.get(
            "source",
            ""
        )
    )

    link = clean_link(
        story.get(
            "link",
            ""
        )
    )

    timestamp = story.get(
        "timestamp",
        0
    )

    try:
        timestamp = int(
            timestamp or 0
        )
    except Exception:
        timestamp = 0


    image = normalize_image_url(
        story.get(
            "image",
            ""
        ),
        link
    )

    if not image:

        image = extract_page_image(
            link
        )


   
    published_at = int(time.time())

new_item = {
    "title": title,
    "description": description,
    "source": source_name,
    "category": "سوريا",

    # وقت الخبر كما يرسله المصدر
    "timestamp": timestamp,

    # وقت دخول الخبر فعلياً إلى نبض سوريا
    "published_at": published_at,

    "time": format_story_time(published_at),

    "image": image,
    "url": link
}


    app_news = [
        item
        for item in app_news
        if (
            isinstance(
                item,
                dict
            )
            and item.get(
                "url"
            ) != "https://example.com"
        )
    ]


    filtered_news = []

    for item in app_news:

        if not isinstance(
            item,
            dict
        ):
            continue

        old_url = clean_link(
            item.get(
                "url",
                ""
            )
        )

        old_title = clean_title(
            item.get(
                "title",
                ""
            )
        )

        if (
            link
            and old_url
            and link == old_url
        ):
            continue

        if (
            title
            and old_title
            and normalize_title(
                title
            )
            == normalize_title(
                old_title
            )
        ):
            continue

        filtered_news.append(
            item
        )


    filtered_news.insert(
        0,
        new_item
    )

    filtered_news = filtered_news[
        :MAX_APP_NEWS
    ]


    try:

        with open(
            NEWS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                filtered_news,
                file,
                ensure_ascii=False,
                indent=2
            )

        print(
            "📱 تم تحديث news.json للتطبيق"
        )

        if new_item["time"]:
            print(
                "🕒 وقت الخبر:",
                new_item["time"]
            )
        else:
            print(
                "🕒 المصدر لم يرسل تاريخاً صالحاً لهذا الخبر"
            )

        if image:
            print(
                "🖼️ تم حفظ صورة الخبر للتطبيق"
            )
        else:
            print(
                "🖼️ لم تتوفر صورة مناسبة لهذا الخبر"
            )


    except Exception as e:

        print(
            "⚠️ تعذر تحديث news.json للتطبيق:",
            e
        )


'''

if marker_before_remember not in source:
    raise RuntimeError(
        "تعذر العثور على الدالة remember_story داخل v10."
    )

source = source.replace(
    marker_before_remember,
    v12_functions + marker_before_remember,
    1
)


# =========================================================
# 4) حفظ صورة RSS داخل مرشحي المصادر المباشرة
# =========================================================

old_rss_candidate = '''            "summary": summary,
            "link": link,
            "source": source["name"],'''

new_rss_candidate = '''            "summary": summary,
            "link": link,
            "image": extract_item_image(
                item,
                link
            ),
            "source": source["name"],'''

if old_rss_candidate not in source:
    raise RuntimeError(
        "تعذر العثور على بيانات مرشح RSS داخل v10."
    )

source = source.replace(
    old_rss_candidate,
    new_rss_candidate,
    1
)


# =========================================================
# 5) حفظ صورة RSS داخل مرشحي Google News إن توفرت
# =========================================================

old_google_candidate = '''            "summary": "",
            "link": link,
            "source": source["name"],'''

new_google_candidate = '''            "summary": "",
            "link": link,
            "image": extract_item_image(
                item,
                link
            ),
            "source": source["name"],'''

if old_google_candidate not in source:
    raise RuntimeError(
        "تعذر العثور على بيانات مرشح Google News داخل v10."
    )

source = source.replace(
    old_google_candidate,
    new_google_candidate,
    1
)


# =========================================================
# 6) بعد فك رابط Google News نحاول صورة المصدر الأصلي
# =========================================================

old_google_resolve = '''        story["link"] = resolved_link
        story["direct_link"] = direct_link

        if direct_link:'''

new_google_resolve = '''        story["link"] = resolved_link
        story["direct_link"] = direct_link

        if (
            direct_link
            and not story.get(
                "image"
            )
        ):

            story["image"] = extract_page_image(
                resolved_link
            )

        if direct_link:'''

if old_google_resolve not in source:
    raise RuntimeError(
        "تعذر العثور على موضع فك رابط Google News داخل v10."
    )

source = source.replace(
    old_google_resolve,
    new_google_resolve,
    1
)


# =========================================================
# 7) تحديث news.json بعد نجاح النشر
# =========================================================

old_publish_success = '''        remember_story(
            story,
            published
        )

        return True'''

new_publish_success = '''        remember_story(
            story,
            published
        )

        try:

            save_story_for_app(
                story
            )

        except Exception as e:

            print(
                "⚠️ خطأ غير متوقع أثناء تحديث التطبيق:",
                e
            )

        return True'''

if old_publish_success not in source:
    raise RuntimeError(
        "تعذر العثور على موضع remember_story داخل publish_story في v10."
    )

source = source.replace(
    old_publish_success,
    new_publish_success,
    1
)


# =========================================================
# 8) تغيير اسم الإصدار الظاهر في السجل
# =========================================================

source = source.replace(
    "بوت أخبار سوريا - Telegram + Facebook - v10",
    "بوت أخبار سوريا - Telegram + Facebook + App - v12",
    1
)


# =========================================================
# 9) فحص ثم تشغيل نسخة v10 بعد تطبيق تعديلات v12
# =========================================================

compiled = compile(
    source,
    str(V10_FILE),
    "exec"
)

exec(
    compiled,
    globals(),
    globals()
)
