from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
import logging
import threading
import time
import json
from datetime import datetime
from app.services.real_training_service import real_training_service

logger = logging.getLogger(__name__)

real_training_api = Blueprint('real_training_api', __name__, url_prefix='/api')

# In-memory storage for training sessions (for demonstration purposes)
training_sessions = {}

def run_training_session(training_id, model_type, config):
    """Run a training session (to be executed in a separate thread)"""
    try:
        # Update session status to 'training'
        training_sessions[training_id]['status'] = 'training'
        
        # Simulate training process
        for epoch in range(1, config['epochs'] + 1):
            # Check if stop was requested
            if training_sessions[training_id].get('stop_requested'):
                training_sessions[training_id]['status'] = 'stopped'
                logger.info(f"Training session {training_id} stopped by user")
                return
            
            # Update current epoch
            training_sessions[training_id]['current_epoch'] = epoch
            
            # Simulate epoch training time
            time.sleep(1)
            
            # Log epoch completion
            logger.info(f"Training session {training_id}: Completed epoch {epoch}/{config['epochs']}")
        
        # Update session status to 'completed'
        training_sessions[training_id]['status'] = 'completed'
        logger.info(f"Training session {training_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in training session {training_id}: {e}")
        training_sessions[training_id]['status'] = 'error'
        training_sessions[training_id]['error'] = str(e)

@real_training_api.route('/start', methods=['POST'])
def start_training():
    """Start model training"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        model_type = data.get('model_type', 'lstm').lower()
        config = {
            'epochs': int(data.get('epochs', 50)),
            'batch_size': int(data.get('batch_size', 32)),
            'learning_rate': float(data.get('learning_rate', 0.001)),
            'lookback': int(data.get('lookback', 24))
        }
        
        # Generate training ID
        training_id = f"{model_type}_{int(time.time())}"
        
        # Store training configuration
        training_sessions[training_id] = {
            'model_type': model_type,
            'config': config,
            'status': 'starting',
            'progress': 0,
            'start_time': datetime.now().isoformat(),
            'logs': [],
            'current_epoch': 0,
            'total_epochs': config['epochs'],
            'metrics': {}
        }
        
        # Start training in background thread
        thread = threading.Thread(
            target=run_training_session,
            args=(training_id, model_type, config)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started training session {training_id} for {model_type}")
        
        # If this is a form submission (from web interface), redirect to status page
        if request.form:
            return redirect(url_for('real_training_api.training_status', training_id=training_id))
        
        # If this is an API call, return JSON
        return jsonify({
            'success': True,
            'training_id': training_id,
            'model_type': model_type,
            'config': config,
            'message': f'Training started for {model_type.upper()} model',
            'status_url': f'/api/real_training/status/{training_id}'
        })
        
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@real_training_api.route('/status/<training_id>')
def training_status(training_id):
    """Show training status page"""
    try:
        if training_id not in training_sessions:
            return render_template('error.html', error=f"Training session {training_id} not found"), 404
        
        session = training_sessions[training_id]
        
        return render_template('training_status_live.html', 
                             training_id=training_id,
                             session=session,
                             model_type=session['model_type'],
                             config=session['config'])
        
    except Exception as e:
        logger.error(f"Error showing training status: {e}")
        return render_template('error.html', error=str(e)), 500

@real_training_api.route('/stop/<training_id>', methods=['POST'])
def stop_training(training_id):
    """Stop training session"""
    try:
        if training_id not in training_sessions:
            return jsonify({'success': False, 'error': 'Training session not found'}), 404
        
        # Mark session for stopping
        training_sessions[training_id]['status'] = 'stopping'
        training_sessions[training_id]['stop_requested'] = True
        
        logger.info(f"Stop requested for training session {training_id}")
        
        return jsonify({
            'success': True,
            'message': f'Stop requested for training session {training_id}'
        })
        
    except Exception as e:
        logger.error(f"Error stopping training: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@real_training_api.route('/start_real_training', methods=['POST'])
def start_real_training():
    """Start real model training"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        model_type = data.get('model_type')
        if not model_type:
            return jsonify({'success': False, 'error': 'Model type is required'}), 400
        
        # Training configuration
        config = {
            'epochs': data.get('epochs', 50),
            'batch_size': data.get('batch_size', 32),
            'learning_rate': data.get('learning_rate', 0.001),
            'sequence_length': data.get('sequence_length', 24),
            'dropout': data.get('dropout', 0.2),
            'units': data.get('units', 50),
            'data_days': data.get('data_days', 365),
        }
        
        # Model-specific parameters
        if model_type.lower() == 'cnn':
            config.update({
                'filters': data.get('filters', 64),
                'kernel_size': data.get('kernel_size', 3)
            })
        elif model_type.lower() == 'transformer':
            config.update({
                'num_heads': data.get('num_heads', 8),
                'key_dim': data.get('key_dim', 64),
                'ff_dim': data.get('ff_dim', 256)
            })
        
        # Start training
        job_id = real_training_service.start_training(model_type, config)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Started real training for {model_type}',
            'config': config
        })
        
    except Exception as e:
        logger.error(f"Error starting real training: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@real_training_api.route('/stop_training/<job_id>', methods=['POST'])
def stop_training_job(job_id):
    """Stop training for a specific job"""
    try:
        success = real_training_service.stop_training(job_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Stop signal sent for job {job_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Job {job_id} not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error stopping training: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@real_training_api.route('/training_status/<job_id>', methods=['GET'])
def get_training_status(job_id):
    """Get training status for a specific job"""
    try:
        status = real_training_service.get_training_status(job_id)
        
        if status:
            # Convert datetime objects to strings for JSON serialization
            status_copy = status.copy()
            for key in ['start_time', 'end_time', 'last_update']:
                if key in status_copy and status_copy[key]:
                    status_copy[key] = status_copy[key].isoformat()
            
            # Remove thread object from response
            if 'thread' in status_copy:
                del status_copy['thread']
            
            return jsonify({
                'success': True,
                'status': status_copy
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Job {job_id} not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@real_training_api.route('/all_training_jobs', methods=['GET'])
def get_all_training_jobs():
    """Get all training jobs"""
    try:
        all_jobs = real_training_service.get_all_training_jobs()
        
        # Convert datetime objects and remove thread objects
        jobs_response = {}
        for job_id, job_data in all_jobs.items():
            job_copy = job_data.copy()
            
            # Convert datetime objects
            for key in ['start_time', 'end_time', 'last_update']:
                if key in job_copy and job_copy[key]:
                    job_copy[key] = job_copy[key].isoformat()
            
            # Remove thread object
            if 'thread' in job_copy:
                del job_copy['thread']
            
            jobs_response[job_id] = job_copy
        
        return jsonify({
            'success': True,
            'jobs': jobs_response
        })
        
    except Exception as e:
        logger.error(f"Error getting all training jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@real_training_api.route('/active_training_jobs', methods=['GET'])
def get_active_training_jobs():
    """Get only active training jobs"""
    try:
        all_jobs = real_training_service.get_all_training_jobs()
        
        # Filter active jobs
        active_jobs = {}
        for job_id, job_data in all_jobs.items():
            if job_data.get('status') in ['initializing', 'data_preparation', 'training']:
                job_copy = job_data.copy()
                
                # Convert datetime objects
                for key in ['start_time', 'end_time', 'last_update']:
                    if key in job_copy and job_copy[key]:
                        job_copy[key] = job_copy[key].isoformat()
                
                # Remove thread object
                if 'thread' in job_copy:
                    del job_copy['thread']
                
                active_jobs[job_id] = job_copy
        
        return jsonify({
            'success': True,
            'jobs': active_jobs
        })
        
    except Exception as e:
        logger.error(f"Error getting active training jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@real_training_api.route('/api/stop_training/<model_type>', methods=['POST'])
def stop_training_api(model_type):
    """API endpoint to stop training for a specific model"""
    try:
        logger.info(f"Request to stop training for model type: {model_type}")
        
        # Get the model manager
        if hasattr(current_app, 'model_manager'):
            model_manager = current_app.model_manager
        else:
            # Try to import from app
            try:
                from app.app import model_manager
            except ImportError:
                model_manager = None
        
        if not model_manager:
            logger.error("Model manager not available")
            return jsonify({
                'success': False,
                'error': 'Model manager not available'
            }), 500
            
        # Try to stop the training
        result = model_manager.stop_training(model_type)
        
        if isinstance(result, dict) and result.get('success', False):
            logger.info(f"Successfully stopped training for {model_type}")
            return jsonify({
                'success': True,
                'message': f"Training stopped for {model_type} model"
            })
        else:
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else 'Failed to stop training'
            logger.error(f"Failed to stop training: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping training: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
