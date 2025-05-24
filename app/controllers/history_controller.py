"""
Controller for model history pages and functionality
"""
import logging
from flask import render_template, jsonify, request, Blueprint
from app.models import ModelHistory

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
def index():
    """Display model training history page"""
    try:
        # Query the database for all models
        models = ModelHistory.query.order_by(ModelHistory.timestamp.desc()).all()
        
        # Render the template with model data
        return render_template('history.html', models=models)
    except Exception as e:
        logger.error(f"Error in history index: {str(e)}", exc_info=True)
        return render_template('history.html', models=[], error=str(e))

@history_bp.route('/api/model_comparison')
def model_comparison_data():
    """API endpoint for model comparison data"""
    try:
        # Get model types to include
        model_types = request.args.get('types')
        if model_types:
            model_types = [t.strip().upper() for t in model_types.split(',')]
            models = ModelHistory.query.filter(ModelHistory.model_type.in_(model_types))
        else:
            models = ModelHistory.query
        
        # Get metrics for each model type
        metrics_by_type = {}
        for model in models.all():
            model_type = model.model_type
            if model_type not in metrics_by_type:
                metrics_by_type[model_type] = []
            
            metrics_by_type[model_type].append({
                'id': model.id,
                'r2': model.r2,
                'mae': model.mae,
                'rmse': model.rmse,
                'mse': model.mse,
                'training_loss': model.training_loss,
                'validation_loss': model.validation_loss,
                'timestamp': model.timestamp.isoformat() if model.timestamp else None,
                'is_active': model.is_active
            })
        
        # For each model type, compute average metrics
        summary = []
        for model_type, models_data in metrics_by_type.items():
            # Calculate averages, filtering out None values
            avg_r2 = sum(m['r2'] for m in models_data if m['r2'] is not None) / sum(1 for m in models_data if m['r2'] is not None) if any(m['r2'] is not None for m in models_data) else None
            avg_mae = sum(m['mae'] for m in models_data if m['mae'] is not None) / sum(1 for m in models_data if m['mae'] is not None) if any(m['mae'] is not None for m in models_data) else None
            avg_rmse = sum(m['rmse'] for m in models_data if m['rmse'] is not None) / sum(1 for m in models_data if m['rmse'] is not None) if any(m['rmse'] is not None for m in models_data) else None
            
            summary.append({
                'model_type': model_type,
                'count': len(models_data),
                'avg_r2': avg_r2,
                'avg_mae': avg_mae,
                'avg_rmse': avg_rmse,
                'best_model': min(models_data, key=lambda x: x['rmse'] if x['rmse'] is not None else float('inf')) if models_data else None,
                'active_model': next((m for m in models_data if m['is_active']), None)
            })
        
        return jsonify({
            'success': True,
            'summary': summary,
            'models_by_type': metrics_by_type
        })
    
    except Exception as e:
        logger.error(f"Error in model comparison data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@history_bp.route('/api/model_export')
def export_model():
    """Export model configuration"""
    try:
        model_id = request.args.get('id')
        if not model_id:
            return jsonify({'success': False, 'error': 'No model ID provided'}), 400
        
        # Get model from database
        model = ModelHistory.query.get(int(model_id))
        if not model:
            return jsonify({'success': False, 'error': 'Model not found'}), 404
        
        # Convert to dict for export
        export_data = model.to_dict()
        
        # Add specific params
        specific_params = model.get_specific_params()
        if specific_params:
            export_data['specific_params'] = specific_params
        
        return jsonify({
            'success': True,
            'model': export_data
        })
    
    except Exception as e:
        logger.error(f"Error exporting model: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
