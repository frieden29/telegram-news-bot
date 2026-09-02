const NEWS_URL = "./news.json";

const STORAGE_KEY = "nabd-syria-news-cache-v2";

const newsList = document.getElementById("newsList");
const loadingMessage = document.getElementById("loadingMessage");
const errorMessage = document.getElementById("errorMessage");

const detailsScreen = document.getElementById("detailsScreen");
const detailsTitle = document.getElementById("detailsTitle");
const detailsDescription = document.getElementById("detailsDescription");
const detailsSource = document.getElementById("detailsSource");
const detailsTime = document.getElementById("detailsTime");

const detailsLink =
    document.getElementById("detailsLink") ||
    document.querySelector(".source-button");

const homeButton =
    document.getElementById("homeButton") ||
    document.querySelector(".home-button");

const header = document.querySelector(".header");

let refreshButton = null;
let currentDetailsUrl = "";


/* =========================================================
   أدوات عامة
   ========================================================= */

function safeText(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value).trim();
}


/* =========================================================
   تنسيق وقت برلين
   ========================================================= */

function formatBerlinTime(unixSeconds) {

    const value =
        Number(unixSeconds || 0);

    if (
        !Number.isFinite(value) ||
        value <= 0
    ) {
        return "";
    }

    try {

        return new Intl.DateTimeFormat(
            "de-DE",
            {
                timeZone: "Europe/Berlin",
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            }
        ).format(
            new Date(value * 1000)
        );

    } catch (error) {

        console.warn(
            "تعذر تحويل الوقت:",
            error
        );

        return "";
    }
}


/* =========================================================
   الوقت المعروض في التطبيق
   ========================================================= */

function getNewsTime(news) {

    /*
     * الأولوية فقط لوقت دخول الخبر إلى نبض سوريا.
     * هذا هو الأقرب إلى وقت نشره على Telegram.
     */
    const publishedAt =
        Number(news.published_at || 0);

    const publishedTime =
        formatBerlinTime(
            publishedAt
        );

    if (publishedTime) {
        return publishedTime;
    }


    /*
     * الأخبار القديمة التي سبقت published_at
     * نعرض وقتها المخزن كما هو، لكن لا نستخدم
     * timestamp الخاص بالمصدر لتصدر الأخبار.
     */
    const savedTime =
        safeText(news.time);

    if (
        savedTime &&
        savedTime !== "الآن"
    ) {
        return savedTime;
    }

    return "وقت النشر غير متوفر";
}


/* =========================================================
   الصور
   ========================================================= */

function getNewsImage(news) {

    const image =
        safeText(news.image);

    if (
        image.startsWith("https://") ||
        image.startsWith("http://")
    ) {
        return image;
    }

    return "";
}


function createNewsImage(
    news,
    className
) {

    const imageUrl =
        getNewsImage(news);

    if (!imageUrl) {
        return null;
    }

    const img =
        document.createElement("img");

    img.className =
        className;

    img.src =
        imageUrl;

    img.alt =
        safeText(news.title) ||
        "صورة الخبر";

    img.loading =
        "lazy";

    img.decoding =
        "async";

    img.addEventListener(
        "error",
        () => {
            img.remove();
        }
    );

    return img;
}


/* =========================================================
   منع أخبار Archives القديمة من الظهور
   ========================================================= */

function isArchiveNews(news) {

    const text =
        (
            safeText(news.title) +
            " " +
            safeText(news.url)
        ).toLowerCase();

    return (
        text.includes("archive") ||
        text.includes("archives") ||
        text.includes("أرشيف") ||
        text.includes("الأرشيف")
    );
}


/* =========================================================
   ترتيب الأخبار
   ========================================================= */

function sortNewsByTime(newsItems) {

    return newsItems
        .map(
            (news, index) => ({
                news,
                index
            })
        )
        .sort(
            (a, b) => {

                const aPublished =
                    Number(
                        a.news.published_at || 0
                    );

                const bPublished =
                    Number(
                        b.news.published_at || 0
                    );

                const aHasPublished =
                    Number.isFinite(aPublished) &&
                    aPublished > 0;

                const bHasPublished =
                    Number.isFinite(bPublished) &&
                    bPublished > 0;


                /*
                 * الأخبار الجديدة التي لديها published_at
                 * ترتب حسب وقت دخولها إلى نبض سوريا.
                 */
                if (
                    aHasPublished &&
                    bHasPublished
                ) {
                    return (
                        bPublished -
                        aPublished
                    );
                }


                /*
                 * أي خبر جديد يأتي قبل الأخبار القديمة.
                 */
                if (aHasPublished) {
                    return -1;
                }

                if (bHasPublished) {
                    return 1;
                }


                /*
                 * الأخبار القديمة التي لا تملك published_at
                 * تبقى بترتيب news.json ولا نعتمد timestamp
                 * الخاص بالمصدر.
                 */
                return (
                    a.index -
                    b.index
                );
            }
        )
        .map(
            item => item.news
        );
}


/* =========================================================
   زر تحديث الأخبار
   ========================================================= */

function createRefreshButton() {

    if (!header) {
        return;
    }

    const oldButton =
        document.getElementById(
            "refreshNewsButton"
        );

    if (oldButton) {

        refreshButton =
            oldButton;

        return;
    }

    const actions =
        document.createElement("div");

    actions.className =
        "header-actions";

    refreshButton =
        document.createElement("button");

    refreshButton.id =
        "refreshNewsButton";

    refreshButton.className =
        "refresh-button";

    refreshButton.type =
        "button";

    refreshButton.innerHTML =
        '<span class="refresh-icon">↻</span> تحديث الأخبار';

    refreshButton.addEventListener(
        "click",
        () => {
            loadNews(true);
        }
    );

    actions.appendChild(
        refreshButton
    );

    header.appendChild(
        actions
    );
}


/* =========================================================
   حالة زر التحديث
   ========================================================= */

function setRefreshLoading(
    isLoading
) {

    if (!refreshButton) {
        return;
    }

    refreshButton.disabled =
        isLoading;

    if (isLoading) {

        refreshButton.innerHTML =
            '<span class="refresh-icon rotating">↻</span> جارٍ التحديث...';

    } else {

        refreshButton.innerHTML =
            '<span class="refresh-icon">↻</span> تحديث الأخبار';
    }
}


/* =========================================================
   الصفحة الرئيسية
   ========================================================= */

function showHome() {

    currentDetailsUrl =
        "";

    if (header) {

        header.classList.remove(
            "hidden"
        );
    }

    if (newsList) {

        newsList.classList.remove(
            "hidden"
        );
    }

    if (detailsScreen) {

        detailsScreen.classList.add(
            "hidden"
        );
    }

    window.scrollTo(
        0,
        0
    );
}


/* =========================================================
   فتح المصدر الخارجي
   ========================================================= */

function openExternalSource(url) {

    const safeUrl =
        safeText(url);

    if (
        !safeUrl ||
        (
            !safeUrl.startsWith("https://") &&
            !safeUrl.startsWith("http://")
        )
    ) {
        return;
    }

    /*
     * لا نستخدم window.open.
     * نوجّه الرابط الخارجي مباشرة.
     */
    window.location.href =
        safeUrl;
}


/* =========================================================
   تفاصيل الخبر
   ========================================================= */

function showDetails(news) {

    if (!detailsScreen) {
        return;
    }

    if (detailsTitle) {

        detailsTitle.textContent =
            safeText(news.title);
    }

    if (detailsDescription) {

        const description =
            safeText(
                news.description
            );

        detailsDescription.textContent =
            description;

        detailsDescription.classList.toggle(
            "hidden",
            !description
        );
    }

    if (detailsSource) {

        detailsSource.textContent =
            safeText(news.source);
    }

    if (detailsTime) {

        detailsTime.textContent =
            getNewsTime(news);
    }


    currentDetailsUrl =
        safeText(news.url);


    if (detailsLink) {

        const hasValidUrl =
            currentDetailsUrl.startsWith(
                "https://"
            ) ||
            currentDetailsUrl.startsWith(
                "http://"
            );

        detailsLink.classList.toggle(
            "hidden",
            !hasValidUrl
        );

        if (hasValidUrl) {

            detailsLink.setAttribute(
                "href",
                currentDetailsUrl
            );

            detailsLink.setAttribute(
                "target",
                "_self"
            );

            detailsLink.setAttribute(
                "rel",
                "external"
            );

        } else {

            detailsLink.removeAttribute(
                "href"
            );
        }
    }


    const detailsCard =
        detailsScreen.querySelector(
            ".details-card"
        );

    if (detailsCard) {

        const oldImage =
            detailsCard.querySelector(
                ".details-image"
            );

        if (oldImage) {
            oldImage.remove();
        }

        const image =
            createNewsImage(
                news,
                "details-image"
            );

        if (image) {

            detailsCard.insertBefore(
                image,
                detailsCard.firstChild
            );
        }
    }


    if (header) {

        header.classList.add(
            "hidden"
        );
    }

    if (newsList) {

        newsList.classList.add(
            "hidden"
        );
    }

    detailsScreen.classList.remove(
        "hidden"
    );

    window.scrollTo(
        0,
        0
    );
}


/* =========================================================
   عرض الأخبار
   ========================================================= */

function renderNews(newsItems) {

    if (!newsList) {
        return;
    }

    newsList.innerHTML =
        "";

    if (
        !Array.isArray(newsItems) ||
        newsItems.length === 0
    ) {

        newsList.innerHTML =
            '<div class="message">لا توجد أخبار متاحة حالياً.</div>';

        return;
    }


    /*
     * إزالة أخبار Archive القديمة.
     */
    const cleanNews =
        newsItems.filter(
            news =>
                !isArchiveNews(news)
        );


    /*
     * ترتيب الأخبار حسب published_at.
     */
    const sortedNews =
        sortNewsByTime(
            cleanNews
        );


    sortedNews.forEach(
        news => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "news-card";


            const mainRow =
                document.createElement(
                    "div"
                );

            mainRow.className =
                "news-main-row";


            const textArea =
                document.createElement(
                    "div"
                );

            textArea.className =
                "news-text-area";


            const title =
                document.createElement(
                    "h2"
                );

            title.className =
                "news-title";

            title.textContent =
                safeText(
                    news.title
                );

            textArea.appendChild(
                title
            );


            const descriptionText =
                safeText(
                    news.description
                );

            if (descriptionText) {

                const description =
                    document.createElement(
                        "p"
                    );

                description.className =
                    "news-description";

                description.textContent =
                    descriptionText;

                textArea.appendChild(
                    description
                );
            }


            mainRow.appendChild(
                textArea
            );


            const image =
                createNewsImage(
                    news,
                    "news-image"
                );

            if (image) {

                mainRow.appendChild(
                    image
                );
            }


            card.appendChild(
                mainRow
            );


            const meta =
                document.createElement(
                    "div"
                );

            meta.className =
                "news-meta";


            const source =
                document.createElement(
                    "span"
                );

            source.className =
                "news-source";

            source.textContent =
                safeText(
                    news.source
                );


            const time =
                document.createElement(
                    "span"
                );

            time.className =
                "news-time";

            time.textContent =
                getNewsTime(
                    news
                );


            meta.appendChild(
                source
            );

            meta.appendChild(
                time
            );

            card.appendChild(
                meta
            );


            card.addEventListener(
                "click",
                () => {

                    showDetails(
                        news
                    );
                }
            );


            newsList.appendChild(
                card
            );
        }
    );
}


/* =========================================================
   الأخبار المحفوظة
   ========================================================= */

function getSavedNews() {

    try {

        const saved =
            localStorage.getItem(
                STORAGE_KEY
            );

        if (!saved) {
            return null;
        }

        const data =
            JSON.parse(saved);

        if (
            Array.isArray(data) &&
            data.length > 0
        ) {
            return data;
        }

    } catch (error) {

        console.warn(
            "خطأ في الأخبار المحفوظة:",
            error
        );
    }

    return null;
}


/* =========================================================
   تحميل الأخبار
   ========================================================= */

async function loadNews(
    manualRefresh = false
) {

    const savedNews =
        getSavedNews();


    /*
     * عرض آخر نسخة محفوظة فوراً.
     */
    if (
        !manualRefresh &&
        savedNews
    ) {

        renderNews(
            savedNews
        );

        if (loadingMessage) {

            loadingMessage.classList.add(
                "hidden"
            );
        }
    }


    if (
        !savedNews &&
        !manualRefresh &&
        loadingMessage
    ) {

        loadingMessage.classList.remove(
            "hidden"
        );
    }


    if (manualRefresh) {

        setRefreshLoading(
            true
        );
    }


    if (errorMessage) {

        errorMessage.classList.add(
            "hidden"
        );
    }


    let timeout =
        null;


    try {

        const controller =
            new AbortController();


        timeout =
            setTimeout(
                () => {

                    controller.abort();

                },
                8000
            );


        const separator =
            NEWS_URL.includes("?")
            ? "&"
            : "?";
        const loading =
    document.getElementById("loading");

loading.classList.remove("hidden");

        const response =
            await fetch(
                NEWS_URL +
                separator +
                "t=" +
                Date.now(),
                {
                    cache: "no-store",
                    signal: controller.signal
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " +
                response.status
            );
        }


        const data =
            await response.json();


        if (!Array.isArray(data)) {

            throw new Error(
                "news.json غير صالح"
            );
        }


        renderNews(
            data
        );


        try {

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(data)
            );

        } catch (error) {

            console.warn(
                "تعذر حفظ الأخبار:",
                error
            );
        }


    } catch (error) {

        console.warn(
            "تعذر تحديث الأخبار:",
            error
        );


        if (
            !savedNews &&
            errorMessage
        ) {

            errorMessage.textContent =
                "تعذر تحميل الأخبار. حاول الضغط على تحديث الأخبار.";

            errorMessage.classList.remove(
                "hidden"
            );
        }


    } finally {
        

     const loading =
        document.getElementById("loading");

    loading.classList.add("hidden");


    if (timeout) {

        if (timeout) {

            clearTimeout(
                timeout
            );
        }


        if (loadingMessage) {

            loadingMessage.classList.add(
                "hidden"
            );
        }


        setRefreshLoading(
            false
        );
    }
}


/* =========================================================
   زر العودة للرئيسية
   ========================================================= */

if (homeButton) {

    homeButton.addEventListener(
        "click",
        event => {

            event.preventDefault();

            showHome();
        }
    );
}


/* =========================================================
   زر قراءة الخبر من المصدر
   ========================================================= */

if (detailsLink) {

    detailsLink.addEventListener(
        "click",
        event => {

            event.preventDefault();

            event.stopPropagation();

            openExternalSource(
                currentDetailsUrl
            );
        }
    );
}


/* =========================================================
   بدء التطبيق
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        createRefreshButton();

        showHome();

        loadNews(false);
    }
);


/* =========================================================
   Service Worker
   ========================================================= */

if (
    "serviceWorker"
    in navigator
) {

    window.addEventListener(
        "load",
        () => {

            navigator
                .serviceWorker
                .register(
                    "./sw.js"
                )
                .then(
                    registration => {

                        registration.update();
                    }
                )
                .catch(
                    error => {

                        console.warn(
                            "Service Worker:",
                            error
                        );
                    }
                );
        }
    );
}