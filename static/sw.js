// MedLife Touchscreen PWA Service Worker (V2 - Auto Cache Flush & Security Sync)
const CACHE_NAME = 'medlife-kiosk-v2-secure';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  // HTML sahifalari uchun har doim to'g'ridan-to'g'ri serverga murojaat qilish (No-Cache)
  if (event.request.mode === 'navigate' || event.request.destination === 'document') {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' }).catch((err) => {
        return new Response('<h1>Aloqa mavjud emas yoki server qulflangan</h1>', {
          headers: { 'Content-Type': 'text/html; charset=utf-8' }
        });
      })
    );
    return;
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
