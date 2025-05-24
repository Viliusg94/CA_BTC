"""
API endpoints for model metrics operations
"""
from flask import Blueprint, jsonify, request
import logging
import os
import json

logger = logging.getLogger(__name__)

model_metrics_api = Blueprint('model_metrics_api', __name__)

@model_metrics_api.route('/api/model_details/<model_type>', methods=['GET'])
def get_model_details(model_type):
    """Get detailed information about a specific model"""
    try:
        app = model_metrics_api.current_app
        model_manager = None
        
        # Try to get model manager from app
        if hasattr(app, 'config') and 'MODEL_MANAGER' in app.config:
            model_manager = app.config['MODEL_MANAGER']
        elif hasattr(app, 'model_manager'):
            model_manager = app.model_manager
        
        # Default details structure
        details = {
            'model_type': model_type.upper(),
            'status': 'Unknown',
            'last_trained': 'Never',
            'performance': 'Unknown',
            'config': {},
            'metrics': {}
        }
        
        # Get configuration and status if model manager is available
        if model_manager:
            try:
                config = model_manager.get_model_config(model_type)
                status = model_manager.get_model_status(model_type)
                
                details.update({
                    'status': status.get('status', 'Unknown'),
                    'last_trained': status.get('last_trained', 'Never'),
                    'performance': status.get('performance', 'Unknown'),
                    'config': config or {}
                })
            except Exception as e:
                logger.error(f"Error getting model details from manager: {str(e)}")
        
        # Try to get metrics from model info file
        models_dir = os.path.join(os.path.dirname(app.instance_path), 'models')
        info_path = os.path.join(models_dir, f"{model_type.lower()}_model_info.json")
        
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r') as f:
                    model_info = json.load(f)
                    
                if 'metrics' in model_info:
                    details['metrics'] = model_info['metrics']
                    
                # Get more details if available
                if 'training_time' in model_info:
                    details['training_time'] = model_info['training_time']
                if 'params' in model_info:
                    details['params'] = model_info['params']
            except Exception as e:
                logger.error(f"Error loading model info file: {str(e)}")
        
        # Try to get active model from database
        try:
            from app.models import ModelHistory
            active_model = ModelHistory.query.filter_by(
                model_type=model_type.upper(), 
                is_active=True
            ).first()
            
            if active_model:
                db_details = active_model.to_dict()
                # Add database details
                details['db_info'] = db_details
                
                # Update metrics if not already present
                if not details['metrics'] and 'r2' in db_details:
                    details['metrics'] = {
                        'r2': db_details.get('r2'),
                        'mae': db_details.get('mae'),
                        'rmse': db_details.get('rmse'),
                        'mse': db_details.get('mse')
                    }
        except Exception as e:
            logger.error(f"Error getting model from database: {str(e)}")
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        logger.error(f"Error in get_model_details: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
