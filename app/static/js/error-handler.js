/**
 * Error Handler JavaScript Library
 * Handles client-side error tracking and reporting
 */

class ErrorHandler {
    constructor(options = {}) {
        this.options = Object.assign({
            apiBaseUrl: '/api/progress/errors',
            captureGlobalErrors: true,
            capturePromiseRejections: true,
            captureAjaxErrors: true,
            logToConsole: true,
            maxErrorsStored: 20
        }, options);
        
        this.errors = [];
        this.initialized = false;
    }
    
    /**
     * Initialize the error handler
     */
    init() {
        if (this.initialized) return;
        
        if (this.options.captureGlobalErrors) {
            this.setupGlobalErrorHandler();
        }
        
        if (this.options.capturePromiseRejections) {
            this.setupPromiseRejectionHandler();
        }
        
        if (this.options.captureAjaxErrors) {
            this.setupAjaxErrorHandler();
        }
        
        this.initialized = true;
        console.log('Error handler initialized');
    }
    
    /**
     * Set up global error handler
     */
    setupGlobalErrorHandler() {
        window.onerror = (message, source, lineno, colno, error) => {
            this.logError({
                type: 'global',
                message,
                source,
                lineno,
                colno,
                stack: error?.stack,
                timestamp: new Date().toISOString()
            });
            
            return false; // Let the error propagate
        };
    }
    
    /**
     * Set up promise rejection handler
     */
    setupPromiseRejectionHandler() {
        window.addEventListener('unhandledrejection', event => {
            const error = {
                type: 'promise',
                message: 'Unhandled Promise Rejection',
                reason: event.reason?.toString(),
                timestamp: new Date().toISOString()
            };
            
            if (event.reason instanceof Error) {
                error.stack = event.reason.stack;
            }
            
            this.logError(error);
        });
    }
    
    /**
     * Set up AJAX error handler
     */
    setupAjaxErrorHandler() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    this.logError({
                        type: 'fetch',
                        message: `Fetch error: ${response.status} ${response.statusText}`,
                        url: args[0]?.toString(),
                        status: response.status,
                        timestamp: new Date().toISOString()
                    });
                }
                
                return response;
            } catch (error) {
                this.logError({
                    type: 'fetch',
                    message: `Fetch network error: ${error.message}`,
                    url: args[0]?.toString(),
                    stack: error.stack,
                    timestamp: new Date().toISOString()
                });
                
                throw error;
            }
        };
        
        // Also intercept XHR
        const originalXhrOpen = XMLHttpRequest.prototype.open;
        const originalXhrSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(...args) {
            this._errorHandler_url = args[1];
            return originalXhrOpen.apply(this, args);
        };
        
        XMLHttpRequest.prototype.send = function(...args) {
            this.addEventListener('error', () => {
                errorHandler.logError({
                    type: 'xhr',
                    message: 'XHR network error',
                    url: this._errorHandler_url,
                    timestamp: new Date().toISOString()
                });
            });
            
            this.addEventListener('load', () => {
                if (this.status >= 400) {
                    errorHandler.logError({
                        type: 'xhr',
                        message: `XHR error: ${this.status}`,
                        url: this._errorHandler_url,
                        status: this.status,
                        timestamp: new Date().toISOString()
                    });
                }
            });
            
            return originalXhrSend.apply(this, args);
        };
    }
    
    /**
     * Log an error
     * @param {Object} error - Error information
     */
    logError(error) {
        // Add to local array
        this.errors.push(error);
        
        // Trim array if needed
        if (this.errors.length > this.options.maxErrorsStored) {
            this.errors.shift();
        }
        
        // Log to console if enabled
        if (this.options.logToConsole) {
            console.error('Error captured:', error);
        }
        
        // Send to server
        this.sendErrorToServer(error);
        
        // Create alert if DOM element exists
        this.createErrorAlert(error);
    }
    
    /**
     * Send error to server
     * @param {Object} error - Error information
     */
    sendErrorToServer(error) {
        try {
            fetch(`${this.options.apiBaseUrl}/report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    error_type: error.type,
                    message: error.message,
                    source: 'client',
                    details: {
                        url: window.location.href,
                        userAgent: navigator.userAgent,
                        ...error
                    }
                })
            }).catch(e => {
                console.error('Failed to send error to server:', e);
            });
        } catch (e) {
            console.error('Error sending error to server:', e);
        }
    }
    
    /**
     * Create an error alert in the UI
     * @param {Object} error - Error information
     */
    createErrorAlert(error) {
        // Check if alerts container exists
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;
        
        const alertElement = document.createElement('div');
        alertElement.className = 'alert alert-danger alert-dismissible fade show';
        alertElement.role = 'alert';
        
        alertElement.innerHTML = `
            <strong>Error:</strong> ${error.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertsContainer.appendChild(alertElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alertElement.classList.remove('show');
            setTimeout(() => {
                alertElement.remove();
            }, 150);
        }, 5000);
    }
    
    /**
     * Get all errors
     * @returns {Array} Array of errors
     */
    getErrors() {
        return [...this.errors];
    }
    
    /**
     * Clear all errors
     */
    clearErrors() {
        this.errors = [];
    }
}

// Create a global instance
window.errorHandler = new ErrorHandler();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.errorHandler.init();
});
