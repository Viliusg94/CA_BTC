from flask import Blueprint, request, jsonify
import logging

from app.services.model_training_service import training_service

logger = logging.getLogger(__name__)

training_api_v2 = Blueprint('training_api_v2', __name__, url_prefix='/api/training')

@training_api_v2.route('/start', methods=['POST'])
def start_training():
    """Start model training"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        model_type = data.get('model_type')
        if not model_type:
            return jsonify({'success': False, 'error': 'No model type specified'}), 400
        
        # Extract training configuration
        config = {
            'epochs': data.get('epochs', 50),
            'batch_size': data.get('batch_size', 32),
            'learning_rate': data.get('learning_rate', 0.001),
            'sequence_length': data.get('sequence_length', 24),
            'units': data.get('units', 50),
            'dropout': data.get('dropout', 0.2),
            'filters': data.get('filters', 64),
            'kernel_size': data.get('kernel_size', 3),
            'num_heads': data.get('num_heads', 4),
            'd_model': data.get('d_model', 64)
        }
        
        result = training_service.start_training(model_type, config)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@training_api_v2.route('/status/<job_id>')
def get_training_status(job_id):
    """Get training status for a specific job"""
    try:
        status = training_service.get_training_status(job_id)
        if not status:
            return jsonify({'error': 'Job not found'}), 404
        
        # Convert datetime objects to strings for JSON serialization
        status_copy = status.copy()
        for key in ['start_time', 'end_time']:
            if key in status_copy and status_copy[key]:
                status_copy[key] = status_copy[key].isoformat()
        
        return jsonify(status_copy)
        
    except Exception as e:
        logger.error(f"Error getting training status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@training_api_v2.route('/jobs')
def get_all_jobs():
    """Get all training jobs"""
    try:
        jobs = training_service.get_all_training_jobs()
        
        # Convert datetime objects to strings for JSON serialization
        jobs_copy = {}
        for job_id, job_data in jobs.items():
            job_copy = job_data.copy()
            for key in ['start_time', 'end_time']:
                if key in job_copy and job_copy[key]:
                    job_copy[key] = job_copy[key].isoformat()
            jobs_copy[job_id] = job_copy
        
        return jsonify(jobs_copy)
        
    except Exception as e:
        logger.error(f"Error getting training jobs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@training_api_v2.route('/stop/<job_id>', methods=['POST'])
def stop_training(job_id):
    """Stop a training job"""
    try:
        success = training_service.stop_training(job_id)
        if success:
            return jsonify({'success': True, 'message': f'Training job {job_id} stopped'})
        else:
            return jsonify({'success': False, 'error': 'Job not found or already completed'}), 404
            
    except Exception as e:
        logger.error(f"Error stopping training: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@training_api_v2.route('/tensorflow_status')
def tensorflow_status():
    """Check TensorFlow availability"""
    return jsonify({
        'tensorflow_available': training_service.tensorflow_available,
        'models_dir': training_service.models_dir
    })
