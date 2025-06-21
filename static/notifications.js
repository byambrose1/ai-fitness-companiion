
// Push notification utilities
class NotificationManager {
  constructor() {
    this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
  }

  async requestPermission() {
    if (!this.isSupported) return false;
    
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  async scheduleReminder(time = '09:00') {
    if (!this.isSupported) return;
    
    const registration = await navigator.serviceWorker.ready;
    
    // Calculate milliseconds until next reminder time
    const now = new Date();
    const [hours, minutes] = time.split(':');
    const reminderTime = new Date();
    reminderTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);
    
    if (reminderTime <= now) {
      reminderTime.setDate(reminderTime.getDate() + 1);
    }
    
    const delay = reminderTime.getTime() - now.getTime();
    
    // Schedule notification
    setTimeout(() => {
      this.showReminder();
      // Schedule next reminder
      this.scheduleReminder(time);
    }, delay);
  }

  showReminder() {
    if (!this.isSupported) return;
    
    const options = {
      body: '💚 Time for your daily wellness check-in!',
      icon: '/static/icon-192.png',
      badge: '/static/icon-192.png',
      vibrate: [200, 100, 200],
      data: {
        url: '/daily-log'
      },
      actions: [
        {
          action: 'log',
          title: 'Log Now'
        },
        {
          action: 'later',
          title: 'Remind Later'
        }
      ]
    };

    new Notification('Fitness Companion', options);
  }

  async setupPushNotifications() {
    if (!this.isSupported) return;
    
    const registration = await navigator.serviceWorker.ready;
    
    // Request notification permission
    const permission = await this.requestPermission();
    if (!permission) return;
    
    // Schedule daily reminders
    this.scheduleReminder('09:00'); // 9 AM reminder
    this.scheduleReminder('21:00'); // 9 PM reminder
    
    console.log('Push notifications setup complete');
  }
}

// Initialize notifications
const notificationManager = new NotificationManager();

// Auto-setup on page load
document.addEventListener('DOMContentLoaded', () => {
  // Setup notifications after user interaction
  document.addEventListener('click', () => {
    notificationManager.setupPushNotifications();
  }, { once: true });
});

window.notificationManager = notificationManager;
