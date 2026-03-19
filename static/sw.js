const CACHE_NAME = 'nuttracker-v3';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/script.js',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  self.skipWaiting(); // Force the waiting service worker to become the active service worker
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('activate', event => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim()) // Immediately take control of all clients
    );
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Network-First for everything on our origin to ensure updates are seen
    if (url.origin === location.origin) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // Update cache with new version if successful
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
        return;
    }

    // Default strategy for external assets
    event.respondWith(
        caches.match(event.request).then(response => response || fetch(event.request))
    );
});
