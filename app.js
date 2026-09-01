const NEWS_URL =
    "https://raw.githubusercontent.com/frieden29/telegram-news-bot/refs/heads/main/news.json";


const homeScreen =
    document.getElementById("homeScreen");

const detailsScreen =
    document.getElementById("detailsScreen");

const newsListElement =
    document.getElementById("newsList");

const loadingElement =
    document.getElementById("loading");

const errorElement =
    document.getElementById("error");


const detailsTitle =
    document.getElementById("detailsTitle");

const detailsDescription =
    document.getElementById("detailsDescription");

const detailsSource =
    document.getElementById("detailsSource");

const detailsTime =
    document.getElementById("detailsTime");

const sourceButton =
    document.getElementById("sourceButton");

const homeButton =
    document.getElementById("homeButton");


let newsList = [];


/* ==============================
   تحميل الأخبار
============================== */

async function loadNews() {

    loadingElement.classList.remove("hidden");
    errorElement.classList.add("hidden");

    try {

        /*
         * نضيف الوقت إلى الرابط حتى لا يعرض
         * GitHub نسخة قديمة من news.json
         */
        const url =
            `${NEWS_URL}?t=${Date.now()}`;

        const response =
            await fetch(
                url,
                {
                    cache: "no-store"
                }
            );

        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );
        }

        newsList =
            await response.json();

        renderNews();

        loadingElement.classList.add(
            "hidden"
        );

    } catch (error) {

        console.error(error);

        loadingElement.classList.add(
            "hidden"
        );

        errorElement.classList.remove(
            "hidden"
        );
    }
}


/* ==============================
   عرض الأخبار
============================== */

function renderNews() {

    newsListElement.innerHTML = "";

    newsList.forEach((news, index) => {

        const card =
            document.createElement("article");

        card.className =
            "news-card";


        const title =
            document.createElement("h2");

        title.className =
            "news-title";

        title.textContent =
            news.title || "";


        card.appendChild(title);


        if (
            news.description &&
            news.description.trim() !== ""
        ) {

            const description =
                document.createElement("p");

            description.className =
                "news-description";

            description.textContent =
                news.description;

            card.appendChild(
                description
            );
        }


        const meta =
            document.createElement("div");

        meta.className =
            "news-meta";


        const source =
            document.createElement("span");

        source.className =
            "news-source";

        source.textContent =
            news.source || "";


        const time =
            document.createElement("span");

        time.className =
            "news-time";

        time.textContent =
            news.time || "";


        meta.appendChild(source);
        meta.appendChild(time);

        card.appendChild(meta);


        card.addEventListener(
            "click",
            () => {
                showDetails(index);
            }
        );


        newsListElement.appendChild(
            card
        );
    });
}


/* ==============================
   صفحة تفاصيل الخبر
============================== */

function showDetails(index) {

    const news =
        newsList[index];

    if (!news) {
        return;
    }


    detailsTitle.textContent =
        news.title || "";

    detailsDescription.textContent =
        news.description || "";

    detailsSource.textContent =
        news.source || "";

    detailsTime.textContent =
        news.time || "";

    sourceButton.href =
        news.url || "#";


    homeScreen.classList.add(
        "hidden"
    );

    detailsScreen.classList.remove(
        "hidden"
    );


    window.scrollTo({
        top: 0,
        behavior: "instant"
    });
}


/* ==============================
   العودة إلى الصفحة الرئيسية
============================== */

function showHome() {

    detailsScreen.classList.add(
        "hidden"
    );

    homeScreen.classList.remove(
        "hidden"
    );

    window.scrollTo({
        top: 0,
        behavior: "instant"
    });
}


homeButton.addEventListener(
    "click",
    showHome
);


/* ==============================
   Service Worker
============================== */

if ("serviceWorker" in navigator) {

    window.addEventListener(
        "load",
        () => {

            navigator.serviceWorker
                .register("sw.js")
                .catch(error => {

                    console.error(
                        "Service Worker:",
                        error
                    );
                });
        }
    );
}


/* تشغيل التطبيق */

loadNews();