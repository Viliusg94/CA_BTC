#!/usr/bin/env python3
"""
Fix script for missing routes in Bitcoin LSTM application
This script temporarily adds missing routes for models and training_status.
"""
import os
import json
import logging
import traceback
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_fixed_endpoints():
    """Create a file with fixed endpoints"""
    logger.info("Creating fixed endpoints file...")
    
    file_content = '''"""
Fixed API endpoints for model management
This file contains implementations of API endpoints that were missing or not working properly
"""
from flask import jsonify, request, render_template, flash, redirect
import logging
import os
import json
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

def register_endpoints(app, db=None, ModelHistory=None, model_manager=None):
    """Register all API endpoints"""
    
    @app.route('/models')
    def models_page():
        """Models management page"""
        try:
            logger.info("Loading models page")
            
            # Get model files from directory
            models_dir = os.path.join(os.path.dirname(app.instance_path), 'models')
            model_files = {}
            
            if os.path.exists(models_dir):
                for filename in os.listdir(models_dir):
                    if filename.endswith('.h5'):
                        model_type = filename.replace('_model.h5', '').upper()
                        model_files[model_type] = filename
            
            # Get model history from database if available
            model_history = {}
            if db and ModelHistory:
                try:
                    models = ModelHistory.query.all()
                    for model in models:
                        if model.model_type not in model_history:
                            model_history[model.model_type] = []
                        model_history[model.model_type].append(model.to_dict())
                except Exception as e:
                    logger.error(f"Error fetching model history: {e}")
            
            return render_template('models.html', 
                                 model_files=model_files,
                                 model_history=model_history)
        except Exception as e:
            logger.error(f"Error in models page: {e}", exc_info=True)
            return render_template('error.html', error=str(e))

    @app.route('/training_status')
    def training_status():
        """Training status page"""
        try:
            logger.info("Loading training status page")
            
            # Get training progress for all model types
            all_status = {}
            model_types = ['lstm', 'gru', 'cnn', 'transformer']
            training_models = 0
            
            if model_manager:
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
                        logger.error(f"Error getting progress for {model_type}: {e}")
                        all_status[model_type] = {
                            'progress': {'status': 'Error', 'progress': 0, 'error': str(e)},
                            'status': {'status': 'Unknown'},
                            'is_training': False
                        }
            else:
                # Fallback data if model_manager is not available
                for model_type in model_types:
                    all_status[model_type] = {
                        'progress': {'status': 'Manager Unavailable', 'progress': 0},
                        'status': {'status': 'Manager Unavailable'},
                        'is_training': False
                    }
            
            # Create training summary
            training_summary = {
                'training_models': training_models
            }
            
            return render_template('training_status.html', 
                                 all_status=all_status, 
                                 training_summary=training_summary)
        except Exception as e:
            logger.error(f"Error in training status page: {e}", exc_info=True)
            return render_template('error.html', error=str(e))
            
    # Add critical API endpoints
    @app.route('/api/model_history_db')
    def api_model_history_db():
        """API endpoint to get all model history from database"""
        try:
            logger.info("API: Fetching model history from database")
            
            if not db or not ModelHistory:
                return jsonify({'success': False, 'error': 'Database not available'})
            
            try:
                models = ModelHistory.query.order_by(ModelHistory.timestamp.desc()).all()
                model_data = [model.to_dict() for model in models]
                
                return jsonify({
                    'success': True,
                    'models': model_data,
                    'count': len(model_data)
                })
            except Exception as db_error:
                logger.error(f"Database error: {db_error}", exc_info=True)
                return jsonify({'success': False, 'error': f'Database error: {str(db_error)}'})
                
        except Exception as e:
            logger.error(f"Error fetching model history: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/model/config', methods=['GET', 'POST'])
    def model_config():
        """Model configuration API endpoint"""
        if request.method == 'GET':
            model_type = request.args.get('model_type')
            if not model_type:
                return jsonify({'error': 'No model type specified'}), 400
            
            if not model_manager:
                return jsonify({'error': 'ModelManager not available'}), 500
            
            try:
                config = model_manager.get_model_config(model_type)
                return jsonify({'model_type': model_type, 'config': config})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.json
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                model_type = data.get('model_type')
                config = data.get('config')
                
                if not model_type or not config:
                    return jsonify({'error': 'Missing model_type or config'}), 400
                
                if not model_manager:
                    return jsonify({'error': 'ModelManager not available'}), 500
                
                success = model_manager.update_model_config(model_type, config)
                
                if success:
                    return jsonify({
                        'status': 'success',
                        'message': f'Model {model_type} config updated',
                        'config': config
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to update {model_type} config'
                    }), 500
                    
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/model/progress')
    def model_progress():
        """Model training progress API endpoint"""
        model_type = request.args.get('model_type')
        if not model_type:
            return jsonify({'error': 'No model type specified'}), 400
        
        if not model_manager:
            return jsonify({'error': 'ModelManager not available'}), 500
        
        try:
            progress = model_manager.get_training_progress(model_type)
            return jsonify({'model_type': model_type, 'progress': progress})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/model_details/<model_type>')
    def api_model_details(model_type):
        """Model details API endpoint"""
        try:
            if not model_manager:
                return jsonify({
                    'success': True,
                    'details': {
                        'model_type': model_type,
                        'status': 'Unknown',
                        'message': 'ModelManager not available'
                    }
                })
            
            status = model_manager.get_model_status(model_type)
            config = model_manager.get_model_config(model_type)
            
            details = {
                'model_type': model_type,
                'status': status.get('status', 'Unknown'),
                'last_trained': status.get('last_trained', 'Never'),
                'performance': status.get('performance', 'Unknown'),
                'config': config
            }
            
            return jsonify({'success': True, 'details': details})
            
        except Exception as e:
            logger.error(f"Error in model details API: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/training_status')
    def api_training_status():
        """API endpoint to get all training status"""
        try:
            # Get training progress for all model types
            all_status = {}
            model_types = ['lstm', 'gru', 'cnn', 'transformer']
            training_models = 0
            
            if model_manager:
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
                        logger.error(f"Error getting progress for {model_type}: {e}")
                        all_status[model_type] = {
                            'progress': {'status': 'Error', 'progress': 0, 'error': str(e)},
                            'status': {'status': 'Unknown'},
                            'is_training': False
                        }
            else:
                # Fallback data if model_manager is not available
                for model_type in model_types:
                    all_status[model_type] = {
                        'progress': {'status': 'Manager Unavailable', 'progress': 0},
                        'status': {'status': 'Manager Unavailable'},
                        'is_training': False
                    }
            
            # Create training summary
            training_summary = {
                'training_models': training_models
            }
            
            return jsonify({
                'success': True,
                'all_status': all_status,
                'training_summary': training_summary
            })
            
        except Exception as e:
            logger.error(f"Error in training status API: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})
    
    logger.info("All fixed endpoints registered successfully")
'''
    
    # Write the fixed endpoints file
    filepath = os.path.join('app', 'fixed_endpoints.py')
    with open(filepath, 'w') as f:
        f.write(file_content)
    
    logger.info(f"Created fixed endpoints file: {filepath}")
    return filepath

def modify_app_py(fixed_endpoints_path):
    """Modify app.py to import and use the fixed endpoints"""
    logger.info("Modifying app.py...")
    
    app_py_path = os.path.join('app', 'app.py')
    backup_path = os.path.join('app', 'app.py.bak')
    
    # Create backup
    if os.path.exists(app_py_path):
        with open(app_py_path, 'r') as f:
            original_content = f.read()
            
        with open(backup_path, 'w') as f:
            f.write(original_content)
        
        logger.info(f"Created backup of app.py: {backup_path}")
    
    # Add import for fixed endpoints
    try:
        # Read existing content
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Check if fixed_endpoints already imported
        if 'from app.fixed_endpoints import register_endpoints' in content:
            logger.info("Fixed endpoints already imported in app.py")
        else:
            # Find the line with new_endpoints import
            import_line = 'from new_endpoints import register_endpoints'
            fixed_import = 'from app.fixed_endpoints import register_endpoints'
            
            if import_line in content:
                # Replace with fixed import
                content = content.replace(import_line, f"# {import_line} - Temporarily disabled\n{fixed_import}")
            else:
                # Add import after other imports
                import_section = content.find('import')
                if import_section != -1:
                    # Find the end of import section
                    import_end = content.find('\n\n', import_section)
                    if import_end != -1:
                        content = content[:import_end] + f"\n{fixed_import}" + content[import_end:]
                    else:
                        # Fallback: just add at the beginning
                        content = f"{fixed_import}\n\n" + content
                else:
                    # Fallback: just add at the beginning
                    content = f"{fixed_import}\n\n" + content
            
            # Write modified content
            with open(app_py_path, 'w') as f:
                f.write(content)
            
            logger.info("Modified app.py to use fixed endpoints")
            
    except Exception as e:
        logger.error(f"Error modifying app.py: {e}", exc_info=True)
        logger.info("Rolling back changes...")
        
        if os.path.exists(backup_path):
            # Restore from backup
            with open(backup_path, 'r') as f:
                original_content = f.read()
                
            with open(app_py_path, 'w') as f:
                f.write(original_content)
            
            logger.info("Restored app.py from backup")
        
        return False
    
    return True

def create_restart_script():
    """Create a script to restart the Flask server"""
    logger.info("Creating restart script...")
    
    script_content = '''#!/usr/bin/env python3
"""
Restart Flask server script
This script stops and restarts the Flask server process
"""
import os
import signal
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_flask_pid():
    """Find PID of the Flask server process"""
    try:
        # Using pgrep to find Flask process
        process = subprocess.Popen(['pgrep', '-f', 'python.*app/app.py'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        
        if stdout:
            pids = stdout.decode().strip().split('\\n')
            if pids:
                return int(pids[0])
        
        # Try alternative method using ps and grep
        process = subprocess.Popen(['ps', 'aux'], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        
        if stdout:
            lines = stdout.decode().strip().split('\\n')
            for line in lines:
                if 'python' in line and 'app/app.py' in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        return int(parts[1])
        
        return None
    except Exception as e:
        logger.error(f"Error finding Flask PID: {e}")
        return None

def stop_flask_server():
    """Stop the Flask server process"""
    pid = find_flask_pid()
    
    if pid:
        logger.info(f"Found Flask server with PID {pid}")
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Sent SIGTERM to PID {pid}")
            
            # Wait for process to terminate
            for _ in range(5):
                time.sleep(1)
                try:
                    os.kill(pid, 0)  # Check if process exists
                except OSError:
                    logger.info(f"Process {pid} terminated")
                    return True
            
            # Force kill if still running
            try:
                os.kill(pid, signal.SIGKILL)
                logger.info(f"Sent SIGKILL to PID {pid}")
                return True
            except OSError:
                logger.info(f"Process {pid} already terminated")
                return True
                
        except Exception as e:
            logger.error(f"Error stopping Flask server: {e}")
            return False
    else:
        logger.info("Flask server not running")
        return True

def start_flask_server():
    """Start the Flask server"""
    try:
        logger.info("Starting Flask server...")
        
        # Start Flask in a new process
        subprocess.Popen(['python', 'app/app.py'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        start_new_session=True)
        
        logger.info("Flask server started")
        return True
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Flask Server Restart Script ===")
    
    # Stop the server if running
    stop_result = stop_flask_server()
    
    if stop_result:
        # Wait a moment before starting
        time.sleep(2)
        
        # Start the server
        start_result = start_flask_server()
        
        if start_result:
            logger.info("Flask server successfully restarted")
        else:
            logger.error("Failed to start Flask server")
    else:
        logger.error("Failed to stop Flask server")
'''
    
    # Write the restart script
    filepath = 'restart_server.py'
    with open(filepath, 'w') as f:
        f.write(script_content)
    
    # Make executable
    try:
        os.chmod(filepath, 0o755)
    except:
        pass
    
    logger.info(f"Created restart script: {filepath}")
    return filepath

def main():
    """Main function"""
    logger.info("=== Bitcoin LSTM Application Fix Script ===")
    
    try:
        # Create fixed endpoints file
        fixed_endpoints_path = create_fixed_endpoints()
        
        # Modify app.py
        if modify_app_py(fixed_endpoints_path):
            logger.info("Successfully modified app.py")
        else:
            logger.error("Failed to modify app.py")
            
        # Create restart script
        restart_script = create_restart_script()
        
        logger.info("\n=== Fix Completed ===")
        logger.info("To apply the fix, run the restart script:")
        logger.info(f"  python {restart_script}")
        logger.info("\nYou should now be able to access:")
        logger.info("  - http://localhost:5000/models")
        logger.info("  - http://localhost:5000/training_status")
        
    except Exception as e:
        logger.error(f"Error in fix script: {e}")
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
