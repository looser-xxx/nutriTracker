const CACHE_NAME = 'nuttracker-v6';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // If it's a JS file, especially main.js, we want to bypass cache if there's a version string
    // or just generally try to get the latest.
    if (url.origin === location.origin) {
        if (url.pathname.endsWith('.js')) {
            // Network-only for JS to ensure we get the latest versioned file
            event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
            return;
        }

        event.respondWith(
            fetch(event.request)
                .then(response => {
                    if (response.ok && urlsToCache.includes(url.pathname)) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
    } else {
        event.respondWith(
            caches.match(event.request).then(response => response || fetch(event.request))
        );
    }
});
