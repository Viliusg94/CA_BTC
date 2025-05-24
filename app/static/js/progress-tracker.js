/**
 * Progress Tracker JavaScript Library
 * Handles real-time updates of progress for long-running tasks
 */

class ProgressTracker {
    constructor(options = {}) {
        this.options = Object.assign({
            apiBaseUrl: '/api/progress',
            updateInterval: 2000, // 2 seconds
            onUpdate: null,
            onComplete: null,
            onError: null
        }, options);
        
        this.activeTaskIds = new Set();
        this.taskData = new Map();
        this.pollingInterval = null;
        this.initialized = false;
    }
    
    /**
     * Initialize the progress tracker
     */
    init() {
        if (this.initialized) return;
        
        // Start polling if we have tasks to track
        if (this.activeTaskIds.size > 0) {
            this.startPolling();
        }
        
        this.initialized = true;
        console.log('Progress tracker initialized');
    }
    
    /**
     * Start tracking a specific task
     * @param {string} taskId - The ID of the task to track
     */
    trackTask(taskId) {
        if (!taskId) return;
        
        this.activeTaskIds.add(taskId);
        
        // Start polling if not already started
        if (this.initialized && !this.pollingInterval) {
            this.startPolling();
        }
        
        console.log(`Tracking task: ${taskId}`);
    }
    
    /**
     * Stop tracking a specific task
     * @param {string} taskId - The ID of the task to stop tracking
     */
    stopTracking(taskId) {
        if (!taskId) return;
        
        this.activeTaskIds.delete(taskId);
        this.taskData.delete(taskId);
        
        // Stop polling if no tasks left
        if (this.activeTaskIds.size === 0 && this.pollingInterval) {
            this.stopPolling();
        }
        
        console.log(`Stopped tracking task: ${taskId}`);
    }
    
    /**
     * Start polling for updates
     */
    startPolling() {
        if (this.pollingInterval) return;
        
        this.pollingInterval = setInterval(() => {
            this.updateAllTasks();
        }, this.options.updateInterval);
        
        console.log('Started polling for progress updates');
    }
    
    /**
     * Stop polling for updates
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('Stopped polling for progress updates');
        }
    }
    
    /**
     * Update all active tasks
     */
    updateAllTasks() {
        this.activeTaskIds.forEach(taskId => {
            this.updateTask(taskId);
        });
    }
    
    /**
     * Update a specific task
     * @param {string} taskId - The ID of the task to update
     */
    updateTask(taskId) {
        if (!taskId) return;
        
        fetch(`${this.options.apiBaseUrl}/task/${taskId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.success) {
                    throw new Error(data.error || 'Unknown error');
                }
                
                const taskData = data.task;
                const previousData = this.taskData.get(taskId);
                
                // Store the updated data
                this.taskData.set(taskId, taskData);
                
                // Call update callback
                if (this.options.onUpdate) {
                    this.options.onUpdate(taskId, taskData, previousData);
                }
                
                // Check if task is complete or failed
                if (taskData.status === 'completed' || taskData.status === 'failed') {
                    if (this.options.onComplete) {
                        this.options.onComplete(taskId, taskData);
                    }
                    
                    // Automatically stop tracking completed tasks
                    this.stopTracking(taskId);
                }
            })
            .catch(error => {
                console.error(`Error updating task ${taskId}:`, error);
                
                if (this.options.onError) {
                    this.options.onError(taskId, error);
                }
            });
    }
    
    /**
     * Get the current data for a task
     * @param {string} taskId - The ID of the task
     * @returns {Object|null} The task data or null if not found
     */
    getTaskData(taskId) {
        return this.taskData.get(taskId) || null;
    }
    
    /**
     * Get all active task IDs
     * @returns {Array} Array of active task IDs
     */
    getActiveTaskIds() {
        return Array.from(this.activeTaskIds);
    }
    
    /**
     * Manually refresh a task
     * @param {string} taskId - The ID of the task to refresh
     * @returns {Promise} A promise that resolves when the task is updated
     */
    refreshTask(taskId) {
        return new Promise((resolve, reject) => {
            fetch(`${this.options.apiBaseUrl}/task/${taskId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data.success) {
                        throw new Error(data.error || 'Unknown error');
                    }
                    
                    const taskData = data.task;
                    this.taskData.set(taskId, taskData);
                    
                    resolve(taskData);
                })
                .catch(error => {
                    console.error(`Error refreshing task ${taskId}:`, error);
                    reject(error);
                });
        });
    }
}

// Create a global instance
window.progressTracker = new ProgressTracker();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.progressTracker.init();
});
