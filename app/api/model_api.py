"""
Model API endpoint definitions
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json
import os

# Import database models
try:
    from app.models import db, ModelHistory
    database_enabled = True
except ImportError:
    database_enabled = False

# Import model service
try:
    from app.services.model_service import ModelTrainingService
    model_service = ModelTrainingService()
except ImportError:
    model_service = None

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
model_api = Blueprint('model_api', __name__, url_prefix='/api/models')

# Documentation for endpoints
model_endpoints = {
    "/api/model/train": {
        "description": "Train a new model with specified parameters",
        "methods": ["POST"],
        "parameters": [
            {"name": "model_type", "type": "string", "required": True, "description": "Type of model (LSTM, GRU, CNN, TRANSFORMER)"},
            {"name": "config", "type": "object", "required": True, "description": "Model configuration parameters"}
        ],
        "responses": {
            "200": {"description": "Training started successfully", "schema": {"success": True, "task_id": "string"}},
            "400": {"description": "Invalid parameters", "schema": {"success": False, "error": "string"}}
        },
        "example": {
            "request": {
                "model_type": "LSTM",
                "config": {
                    "epochs": 50,
                    "batch_size": 32,
                    "learning_rate": 0.001,
                    "lookback": 30,
                    "dropout": 0.2
                }
            },
            "response": {
                "success": True,
                "task_id": "12345",
                "message": "Model training started"
            }
        }
    },
    "/api/model/status": {
        "description": "Get model training status",
        "methods": ["GET"],
        "parameters": [
            {"name": "model_type", "type": "string", "required": True, "description": "Type of model (LSTM, GRU, CNN, TRANSFORMER)"}
        ],
        "responses": {
            "200": {"description": "Model status retrieved successfully", 
                   "schema": {"success": True, "status": "string", "progress": "number"}},
            "404": {"description": "Model not found", "schema": {"success": False, "error": "string"}}
        },
        "example": {
            "request": "?model_type=LSTM",
            "response": {
                "success": True,
                "status": "training",
                "progress": 75,
                "current_epoch": 30,
                "total_epochs": 50
            }
        }
    },
    "/api/model/config": {
        "description": "Get or update model configuration",
        "methods": ["GET", "POST"],
        "parameters": [
            {"name": "model_type", "type": "string", "required": True, "description": "Type of model (LSTM, GRU, CNN, TRANSFORMER)"},
            {"name": "config", "type": "object", "required": False, "description": "New model configuration (POST only)"}
        ],
        "responses": {
            "200": {"description": "Config retrieved or updated successfully", 
                    "schema": {"success": True, "config": "object"}},
            "400": {"description": "Invalid parameters", "schema": {"success": False, "error": "string"}}
        },
        "example": {
            "request": "?model_type=LSTM",
            "response": {
                "success": True,
                "config": {
                    "epochs": 50,
                    "batch_size": 32,
                    "learning_rate": 0.001,
                    "lookback": 30,
                    "dropout": 0.2
                }
            }
        }
    }
}

@model_api.route('/train_model', methods=['POST'])
def train_model():
    """Start model training with the specified parameters"""
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Validate required parameters
        required_params = ['model_type', 'epochs', 'batch_size', 'learning_rate', 'lookback']
        for param in required_params:
            if param not in form_data:
                return jsonify({'success': False, 'error': f'Missing parameter: {param}'}), 400
        
        # Get the model training service
        model_service = current_app.model_training_service
        if not model_service:
            return jsonify({'success': False, 'error': 'Model training service not available'}), 500
        
        # Start training
        model_type = form_data['model_type']
        success, result = model_service.train_model(model_type, form_data)
        
        if success:
            return jsonify({'success': True, 'training_id': result})
        else:
            return jsonify({'success': False, 'error': result}), 400
        
    except Exception as e:
        logger.error(f"Error in train_model endpoint: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/training_progress/<model_type>', methods=['GET'])
def training_progress(model_type):
    """Get training progress for a specific model"""
    try:
        # Get the model training service
        model_service = current_app.model_training_service
        if not model_service:
            return jsonify({'success': False, 'error': 'Model training service not available'}), 500
        
        # Get progress
        progress = model_service.get_training_status(model_type)
        
        return jsonify({'success': True, 'progress': progress})
    
    except Exception as e:
        logger.error(f"Error in training_progress endpoint: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/stop_training', methods=['POST'])
def stop_training():
    """Stop training for a specific model"""
    try:
        # Get request data
        data = request.json
        if not data or 'model_type' not in data:
            return jsonify({'success': False, 'error': 'Missing model_type parameter'}), 400
        
        model_type = data['model_type']
        
        # Get the model training service
        model_service = current_app.model_training_service
        if not model_service:
            return jsonify({'success': False, 'error': 'Model training service not available'}), 500
        
        # Stop training
        success, message = model_service.stop_training(model_type)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
        
    except Exception as e:
        logger.error(f"Error in stop_training endpoint: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/model_history_db', methods=['GET'])
def model_history():
    """Get all model history entries from the database"""
    try:
        # Query the database
        models = ModelHistory.query.order_by(ModelHistory.timestamp.desc()).all()
        
        # Convert to list of dictionaries
        result = []
        for model in models:
            result.append(model.to_dict())
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in model_history endpoint: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/model_params/<int:model_id>', methods=['GET'])
def model_params(model_id):
    """Get parameters for a specific model"""
    try:
        # Query the database
        model = ModelHistory.query.get(model_id)
        if not model:
            return jsonify({'success': False, 'error': 'Model not found'}), 404
        
        # Return model parameters
        return jsonify({'success': True, 'model': model.to_dict()})
    
    except Exception as e:
        logger.error(f"Error in model_params endpoint: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/delete_model_history/<model_type>/<int:model_id>', methods=['DELETE'])
def delete_model_history(model_type, model_id):
    """Delete a model history entry"""
    try:
        # Query the database
        model = ModelHistory.query.filter_by(id=model_id, model_type=model_type.upper()).first()
        if not model:
            return jsonify({'success': False, 'error': 'Model not found'}), 404
        
        # Delete the model
        db.session.delete(model)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error in delete_model_history endpoint: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/use_model/<model_type>/<int:model_id>', methods=['POST'])
def use_model(model_type, model_id):
    """Set a model as active"""
    try:
        # Query the database
        model = ModelHistory.query.filter_by(id=model_id, model_type=model_type.upper()).first()
        if not model:
            return jsonify({'success': False, 'error': 'Model not found'}), 404
        
        # Set all models of this type to inactive
        ModelHistory.query.filter_by(model_type=model_type.upper()).update({'is_active': False})
        
        # Set this model to active
        model.is_active = True
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error in use_model endpoint: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/training_status', methods=['GET'])
def training_status():
    """Get training status for all models"""
    try:
        # Get the model training service
        model_service = current_app.model_training_service
        if not model_service:
            return jsonify({'success': False, 'error': 'Model training service not available'}), 500
        
        # Model types
        model_types = ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm']
        
        # Get status for each model
        models_status = {}
        any_training = False
        
        for model_type in model_types:
            status = model_service.get_training_status(model_type)
            is_training = status.get('status') == 'Apmokomas'
            
            models_status[model_type] = {
                'name': model_type.upper(),
                'model_status': {
                    'status': 'Apmokomas' if is_training else status.get('status', 'Neapmokytas')
                },
                'training_progress': status,
                'is_training': is_training
            }
            
            if is_training:
                any_training = True
        
        return jsonify({
            'success': True, 
            'models_status': models_status,
            'any_training': any_training
        })
    
    except Exception as e:
        logger.error(f"Error in training_status endpoint: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@model_api.route('/train', methods=['POST'])
def start_model_training():
    """Start training a new model"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        model_type = data.get('model_type')
        if not model_type:
            return jsonify({
                'status': 'error',
                'message': 'Model type is required'
            }), 400
        
        # Validate model type
        valid_types = ['LSTM', 'GRU', 'CNN', 'Transformer', 'CNN_LSTM']
        if model_type.upper() not in valid_types:
            return jsonify({
                'status': 'error',
                'message': f'Invalid model type. Valid types: {valid_types}'
            }), 400
        
        # Get the model training service
        model_service = current_app.model_training_service
        if not model_service:
            return jsonify({
                'status': 'error',
                'message': 'Model training service not available'
            }), 500
        
        # Start training
        training_id = model_service.start_training(model_type, data.get('config', {}))
        
        return jsonify({
            'status': 'success',
            'message': f'Training started for {model_type}',
            'training_id': training_id
        })
        
    except Exception as e:
        logger.error(f"Error starting model training: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@model_api.route('/predict', methods=['POST'])
def predict():
    """Generate predictions using a model"""
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        days = data.get('days', 7)
        
        if not model_id:
            return jsonify({'error': 'Model ID is required'}), 400
        
        # Get prediction service
        from app.services.prediction_service import prediction_service
        
        # Generate predictions
        predictions = prediction_service.generate_predictions(model_id, days)
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
        
    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_api.route('/list', methods=['GET'])
def list_models():
    """List all available models"""
    try:
        from app.models import ModelHistory
        
        models = ModelHistory.query.all()
        model_list = [model.to_dict() for model in models]
        
        return jsonify({
            'success': True,
            'models': model_list
        })
        
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_api.route('/<int:model_id>', methods=['GET'])
def get_model(model_id):
    """Get specific model details"""
    try:
        from app.models import ModelHistory
        
        model = ModelHistory.query.get_or_404(model_id)
        
        return jsonify({
            'success': True,
            'model': model.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting model: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_api.route('/<int:model_id>', methods=['DELETE'])
def delete_model(model_id):
    """Delete a model"""
    try:
        from app.models import ModelHistory, db
        
        model = ModelHistory.query.get_or_404(model_id)
        db.session.delete(model)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Model deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting model: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_api.route('/<int:model_id>/activate', methods=['POST'])
def activate_model(model_id):
    """Activate a model for predictions"""
    try:
        from app.models import ModelHistory, db
        
        model = ModelHistory.query.get_or_404(model_id)
        
        # Deactivate all models of the same type
        ModelHistory.query.filter_by(model_type=model.model_type).update({'is_active': False})
        
        # Activate the selected model
        model.is_active = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Model {model_id} activated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error activating model: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_api.route('/api/models/list', methods=['GET'])
def list_models_files():
    """Get list of all available models"""
    try:
        # Get models directory from the app config
        app = model_api.current_app
        models_dir = os.path.join(os.path.dirname(app.instance_path), 'models')
        
        # Check if directory exists
        if not os.path.exists(models_dir):
            return jsonify({
                'success': False,
                'error': 'Models directory not found'
            }), 404
        
        # Get list of model files
        model_files = {}
        for filename in os.listdir(models_dir):
            if filename.endswith('.h5'):
                model_type = filename.replace('_model.h5', '').upper()
                model_files[model_type] = filename
        
        # Try to get model manager from app
        model_manager = None
        if hasattr(app, 'config') and 'MODEL_MANAGER' in app.config:
            model_manager = app.config['MODEL_MANAGER']
        elif hasattr(app, 'model_manager'):
            model_manager = app.model_manager
            
        active_models = {}
        if model_manager:
            # Get active models status
            for model_type in model_files.keys():
                status = model_manager.get_model_status(model_type.lower())
                active_models[model_type] = status
        
        return jsonify({
            'success': True,
            'models': model_files,
            'active_models': active_models,
            'model_types': list(model_files.keys())
        })
        
    except Exception as e:
        logger.error(f"Error in list_models: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@model_api.route('/api/training_status', methods=['GET'])
def get_training_status():
    """Get status of all model training processes"""
    try:
        app = model_api.current_app
        model_manager = None
        
        # Try to get model manager from app
        if hasattr(app, 'config') and 'MODEL_MANAGER' in app.config:
            model_manager = app.config['MODEL_MANAGER']
        elif hasattr(app, 'model_manager'):
            model_manager = app.model_manager
            
        if not model_manager:
            return jsonify({
                'success': False, 
                'error': 'Model manager not available'
            }), 500
            
        # Get training status for all model types
        all_status = {}
        training_models = 0
        model_types = ['lstm', 'gru', 'cnn', 'transformer']
        
        for model_type in model_types:
            try:
                progress = model_manager.get_training_progress(model_type)
                status = model_manager.get_model_status(model_type)
                
                # Check if this model is currently training
                is_training = progress.get('status') == 'Training' if progress else False
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
        
        return jsonify({
            'success': True,
            'all_status': all_status,
            'training_summary': {
                'training_models': training_models
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_training_status: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500