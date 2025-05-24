"""
Enhanced model service with improved error handling and reporting
"""
import os
import json
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedModelService:
    """Enhanced model service with better error handling and progress tracking"""
    
    def __init__(self):
        self.app = None
        self.model_configs = {}
        self.training_status = {}
        self.lock = threading.Lock()
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.load_configs()
        logger.info("Enhanced model service initialized")
        
    def load_configs(self):
        """Load model configurations from disk"""
        try:
            config_dir = os.path.join(os.path.dirname(self.app.instance_path), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            for model_type in ['lstm', 'gru', 'cnn', 'transformer']:
                config_path = os.path.join(config_dir, f'{model_type}_config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        self.model_configs[model_type] = json.load(f)
                else:
                    # Create default config
                    self.model_configs[model_type] = self.get_default_config(model_type)
                    with open(config_path, 'w') as f:
                        json.dump(self.model_configs[model_type], f, indent=2)
        except Exception as e:
            logger.error(f"Error loading model configs: {e}")
            # Use defaults if loading fails
            for model_type in ['lstm', 'gru', 'cnn', 'transformer']:
                self.model_configs[model_type] = self.get_default_config(model_type)
    
    def get_default_config(self, model_type):
        """Get default configuration for a model type"""
        base_config = {
            'epochs': 50,
            'batch_size': 32,
            'learning_rate': 0.001,
            'lookback': 24,
            'dropout': 0.2,
            'validation_split': 0.2,
            'early_stopping': True,
            'patience': 10
        }
        
        if model_type == 'lstm':
            base_config.update({
                'lstm_units': 50,
                'recurrent_dropout': 0.1,
                'layers': 2
            })
        elif model_type == 'gru':
            base_config.update({
                'gru_units': 50,
                'recurrent_dropout': 0.1,
                'layers': 2
            })
        elif model_type == 'transformer':
            base_config.update({
                'num_heads': 4,
                'd_model': 64,
                'ff_dim': 128
            })
        elif model_type == 'cnn':
            base_config.update({
                'filters': [32, 64, 128],
                'kernel_size': [3, 3, 3]
            })
            
        return base_config
    
    def get_model_config(self, model_type):
        """Get configuration for a specific model type"""
        return self.model_configs.get(model_type.lower(), self.get_default_config(model_type.lower()))
    
    def update_model_config(self, model_type, config_updates):
        """Update model configuration"""
        try:
            model_type = model_type.lower()
            with self.lock:
                if model_type not in self.model_configs:
                    self.model_configs[model_type] = self.get_default_config(model_type)
                
                # Update config with new values
                self.model_configs[model_type].update(config_updates)
                
                # Save updated config
                config_dir = os.path.join(os.path.dirname(self.app.instance_path), 'config')
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir)
                
                config_path = os.path.join(config_dir, f'{model_type}_config.json')
                with open(config_path, 'w') as f:
                    json.dump(self.model_configs[model_type], f, indent=2)
                
                logger.info(f"Updated {model_type} configuration")
                return True
        except Exception as e:
            logger.error(f"Error updating model config: {e}")
            return False
    
    def get_training_progress(self, model_type):
        """Get training progress for a specific model"""
        model_type = model_type.lower()
        progress = self.training_status.get(model_type, {})
        
        # Return a valid progress structure even if none exists
        if not progress:
            return {
                'status': 'idle',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'metrics': {},
                'message': 'No training in progress'
            }
            
        return progress
    
    def update_training_progress(self, model_type, progress_data):
        """Update training progress"""
        try:
            model_type = model_type.lower()
            with self.lock:
                if model_type not in self.training_status:
                    self.training_status[model_type] = {}
                
                # Update with new progress data
                self.training_status[model_type].update(progress_data)
                self.training_status[model_type]['last_updated'] = time.time()
                
                logger.debug(f"Updated {model_type} training progress: {progress_data}")
                return True
        except Exception as e:
            logger.error(f"Error updating training progress: {e}")
            return False
    
    def get_model_status(self, model_type):
        """Get overall status of a model"""
        model_type = model_type.lower()
        try:
            # Check if model file exists
            models_dir = os.path.join(os.path.dirname(self.app.instance_path), 'models')
            model_path = os.path.join(models_dir, f'{model_type}_model.h5')
            
            if os.path.exists(model_path):
                mtime = os.path.getmtime(model_path)
                last_trained = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # Check for info file
                info_path = os.path.join(models_dir, f'{model_type}_model_info.json')
                if os.path.exists(info_path):
                    with open(info_path, 'r') as f:
                        info = json.load(f)
                        return {
                            'status': 'trained',
                            'last_trained': last_trained,
                            'performance': f"R²: {info['metrics'].get('r2', 'N/A')}, RMSE: {info['metrics'].get('rmse', 'N/A')}"
                        }
                
                return {
                    'status': 'trained',
                    'last_trained': last_trained,
                    'performance': 'Unknown'
                }
            
            # Check if training is in progress
            if model_type in self.training_status:
                progress = self.training_status[model_type]
                return {
                    'status': progress.get('status', 'unknown'),
                    'message': progress.get('message', ''),
                    'last_updated': datetime.fromtimestamp(progress.get('last_updated', 0)).strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # Not trained and not training
            return {
                'status': 'not_trained',
                'message': 'Model has not been trained yet'
            }
        except Exception as e:
            logger.error(f"Error getting model status: {e}")
            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }
    
    def train_model(self, model_type):
        """Start model training - just updates status for now as actual training is handled elsewhere"""
        model_type = model_type.lower()
        
        # Check if already training
        with self.lock:
            if model_type in self.training_status and self.training_status[model_type].get('status') == 'training':
                return False, "Model is already training"
        
        # Update status to indicate training has started
        self.update_training_progress(model_type, {
            'status': 'initializing',
            'progress': 0,
            'current_epoch': 0,
            'total_epochs': self.model_configs.get(model_type, {}).get('epochs', 50),
            'message': 'Initializing training',
            'start_time': time.time()
        })
        
        logger.info(f"Training initiated for {model_type} model")
        
        # In a real implementation, we would start the training process here
        # For this fix, we'll just update the status and let other components handle training
        
        return True, f"Training initiated for {model_type} model"
    
    def stop_training(self, model_type):
        """Stop model training"""
        model_type = model_type.lower()
        
        with self.lock:
            if model_type not in self.training_status or self.training_status[model_type].get('status') != 'training':
                return False, "No active training to stop"
            
            # Update status to indicate training should stop
            self.training_status[model_type]['status'] = 'stopping'
            self.training_status[model_type]['message'] = 'Stopping training'
            self.training_status[model_type]['last_updated'] = time.time()
        
        logger.info(f"Stopping training for {model_type} model")
        return True, f"Stopping training for {model_type} model"
    
    def reset_training_status(self, model_type):
        """Reset training status for a model that may be stuck"""
        model_type = model_type.lower()
        
        with self.lock:
            if model_type in self.training_status:
                self.training_status[model_type] = {
                    'status': 'idle',
                    'progress': 0,
                    'message': 'Training status reset',
                    'last_updated': time.time()
                }
                
        logger.info(f"Reset training status for {model_type} model")
        return True, f"Reset training status for {model_type} model"

# Create a singleton instance
enhanced_model_service = EnhancedModelService()
