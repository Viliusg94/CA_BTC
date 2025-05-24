"""
Error handling service for capturing and managing errors
"""
import logging
import threading
import time
import json
import os
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handle and track errors across the application"""
    
    def __init__(self):
        self.errors = {}
        self.lock = threading.Lock()
        self.app = None
        self.max_errors = 100  # Maximum number of errors to keep
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        logger.info("Error handler initialized")
        
    def log_error(self, error_type, message, source=None, details=None, context=None):
        """Log an error with details"""
        error_id = str(int(time.time() * 1000))  # Timestamp-based ID
        
        error_data = {
            'error_id': error_id,
            'error_type': error_type,
            'message': message,
            'timestamp': time.time(),
            'source': source or 'unknown',
            'details': details or {},
            'context': context or {},
            'stack_trace': traceback.format_exc() if error_type == 'exception' else None
        }
        
        with self.lock:
            self.errors[error_id] = error_data
            
            # Trim if we have too many errors
            if len(self.errors) > self.max_errors:
                # Remove oldest errors
                sorted_ids = sorted(self.errors.keys(), 
                                   key=lambda k: self.errors[k]['timestamp'])
                for old_id in sorted_ids[:len(sorted_ids) - self.max_errors]:
                    del self.errors[old_id]
        
        # Log to the application logger
        log_message = f"ERROR [{error_type}] {message}"
        if source:
            log_message += f" (source: {source})"
            
        logger.error(log_message)
        if error_type == 'exception' and error_data['stack_trace']:
            logger.error(error_data['stack_trace'])
            
        return error_id
    
    def log_exception(self, exception, source=None, context=None):
        """Log an exception"""
        return self.log_error(
            'exception', 
            str(exception), 
            source=source, 
            details={'exception_type': type(exception).__name__},
            context=context
        )
    
    def get_error(self, error_id):
        """Get details for a specific error"""
        with self.lock:
            if error_id in self.errors:
                return dict(self.errors[error_id])
            return None
    
    def get_recent_errors(self, limit=10, error_type=None, source=None):
        """Get recent errors, optionally filtered by type or source"""
        with self.lock:
            filtered_errors = []
            
            for error in sorted(
                self.errors.values(), 
                key=lambda e: e['timestamp'], 
                reverse=True
            ):
                if error_type and error['error_type'] != error_type:
                    continue
                if source and error['source'] != source:
                    continue
                
                filtered_errors.append(dict(error))
                if len(filtered_errors) >= limit:
                    break
                    
            return filtered_errors
    
    def clear_errors(self, older_than=None):
        """Clear all errors or only those older than a certain time"""
        with self.lock:
            if older_than is None:
                # Clear all errors
                count = len(self.errors)
                self.errors = {}
                return count
            else:
                # Clear only old errors
                cutoff_time = time.time() - older_than
                to_remove = [
                    error_id for error_id, error in self.errors.items()
                    if error['timestamp'] < cutoff_time
                ]
                
                for error_id in to_remove:
                    del self.errors[error_id]
                    
                return len(to_remove)
    
    def summarize_errors(self):
        """Generate a summary of recent errors"""
        with self.lock:
            if not self.errors:
                return {
                    'total_errors': 0,
                    'error_types': {},
                    'sources': {},
                    'recent_errors': []
                }
            
            # Count by type and source
            error_types = {}
            sources = {}
            
            for error in self.errors.values():
                error_type = error['error_type']
                source = error['source']
                
                if error_type in error_types:
                    error_types[error_type] += 1
                else:
                    error_types[error_type] = 1
                    
                if source in sources:
                    sources[source] += 1
                else:
                    sources[source] = 1
            
            # Get 5 most recent errors
            recent_errors = []
            for error in sorted(
                self.errors.values(), 
                key=lambda e: e['timestamp'], 
                reverse=True
            )[:5]:
                recent_errors.append({
                    'error_id': error['error_id'],
                    'error_type': error['error_type'],
                    'message': error['message'],
                    'timestamp': error['timestamp'],
                    'source': error['source']
                })
                
            return {
                'total_errors': len(self.errors),
                'error_types': error_types,
                'sources': sources,
                'recent_errors': recent_errors
            }
    
    def get_error_count(self, hours=24, error_type=None, source=None):
        """Get count of errors in the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self.lock:
            count = 0
            for error in self.errors.values():
                if error['timestamp'] < cutoff_time:
                    continue
                if error_type and error['error_type'] != error_type:
                    continue
                if source and error['source'] != source:
                    continue
                count += 1
                
            return count

# Create a singleton instance
error_handler = ErrorHandler()
