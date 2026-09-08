const CACHE_NAME = "sjacs-public-v3";

const urlsToCache = [
  "/",
  "/index.html",
  "/about.html",
  "/academics.html",
  "/admissions.html",
  "/admission-form.html",
  "/gallery.html",
  "/contact.html",
  "/css/style.css",
  "/js/script.js",
  "/manifest.json",
  "images/logo.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          return cacheName !== CACHE_NAME;
        }).map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;

  // Network-first keeps published pages fresh while retaining offline support.
  event.respondWith(fetch(event.request).then(response => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response because it's a one-time use stream
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

    return response;
  }).catch(() => caches.match(event.request)));
});

self.addEventListener('push', event => {
  let data = { title: 'SS Joachim and Anne', body: 'Your application status has been updated.', url: '/admission-dashboard' };
  if (event.data) {
    try { data = { ...data, ...event.data.json() }; } catch (error) { /* Keep the default notification. */ }
  }
  event.waitUntil(self.registration.showNotification(data.title, {
    body: data.body,
    icon: '/images/logo.png',
    badge: '/images/logo.png',
    tag: 'sjacs-applicant-notification',
    data: { url: data.url || '/admission-dashboard' }
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || '/admission-dashboard';
  event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
    for (const client of clientList) {
      if ('focus' in client) {
        client.navigate(targetUrl);
        return client.focus();
      }
    }
    return clients.openWindow(targetUrl);
  }));
});
