const NEWS_URL =
    "https://raw.githubusercontent.com/frieden29/telegram-news-bot/refs/heads/main/news.json";

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
    document.getElementById("detailsLink");

const homeButton =
    document.getElementById("homeButton")
    || document.querySelector(".home-button");

const header =
    document.querySelector(".header");


function safeText(value) {

    if (
        value === null
        || value === undefined
    ) {
        return "";
    }

    return String(value).trim();
}


function getNewsTime(news) {

    const timeText = safeText(
        news.time
    );

    if (
        timeText
        && timeText !== "الآن"
    ) {
        return timeText;
    }

    const timestamp = Number(
        news.timestamp || 0
    );

    if (
        Number.isFinite(timestamp)
        && timestamp > 0
    ) {

        try {

            return new Intl.DateTimeFormat(
                "ar-SY",
                {
                    timeZone: "Asia/Damascus",
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
                "تعذر تنسيق وقت الخبر:",
                error
            );
        }
    }

    return "التاريخ غير متوفر";
}


function getNewsImage(news) {

    const image = safeText(
        news.image
    );

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

    const imageUrl = getNewsImage(
        news
    );

    if (!imageUrl) {
        return null;
    }

    const img = document.createElement(
        "img"
    );

    img.className = className;

    img.src = imageUrl;

    img.alt = safeText(
        news.title
    ) || "صورة الخبر";

    img.loading = "lazy";
    img.decoding = "async";
    img.referrerPolicy = "no-referrer";

    img.addEventListener(
        "error",
        () => {
            img.remove();
        }
    );

    return img;
}


function setHomeVisible(
    visible
) {

    if (header) {
        header.classList.toggle(
            "hidden",
            !visible
        );
    }

    if (newsList) {
        newsList.classList.toggle(
            "hidden",
            !visible
        );
    }

    if (loadingMessage) {
        loadingMessage.classList.add(
            "hidden"
        );
    }

    if (errorMessage) {
        errorMessage.classList.add(
            "hidden"
        );
    }

    if (detailsScreen) {
        detailsScreen.classList.toggle(
            "hidden",
            visible
        );
    }
}


function showDetails(
    news
) {

    if (!detailsScreen) {

        const url = safeText(
            news.url
        );

        if (url) {
            window.open(
                url,
                "_blank",
                "noopener,noreferrer"
            );
        }

        return;
    }


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


    if (detailsLink) {

        const url = safeText(
            news.url
        );

        detailsLink.href =
            url || "#";

        detailsLink.classList.toggle(
            "hidden",
            !url
        );
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


    setHomeVisible(
        false
    );

    window.scrollTo({
        top: 0,
        behavior: "instant"
    });

    history.pushState(
        { details: true },
        "",
        "#news"
    );
}


function renderNews(
    newsItems
) {

    if (!newsList) {
        return;
    }

    newsList.innerHTML = "";


    if (
        !Array.isArray(newsItems)
        || newsItems.length === 0
    ) {

        newsList.innerHTML =
            '<div class="message">لا توجد أخبار متاحة حالياً.</div>';

        return;
    }


    newsItems.forEach(
        (news) => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "news-card";

            card.tabIndex = 0;

            card.setAttribute(
                "role",
                "button"
            );


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


            const openNews = () => {
                showDetails(
                    news
                );
            };


            card.addEventListener(
                "click",
                openNews
            );


            card.addEventListener(
                "keydown",
                (event) => {

                    if (
                        event.key === "Enter"
                        || event.key === " "
                    ) {

                        event.preventDefault();

                        openNews();
                    }
                }
            );


            newsList.appendChild(
                card
            );
        }
    );
}


async function loadNews() {

    if (loadingMessage) {

        loadingMessage.classList.remove(
            "hidden"
        );
    }

    if (errorMessage) {

        errorMessage.classList.add(
            "hidden"
        );
    }


    try {

        const response =
            await fetch(
                `${NEWS_URL}?v=${Date.now()}`,
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        renderNews(
            data
        );


    } catch (error) {

        console.error(
            "تعذر تحميل الأخبار:",
            error
        );


        if (errorMessage) {

            errorMessage.textContent =
                "تعذر تحميل الأخبار. تحقق من الاتصال بالإنترنت ثم حاول مرة أخرى.";

            errorMessage.classList.remove(
                "hidden"
            );

        } else if (newsList) {

            newsList.innerHTML =
                '<div class="message error">تعذر تحميل الأخبار.</div>';
        }


    } finally {

        if (loadingMessage) {

            loadingMessage.classList.add(
                "hidden"
            );
        }
    }
}


function goHome() {

    setHomeVisible(
        true
    );

    if (
        location.hash === "#news"
    ) {

        history.replaceState(
            null,
            "",
            location.pathname
            + location.search
        );
    }

    window.scrollTo({
        top: 0,
        behavior: "instant"
    });
}


if (homeButton) {

    homeButton.addEventListener(
        "click",
        goHome
    );
}


window.addEventListener(
    "popstate",
    () => {

        if (
            location.hash !== "#news"
        ) {

            setHomeVisible(
                true
            );
        }
    }
);


document.addEventListener(
    "DOMContentLoaded",
    () => {

        setHomeVisible(
            true
        );

        loadNews();
    }
);


if (
    "serviceWorker"
    in navigator
) {

    window.addEventListener(
        "load",
        () => {

            navigator.serviceWorker
                .register(
                    "./sw.js"
                )
                .catch(
                    (error) => {

                        console.warn(
                            "تعذر تسجيل Service Worker:",
                            error
                        );
                    }
                );
        }
    );
}
