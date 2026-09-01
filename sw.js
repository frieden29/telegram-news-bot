const CACHE_NAME =
    "syria-news-v1";

const APP_FILES = [
    "./",
    "./index.html",
    "./style.css",
    "./app.js",
    "./manifest.json"
];


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

        self.skipWaiting();
    }
);


self.addEventListener(
    "activate",
    event => {

        event.waitUntil(

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
                })
        );

        self.clients.claim();
    }
);


self.addEventListener(
    "fetch",
    event => {

        /*
         * لا نخزّن news.json،
         * حتى تبقى الأخبار حديثة.
         */
        if (
            event.request.url.includes(
                "news.json"
            )
        ) {

            event.respondWith(
                fetch(event.request)
            );

            return;
        }


        event.respondWith(

            caches
                .match(event.request)
                .then(response => {

                    return (
                        response ||
                        fetch(event.request)
                    );
                })
        );
    }
);