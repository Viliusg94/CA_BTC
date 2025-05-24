"""
API endpoints for model training
"""
from flask import Blueprint, jsonify, request
import logging
import json
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Create the blueprint
training_api = Blueprint('training_api', __name__, url_prefix='/api')

# Global training status storage
training_status = {}
training_threads = {}

def simulate_model_training(model_type, config):
    """Simulate model training process"""
    try:
        total_epochs = config.get('epochs', 50)
        
        # Update status to training
        training_status[model_type] = {
            'status': 'training',
            'progress': 0,
            'current_epoch': 0,
            'total_epochs': total_epochs,
            'start_time': datetime.now().isoformat(),
            'error': None
        }
        
        logger.info(f"Starting simulated training for {model_type}")
        
        # Simulate training epochs
        for epoch in range(1, total_epochs + 1):
            if training_status.get(model_type, {}).get('status') == 'stopped':
                break
                
            # Simulate epoch training time (1-3 seconds per epoch)
            time.sleep(2)
            
            # Update progress
            progress = (epoch / total_epochs) * 100
            training_status[model_type].update({
                'progress': progress,
                'current_epoch': epoch,
                'status': 'training'
            })
            
            logger.info(f"{model_type} training: epoch {epoch}/{total_epochs} ({progress:.1f}%)")
        
        # Check if training was stopped
        if training_status.get(model_type, {}).get('status') == 'stopped':
            training_status[model_type]['status'] = 'stopped'
            logger.info(f"{model_type} training was stopped")
            return
        
        # Simulate saving model
        time.sleep(2)
        
        # Generate mock metrics
        import random
        metrics = {
            'rmse': round(random.uniform(800, 1200), 2),
            'mae': round(random.uniform(600, 900), 2),
            'r2': round(random.uniform(0.75, 0.95), 4),
            'mape': round(random.uniform(2.5, 8.0), 2)
        }
        
        # Update status to completed
        training_status[model_type].update({
            'status': 'completed',
            'progress': 100,
            'current_epoch': total_epochs,
            'end_time': datetime.now().isoformat(),
            'metrics': metrics
        })
        
        logger.info(f"{model_type} training completed successfully")
        
        # Save to database if available
        try:
            from app.app import db, ModelHistory
            with db.app.app_context():
                new_model = ModelHistory(
                    model_type=model_type.upper(),
                    r2=metrics['r2'],
                    mae=metrics['mae'],
                    rmse=metrics['rmse'],
                    epochs=total_epochs,
                    batch_size=config.get('batch_size', 32),
                    learning_rate=config.get('learning_rate', 0.001),
                    is_active=True,
                    timestamp=datetime.now(),
                    training_time=total_epochs * 2,  # Simulated training time
                    model_params=json.dumps(config)
                )
                
                # Deactivate other models of the same type
                ModelHistory.query.filter_by(model_type=model_type.upper(), is_active=True).update({'is_active': False})
                
                db.session.add(new_model)
                db.session.commit()
                logger.info(f"Saved {model_type} model to database")
        except Exception as e:
            logger.error(f"Error saving model to database: {e}")
        
    except Exception as e:
        logger.error(f"Error in {model_type} training: {e}")
        training_status[model_type] = {
            'status': 'failed',
            'progress': 0,
            'error': str(e),
            'end_time': datetime.now().isoformat()
        }

@training_api.route('/start_training', methods=['POST'])
def start_training():
    """Start model training"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        model_type = data.get('model_type')
        if not model_type:
            return jsonify({'success': False, 'error': 'Model type not specified'}), 400
        
        # Check if model is already training
        current_status = training_status.get(model_type, {})
        if current_status.get('status') == 'training':
            return jsonify({'success': False, 'error': f'{model_type} is already training'}), 400
        
        # Validate configuration
        config = {
            'epochs': data.get('epochs', 50),
            'batch_size': data.get('batch_size', 32),
            'learning_rate': data.get('learning_rate', 0.001),
            'sequence_length': data.get('sequence_length', 24)
        }
        
        # Validate parameters
        if not (1 <= config['epochs'] <= 200):
            return jsonify({'success': False, 'error': 'Epochs must be between 1 and 200'}), 400
        
        if config['batch_size'] not in [8, 16, 32, 64, 128]:
            return jsonify({'success': False, 'error': 'Batch size must be 8, 16, 32, 64, or 128'}), 400
        
        # Start training in a separate thread
        training_thread = threading.Thread(
            target=simulate_model_training,
            args=(model_type, config),
            daemon=True
        )
        training_thread.start()
        training_threads[model_type] = training_thread
        
        logger.info(f"Started training for {model_type} with config: {config}")
        
        return jsonify({
            'success': True,
            'message': f'{model_type} training started',
            'model_type': model_type,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@training_api.route('/training_progress')
def get_training_progress():
    """Get training progress for a model"""
    try:
        model_type = request.args.get('model_type')
        if not model_type:
            return jsonify({'success': False, 'error': 'Model type not specified'}), 400
        
        status = training_status.get(model_type, {
            'status': 'idle',
            'progress': 0,
            'current_epoch': 0,
            'total_epochs': 0
        })
        
        return jsonify({
            'success': True,
            'model_type': model_type,
            'status': status.get('status', 'idle'),
            'progress': status.get('progress', 0),
            'current_epoch': status.get('current_epoch', 0),
            'total_epochs': status.get('total_epochs', 0),
            'error': status.get('error'),
            'metrics': status.get('metrics')
        })
        
    except Exception as e:
        logger.error(f"Error getting training progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@training_api.route('/stop_training', methods=['POST'])
def stop_training_endpoint():
    """Stop model training"""
    try:
        data = request.get_json()
        model_type = data.get('model_type') if data else request.args.get('model_type')
        
        if not model_type:
            return jsonify({'success': False, 'error': 'Model type not specified'}), 400
        
        # Update status to stopped
        if model_type in training_status:
            training_status[model_type]['status'] = 'stopped'
            training_status[model_type]['end_time'] = datetime.now().isoformat()
        
        logger.info(f"Stopped training for {model_type}")
        
        return jsonify({
            'success': True,
            'message': f'{model_type} training stopped',
            'model_type': model_type
        })
        
    except Exception as e:
        logger.error(f"Error stopping training: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@training_api.route('/training_status')
def get_all_training_status():
    """Get training status for all models"""
    try:
        return jsonify({
            'success': True,
            'training_status': training_status
        })
        
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@training_api.route('/api/training_status', methods=['GET'])
def get_training_status():
    """API endpoint to get all models training status"""
    try:
        logger.info("Getting training status for all models")
        
        # Get model manager from app
        model_manager = current_app.config.get('MODEL_MANAGER')
        if not model_manager and hasattr(current_app, 'model_manager'):
            model_manager = current_app.model_manager
        
        # Fallback to global if available
        if not model_manager and 'model_manager' in globals():
            model_manager = globals()['model_manager']
        
        if not model_manager:
            logger.warning("ModelManager not found in application context")
            return jsonify({
                'success': False,
                'error': 'ModelManager not available',
                'all_status': {}
            })
        
        # Get all model types
        model_types = ['lstm', 'gru', 'cnn', 'transformer']
        all_status = {}
        training_models = 0
        
        # Get status for each model type
        for model_type in model_types:
            try:
                progress = model_manager.get_training_progress(model_type)
                status = model_manager.get_model_status(model_type)
                
                # Determine if training
                is_training = (
                    progress.get('status', '').lower() in ['training', 'treniruojama'] or
                    (progress.get('progress', 0) > 0 and progress.get('progress', 0) < 100)
                )
                
                if is_training:
                    training_models += 1
                
                all_status[model_type] = {
                    'progress': progress,
                    'status': status,
                    'is_training': is_training
                }
                
            except Exception as e:
                logger.error(f"Error getting status for {model_type}: {str(e)}")
                all_status[model_type] = {
                    'progress': {'status': 'Error', 'progress': 0, 'error': str(e)},
                    'status': {'status': 'Unknown'},
                    'is_training': False
                }
        
        # Debug log of training status
        logger.info(f"Training status: {training_models} models training")
        for model_type, status in all_status.items():
            is_training = status['is_training']
            progress = status['progress'].get('progress', 0)
            logger.info(f"  {model_type}: training={is_training}, progress={progress}%")
        
        return jsonify({
            'success': True,
            'all_status': all_status,
            'training_summary': {
                'training_models': training_models
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting training status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@training_api.route('/api/train_model', methods=['POST'])
def train_model():
    """Start training a model"""
    try:
        data = request.form if request.form else request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        model_type = data.get('model_type', '').lower()
        if not model_type:
            return jsonify({
                'success': False,
                'error': 'Model type is required'
            }), 400
            
        # Get model manager from app
        app = training_api.current_app
        model_manager = None
        
        if hasattr(app, 'config') and 'MODEL_MANAGER' in app.config:
            model_manager = app.config['MODEL_MANAGER']
        elif hasattr(app, 'model_manager'):
            model_manager = app.model_manager
            
        if not model_manager:
            return jsonify({
                'success': False,
                'error': 'Model manager not available'
            }), 500
            
        # Extract parameters from data
        params = {}
        param_keys = [
            'epochs', 'batch_size', 'learning_rate', 'lookback', 'dropout',
            'units', 'layers', 'num_heads', 'd_model', 'filters', 'kernel_size'
        ]
        
        for key in param_keys:
            if key in data:
                try:
                    # Convert numerical values
                    if key in ['epochs', 'batch_size', 'lookback', 'units', 'layers', 'num_heads', 'd_model']:
                        params[key] = int(data[key])
                    elif key in ['learning_rate', 'dropout']:
                        params[key] = float(data[key])
                    elif key in ['filters', 'kernel_size']:
                        # These might be arrays, parse if provided as string
                        value = data[key]
                        if isinstance(value, str):
                            try:
                                import json
                                params[key] = json.loads(value)
                            except:
                                params[key] = value
                        else:
                            params[key] = value
                    else:
                        params[key] = data[key]
                except ValueError:
                    # Skip if conversion fails
                    pass
        
        # Update model configuration if params provided
        if params:
            model_manager.update_model_config(model_type, params)
            
        # Start training
        success = model_manager.train_model(model_type)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Started training {model_type.upper()} model',
                'model_type': model_type
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start training {model_type.upper()} model'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in train_model: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@training_api.route('/api/stop_training/<model_type>', methods=['POST'])
def stop_model_training(model_type):
    """Stop training a model"""
    try:
        # Get model manager from app
        app = training_api.current_app
        model_manager = None
        
        if hasattr(app, 'config') and 'MODEL_MANAGER' in app.config:
            model_manager = app.config['MODEL_MANAGER']
        elif hasattr(app, 'model_manager'):
            model_manager = app.model_manager
            
        if not model_manager:
            return jsonify({
                'success': False,
                'error': 'Model manager not available'
            }), 500
            
        # Stop training
        success = model_manager.stop_training(model_type)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Stopped training {model_type.upper()} model'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop training {model_type.upper()} model'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in stop_training: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@training_api.route('/api/stop_all_training', methods=['POST'])
def stop_all_training():
    """Stop all active training"""
    try:
        # Get model manager from app
        app = training_api.current_app
        model_manager = None
        
        if hasattr(app, 'config') and 'MODEL_MANAGER' in app.config:
            model_manager = app.config['MODEL_MANAGER']
        elif hasattr(app, 'model_manager'):
            model_manager = app.model_manager
            
        if not model_manager:
            return jsonify({
                'success': False,
                'error': 'Model manager not available'
            }), 500
            
        # Stop all training
        model_types = ['lstm', 'gru', 'cnn', 'transformer']
        stopped_count = 0
        
        for model_type in model_types:
            status = model_manager.get_training_progress(model_type)
            if status.get('status') == 'Training':
                if model_manager.stop_training(model_type):
                    stopped_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Stopped {stopped_count} training processes',
            'stopped_count': stopped_count
        })
            
    except Exception as e:
        logger.error(f"Error in stop_all_training: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
