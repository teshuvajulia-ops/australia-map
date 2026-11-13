/* Network first, so visitors always get the newest events; cached copy is only a fallback when offline. */
var C = 'cityside-v3';
self.addEventListener('install', function(e){ self.skipWaiting(); });
self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(k){ return Promise.all(k.filter(function(x){return x!==C;}).map(function(x){return caches.delete(x);})); }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener('fetch', function(e){
  var r = e.request;
  if(r.method!=='GET' || new URL(r.url).origin!==location.origin) return;
  e.respondWith(fetch(r, {cache:'no-cache'}).then(function(res){
    var cp = res.clone(); caches.open(C).then(function(c){ c.put(r,cp); }); return res;
  }).catch(function(){ return caches.match(r); }));
});
