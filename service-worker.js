const CACHE_NAME = 'controller-web-app-cache-v1'; // Você pode incrementar a versão para garantir que o cache seja atualizado
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/images/logo_principal.png',
  '/static/manifest.json',
  '/static/service-worker.js', // Adicione o próprio Service Worker
  '/static/images/icon-96x96.png', // Adicione o ícone 96x96
  '/static/images/icon-192x192.png', // Adicione o ícone 192x192
  '/static/images/icon-512x512.png'  // Adicione o ícone 512x512
];

// Instalação do Service Worker: Abre um cache e adiciona os arquivos essenciais
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Interceptação de requisições: Serve os arquivos do cache, se disponíveis
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Retorna o recurso do cache se ele existir
        if (response) {
          return response;
        }
        // Se não estiver no cache, faz a requisição normal à rede
        return fetch(event.request);
      })
  );
});

// Ativação do Service Worker: Remove caches antigos
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
    })
  );
});