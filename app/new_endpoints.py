"""
New API endpoints for model management and prediction
"""

from flask import Blueprint, jsonify, request, render_template
import logging
from .model_manager import ModelManager
from .database import get_db_connection

logger = logging.getLogger(__name__)

# Create blueprint
new_endpoints = Blueprint('new_endpoints', __name__)

# Initialize model manager
model_manager = ModelManager()

@new_endpoints.route('/models')
def models_page():
    """Render the models management page"""
    return render_template('models.html')

@new_endpoints.route('/training-status')
def training_status_page():
    """Render the training status page"""
    return render_template('training_status.html')

# ...existing code...
@new_endpoints.route('/api/models/active', methods=['GET'])
def get_active_models():
    """Get all active and trained models from database"""
    try:
        models = model_manager.get_active_trained_models()
        
        if not models:
            return jsonify({
                'success': False,
                'message': 'No active trained models found',
                'models': []
            }), 200
        
        return jsonify({
            'success': True,
            'message': f'Found {len(models)} active trained models',
            'models': models
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting active models: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'models': []        }), 500

@new_endpoints.route('/api/models/predict/<model_type>', methods=['POST'])
def predict_btc_price(model_type):
    """Predict BTC price for next 7 days using specified model"""
    try:
        # Validate model type
        valid_models = ['lstm', 'gru', 'cnn', 'transformer']
        if model_type not in valid_models:
            return jsonify({
                'success': False,
                'error': f'Invalid model type. Must be one of: {valid_models}'
            }), 400
        
        # Check if model is active and trained
        active_models = model_manager.get_active_trained_models()
        model_found = any(model['model_type'] == model_type for model in active_models)
        
        if not model_found:
            return jsonify({
                'success': False,
                'error': f'Model {model_type} is not active or trained'
            }), 400
        
        # Generate predictions
        predictions = model_manager.predict_next_7_days(model_type)
        
        if not predictions:
            return jsonify({
                'success': False,
                'error': 'Failed to generate predictions'
            }), 500
        
        return jsonify({
            'success': True,
            'model_type': model_type,
            'predictions': predictions,
            'prediction_count': len(predictions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error predicting with {model_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@new_endpoints.route('/api/models/status/<model_type>', methods=['GET'])
def get_model_detailed_status(model_type):
    """Get detailed status of a specific model"""
    try:
        # Get model status from model manager
        status = model_manager.get_model_status(model_type)
        
        # Get additional info from database
        conn = get_db_connection()
        cursor = conn.cursor()
        model_name = f'{model_type}_btc_model'
        
        cursor.execute('''
            SELECT status, is_trained, accuracy, r2_score, mae, rmse, mape, 
                   last_trained, created_at
            FROM models 
            WHERE model_name = ?
        ''', (model_name,))
        
        db_result = cursor.fetchone()
        conn.close()
        
        if db_result:
            status.update({
                'database_status': db_result[0],
                'is_trained': bool(db_result[1]),
                'accuracy': db_result[2],
                'r2_score': db_result[3],
                'mae': db_result[4],
                'rmse': db_result[5],
                'mape': db_result[6],
                'last_trained': db_result[7],
                'created_at': db_result[8]
            })
        
        return jsonify({
            'success': True,
            'model_type': model_type,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting model status for {model_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@new_endpoints.route('/api/models/train/<model_type>', methods=['POST'])
def train_model(model_type):
    """Start training a specific model"""
    try:
        # Validate model type
        valid_models = ['lstm', 'gru', 'cnn', 'transformer']
        if model_type not in valid_models:
            return jsonify({
                'success': False,
                'error': f'Invalid model type. Must be one of: {valid_models}'
            }), 400
        
        # Get optional configuration from request
        config = request.get_json() if request.is_json else {}
        
        # Start training
        success = model_manager.start_training(model_type, config)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Training started for {model_type}',
                'model_type': model_type
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start training for {model_type}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error starting training for {model_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@new_endpoints.route('/api/models/training/progress/<model_type>', methods=['GET'])
def get_training_progress(model_type):
    """Get training progress for a specific model"""
    try:
        progress = model_manager.get_training_progress(model_type)
        
        return jsonify({
            'success': True,
            'model_type': model_type,
            'progress': progress
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting training progress for {model_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@new_endpoints.route('/api/models/training/stop/<model_type>', methods=['POST'])
def stop_training(model_type):
    """Stop training for a specific model"""
    try:
        success = model_manager.stop_training(model_type)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Training stopped for {model_type}',
                'model_type': model_type
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop training for {model_type}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error stopping training for {model_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@new_endpoints.route('/api/models/all/status', methods=['GET'])
def get_all_models_status():
    """Get status of all models"""
    try:
        model_types = ['lstm', 'gru', 'cnn', 'transformer']
        all_status = {}
        
        for model_type in model_types:
            all_status[model_type] = model_manager.get_model_status(model_type)
        
        # Also get training status
        training_status = model_manager.get_all_training_status()
        
        return jsonify({
            'success': True,
            'models_status': all_status,
            'training_status': training_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all models status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@new_endpoints.route('/api/predictions/history/<model_type>', methods=['GET'])
def get_prediction_history(model_type):
    """Get prediction history for a specific model"""
    try:
        # This would typically get from a predictions table
        # For now, return empty list as placeholder
        return jsonify({
            'success': True,
            'model_type': model_type,
            'predictions': [],
            'message': 'Prediction history feature coming soon'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting prediction history for {model_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500