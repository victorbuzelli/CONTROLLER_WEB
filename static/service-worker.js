const CACHE_NAME = 'controller-web-app-cache-v1';
const urlsToCache = [
  '/', // Cache a página inicial
  '/static/css/style.css',
  '/static/images/logo_principal.png', // Certifique-se de que o nome está correto
  '/static/manifest.json'
  // Adicione aqui outros arquivos que seu aplicativo usa e que precisam ser offline
  // Por exemplo, arquivos JavaScript, outras imagens, etc.
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