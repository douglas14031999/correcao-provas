// Prova Canoa - PWA Service Worker
const CACHE_NAME = 'prova-canoa-v7';
const PRECACHE_ASSETS = [
  '/',
  '/manifest.json',
  '/static/styles.css',
  '/static/app.js',
  '/static/assets/logo-placeholder.svg',
  '/pwa-icon-192.png',
  '/pwa-icon-512.png',
  '/api/settings/pwa-icon?size=192',
  '/api/settings/pwa-icon?size=512'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Pré-carrega os arquivos essenciais silenciosamente
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Aviso de pré-cache (alguns recursos dinâmicos podem carregar depois):', err);
      });
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Não intercepta chamadas de API ou uploads em tempo real
  if (url.pathname.startsWith('/api/') || event.request.method !== 'GET') {
    return;
  }

  // Estratégia Stale-While-Revalidate para ativos estáticos da interface
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        return cachedResponse;
      });

      return cachedResponse || fetchPromise;
    })
  );
});
