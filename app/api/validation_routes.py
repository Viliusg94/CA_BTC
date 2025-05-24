"""
API validation routes for health checking and documentation
"""
import logging
from flask import Blueprint, jsonify, request, current_app

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
api_validation = Blueprint('api_validation', __name__, url_prefix='/api')

# Documentation for endpoints
api_endpoints = {
    "/api/health": {
        "description": "Health check endpoint for the API",
        "methods": ["GET"],
        "parameters": [],
        "responses": {
            "200": {"description": "API is healthy", "schema": {"status": "ok", "version": "string"}},
            "500": {"description": "API is not healthy", "schema": {"status": "error", "message": "string"}}
        },
        "example": {
            "response": {
                "status": "ok",
                "version": "1.0.0",
                "database": "connected",
                "services": {
                    "prediction": "running",
                    "training": "running"
                }
            }
        }
    },
    "/api/docs": {
        "description": "Get API documentation",
        "methods": ["GET"],
        "parameters": [
            {"name": "format", "type": "string", "required": False, "description": "Documentation format (json, html)", "default": "json"}
        ],
        "responses": {
            "200": {"description": "API documentation", "schema": {"endpoints": "object"}}
        },
        "example": {
            "request": "?format=json",
            "response": {
                "endpoints": {
                    "/api/health": {
                        "description": "Health check endpoint for the API",
                        "methods": ["GET"]
                    },
                    "/api/docs": {
                        "description": "Get API documentation",
                        "methods": ["GET"]
                    }
                }
            }
        }
    },
    "/api/price_history": {
        "description": "Get Bitcoin price history",
        "methods": ["GET"],
        "parameters": [
            {"name": "days", "type": "number", "required": False, "description": "Number of days of history to retrieve", "default": 30}
        ],
        "responses": {
            "200": {"description": "Price history data", "schema": {"status": "success", "data": "object"}},
            "500": {"description": "Error fetching price history", "schema": {"status": "error", "message": "string"}}
        },
        "example": {
            "request": "?days=7",
            "response": {
                "status": "success",
                "data": {
                    "dates": ["2023-03-10", "2023-03-11", "..."],
                    "prices": [45000.0, 46000.0, "..."],
                    "volumes": [10000, 12000, "..."]
                }
            }
        }
    }
}

@api_validation.route('/health')
def health_check():
    """Health check endpoint for the API"""
    try:
        # Check if database is available
        from app.models import db
        database_status = "connected"
        
        try:
            # Try a simple query
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
        except Exception as db_error:
            logger.warning(f"Database check failed: {str(db_error)}")
            database_status = "error"
        
        # Check if prediction service is available
        prediction_status = "running"
        try:
            if hasattr(current_app, 'prediction_service'):
                if not current_app.prediction_service.running:
                    prediction_status = "stopped"
            else:
                prediction_status = "not initialized"
        except Exception:
            prediction_status = "error"
        
        # Check if training service is available
        training_status = "running"
        try:
            if hasattr(current_app, 'model_training_service'):
                # SimpleCheck if service is functional
                if not hasattr(current_app.model_training_service, 'get_model_status'):
                    training_status = "limited"
            else:
                training_status = "not initialized"
        except Exception:
            training_status = "error"
        
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "database": database_status,
            "services": {
                "prediction": prediction_status,
                "training": training_status
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_validation.route('/docs')
def api_docs():
    """API documentation endpoint"""
    try:
        documentation_format = request.args.get('format', 'json')
        
        # Get all endpoint documentation from different route modules
        endpoints = {}
        endpoints.update(api_endpoints)
        
        # Try to import and include other endpoint docs
        try:
            from app.api.model_api import model_endpoints
            endpoints.update(model_endpoints)
        except ImportError:
            pass
        
        try:
            from app.api.model_history_api import history_endpoints
            endpoints.update(history_endpoints)
        except ImportError:
            pass
        
        try:
            from app.api.model_metrics_api import metrics_endpoints
            endpoints.update(metrics_endpoints)
        except ImportError:
            pass
        
        if documentation_format == 'html':
            # If HTML format is requested, render a template
            from flask import render_template
            return render_template('documentation/api_docs.html', endpoints=endpoints)
        else:
            # Default to JSON format
            return jsonify({"endpoints": endpoints})
            
    except Exception as e:
        logger.error(f"Error generating API docs: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e)
        }), 500