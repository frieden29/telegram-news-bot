const NEWS_URL = "./news.json";

const STORAGE_KEY =
    "nabd-syria-news-cache-v1";

const newsList =
    document.getElementById("newsList");

const loadingMessage =
    document.getElementById("loadingMessage");

const errorMessage =
    document.getElementById("errorMessage");

const detailsScreen =
    document.getElementById("detailsScreen");

const detailsTitle =
    document.getElementById("detailsTitle");

const detailsDescription =
    document.getElementById("detailsDescription");

const detailsSource =
    document.getElementById("detailsSource");

const detailsTime =
    document.getElementById("detailsTime");

const detailsLink =
    document.getElementById("detailsLink")
    || document.querySelector(".source-button");

const homeButton =
    document.getElementById("homeButton")
    || document.querySelector(".home-button");

const header =
    document.querySelector(".header");

let refreshButton = null;


/* =========================================================
   أدوات عامة
   ========================================================= */

function safeText(value) {

    if (
        value === null
        || value === undefined
    ) {
        return "";
    }

    return String(value).trim();
}


/* =========================================================
   التاريخ والوقت - توقيت برلين
   ========================================================= */

function getNewsTime(news) {

    /*
     * الأولوية لوقت دخول الخبر إلى نبض سوريا
     * وهو الأقرب إلى وقت نشره على Telegram.
     */
    const publishedAt =
        Number(news.published_at || 0);

    if (
        Number.isFinite(publishedAt)
        && publishedAt > 0
    ) {

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
                new Date(
                    publishedAt * 1000
                )
            );

        } catch (error) {

            console.warn(
                "تعذر تحويل وقت النشر:",
                error
            );
        }
    }


    /*
     * احتياطي فقط للأخبار القديمة
     * التي لا تحتوي published_at.
     */
    const timestamp =
        Number(news.timestamp || 0);

    if (
        Number.isFinite(timestamp)
        && timestamp > 0
    ) {

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
                new Date(
                    timestamp * 1000
                )
            );

        } catch (error) {

            console.warn(
                "تعذر تحويل وقت المصدر:",
                error
            );
        }
    }


    return "التاريخ غير متوفر";
}
    

    const oldTime =
        safeText(news.time);

    if (
        oldTime
        && oldTime !== "الآن"
    ) {
        return oldTime;
    }


    return "التاريخ غير متوفر";
}


/* =========================================================
   الصور
   ========================================================= */

function getNewsImage(news) {

    const image =
        safeText(news.image);

    if (
        image.startsWith("https://")
        || image.startsWith("http://")
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
        safeText(news.title)
        || "صورة الخبر";

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
   ترتيب الأخبار
   ========================================================= */

function getSortTimestamp(news) {

    const now =
        Math.floor(Date.now() / 1000);

    const publishedAt =
        Number(news.published_at || 0);

    if (publishedAt > 0) {
        return publishedAt;
    }

    const sourceTimestamp =
        Number(news.timestamp || 0);

    /*
     * إذا أرسل المصدر وقتاً مستقبلياً
     * بأكثر من 5 دقائق فلا نعطيه الأولوية.
     */
    if (
        sourceTimestamp > 0
        && sourceTimestamp <= now + 300
    ) {
        return sourceTimestamp;
    }

    return 0;
}


function sortNewsByTime(newsItems) {

    return [...newsItems].sort(
        (a, b) => {

            const timeA =
                Number(
                    a.published_at
                    || a.timestamp
                    || 0
                );

            const timeB =
                Number(
                    b.published_at
                    || b.timestamp
                    || 0
                );

            return timeB - timeA;
        }
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
   الصفحة الرئيسية / التفاصيل
   ========================================================= */

function showHome() {

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


    /*
     * مهم جداً:
     * لا نستخدم window.open هنا.
     *
     * نجعل الزر رابطاً خارجياً عادياً.
     * وهذا أكثر ثباتاً على iPhone PWA.
     */

    if (detailsLink) {

        const url =
            safeText(news.url);


        if (url) {

            detailsLink.href =
                url;

            detailsLink.target =
                "_blank";

            detailsLink.rel =
                "noopener noreferrer";

            detailsLink.classList.remove(
                "hidden"
            );


            /*
             * إزالة أي onclick قديم
             * بقي من النسخ السابقة.
             */

            detailsLink.onclick =
                null;

        } else {

            detailsLink.classList.add(
                "hidden"
            );

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
   رسم الأخبار
   ========================================================= */

function renderNews(newsItems) {

    if (!newsList) {
        return;
    }


    newsList.innerHTML =
        "";


    if (
        !Array.isArray(newsItems)
        || newsItems.length === 0
    ) {

        newsList.innerHTML =
            '<div class="message">لا توجد أخبار متاحة حالياً.</div>';

        return;
    }


    const sortedNews =
        sortNewsByTime(
            newsItems
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
                safeText(news.title);


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
                safeText(news.source);


            const time =
                document.createElement(
                    "span"
                );

            time.className =
                "news-time";

            time.textContent =
                getNewsTime(news);


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
   الأخبار المحفوظة على الهاتف
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
            Array.isArray(data)
            && data.length > 0
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
     * نعرض آخر نسخة محفوظة فوراً.
     */

    if (
        !manualRefresh
        && savedNews
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
        !savedNews
        && !manualRefresh
        && loadingMessage
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


    try {

        /*
         * مهلة قصوى 8 ثوانٍ.
         * حتى لا يبقى التطبيق معلقاً.
         */

        const controller =
            new AbortController();


        const timeout =
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


        const response =
            await fetch(
                NEWS_URL
                + separator
                + "t="
                + Date.now(),
                {
                    cache: "no-store",
                    signal: controller.signal
                }
            );


        clearTimeout(
            timeout
        );


        if (!response.ok) {

            throw new Error(
                "HTTP "
                + response.status
            );
        }


        const data =
            await response.json();


        if (!Array.isArray(data)) {

            throw new Error(
                "news.json غير صالح"
            );
        }


        /*
         * الأخبار الجديدة تظهر فوراً.
         */

        renderNews(
            data
        );


        /*
         * حفظها للهاتف.
         */

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


        /*
         * لا نمسح الأخبار المحفوظة.
         */

        if (
            !savedNews
            && errorMessage
        ) {

            errorMessage.textContent =
                "تعذر تحميل الأخبار. حاول الضغط على تحديث الأخبار.";

            errorMessage.classList.remove(
                "hidden"
            );
        }


    } finally {

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
   زر العودة
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
