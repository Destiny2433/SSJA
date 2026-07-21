const CACHE_NAME = 'sjacs-admin-v1';
const OFFLINE_URL = '/admin-dashboard';

// Files to cache for offline use
const CACHE_ASSETS = [
    '/admin-dashboard',
    '/admin',
    '/css/admin-style.css',
    '/js/admin.js',
    '/images/logo.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install - cache files
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(CACHE_ASSETS).catch(err => {
                console.warn('Some admin assets could not be cached:', err);
            });
        })
    );
    self.skipWaiting();
});

// Activate - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames =>
            Promise.all(cacheNames
                .filter(name => name !== CACHE_NAME)
                .map(name => caches.delete(name)))
        )
    );
    self.clients.claim();
});

// Fetch - serve cached or network
self.addEventListener('fetch', event => {
    // Skip non-GET and non-http(s) requests
    if (event.request.method !== 'GET') return;
    if (!event.request.url.startsWith('http')) return;

    // For API calls, go network-first
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(JSON.stringify({success: false, message: 'You are offline'}),
                    {headers: {'Content-Type': 'application/json'}});
            })
        );
        return;
    }

    // For everything else, cache-first
    event.respondWith(
        caches.match(event.request).then(cached => {
            return cached || fetch(event.request).then(response => {
                if (response && response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone));
                }
                return response;
            }).catch(() => caches.match(OFFLINE_URL));
        })
    );
});

// Push Notification - fires when server sends a push
self.addEventListener('push', event => {
    let data = {title: 'SJACS Admin', body: 'You have a new notification!', url: '/admin-dashboard'};
    if (event.data) {
        try { data = JSON.parse(event.data.text()); } catch(e) {}
    }

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: '/images/logo.png',
            badge: '/images/logo.png',
            vibrate: [200, 100, 200],
            tag: 'sjacs-admin-notification',
            requireInteraction: true,
            data: { url: data.url }
        })
    );
});

// Notification Click - open the dashboard when user taps notification
self.addEventListener('notificationclick', event => {
    event.notification.close();
    const targetUrl = (event.notification.data && event.notification.data.url) || '/admin-dashboard';
    event.waitUntil(
        clients.matchAll({type: 'window', includeUncontrolled: true}).then(clientList => {
            for (const client of clientList) {
                if (client.url.includes('/admin') && 'focus' in client) {
                    return client.focus();
                }
            }
            return clients.openWindow(targetUrl);
        })
    );
});
