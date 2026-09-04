/* =========================================================
   Firebase
   ========================================================= */

import {
    initializeApp
} from "https://www.gstatic.com/firebasejs/12.18.0/firebase-app.js";

import {
    getDatabase,
    ref,
    onValue,
    runTransaction
} from "https://www.gstatic.com/firebasejs/12.18.0/firebase-database.js";


const firebaseConfig = {

    apiKey:
        "AIzaSyDBN_qDkWhH4_ICPGxDLpQenRBBHWoGomk",

    authDomain:
        "nabd-syria-4a890.firebaseapp.com",

    databaseURL:
        "https://nabd-syria-4a890-default-rtdb.europe-west1.firebasedatabase.app",

    projectId:
        "nabd-syria-4a890",

    storageBucket:
        "nabd-syria-4a890.firebasestorage.app",

    messagingSenderId:
        "137822033129",

    appId:
        "1:137822033129:web:059e0e5ec1d335fec34c78",

    measurementId:
        "G-VLZW7ZYM2Y"
};


const firebaseApp =
    initializeApp(
        firebaseConfig
    );


const database =
    getDatabase(
        firebaseApp
    );


/* =========================================================
   إعدادات الأخبار
   ========================================================= */

const NEWS_URL =
    "./news.json";

const STORAGE_KEY =
    "nabd-syria-news-cache-v2";


/* =========================================================
   مفاتيح العدادات المحلية
   ========================================================= */

/*
 * الزائر:
 * يحسب مرة واحدة على هذا المتصفح.
 */
const VISITOR_STORAGE_KEY =
    "nabd-syria-visitor-counted-v1";


/*
 * القراءة:
 * يحتسب كل خبر مرة واحدة لكل متصفح.
 */
const READ_STORAGE_PREFIX =
    "nabd-syria-read-";


/*
 * المشاهدة:
 * تحتسب مرة واحدة لكل جلسة تصفح.
 */
const VIEW_SESSION_PREFIX =
    "nabd-syria-view-";


/* =========================================================
   عناصر الصفحة
   ========================================================= */

const newsList =
    document.getElementById(
        "newsList"
    );


const loadingMessage =
    document.getElementById(
        "loadingMessage"
    ) ||
    document.getElementById(
        "loading"
    );


const errorMessage =
    document.getElementById(
        "errorMessage"
    ) ||
    document.getElementById(
        "error"
    );


const detailsScreen =
    document.getElementById(
        "detailsScreen"
    );


const detailsTitle =
    document.getElementById(
        "detailsTitle"
    );


const detailsDescription =
    document.getElementById(
        "detailsDescription"
    );


const detailsSource =
    document.getElementById(
        "detailsSource"
    );


const detailsTime =
    document.getElementById(
        "detailsTime"
    );


const detailsLink =
    document.getElementById(
        "sourceButton"
    ) ||
    document.getElementById(
        "detailsLink"
    ) ||
    document.querySelector(
        ".source-button"
    );


const homeButton =
    document.getElementById(
        "homeButton"
    ) ||
    document.querySelector(
        ".home-button"
    );


const visitorCount =
    document.getElementById(
        "visitorCount"
    );


const detailsViews =
    document.getElementById(
        "detailsViews"
    );


const detailsReads =
    document.getElementById(
        "detailsReads"
    );


const header =
    document.querySelector(
        ".header"
    );


/* =========================================================
   متغيرات عامة
   ========================================================= */

let refreshButton =
    null;


let currentDetailsUrl =
    "";


let currentNewsId =
    "";


let latestStats = {
    visitors: 0,
    news: {}
};


let visibilityObserver =
    null;


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


    return String(
        value
    ).trim();
}


/* =========================================================
   تنسيق الأرقام
   ========================================================= */

function formatNumber(value) {

    const number =
        Number(
            value || 0
        );


    if (
        !Number.isFinite(number) ||
        number < 0
    ) {

        return "0";
    }


    try {

        return new Intl.NumberFormat(
            "ar"
        ).format(
            number
        );

    } catch (error) {

        return String(
            number
        );
    }
}


/* =========================================================
   إنشاء رقم ثابت للخبر
   ========================================================= */

/*
 * Firebase لا يسمح ببعض الرموز داخل أسماء المفاتيح.
 *
 * لذلك ننشئ ID قصيراً وثابتاً من:
 *
 * الرابط
 * أو العنوان + وقت النشر
 */

function createNewsId(news) {

    const sourceText =
        safeText(
            news.url
        ) ||
        (
            safeText(news.title) +
            "|" +
            safeText(news.published_at) +
            "|" +
            safeText(news.source)
        );


    let hash =
        2166136261;


    for (
        let i = 0;
        i < sourceText.length;
        i++
    ) {

        hash ^=
            sourceText.charCodeAt(
                i
            );


        hash =
            Math.imul(
                hash,
                16777619
            );
    }


    return (
        "n" +
        (
            hash >>> 0
        ).toString(16)
    );
}


/* =========================================================
   قراءة إحصاءات خبر
   ========================================================= */

function getNewsStats(newsId) {

    const allNewsStats =
        latestStats.news || {};


    const newsStats =
        allNewsStats[newsId] || {};


    return {

        views:
            Number(
                newsStats.views || 0
            ),

        reads:
            Number(
                newsStats.reads || 0
            )
    };
}


/* =========================================================
   تحديث الأرقام الظاهرة
   ========================================================= */

function updateVisibleStatistics() {

    /*
     * عدد الزوار
     */
    if (visitorCount) {

        visitorCount.textContent =
            formatNumber(
                latestStats.visitors
            );
    }


    /*
     * عدادات البطاقات
     */
    document
        .querySelectorAll(
            ".news-card[data-news-id]"
        )
        .forEach(
            card => {

                const newsId =
                    card.dataset.newsId;


                const stats =
                    getNewsStats(
                        newsId
                    );


                const viewsElement =
                    card.querySelector(
                        ".news-views-count"
                    );


                const readsElement =
                    card.querySelector(
                        ".news-reads-count"
                    );


                if (viewsElement) {

                    viewsElement.textContent =
                        formatNumber(
                            stats.views
                        );
                }


                if (readsElement) {

                    readsElement.textContent =
                        formatNumber(
                            stats.reads
                        );
                }
            }
        );


    /*
     * عدادات صفحة التفاصيل
     */
    if (currentNewsId) {

        const stats =
            getNewsStats(
                currentNewsId
            );


        if (detailsViews) {

            detailsViews.textContent =
                formatNumber(
                    stats.views
                );
        }


        if (detailsReads) {

            detailsReads.textContent =
                formatNumber(
                    stats.reads
                );
        }
    }
}


/* =========================================================
   الاستماع لإحصاءات Firebase
   ========================================================= */

function listenForStatistics() {

    const statsReference =
        ref(
            database,
            "stats"
        );


    onValue(

        statsReference,

        snapshot => {

            const value =
                snapshot.val() || {};


            latestStats = {

                visitors:
                    Number(
                        value.visitors || 0
                    ),

                news:
                    value.news || {}
            };


            updateVisibleStatistics();
        },

        error => {

            console.warn(
                "تعذر قراءة إحصاءات Firebase:",
                error
            );
        }
    );
}


/* =========================================================
   زيادة عداد Firebase
   ========================================================= */

async function incrementCounter(
    path
) {

    try {

        const counterReference =
            ref(
                database,
                path
            );


        const result =
            await runTransaction(

                counterReference,

                currentValue => {

                    const currentNumber =
                        Number(
                            currentValue || 0
                        );


                    if (
                        !Number.isFinite(
                            currentNumber
                        ) ||
                        currentNumber < 0
                    ) {

                        return 1;
                    }


                    return (
                        currentNumber + 1
                    );
                }
            );


        return (
            result.committed === true
        );

    } catch (error) {

        console.warn(
            "تعذر تحديث العداد:",
            path,
            error
        );


        return false;
    }
}


/* =========================================================
   عداد زوار نبض سوريا
   ========================================================= */

async function registerVisitor() {

    try {

        const alreadyCounted =
            localStorage.getItem(
                VISITOR_STORAGE_KEY
            );


        if (alreadyCounted) {

            return;
        }


        const success =
            await incrementCounter(
                "stats/visitors"
            );


        /*
         * لا نحفظ العلامة إلا بعد نجاح Firebase.
         * إذا لم يتوفر الإنترنت سيحاول التطبيق مرة أخرى
         * في المرة القادمة.
         */
        if (success) {

            localStorage.setItem(
                VISITOR_STORAGE_KEY,
                "1"
            );
        }

    } catch (error) {

        console.warn(
            "تعذر تسجيل الزائر:",
            error
        );
    }
}


/* =========================================================
   تسجيل مشاهدة خبر
   ========================================================= */

async function registerNewsView(
    newsId
) {

    if (!newsId) {
        return;
    }


    const storageKey =
        VIEW_SESSION_PREFIX +
        newsId;


    try {

        /*
         * لا نكرر مشاهدة نفس الخبر
         * خلال جلسة التصفح نفسها.
         */
        if (
            sessionStorage.getItem(
                storageKey
            )
        ) {

            return;
        }


        const success =
            await incrementCounter(
                "stats/news/" +
                newsId +
                "/views"
            );


        if (success) {

            sessionStorage.setItem(
                storageKey,
                "1"
            );
        }

    } catch (error) {

        console.warn(
            "تعذر تسجيل مشاهدة الخبر:",
            error
        );
    }
}


/* =========================================================
   تسجيل قراءة خبر
   ========================================================= */

async function registerNewsRead(
    newsId
) {

    if (!newsId) {
        return;
    }


    const storageKey =
        READ_STORAGE_PREFIX +
        newsId;


    try {

        /*
         * القراءة تحتسب مرة واحدة لهذا الخبر
         * من هذا المتصفح.
         */
        if (
            localStorage.getItem(
                storageKey
            )
        ) {

            return;
        }


        const success =
            await incrementCounter(
                "stats/news/" +
                newsId +
                "/reads"
            );


        if (success) {

            localStorage.setItem(
                storageKey,
                "1"
            );
        }

    } catch (error) {

        console.warn(
            "تعذر تسجيل قراءة الخبر:",
            error
        );
    }
}


/* =========================================================
   مراقبة ظهور الأخبار على الشاشة
   ========================================================= */

function createVisibilityObserver() {

    if (
        visibilityObserver
    ) {

        visibilityObserver.disconnect();

        visibilityObserver =
            null;
    }


    /*
     * إذا كان المتصفح لا يدعم IntersectionObserver
     * نحتسب الأخبار الظاهرة عند إنشائها.
     */
    if (
        !(
            "IntersectionObserver"
            in window
        )
    ) {

        document
            .querySelectorAll(
                ".news-card[data-news-id]"
            )
            .forEach(
                card => {

                    registerNewsView(
                        card.dataset.newsId
                    );
                }
            );


        return;
    }


    visibilityObserver =
        new IntersectionObserver(

            entries => {

                entries.forEach(
                    entry => {

                        /*
                         * نحتسب المشاهدة عندما يظهر
                         * نصف بطاقة الخبر تقريباً.
                         */
                        if (
                            entry.isIntersecting &&
                            entry.intersectionRatio >= 0.5
                        ) {

                            const card =
                                entry.target;


                            const newsId =
                                card.dataset.newsId;


                            registerNewsView(
                                newsId
                            );


                            /*
                             * بعد أول ظهور لا نحتاج
                             * لمراقبة البطاقة مرة أخرى.
                             */
                            visibilityObserver.unobserve(
                                card
                            );
                        }
                    }
                );
            },

            {
                threshold: [
                    0.5
                ]
            }
        );


    document
        .querySelectorAll(
            ".news-card[data-news-id]"
        )
        .forEach(
            card => {

                visibilityObserver.observe(
                    card
                );
            }
        );
}


/* =========================================================
   تنسيق وقت برلين
   ========================================================= */

function formatBerlinTime(
    unixSeconds
) {

    const value =
        Number(
            unixSeconds || 0
        );


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
                timeZone:
                    "Europe/Berlin",

                day:
                    "2-digit",

                month:
                    "2-digit",

                year:
                    "numeric",

                hour:
                    "2-digit",

                minute:
                    "2-digit",

                hour12:
                    false
            }

        ).format(

            new Date(
                value * 1000
            )
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
     * الأولوية لوقت دخول الخبر
     * إلى نبض سوريا.
     */
    const publishedAt =
        Number(
            news.published_at || 0
        );


    const publishedTime =
        formatBerlinTime(
            publishedAt
        );


    if (publishedTime) {

        return publishedTime;
    }


    /*
     * الأخبار القديمة التي سبقت published_at
     */
    const savedTime =
        safeText(
            news.time
        );


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
        safeText(
            news.image
        );


    if (
        image.startsWith(
            "https://"
        ) ||
        image.startsWith(
            "http://"
        )
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
        getNewsImage(
            news
        );


    if (!imageUrl) {

        return null;
    }


    const img =
        document.createElement(
            "img"
        );


    img.className =
        className;


    img.src =
        imageUrl;


    img.alt =
        safeText(
            news.title
        ) ||
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
   منع أخبار Archives القديمة
   ========================================================= */

function isArchiveNews(news) {

    const text =
        (
            safeText(
                news.title
            ) +
            " " +
            safeText(
                news.url
            )
        ).toLowerCase();


    return (

        text.includes(
            "archive"
        ) ||

        text.includes(
            "archives"
        ) ||

        text.includes(
            "أرشيف"
        ) ||

        text.includes(
            "الأرشيف"
        )
    );
}


/* =========================================================
   ترتيب الأخبار
   ========================================================= */

function sortNewsByTime(
    newsItems
) {

    return newsItems

        .map(
            (
                news,
                index
            ) => ({
                news,
                index
            })
        )

        .sort(
            (
                a,
                b
            ) => {

                const aPublished =
                    Number(
                        a.news.published_at || 0
                    );


                const bPublished =
                    Number(
                        b.news.published_at || 0
                    );


                const aHasPublished =
                    Number.isFinite(
                        aPublished
                    ) &&
                    aPublished > 0;


                const bHasPublished =
                    Number.isFinite(
                        bPublished
                    ) &&
                    bPublished > 0;


                if (
                    aHasPublished &&
                    bHasPublished
                ) {

                    return (
                        bPublished -
                        aPublished
                    );
                }


                if (aHasPublished) {

                    return -1;
                }


                if (bHasPublished) {

                    return 1;
                }


                return (
                    a.index -
                    b.index
                );
            }
        )

        .map(
            item =>
                item.news
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
        document.createElement(
            "div"
        );


    actions.className =
        "header-actions";


    refreshButton =
        document.createElement(
            "button"
        );


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

            loadNews(
                true
            );
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


    currentNewsId =
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
        safeText(
            url
        );


    if (
        !safeUrl ||
        (
            !safeUrl.startsWith(
                "https://"
            ) &&
            !safeUrl.startsWith(
                "http://"
            )
        )
    ) {

        return;
    }


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


    currentNewsId =
        createNewsId(
            news
        );


    if (detailsTitle) {

        detailsTitle.textContent =
            safeText(
                news.title
            );
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
            safeText(
                news.source
            );
    }


    if (detailsTime) {

        detailsTime.textContent =
            getNewsTime(
                news
            );
    }


    /*
     * عرض إحصاءات الخبر
     */
    const stats =
        getNewsStats(
            currentNewsId
        );


    if (detailsViews) {

        detailsViews.textContent =
            formatNumber(
                stats.views
            );
    }


    if (detailsReads) {

        detailsReads.textContent =
            formatNumber(
                stats.reads
            );
    }


    currentDetailsUrl =
        safeText(
            news.url
        );


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
   إنشاء سطر الإحصاءات داخل بطاقة الخبر
   ========================================================= */

function createNewsStatistics(
    newsId
) {

    const statistics =
        document.createElement(
            "div"
        );


    statistics.className =
        "news-statistics";


    /*
     * المشاهدات
     */
    const views =
        document.createElement(
            "span"
        );


    views.className =
        "news-stat";


    views.innerHTML =
        '👁 <span class="news-views-count">0</span> مشاهدة';


    /*
     * القراءات
     */
    const reads =
        document.createElement(
            "span"
        );


    reads.className =
        "news-stat";


    reads.innerHTML =
        '📖 <span class="news-reads-count">0</span> قراءة';


    statistics.appendChild(
        views
    );


    statistics.appendChild(
        reads
    );


    const stats =
        getNewsStats(
            newsId
        );


    const viewsCount =
        statistics.querySelector(
            ".news-views-count"
        );


    const readsCount =
        statistics.querySelector(
            ".news-reads-count"
        );


    if (viewsCount) {

        viewsCount.textContent =
            formatNumber(
                stats.views
            );
    }


    if (readsCount) {

        readsCount.textContent =
            formatNumber(
                stats.reads
            );
    }


    return statistics;
}


/* =========================================================
   عرض الأخبار
   ========================================================= */

function renderNews(
    newsItems
) {

    if (!newsList) {

        return;
    }


    if (visibilityObserver) {

        visibilityObserver.disconnect();

        visibilityObserver =
            null;
    }


    newsList.innerHTML =
        "";


    if (
        !Array.isArray(
            newsItems
        ) ||
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
                !isArchiveNews(
                    news
                )
        );


    /*
     * ترتيب الأخبار.
     */
    const sortedNews =
        sortNewsByTime(
            cleanNews
        );


    sortedNews.forEach(
        news => {

            const newsId =
                createNewsId(
                    news
                );


            const card =
                document.createElement(
                    "article"
                );


            card.className =
                "news-card";


            card.dataset.newsId =
                newsId;


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


            /*
             * المصدر والوقت
             */
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


            /*
             * المشاهدات والقراءات
             */
            const statistics =
                createNewsStatistics(
                    newsId
                );


            card.appendChild(
                statistics
            );


            /*
             * فتح صفحة التفاصيل
             */
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


    /*
     * تحديث الأرقام الموجودة
     * من آخر بيانات Firebase.
     */
    updateVisibleStatistics();


    /*
     * بدء مراقبة ظهور الأخبار.
     */
    createVisibilityObserver();
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
            JSON.parse(
                saved
            );


        if (
            Array.isArray(
                data
            ) &&
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


    /*
     * إظهار جاري التحميل فقط
     * إذا لم توجد نسخة محفوظة.
     */
    if (
        !savedNews &&
        !manualRefresh &&
        loadingMessage
    ) {

        loadingMessage.classList.remove(
            "hidden"
        );
    }


    /*
     * تحديث يدوي.
     */
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
            NEWS_URL.includes(
                "?"
            )
                ? "&"
                : "?";


        const response =
            await fetch(

                NEWS_URL +
                separator +
                "t=" +
                Date.now(),

                {
                    cache:
                        "no-store",

                    signal:
                        controller.signal
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


        if (
            !Array.isArray(
                data
            )
        ) {

            throw new Error(
                "news.json غير صالح"
            );
        }


        /*
         * عرض الأخبار الجديدة.
         */
        renderNews(
            data
        );


        /*
         * حفظ الأخبار.
         */
        try {

            localStorage.setItem(

                STORAGE_KEY,

                JSON.stringify(
                    data
                )
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

        async event => {

            event.preventDefault();

            event.stopPropagation();


            /*
             * نسجل القراءة أولاً.
             */
            if (currentNewsId) {

                await registerNewsRead(
                    currentNewsId
                );
            }


            /*
             * ثم نفتح المصدر.
             */
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

        /*
         * إنشاء زر التحديث.
         */
        createRefreshButton();


        /*
         * إظهار الصفحة الرئيسية.
         */
        showHome();


        /*
         * الاستماع لأرقام Firebase.
         */
        listenForStatistics();


        /*
         * تسجيل الزائر.
         */
        registerVisitor();


        /*
         * تحميل الأخبار.
         */
        loadNews(
            false
        );
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
