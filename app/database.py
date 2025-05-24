"""
Database configuration and setup
"""
import os
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def init_db(app):
    """Initialize database with the Flask app"""
    try:
        # Ensure Data directory exists
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Database path
        db_path = os.path.join(data_dir, 'models.db')
        
        # Configure SQLAlchemy
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }
        
        logger.info(f"Database initialized at {db_path}")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        return False