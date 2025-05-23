"""
Startup diagnostic script to identify and resolve application startup issues
"""

import os
import sys
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('startup_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'flask',
        'numpy',
        'pandas',
        'sklearn',
        'requests'
    ]
    
    optional_packages = [
        'tensorflow',
        'sqlalchemy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} - OK")
        except ImportError as e:
            logger.error(f"✗ {package} - MISSING: {e}")
            missing_packages.append(package)
    
    for package in optional_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} - OK")
        except ImportError as e:
            logger.warning(f"~ {package} - OPTIONAL MISSING: {e}")
    
    return missing_packages

def check_directories():
    """Check if required directories exist"""
    logger.info("Checking directories...")
    
    required_dirs = [
        'models',
        'data',
        'templates',
        'static'
    ]
    
    for dir_name in required_dirs:
        dir_path = os.path.join(os.path.dirname(__file__), dir_name)
        if os.path.exists(dir_path):
            logger.info(f"✓ {dir_name} directory exists")
        else:
            logger.warning(f"~ {dir_name} directory missing, creating...")
            os.makedirs(dir_path, exist_ok=True)

def check_tensorflow():
    """Check TensorFlow availability and performance"""
    logger.info("Checking TensorFlow...")
    
    try:
        start_time = time.time()
        import tensorflow as tf
        load_time = time.time() - start_time
        
        logger.info(f"✓ TensorFlow {tf.__version__} loaded in {load_time:.2f} seconds")
        
        # Check GPU availability
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            logger.info(f"✓ Found {len(gpus)} GPU(s)")
        else:
            logger.info("~ No GPU found, using CPU")
        
        return True
    except ImportError as e:
        logger.error(f"✗ TensorFlow not available: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ TensorFlow error: {e}")
        return False

def test_flask_app():
    """Test basic Flask app functionality"""
    logger.info("Testing Flask app...")
    
    try:
        from flask import Flask
        test_app = Flask(__name__)
        
        @test_app.route('/test')
        def test():
            return "OK"
        
        # Test app creation
        with test_app.test_client() as client:
            response = client.get('/test')
            if response.status_code == 200:
                logger.info("✓ Flask app test successful")
                return True
            else:
                logger.error(f"✗ Flask app test failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Flask app test error: {e}")
        return False

def main():
    """Main diagnostic function"""
    logger.info("=== APPLICATION STARTUP DIAGNOSTIC ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Script location: {os.path.dirname(__file__)}")
    
    # Check all components
    missing_deps = check_dependencies()
    check_directories()
    tf_available = check_tensorflow()
    flask_ok = test_flask_app()
    
    # Summary
    logger.info("=== DIAGNOSTIC SUMMARY ===")
    
    if missing_deps:
        logger.error(f"Missing required packages: {missing_deps}")
        logger.error("Please install missing packages with: pip install " + " ".join(missing_deps))
        return False
    
    if not flask_ok:
        logger.error("Flask basic functionality failed")
        return False
    
    if not tf_available:
        logger.warning("TensorFlow not available - app will run in limited mode")
    
    logger.info("✓ Basic startup checks passed")
    
    # Try to import the main app
    try:
        logger.info("Testing main app import...")
        sys.path.insert(0, os.path.dirname(__file__))
        
        # Test importing key components
        from model_manager import ModelManager
        logger.info("✓ ModelManager import successful")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Main app import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("=== STARTUP DIAGNOSTIC COMPLETE - READY TO LAUNCH ===")
        sys.exit(0)
    else:
        logger.error("=== STARTUP DIAGNOSTIC FAILED - CHECK ERRORS ABOVE ===")
        sys.exit(1)
