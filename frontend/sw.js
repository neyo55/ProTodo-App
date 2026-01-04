// sw.js - Service Worker for ProTodo push notifications

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'ProTodo Reminder';
    const options = {
        body: data.body || 'You have a task due soon!',
        icon: '/icon-192.png',  // Optional: add a 192x192 icon later
        badge: '/badge-72.png',
        vibrate: [200, 100, 200],
        data: data.url || '/app.html'
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data || '/app.html')
    );
});