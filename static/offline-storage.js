
// Offline storage utilities for PWA
class OfflineStorage {
  constructor() {
    this.dbName = 'FitnessCompanionDB';
    this.dbVersion = 1;
    this.db = null;
    this.init();
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create stores
        if (!db.objectStoreNames.contains('dailyLogs')) {
          const dailyLogsStore = db.createObjectStore('dailyLogs', { keyPath: 'id', autoIncrement: true });
          dailyLogsStore.createIndex('date', 'date', { unique: false });
          dailyLogsStore.createIndex('synced', 'synced', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('userSettings')) {
          db.createObjectStore('userSettings', { keyPath: 'key' });
        }
      };
    });
  }

  async saveDailyLog(logData) {
    const transaction = this.db.transaction(['dailyLogs'], 'readwrite');
    const store = transaction.objectStore('dailyLogs');
    
    logData.synced = navigator.onLine;
    logData.timestamp = new Date().toISOString();
    
    return store.add(logData);
  }

  async getPendingLogs() {
    const transaction = this.db.transaction(['dailyLogs'], 'readonly');
    const store = transaction.objectStore('dailyLogs');
    const index = store.index('synced');
    
    return new Promise((resolve, reject) => {
      const request = index.getAll(false);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async markLogSynced(logId) {
    const transaction = this.db.transaction(['dailyLogs'], 'readwrite');
    const store = transaction.objectStore('dailyLogs');
    
    const getRequest = store.get(logId);
    getRequest.onsuccess = () => {
      const log = getRequest.result;
      log.synced = true;
      store.put(log);
    };
  }

  async syncPendingLogs() {
    if (!navigator.onLine) return;
    
    const pendingLogs = await this.getPendingLogs();
    
    for (const log of pendingLogs) {
      try {
        const formData = new FormData();
        Object.keys(log).forEach(key => {
          if (key !== 'id' && key !== 'synced' && key !== 'timestamp') {
            formData.append(key, log[key]);
          }
        });
        
        const response = await fetch('/save-daily-log', {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          await this.markLogSynced(log.id);
        }
      } catch (error) {
        console.error('Failed to sync log:', error);
      }
    }
  }
}

// Initialize offline storage
const offlineStorage = new OfflineStorage();

// Auto-sync when coming back online
window.addEventListener('online', () => {
  offlineStorage.syncPendingLogs();
});

// Export for use in other scripts
window.offlineStorage = offlineStorage;
