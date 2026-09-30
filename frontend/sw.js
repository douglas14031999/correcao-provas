// Prova Canoa - PWA Service Worker
const CACHE_NAME = 'prova-canoa-v14';
const PRECACHE_ASSETS = [
  '/',
  '/manifest.json',
  '/static/styles.css',
  '/static/app.js',
  '/static/manual.html',
  '/static/manual.css',
  '/static/manual.js',
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

  // Não intercepta chamadas de API, uploads ou o módulo de elaboração de provas
  if (url.pathname.startsWith('/api/') || url.pathname.includes('elaborador') || event.request.method !== 'GET') {
    return;
  }

  // Rota do manual e documentação
  if (url.pathname === '/manual' || url.pathname === '/docs') {
    event.respondWith(
      fetch('/static/manual.html').catch(() => caches.match('/static/manual.html'))
    );
    return;
  }

  // Para navegação/HTML principal, sempre busca da rede primeiro para garantir interface atualizada
  if (event.request.mode === 'navigate' || event.request.destination === 'document' || url.pathname === '/') {
    event.respondWith(
      fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
        }
        return networkResponse;
      }).catch(() => caches.match(event.request))
    );
    return;
  }

  // Estratégia Stale-While-Revalidate para outros ativos estáticos (CSS, JS, imagens)
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
