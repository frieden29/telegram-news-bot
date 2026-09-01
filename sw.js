const CACHE_NAME =
    "syria-news-v2";

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
                .then(cache => {

                    return cache.addAll(
                        APP_FILES
                    );
                })
        );

        /*
         * تفعيل النسخة الجديدة فوراً
         * دون انتظار إغلاق التطبيق.
         */
        self.skipWaiting();
    }
);


/* =========================================================
   تفعيل Service Worker الجديد
   وحذف الكاش القديم
   ========================================================= */

self.addEventListener(
    "activate",
    event => {

        event.waitUntil(

            Promise.all([

                caches
                    .keys()
                    .then(keys => {

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
                    }),

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

        const url =
            new URL(request.url);


        /*
         * news.json:
         * دائماً من الإنترنت
         * ولا نستخدم نسخة قديمة.
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
         * app.js و style.css و index.html:
         * نحاول الإنترنت أولاً.
         *
         * إذا نجح:
         * نحفظ النسخة الجديدة في الكاش.
         *
         * إذا فشل الإنترنت:
         * نستخدم النسخة المخزنة.
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
                    .then(response => {

                        const responseCopy =
                            response.clone();

                        caches
                            .open(CACHE_NAME)
                            .then(cache => {

                                cache.put(
                                    request,
                                    responseCopy
                                );
                            });

                        return response;
                    })
                    .catch(() => {

                        return caches.match(
                            request
                        );
                    })
            );

            return;
        }


        /*
         * باقي الملفات:
         * نستخدم الكاش أولاً،
         * ثم الإنترنت عند الحاجة.
         */
        event.respondWith(

            caches
                .match(request)
                .then(response => {

                    return (
                        response
                        ||
                        fetch(request)
                    );
                })
        );
    }
);
