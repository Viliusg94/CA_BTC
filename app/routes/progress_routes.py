"""
Routes for progress tracking dashboard
"""
import logging
from flask import Blueprint, render_template, redirect, url_for, flash
from app.services.progress_tracker import progress_tracker
from app.services.error_handler import error_handler

logger = logging.getLogger(__name__)

progress_routes = Blueprint('progress', __name__, url_prefix='/progress')

@progress_routes.route('/')
def dashboard():
    """Progress tracking dashboard"""
    try:
        # Get all active tasks
        tasks = progress_tracker.get_all_tasks(active_only=True)
        
        # Get error summary
        error_summary = error_handler.summarize_errors()
        
        return render_template(
            'progress/dashboard.html', 
            tasks=tasks,
            error_summary=error_summary
        )
    except Exception as e:
        logger.error(f"Error in progress dashboard: {e}")
        error_handler.log_exception(e, source='progress_routes.dashboard')
        flash(f"Error loading progress dashboard: {str(e)}", "error")
        return redirect(url_for('index'))

@progress_routes.route('/task/<task_id>')
def task_details(task_id):
    """View details for a specific task"""
    try:
        task = progress_tracker.get_task_progress(task_id)
        if not task:
            flash(f"Task {task_id} not found", "error")
            return redirect(url_for('progress.dashboard'))
        
        return render_template('progress/task_details.html', task=task)
    except Exception as e:
        logger.error(f"Error in task details: {e}")
        error_handler.log_exception(e, source='progress_routes.task_details')
        flash(f"Error loading task details: {str(e)}", "error")
        return redirect(url_for('progress.dashboard'))

@progress_routes.route('/errors')
def error_dashboard():
    """Error monitoring dashboard"""
    try:
        # Get error summary
        error_summary = error_handler.summarize_errors()
        
        # Get recent errors (last 20)
        recent_errors = error_handler.get_recent_errors(limit=20)
        
        return render_template(
            'progress/errors.html', 
            error_summary=error_summary,
            recent_errors=recent_errors
        )
    except Exception as e:
        logger.error(f"Error in error dashboard: {e}")
        error_handler.log_exception(e, source='progress_routes.error_dashboard')
        flash(f"Error loading error dashboard: {str(e)}", "error")
        return redirect(url_for('progress.dashboard'))
