"""
Enhanced training routes with progress tracking and error handling
"""
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app.services.enhanced_model_service import enhanced_model_service
from app.services.progress_tracker import progress_tracker
from app.services.error_handler import handle_api_errors, handle_route_errors, ErrorCategory
import logging

logger = logging.getLogger(__name__)

enhanced_training = Blueprint('enhanced_training', __name__, url_prefix='/training')

@enhanced_training.route('/')
@handle_route_errors(ErrorCategory.SYSTEM, redirect_to='index')
def training_dashboard():
    """Enhanced training dashboard with progress tracking"""
    try:
        # Get all active training tasks
        all_progress = progress_tracker.get_all_progress()
        training_tasks = {
            task_id: progress for task_id, progress in all_progress.items()
            if progress.get('metadata', {}).get('model_type')
        }
        
        return render_template('training/enhanced_dashboard.html', 
                             training_tasks=training_tasks)
    except Exception as e:
        logger.error(f"Error loading training dashboard: {e}")
        flash("Error loading training dashboard", "error")
        return redirect(url_for('index'))

@enhanced_training.route('/start', methods=['POST'])
@handle_api_errors(ErrorCategory.MODEL)
def start_training():
    """Start model training with progress tracking"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No training configuration provided'
        }), 400
    
    model_type = data.get('model_type')
    config = data.get('config', {})
    
    if not model_type:
        return jsonify({
            'success': False,
            'error': 'Model type is required'
        }), 400
    
    # Validate model type
    valid_types = ['lstm', 'gru', 'cnn', 'transformer']
    if model_type.lower() not in valid_types:
        return jsonify({
            'success': False,
            'error': f'Invalid model type. Must be one of: {", ".join(valid_types)}'
        }), 400
    
    try:
        # Start training with progress tracking
        task_id = enhanced_model_service.train_model_with_progress(model_type, config)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'Training started for {model_type.upper()} model'
        })
    
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_training.route('/stop/<task_id>', methods=['POST'])
@handle_api_errors(ErrorCategory.MODEL)
def stop_training(task_id):
    """Stop model training"""
    try:
        # Get current progress
        progress = progress_tracker.get_progress(task_id)
        
        if not progress:
            return jsonify({
                'success': False,
                'error': 'Training task not found'
            }), 404
        
        if progress.get('status') not in ['starting', 'running']:
            return jsonify({
                'success': False,
                'error': 'Training is not currently running'
            }), 400
        
        # Set task as stopped
        progress_tracker.set_error(
            task_id,
            "Training stopped by user",
            "User requested training termination"
        )
        
        return jsonify({
            'success': True,
            'message': 'Training stopped successfully'
        })
    
    except Exception as e:
        logger.error(f"Error stopping training: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_training.route('/validate', methods=['POST'])
@handle_api_errors(ErrorCategory.VALIDATION)
def validate_config():
    """Validate training configuration"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No configuration provided'
        }), 400
    
    model_type = data.get('model_type')
    config = data.get('config', {})
    
    # Validation rules
    validation_errors = []
    
    # Model type validation
    if not model_type:
        validation_errors.append('Model type is required')
    elif model_type.lower() not in ['lstm', 'gru', 'cnn', 'transformer']:
        validation_errors.append('Invalid model type')
    
    # Configuration validation
    if 'epochs' in config:
        try:
            epochs = int(config['epochs'])
            if epochs <= 0 or epochs > 1000:
                validation_errors.append('Epochs must be between 1 and 1000')
        except (ValueError, TypeError):
            validation_errors.append('Epochs must be a valid integer')
    
    if 'batch_size' in config:
        try:
            batch_size = int(config['batch_size'])
            if batch_size <= 0 or batch_size > 256:
                validation_errors.append('Batch size must be between 1 and 256')
        except (ValueError, TypeError):
            validation_errors.append('Batch size must be a valid integer')
    
    if 'learning_rate' in config:
        try:
            learning_rate = float(config['learning_rate'])
            if learning_rate <= 0 or learning_rate > 1:
                validation_errors.append('Learning rate must be between 0 and 1')
        except (ValueError, TypeError):
            validation_errors.append('Learning rate must be a valid number')
    
    if validation_errors:
        return jsonify({
            'success': False,
            'errors': validation_errors
        }), 400
    
    return jsonify({
        'success': True,
        'message': 'Configuration is valid'
    })
