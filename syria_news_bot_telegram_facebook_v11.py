# -*- coding: utf-8 -*-
'''
بوت أخبار سوريا - Telegram + Facebook + تطبيق أخبار سوريا - v11

هذه النسخة مبنية بأمان فوق ملف v10 الموجود في نفس المجلد.
تقوم بتحميل كود v10، وإضافة دعم news.json للتطبيق، ثم تشغيله.

المطلوب أن يبقى الملف التالي بجانب هذا الملف:
    syria_news_bot_telegram_facebook_v10.py
'''

from pathlib import Path


BASE_DIR_V11 = Path(__file__).resolve().parent
V10_FILE = BASE_DIR_V11 / "syria_news_bot_telegram_facebook_v10.py"

if not V10_FILE.exists():
    raise FileNotFoundError(
        "لم يتم العثور على syria_news_bot_telegram_facebook_v10.py "
        "بجانب ملف v11."
    )

source = V10_FILE.read_text(encoding="utf-8")


# =========================================================
# 1) إضافة ملف الأخبار الخاص بتطبيق Android
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

# ملف الأخبار الذي يقرأه تطبيق أخبار سوريا
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
# 2) إضافة دالة حفظ الخبر داخل news.json
# =========================================================

marker_before_remember = '''def remember_story(
    story,
    published
):'''

save_app_function = r'''
# =========================================================
# ملف الأخبار الخاص بتطبيق أخبار سوريا
# =========================================================

def save_story_for_app(story):

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


    new_item = {
        "title": title,
        "description": description,
        "source": source_name,
        "category": "سوريا",
        "time": "الآن",
        "url": link
    }


    # إزالة العنصر التجريبي الذي أنشأناه أول مرة للتطبيق.
    app_news = [
        item
        for item in app_news
        if (
            isinstance(item, dict)
            and item.get("url") != "https://example.com"
        )
    ]


    # منع أي تكرار احتياطي داخل news.json حسب الرابط أو العنوان.
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
            and normalize_title(title)
            == normalize_title(old_title)
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

    except Exception as e:

        # فشل ملف التطبيق لا يجب أن يلغي نجاح النشر
        # على Telegram أو Facebook.
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
    save_app_function + marker_before_remember,
    1
)


# =========================================================
# 3) تحديث news.json بعد نجاح النشر على منصة واحدة على الأقل
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

        # إضافة الخبر نفسه إلى ملف التطبيق.
        # أي خطأ هنا لا يوقف Telegram أو Facebook.
        save_story_for_app(
            story
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
# 4) تغيير اسم الإصدار الظاهر في السجل
# =========================================================

source = source.replace(
    "بوت أخبار سوريا - Telegram + Facebook - v10",
    "بوت أخبار سوريا - Telegram + Facebook + App - v11",
    1
)


# =========================================================
# تشغيل نسخة v10 بعد تطبيق تعديلات v11 عليها
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
