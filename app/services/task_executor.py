"""
Užduočių vykdymo mechanizmas - atsakingas už automatinį užduočių vykdymą pagal tvarkaraštį
"""
import threading
import queue
import logging
import time
import traceback
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: int = 0
    max_retries: int = 3
    retry_delay: int = 5
    timeout: int = 3600  # 1 hour default
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}

class TaskResult:
    def __init__(self, task_id: str, status: TaskStatus, result: Any = None, 
                 error: Exception = None, start_time: datetime = None, 
                 end_time: datetime = None, retries: int = 0):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.start_time = start_time
        self.end_time = end_time
        self.retries = retries
        self.duration = None
        
        if start_time and end_time:
            self.duration = (end_time - start_time).total_seconds()

class TaskExecutor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.task_queue = queue.PriorityQueue()
        self.results = {}
        self.running_tasks = {}
        self.workers = []
        self.shutdown_event = threading.Event()
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_cancelled': 0,
            'total_tasks': 0
        }
        
    def submit_task(self, task: Task) -> str:
        """Submit a task for execution with error handling"""
        try:
            # Generate unique task ID
            task_id = f"{task.name}_{int(time.time())}_{id(task)}"
            task.id = task_id
            
            # Add to queue (priority queue uses negative priority for max-heap behavior)
            self.task_queue.put((-task.priority, time.time(), task))
            
            # Initialize result
            self.results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.PENDING
            )
            
            self.stats['total_tasks'] += 1
            logger.info(f"Task {task_id} ({task.name}) submitted to queue")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error submitting task {task.name}: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get task status with error handling"""
        try:
            return self.results.get(task_id)
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e}")
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task if possible"""
        try:
            if task_id in self.results:
                result = self.results[task_id]
                if result.status == TaskStatus.PENDING:
                    result.status = TaskStatus.CANCELLED
                    self.stats['tasks_cancelled'] += 1
                    logger.info(f"Task {task_id} cancelled")
                    return True
                elif result.status == TaskStatus.RUNNING:
                    # Mark for cancellation (actual cancellation depends on task implementation)
                    logger.warning(f"Task {task_id} is running, marked for cancellation")
                    return False
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    def _worker(self, worker_id: int):
        """Worker thread with comprehensive error handling"""
        logger.info(f"Worker {worker_id} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get task from queue with timeout
                try:
                    _, _, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Check if task was cancelled
                if task.id in self.results and self.results[task.id].status == TaskStatus.CANCELLED:
                    logger.info(f"Skipping cancelled task {task.id}")
                    self.task_queue.task_done()
                    continue
                
                # Execute task with retry logic
                self._execute_task_with_retries(task, worker_id)
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                # Continue working despite errors
                
        logger.info(f"Worker {worker_id} stopped")
    
    def _execute_task_with_retries(self, task: Task, worker_id: int):
        """Execute task with retry logic and comprehensive error handling"""
        result = self.results[task.id]
        retry_count = 0
        
        while retry_count <= task.max_retries:
            try:
                # Update status
                result.status = TaskStatus.RUNNING
                result.start_time = datetime.now()
                result.retries = retry_count
                self.running_tasks[task.id] = (task, worker_id)
                
                logger.info(f"Worker {worker_id} executing task {task.id} (attempt {retry_count + 1})")
                
                # Execute task with timeout
                task_result = self._execute_with_timeout(task)
                
                # Task completed successfully
                result.status = TaskStatus.COMPLETED
                result.result = task_result
                result.end_time = datetime.now()
                result.duration = (result.end_time - result.start_time).total_seconds()
                
                self.stats['tasks_completed'] += 1
                logger.info(f"Task {task.id} completed successfully in {result.duration:.2f}s")
                
                # Broadcast success if websocket is available
                self._broadcast_task_update(task.id, result)
                break
                
            except TimeoutError as e:
                retry_count += 1
                error_msg = f"Task {task.id} timed out (attempt {retry_count})"
                logger.warning(error_msg)
                
                if retry_count > task.max_retries:
                    self._handle_task_failure(task, result, e, "Timeout after retries")
                    break
                else:
                    logger.info(f"Retrying task {task.id} in {task.retry_delay} seconds")
                    time.sleep(task.retry_delay)
                    
            except Exception as e:
                retry_count += 1
                error_msg = f"Task {task.id} failed (attempt {retry_count}): {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                if retry_count > task.max_retries:
                    self._handle_task_failure(task, result, e, "Max retries exceeded")
                    break
                else:
                    logger.info(f"Retrying task {task.id} in {task.retry_delay} seconds")
                    time.sleep(task.retry_delay)
            
            finally:
                # Clean up running tasks
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
    
    def _execute_with_timeout(self, task: Task):
        """Execute task with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Task {task.id} exceeded timeout of {task.timeout} seconds")
        
        # Set timeout (Unix systems only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(task.timeout)
        
        try:
            result = task.func(*task.args, **task.kwargs)
            return result
        finally:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel alarm
                signal.signal(signal.SIGALRM, old_handler)  # Restore old handler
    
    def _handle_task_failure(self, task: Task, result: TaskResult, error: Exception, reason: str):
        """Handle task failure with comprehensive logging and notifications"""
        result.status = TaskStatus.FAILED
        result.error = error
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds()
        
        self.stats['tasks_failed'] += 1
        
        error_details = {
            'task_id': task.id,
            'task_name': task.name,
            'reason': reason,
            'error': str(error),
            'traceback': traceback.format_exc(),
            'retries': result.retries,
            'duration': result.duration
        }
        
        logger.error(f"Task {task.id} failed permanently: {reason}", extra=error_details)
        
        # Broadcast failure if websocket is available
        self._broadcast_task_update(task.id, result)
        
        # Could add email notifications, Slack alerts, etc. here
        self._notify_task_failure(error_details)
    
    def _broadcast_task_update(self, task_id: str, result: TaskResult):
        """Broadcast task updates via WebSocket"""
        try:
            from app.services.websocket_service import websocket_manager
            
            websocket_manager.socketio.emit('task_update', {
                'task_id': task_id,
                'status': result.status.value,
                'duration': result.duration,
                'error': str(result.error) if result.error else None,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error broadcasting task update: {e}")
    
    def _notify_task_failure(self, error_details: dict):
        """Send notifications about task failures"""
        try:
            # Could implement email, Slack, or other notifications here
            logger.critical(f"TASK FAILURE NOTIFICATION: {error_details['task_name']} failed")
            
        except Exception as e:
            logger.error(f"Error sending failure notification: {e}")
    
    def start(self):
        """Start the task executor"""
        try:
            if self.workers:
                logger.warning("Task executor already started")
                return
            
            logger.info(f"Starting task executor with {self.max_workers} workers")
            
            for i in range(self.max_workers):
                worker = threading.Thread(target=self._worker, args=(i,), daemon=True)
                worker.start()
                self.workers.append(worker)
            
            logger.info(f"Task executor started with {len(self.workers)} workers")
            
        except Exception as e:
            logger.error(f"Error starting task executor: {e}")
            raise
    
    def stop(self, timeout: int = 30):
        """Stop the task executor gracefully"""
        try:
            logger.info("Stopping task executor...")
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Wait for workers to finish
            for worker in self.workers:
                worker.join(timeout=timeout)
                if worker.is_alive():
                    logger.warning(f"Worker {worker.name} did not stop gracefully")
            
            self.workers.clear()
            logger.info("Task executor stopped")
            
        except Exception as e:
            logger.error(f"Error stopping task executor: {e}")
    
    def get_stats(self):
        """Get executor statistics"""
        return {
            **self.stats,
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'workers_active': len(self.workers)
        }

# Global instance
task_executor = TaskExecutor()