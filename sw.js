const CACHE_NAME =
    "syria-news-v3";

const APP_FILES = [
    "./",
    "./index.html",
    "./style.css",
    "./app.js",
    "./manifest.json"
];


/* =========================================================
   تثبيت Service Worker
   ========================================================= */

self.addEventListener(
    "install",
    event => {

        event.waitUntil(

            caches
                .open(CACHE_NAME)
                .then(
                    cache => {

                        return cache.addAll(
                            APP_FILES
                        );
                    }
                )
        );


        self.skipWaiting();
    }
);


/* =========================================================
   التفعيل وحذف الكاش القديم
   ========================================================= */

self.addEventListener(
    "activate",
    event => {

        event.waitUntil(

            Promise.all([

                caches
                    .keys()
                    .then(
                        keys => {

                            return Promise.all(

                                keys
                                    .filter(
                                        key =>
                                            key !== CACHE_NAME
                                    )
                                    .map(
                                        key =>
                                            caches.delete(
                                                key
                                            )
                                    )
                            );
                        }
                    ),

                self.clients.claim()

            ])
        );
    }
);


/* =========================================================
   جلب الملفات
   ========================================================= */

self.addEventListener(
    "fetch",
    event => {

        const request =
            event.request;


        if (
            request.method
            !== "GET"
        ) {
            return;
        }


        const url =
            new URL(
                request.url
            );


        /*
         * news.json:
         * دائماً من الإنترنت.
         */

        if (
            url.pathname.endsWith(
                "/news.json"
            )
        ) {

            event.respondWith(

                fetch(
                    request,
                    {
                        cache: "no-store"
                    }
                )
            );

            return;
        }


        /*
         * app.js
         * style.css
         * index.html
         * الصفحة الرئيسية
         *
         * الإنترنت أولاً.
         * وإذا لم يتوفر الإنترنت نستخدم الكاش.
         */

        if (
            url.pathname.endsWith(
                "/app.js"
            )
            ||
            url.pathname.endsWith(
                "/style.css"
            )
            ||
            url.pathname.endsWith(
                "/index.html"
            )
            ||
            url.pathname.endsWith("/")
        ) {

            event.respondWith(

                fetch(
                    request,
                    {
                        cache: "no-store"
                    }
                )
                    .then(
                        response => {

                            if (
                                response
                                &&
                                response.ok
                            ) {

                                const responseCopy =
                                    response.clone();


                                caches
                                    .open(
                                        CACHE_NAME
                                    )
                                    .then(
                                        cache => {

                                            cache.put(
                                                request,
                                                responseCopy
                                            );
                                        }
                                    );
                            }


                            return response;
                        }
                    )
                    .catch(
                        () => {

                            return caches.match(
                                request
                            );
                        }
                    )
            );

            return;
        }


        /*
         * باقي الملفات:
         * الكاش أولاً،
         * ثم الإنترنت.
         */

        event.respondWith(

            caches
                .match(
                    request
                )
                .then(
                    cachedResponse => {

                        if (
                            cachedResponse
                        ) {
                            return cachedResponse;
                        }


                        return fetch(
                            request
                        )
                            .then(
                                response => {

                                    if (
                                        !response
                                        ||
                                        !response.ok
                                    ) {
                                        return response;
                                    }


                                    const responseCopy =
                                        response.clone();


                                    caches
                                        .open(
                                            CACHE_NAME
                                        )
                                        .then(
                                            cache => {

                                                cache.put(
                                                    request,
                                                    responseCopy
                                                );
                                            }
                                        );


                                    return response;
                                }
                            );
                    }
                )
        );
    }
);
