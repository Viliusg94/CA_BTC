"""
API endpoints for progress tracking
"""
import logging
import time
from flask import Blueprint, jsonify, request, current_app
from app.services.progress_tracker import progress_tracker
from app.services.error_handler import error_handler

logger = logging.getLogger(__name__)

progress_api = Blueprint('progress_api', __name__)

@progress_api.route('/api/progress/tasks', methods=['GET'])
def get_all_tasks():
    """Get all tasks with progress information"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        tasks = progress_tracker.get_all_tasks(active_only=active_only)
        
        # Convert to list for JSON response
        task_list = []
        for task_id, task in tasks.items():
            task_data = dict(task)
            
            # Format times for display
            if 'start_time' in task_data:
                task_data['start_time_formatted'] = time.strftime(
                    '%Y-%m-%d %H:%M:%S', 
                    time.localtime(task_data['start_time'])
                )
            if 'last_update_time' in task_data:
                task_data['last_update_time_formatted'] = time.strftime(
                    '%Y-%m-%d %H:%M:%S', 
                    time.localtime(task_data['last_update_time'])
                )
            
            task_list.append(task_data)
        
        return jsonify({
            'success': True,
            'tasks': task_list,
            'count': len(task_list)
        })
    except Exception as e:
        error_id = error_handler.log_exception(e, source='progress_api.get_all_tasks')
        logger.error(f"Error getting tasks: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_id': error_id
        }), 500

@progress_api.route('/api/progress/task/<task_id>', methods=['GET'])
def get_task_progress(task_id):
    """Get progress information for a specific task"""
    try:
        task = progress_tracker.get_task_progress(task_id)
        if not task:
            return jsonify({
                'success': False,
                'error': f'Task {task_id} not found'
            }), 404
        
        # Format times for display
        task_data = dict(task)
        if 'start_time' in task_data:
            task_data['start_time_formatted'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(task_data['start_time'])
            )
        if 'last_update_time' in task_data:
            task_data['last_update_time_formatted'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(task_data['last_update_time'])
            )
        if 'estimated_completion' in task_data and task_data['estimated_completion']:
            task_data['estimated_completion_formatted'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(task_data['estimated_completion'])
            )
        
        return jsonify({
            'success': True,
            'task': task_data
        })
    except Exception as e:
        error_id = error_handler.log_exception(e, source='progress_api.get_task_progress')
        logger.error(f"Error getting task progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_id': error_id
        }), 500

@progress_api.route('/api/progress/task/<task_id>', methods=['POST'])
def update_task_progress(task_id):
    """Update progress for a task - protected endpoint for internal use"""
    try:
        # Verify API key for security
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('INTERNAL_API_KEY', 'default_key'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 401
        
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract update parameters
        current_step = data.get('current_step')
        message = data.get('message')
        status = data.get('status')
        metadata = data.get('metadata')
        
        # Update progress
        result = progress_tracker.update_progress(
            task_id, 
            current_step=current_step,
            message=message,
            status=status,
            metadata=metadata
        )
        
        if not result:
            return jsonify({
                'success': False,
                'error': f'Failed to update task {task_id}'
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'Task {task_id} updated successfully'
        })
    except Exception as e:
        error_id = error_handler.log_exception(e, source='progress_api.update_task_progress')
        logger.error(f"Error updating task progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_id': error_id
        }), 500

@progress_api.route('/api/progress/task/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed - protected endpoint for internal use"""
    try:
        # Verify API key for security
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('INTERNAL_API_KEY', 'default_key'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 401
        
        data = request.json or {}
        success = data.get('success', True)
        message = data.get('message')
        metadata = data.get('metadata')
        
        # Complete the task
        result = progress_tracker.complete_task(
            task_id,
            success=success,
            message=message,
            metadata=metadata
        )
        
        if not result:
            return jsonify({
                'success': False,
                'error': f'Failed to complete task {task_id}'
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'Task {task_id} marked as {"completed" if success else "failed"}'
        })
    except Exception as e:
        error_id = error_handler.log_exception(e, source='progress_api.complete_task')
        logger.error(f"Error completing task: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_id': error_id
        }), 500

@progress_api.route('/api/progress/task/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task from progress tracking - admin only"""
    try:
        # Verify admin API key for security
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('ADMIN_API_KEY', 'admin_key'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 401
        
        with progress_tracker.lock:
            if task_id not in progress_tracker.progress_data:
                return jsonify({
                    'success': False,
                    'error': f'Task {task_id} not found'
                }), 404
            
            del progress_tracker.progress_data[task_id]
        
        return jsonify({
            'success': True,
            'message': f'Task {task_id} deleted successfully'
        })
    except Exception as e:
        error_id = error_handler.log_exception(e, source='progress_api.delete_task')
        logger.error(f"Error deleting task: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_id': error_id
        }), 500

@progress_api.route('/api/progress/errors', methods=['GET'])
def get_errors():
    """Get recent errors - admin only"""
    try:
        # Verify admin API key for security
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('ADMIN_API_KEY', 'admin_key'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 401
        
        limit = request.args.get('limit', 10, type=int)
        error_type = request.args.get('type')
        source = request.args.get('source')
        
        errors = error_handler.get_recent_errors(limit=limit, error_type=error_type, source=source)
        
        # Format timestamps for display
        for error in errors:
            if 'timestamp' in error:
                error['timestamp_formatted'] = time.strftime(
                    '%Y-%m-%d %H:%M:%S', 
                    time.localtime(error['timestamp'])
                )
        
        return jsonify({
            'success': True,
            'errors': errors,
            'count': len(errors)
        })
    except Exception as e:
        error_id = error_handler.log_exception(e, source='progress_api.get_errors')
        logger.error(f"Error getting errors: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_id': error_id
        }), 500

@progress_api.route('/api/progress/errors/summary', methods=['GET'])
def get_error_summary():
    """Get error summary - viewable by all users"""
    try:
        summary = error_handler.summarize_errors()
        
        # Format timestamps for display
        for error in summary.get('recent_errors', []):
            if 'timestamp' in error:
                error['timestamp_formatted'] = time.strftime(
                    '%Y-%m-%d %H:%M:%S', 
                    time.localtime(error['timestamp'])
                )
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        error_id = error_handler.log_exception(e, source='progress_api.get_error_summary')
        logger.error(f"Error getting error summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_id': error_id
        }), 500
