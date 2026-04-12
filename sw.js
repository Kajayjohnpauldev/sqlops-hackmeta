const CACHE = "sqlops-v1";
const OFFLINE_FILES = ["/login"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(OFFLINE_FILES))
  );
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  // Never cache API, WebSocket, or auth calls
  if (
    e.request.url.includes("/api/") ||
    e.request.url.includes("/ws/") ||
    e.request.url.includes("/auth/") ||
    e.request.url.includes("/step") ||
    e.request.url.includes("/reset") ||
    e.request.url.includes("/state") ||
    e.request.url.includes("/sql/") ||
    e.request.url.includes("/admin/") ||
    e.request.url.includes("/analytics") ||
    e.request.url.includes("/tasks") ||
    e.request.url.includes("/health")
  ) {
    return;
  }
  e.respondWith(
    fetch(e.request).catch(() =>
      caches.match(e.request).then(r => r || caches.match("/login"))
    )
  );
});
