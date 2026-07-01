var CACHE_NAME = 'hermes-translate-v1';
var PRECACHE_URLS = [
  './translate.html',
  './nav.html',
  'https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap'
];

/* Install — precache static assets */
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return Promise.allSettled(PRECACHE_URLS.map(function(url) {
        return cache.add(url).catch(function() {
          /* ignore individual failures */
        });
      }));
    }).then(function() {
      return self.skipWaiting();
    })
  );
});

/* Activate — clean old caches */
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE_NAME; })
          .map(function(k) { return caches.delete(k); })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

/* Fetch — cache-first strategy */
self.addEventListener('fetch', function(event) {
  /* Only handle GET requests */
  if (event.request.method !== 'GET') return;

  /* Don't intercept API calls */
  if (event.request.url.includes('/agent/') ||
      event.request.url.includes('/translate/') ||
      event.request.url.includes('/status/') ||
      event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then(function(cached) {
      if (cached) {
        /* Background refresh */
        fetch(event.request).then(function(response) {
          if (response.ok) {
            caches.open(CACHE_NAME).then(function(cache) {
              cache.put(event.request, response);
            });
          }
        }).catch(function() {});
        return cached;
      }
      return fetch(event.request).then(function(response) {
        if (!response.ok) return response;
        var clone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, clone);
        });
        return response;
      });
    })
  );
});
