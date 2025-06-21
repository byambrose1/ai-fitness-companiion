
const CACHE_NAME = 'fitness-companion-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/sw.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Install event - cache resources
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline daily logs
self.addEventListener('sync', function(event) {
  if (event.tag === 'daily-log-sync') {
    event.waitUntil(syncDailyLogs());
  }
});

function syncDailyLogs() {
  // Get pending logs from IndexedDB and sync when online
  return new Promise((resolve) => {
    // Implementation for syncing offline logs
    resolve();
  });
}

// Push notifications (for future use)
self.addEventListener('push', function(event) {
  const options = {
    body: 'Time for your daily check-in!',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'log',
        title: 'Log Now',
        icon: '/static/icon-192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icon-192.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Fitness Companion', options)
  );
});
