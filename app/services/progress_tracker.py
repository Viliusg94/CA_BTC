"""
Progress tracking service for long-running operations
"""
import logging
import threading
import time
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Track progress of long-running operations like model training"""
    
    def __init__(self):
        self.progress_data = {}
        self.lock = threading.Lock()
        self.app = None
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        logger.info("Progress tracker initialized")
        
    def start_tracking(self, task_id, task_type, total_steps=100, metadata=None):
        """Start tracking a new task"""
        with self.lock:
            self.progress_data[task_id] = {
                'task_id': task_id,
                'task_type': task_type,
                'status': 'running',
                'progress': 0,
                'current_step': 0,
                'total_steps': total_steps,
                'start_time': time.time(),
                'last_update_time': time.time(),
                'estimated_completion': None,
                'metadata': metadata or {},
                'message': 'Task started'
            }
            
        logger.info(f"Started tracking task {task_id} ({task_type})")
        return True
    
    def update_progress(self, task_id, current_step=None, message=None, status=None, metadata=None):
        """Update progress for a task"""
        with self.lock:
            if task_id not in self.progress_data:
                logger.warning(f"Attempted to update non-existent task {task_id}")
                return False
            
            task = self.progress_data[task_id]
            
            # Update current step if provided
            if current_step is not None:
                task['current_step'] = current_step
                task['progress'] = min(100, int((current_step / task['total_steps']) * 100))
            
            # Update message if provided
            if message is not None:
                task['message'] = message
                
            # Update status if provided
            if status is not None:
                task['status'] = status
                
            # Update metadata if provided
            if metadata is not None:
                if not task.get('metadata'):
                    task['metadata'] = {}
                task['metadata'].update(metadata)
                
            # Update timing information
            current_time = time.time()
            task['last_update_time'] = current_time
            
            # Calculate estimated completion time
            if task['current_step'] > 0 and task['total_steps'] > 0:
                elapsed_time = current_time - task['start_time']
                steps_remaining = task['total_steps'] - task['current_step']
                time_per_step = elapsed_time / task['current_step']
                estimated_remaining = time_per_step * steps_remaining
                task['estimated_completion'] = current_time + estimated_remaining
            
        return True
    
    def complete_task(self, task_id, success=True, message=None, metadata=None):
        """Mark a task as completed"""
        with self.lock:
            if task_id not in self.progress_data:
                logger.warning(f"Attempted to complete non-existent task {task_id}")
                return False
            
            task = self.progress_data[task_id]
            task['status'] = 'completed' if success else 'failed'
            task['progress'] = 100 if success else task['progress']
            task['end_time'] = time.time()
            task['duration'] = task['end_time'] - task['start_time']
            
            if message is not None:
                task['message'] = message
                
            if metadata is not None:
                if not task.get('metadata'):
                    task['metadata'] = {}
                task['metadata'].update(metadata)
                
        logger.info(f"Task {task_id} marked as {'completed' if success else 'failed'}")
        return True
    
    def get_task_progress(self, task_id):
        """Get progress information for a task"""
        with self.lock:
            if task_id not in self.progress_data:
                return None
            
            # Return a copy to avoid concurrency issues
            return dict(self.progress_data[task_id])
    
    def get_all_tasks(self, active_only=False):
        """Get all tasks, optionally filtering to active only"""
        with self.lock:
            if active_only:
                return {
                    task_id: dict(task) 
                    for task_id, task in self.progress_data.items() 
                    if task['status'] in ['running', 'paused']
                }
            else:
                return {task_id: dict(task) for task_id, task in self.progress_data.items()}
    
    def clean_old_tasks(self, max_age_hours=24):
        """Remove completed tasks older than the specified age"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.lock:
            to_remove = []
            for task_id, task in self.progress_data.items():
                if task['status'] in ['completed', 'failed']:
                    if 'end_time' in task and (current_time - task['end_time']) > max_age_seconds:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.progress_data[task_id]
                
        logger.info(f"Cleaned {len(to_remove)} old tasks")
        return len(to_remove)
    
    def serialize_progress(self, task_id):
        """Serialize progress data to JSON-compatible format"""
        with self.lock:
            if task_id not in self.progress_data:
                return None
            
            task = dict(self.progress_data[task_id])
            
            # Convert times to ISO format for JSON
            if 'start_time' in task:
                task['start_time_iso'] = datetime.fromtimestamp(task['start_time']).isoformat()
            if 'last_update_time' in task:
                task['last_update_time_iso'] = datetime.fromtimestamp(task['last_update_time']).isoformat()
            if 'end_time' in task:
                task['end_time_iso'] = datetime.fromtimestamp(task['end_time']).isoformat()
            if 'estimated_completion' in task and task['estimated_completion']:
                task['estimated_completion_iso'] = datetime.fromtimestamp(task['estimated_completion']).isoformat()
                
            return task

# Create a singleton instance
progress_tracker = ProgressTracker()
