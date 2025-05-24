"""
Controller for API documentation
"""
import logging
from flask import Blueprint, render_template, jsonify, current_app, send_from_directory

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
documentation_bp = Blueprint('documentation', __name__, url_prefix='/docs')

@documentation_bp.route('/')
def index():
    """Display API documentation page"""
    try:
        return render_template('documentation/index.html')
    except Exception as e:
        logger.error(f"Error rendering documentation: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@documentation_bp.route('/api-reference')
def api_reference():
    """Display API reference documentation"""
    try:
        return render_template('documentation/api_reference.html')
    except Exception as e:
        logger.error(f"Error rendering API reference: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@documentation_bp.route('/swagger')
def swagger_ui():
    """Display Swagger UI documentation"""
    try:
        return render_template('documentation/swagger.html')
    except Exception as e:
        logger.error(f"Error rendering Swagger UI: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@documentation_bp.route('/endpoints')
def endpoints_json():
    """Return JSON with all API endpoints documentation"""
    try:
        # Collect all API endpoints documentation
        endpoints = get_api_documentation()
        return jsonify(endpoints)
    except Exception as e:
        logger.error(f"Error getting API endpoints: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@documentation_bp.route('/openapi.json')
def openapi_spec():
    """Return OpenAPI specification"""
    try:
        return send_from_directory(current_app.static_folder, 'openapi.json')
    except Exception as e:
        logger.error(f"Error getting OpenAPI spec: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def get_api_documentation():
    """Collect all API endpoint documentation"""
    from app.api.validation_routes import api_endpoints
    from app.api.model_api import model_endpoints
    from app.api.model_history_api import history_endpoints
    from app.api.model_metrics_api import metrics_endpoints
    
    # Combine all endpoints
    all_endpoints = {}
    all_endpoints.update(api_endpoints)
    all_endpoints.update(model_endpoints)
    all_endpoints.update(history_endpoints)
    all_endpoints.update(metrics_endpoints)
    
    return all_endpoints
