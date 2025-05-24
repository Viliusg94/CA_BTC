"""
API endpoints for model history operations
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

model_history_api = Blueprint('model_history_api', __name__)

@model_history_api.route('/api/model_history_db', methods=['GET'])
def get_model_history():
    """Get model history from database"""
    try:
        app = model_history_api.current_app
        
        # Check if the database is available
        if not hasattr(app, 'config') or 'SQLALCHEMY_DATABASE_URI' not in app.config:
            return jsonify({
                'success': False,
                'error': 'Database not configured'
            }), 500
            
        # Get ModelHistory model from app if possible
        ModelHistory = None
        try:
            from app.models import ModelHistory
        except ImportError:
            try:
                # Try to get it from app module
                ModelHistory = app.ModelHistory
            except AttributeError:
                return jsonify({
                    'success': False,
                    'error': 'ModelHistory model not available'
                }), 500
                
        # Query all models from database
        models = ModelHistory.query.order_by(ModelHistory.timestamp.desc()).all()
        
        # Convert models to dictionaries
        models_list = []
        for model in models:
            try:
                models_list.append(model.to_dict())
            except Exception as e:
                logger.error(f"Error converting model to dict: {str(e)}")
                # Include minimal information if to_dict fails
                models_list.append({
                    'id': model.id,
                    'model_type': model.model_type,
                    'is_active': model.is_active,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'models': models_list,
            'count': len(models_list)
        })
        
    except Exception as e:
        logger.error(f"Error in get_model_history: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
