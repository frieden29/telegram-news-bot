const CACHE_NAME =
    "nabd-syria-v9";

const APP_FILES = [
    "./",
    "./index.html",
    "./style.css",
    "./app.js",
    "./manifest.json",
    "./logo2.png"
];


/* =========================================================
   INSTALL
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

        /*
         * فعّل النسخة الجديدة مباشرة.
         */
        self.skipWaiting();
    }
);


/* =========================================================
   ACTIVATE
   ========================================================= */

self.addEventListener(
    "activate",
    event => {

        event.waitUntil(

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
                                        caches.delete(key)
                                )
                        );
                    }
                )
                .then(
                    () =>
                        self.clients.claim()
                )
        );
    }
);


/* =========================================================
   FETCH
   ========================================================= */

self.addEventListener(
    "fetch",
    event => {

        const request =
            event.request;


        if (
            request.method !== "GET"
        ) {
            return;
        }


        const url =
            new URL(
                request.url
            );


        /*
         * news.json
         *
         * دائماً من الإنترنت.
         * لا نستخدم نسخة مخزنة قديمة.
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
         * ملفات التطبيق الأساسية:
         *
         * الإنترنت أولاً.
         * وإذا تعذر الاتصال نرجع للكاش.
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

                                const copy =
                                    response.clone();


                                caches
                                    .open(
                                        CACHE_NAME
                                    )
                                    .then(
                                        cache => {

                                            cache.put(
                                                request,
                                                copy
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
         * الكاش أولاً، ثم الإنترنت.
         */

        event.respondWith(

            caches
                .match(
                    request
                )
                .then(
                    cached => {

                        if (cached) {
                            return cached;
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


                                    const copy =
                                        response.clone();


                                    caches
                                        .open(
                                            CACHE_NAME
                                        )
                                        .then(
                                            cache => {

                                                cache.put(
                                                    request,
                                                    copy
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