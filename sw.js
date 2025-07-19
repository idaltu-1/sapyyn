/**
 * Sapyyn Service Worker - PWA Implementation
 * Provides offline functionality and performance optimizations
 */

const CACHE_NAME = 'sapyyn-v1';
const STATIC_CACHE_NAME = 'sapyyn-static-v1';
const DYNAMIC_CACHE_NAME = 'sapyyn-dynamic-v1';

// Critical resources to cache immediately
const STATIC_ASSETS = [
  '/',
  '/static/css/modern-styles.css',
  '/static/css/accessible-styles.css',
  '/static/js/enhanced-ui.js',
  '/static/js/accessible-navigation.js',
  '/static/images/sapyyn-logo.svg',
  '/static/images/sapyyn-icon.svg',
  '/templates/accessible-base.html',
  '/templates/accessible-login.html',
  '/offline.html'
];

// API endpoints to cache with network fallback
const API_CACHE_PATTERNS = [
  '/api/referrals',
  '/api/appointments',
  '/api/dashboard'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .catch(error => {
        console.error('[SW] Error caching static assets:', error);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME)
            .map(cacheName => caches.delete(cacheName))
        );
      })
  );
  self.clients.claim();
});

// Fetch event - cache strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle API requests
  if (API_CACHE_PATTERNS.some(pattern => url.pathname.includes(pattern))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Handle static assets
  if (request.destination === 'style' || 
      request.destination === 'script' || 
      request.destination === 'image' ||
      url.pathname.includes('/static/')) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Handle HTML pages
  if (request.destination === 'document' || 
      request.headers.get('accept').includes('text/html')) {
    event.respondWith(networkFirstWithOfflineFallback(request));
    return;
  }

  // Default: cache first for other resources
  event.respondWith(cacheFirst(request));
});

// Cache-first strategy for static assets
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.status === 200) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.error('[SW] Cache-first fetch failed:', error);
    return new Response('Resource not available offline', { status: 503 });
  }
}

// Network-first strategy for API calls
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.warn('[SW] Network-first fallback to cache:', error);
    const cached = await caches.match(request);
    return cached || new Response('Network error', { status: 503 });
  }
}

// Network-first with offline fallback for HTML
async function networkFirstWithOfflineFallback(request) {
  try {
    const response = await fetch(request);
    if (response.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.warn('[SW] Network error, serving offline page:', error);
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    
    // Serve offline page for navigation requests
    if (request.destination === 'document') {
      return caches.match('/offline.html');
    }
    
    return new Response('Resource not available offline', { status: 503 });
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(handleBackgroundSync());
  }
});

async function handleBackgroundSync() {
  // Handle queued actions when back online
  const queue = await getBackgroundSyncQueue();
  for (const action of queue) {
    try {
      await fetch(action.url, action.options);
      await removeFromBackgroundSyncQueue(action.id);
    } catch (error) {
      console.error('[SW] Background sync failed:', error);
    }
  }
}

// Push notifications (optional)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/static/images/sapyyn-icon-192.png',
      badge: '/static/images/sapyyn-icon-72.png',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: data.id
      },
      actions: [
        {
          action: 'explore',
          title: 'View Referral',
          icon: '/static/images/icons/action-view.png'
        },
        {
          action: 'close',
          title: 'Dismiss',
          icon: '/static/images/icons/action-close.png'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/dashboard')
    );
  }
});

// Message handling for updates
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Periodic background sync (if supported)
if ('periodicSync' in self.registration) {
  self.addEventListener('periodicSync', (event) => {
    if (event.tag === 'content-sync') {
      event.waitUntil(syncContent());
    }
  });
}

async function syncContent() {
  // Sync content in background
  console.log('[SW] Periodic sync running');
  // Implementation for background content sync
}
