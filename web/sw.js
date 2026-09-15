const CACHE='tdm-web-0.2.1';
const FILES=['./','./index.html','./style.css','./app.js','./domain.js','./audio.js','./staff.js','./store.js','./sync.js','./lessons.js','./icon.svg','./manifest.webmanifest','./fonts/Bravura.otf',...([48,54,60,66,72,78,84,90,96].map(n=>'./piano/'+n+'.pcm'))];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES))));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('tdm-web-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET'||new URL(event.request.url).origin!==location.origin)return;
 // Versioned app shell loads directly from its complete installation cache.
 // A new deployment changes CACHE and installs all assets together.
 event.respondWith(caches.open(CACHE).then(async cache=>{
  const cached=await cache.match(event.request);if(cached)return cached;
  try{return await fetch(event.request);}catch{return new Response('Offline. Open the application online once to cache it.',{status:503});}
 }));
});
