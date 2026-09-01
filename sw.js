const CACHE_NAME =
    "nabd-syria-v4";

const APP_FILES = [
    "./",
    "./index.html",
    "./style.css",
    "./app.js",
    "./manifest.json"
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
         * الأخبار:
         * الإنترنت دائماً.
         *
         * app.js سيحفظ آخر نسخة
         * في localStorage.
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
         * ملفات التطبيق الرئيسية:
         * الإنترنت أولاً.
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
                                && response.ok
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
         * بقية الملفات.
         */

        event.respondWith(

            caches
                .match(request)
                .then(
                    cached => {

                        return (
                            cached
                            ||
                            fetch(request)
                        );
                    }
                )
        );
    }
);
