"""
Routes for prediction page
"""
from flask import Blueprint, render_template, redirect, flash, url_for, current_app
import logging
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import model utilities
try:
    from utils.model_util import get_active_models
    from utils.bitcoin_api import get_real_bitcoin_price
except ImportError:
    # Define fallback function if imports fail
    def get_active_models(db, ModelHistory):
        return []
    
    def get_real_bitcoin_price():
        return 45000.0

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
prediction_routes = Blueprint('prediction', __name__)

@prediction_routes.route('/predict')
def predict_page():
    """Bitcoin price prediction page"""
    try:
        logger.info("Loading prediction page")
        
        # Get current Bitcoin price for initial display
        current_price = get_real_bitcoin_price()
        if current_price is None:
            current_price = 45000.0
        
        # Get active models from database
        active_models = []
        try:
            from flask_sqlalchemy import SQLAlchemy
            from app.models import ModelHistory, db
            
            active_models = get_active_models(db, ModelHistory)
            logger.info(f"Found {len(active_models)} active models")
        except Exception as e:
            logger.error(f"Error getting active models: {str(e)}", exc_info=True)
        
        # Prepare initial template data
        template_data = {
            'current_price': current_price,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'active_models': active_models
        }
        
        return render_template('predict.html', **template_data)
    except Exception as e:
        logger.error(f"Error in predict page: {str(e)}", exc_info=True)
        flash(f"Error loading prediction page: {str(e)}", "error")
        return redirect('/')
