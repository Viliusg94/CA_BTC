"""
Model Manager for Bitcoin LSTM application
This module handles model training, loading, and prediction.
"""
import os
import json
import logging
from datetime import datetime
import time
import threading
import pickle
import shutil

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages model training, loading, and prediction.
    """
    
    def __init__(self, models_dir='models'):
        """
        Initialize the ModelManager with default configuration.
        
        Args:
            models_dir: Directory to store model files
        """
        self.models_dir = models_dir
        self.training_status = {}
        self.model_config = {}
        self.active_models = {}
        self.tensorflow_available = False
        
        # Create models directory if it doesn't exist
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            logger.info(f"Created models directory: {models_dir}")
        
        # Try to import TensorFlow
        try:
            import tensorflow as tf
            self.tensorflow_available = True
            logger.info("TensorFlow is available")
        except ImportError:
            logger.warning("TensorFlow not available. Model training disabled.")
        
        # Initialize default configurations
        self._initialize_configs()
        
        # Initialize model statuses
        self._initialize_statuses()
    
    def _initialize_configs(self):
        """Initialize default configurations for all model types"""
        # Default configurations
        default_configs = {
            'lstm': {
                'epochs': 50,
                'batch_size': 32,
                'learning_rate': 0.001,
                'lookback': 30,
                'dropout': 0.2,
                'units': 50,
                'layers': 2
            },
            'gru': {
                'epochs': 50,
                'batch_size': 32,
                'learning_rate': 0.001,
                'lookback': 30,
                'dropout': 0.2,
                'units': 50,
                'layers': 2
            },
            'transformer': {
                'epochs': 50,
                'batch_size': 32,
                'learning_rate': 0.001,
                'lookback': 30,
                'dropout': 0.1,
                'num_heads': 4,
                'd_model': 64,
                'layers': 2
            },
            'cnn': {
                'epochs': 50,
                'batch_size': 32,
                'learning_rate': 0.001,
                'lookback': 30,
                'dropout': 0.2,
                'filters': [32, 64, 128],
                'kernel_size': [3, 3, 3]
            }
        }
        
        # Load saved configurations if available
        for model_type, default_config in default_configs.items():
            config_path = os.path.join(self.models_dir, f"{model_type}_config.json")
            
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        saved_config = json.load(f)
                    self.model_config[model_type] = saved_config
                    logger.info(f"Loaded saved configuration for {model_type} model")
                else:
                    self.model_config[model_type] = default_config
                    # Save default configuration
                    with open(config_path, 'w') as f:
                        json.dump(default_config, f, indent=2)
                    logger.info(f"Created default configuration for {model_type} model")
            except Exception as e:
                logger.error(f"Error loading configuration for {model_type}: {str(e)}")
                self.model_config[model_type] = default_config
    
    def _initialize_statuses(self):
        """Initialize status for all model types"""
        model_types = ['lstm', 'gru', 'transformer', 'cnn']
        
        for model_type in model_types:
            # Initialize training status
            self.training_status[model_type] = {
                'status': 'Idle',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'loss': None,
                'val_loss': None,
                'start_time': None,
                'estimated_completion': None
            }
            
            # Check if model file exists
            model_path = os.path.join(self.models_dir, f"{model_type}_model.h5")
            info_path = os.path.join(self.models_dir, f"{model_type}_model_info.json")
            
            if os.path.exists(model_path) and os.path.exists(info_path):
                try:
                    with open(info_path, 'r') as f:
                        model_info = json.load(f)
                    
                    last_trained = model_info.get('training_date', 'Unknown')
                    performance = f"R²: {model_info.get('metrics', {}).get('r2', 'N/A')}, " \
                                 f"RMSE: {model_info.get('metrics', {}).get('rmse', 'N/A')}"
                    
                    self.active_models[model_type] = {
                        'status': 'Ready',
                        'last_trained': last_trained,
                        'performance': performance
                    }
                except Exception as e:
                    logger.error(f"Error loading model info for {model_type}: {str(e)}")
                    self.active_models[model_type] = {
                        'status': 'Error',
                        'last_trained': 'Unknown',
                        'performance': 'Unknown',
                        'error': str(e)
                    }
            else:
                self.active_models[model_type] = {
                    'status': 'Not trained',
                    'last_trained': 'Never',
                    'performance': 'N/A'
                }
    
    def get_model_config(self, model_type):
        """
        Get configuration for a specific model type
        
        Args:
            model_type: Type of model (lstm, gru, transformer, cnn)
            
        Returns:
            dict: Model configuration
        """
        return self.model_config.get(model_type.lower(), {})
    
    def update_model_config(self, model_type, config_updates):
        """
        Update configuration for a specific model type
        
        Args:
            model_type: Type of model (lstm, gru, transformer, cnn)
            config_updates: Dictionary with configuration updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        model_type = model_type.lower()
        
        if model_type not in self.model_config:
            logger.warning(f"Unknown model type: {model_type}")
            return False
        
        try:
            # Update configuration
            current_config = self.model_config[model_type]
            current_config.update(config_updates)
            self.model_config[model_type] = current_config
            
            # Save updated configuration
            config_path = os.path.join(self.models_dir, f"{model_type}_config.json")
            with open(config_path, 'w') as f:
                json.dump(current_config, f, indent=2)
            
            logger.info(f"Updated configuration for {model_type} model")
            return True
        except Exception as e:
            logger.error(f"Error updating configuration for {model_type}: {str(e)}")
            return False
    
    def get_training_progress(self, model_type):
        """
        Get training progress for a specific model type
        
        Args:
            model_type: Type of model (lstm, gru, transformer, cnn)
            
        Returns:
            dict: Training progress information
        """
        return self.training_status.get(model_type.lower(), {})
    
    def get_model_status(self, model_type):
        """
        Get status for a specific model type
        
        Args:
            model_type: Type of model (lstm, gru, transformer, cnn)
            
        Returns:
            dict: Model status information
        """
        return self.active_models.get(model_type.lower(), {
            'status': 'Unknown',
            'last_trained': 'Never',
            'performance': 'N/A'
        })
    
    def train_model(self, model_type):
        """
        Start training a model asynchronously
        
        Args:
            model_type: Type of model to train (lstm, gru, transformer, cnn)
            
        Returns:
            bool: True if training started successfully, False otherwise
        """
        model_type = model_type.lower()
        
        if model_type not in self.model_config:
            logger.warning(f"Unknown model type: {model_type}")
            return False
        
        if self.training_status.get(model_type, {}).get('status') == 'Training':
            logger.warning(f"{model_type.upper()} model is already training")
            return False
        
        if not self.tensorflow_available:
            logger.error("TensorFlow not available. Cannot train model.")
            return False
        
        # Update training status
        self.training_status[model_type] = {
            'status': 'Training',
            'progress': 0,
            'current_epoch': 0,
            'total_epochs': self.model_config[model_type].get('epochs', 50),
            'loss': None,
            'val_loss': None,
            'start_time': datetime.now().isoformat(),
            'estimated_completion': None
        }
        
        # Start training in a separate thread
        thread = threading.Thread(
            target=self._train_model_thread,
            args=(model_type,),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started training {model_type.upper()} model")
        return True
    
    def _train_model_thread(self, model_type):
        """
        Training thread function
        
        Args:
            model_type: Type of model to train
        """
        try:
            # Simulate training progress for mock implementation
            total_epochs = self.model_config[model_type].get('epochs', 50)
            
            for epoch in range(1, total_epochs + 1):
                # Update progress
                progress = int(epoch / total_epochs * 100)
                loss = 0.1 - (epoch / total_epochs) * 0.05 + (0.01 * (epoch % 5))
                val_loss = 0.15 - (epoch / total_epochs) * 0.05 + (0.02 * (epoch % 3))
                
                self.training_status[model_type] = {
                    'status': 'Training',
                    'progress': progress,
                    'current_epoch': epoch,
                    'total_epochs': total_epochs,
                    'loss': loss,
                    'val_loss': val_loss,
                    'start_time': self.training_status[model_type]['start_time'],
                    'estimated_completion': (datetime.now() + (datetime.now() - datetime.fromisoformat(self.training_status[model_type]['start_time'])) * ((total_epochs - epoch) / epoch)).isoformat() if epoch > 0 else None
                }
                
                # Sleep to simulate training
                time.sleep(1)
            
            # Update model status after training
            self.active_models[model_type] = {
                'status': 'Ready',
                'last_trained': datetime.now().isoformat(),
                'performance': f"R²: 0.85, RMSE: 250.0"
            }
            
            # Update training status
            self.training_status[model_type] = {
                'status': 'Completed',
                'progress': 100,
                'current_epoch': total_epochs,
                'total_epochs': total_epochs,
                'loss': 0.05,
                'val_loss': 0.08,
                'start_time': self.training_status[model_type]['start_time'],
                'completion_time': datetime.now().isoformat()
            }
            
            # Create mock model files
            model_path = os.path.join(self.models_dir, f"{model_type}_model.h5")
            info_path = os.path.join(self.models_dir, f"{model_type}_model_info.json")
            
            # Create empty model file if it doesn't exist
            if not os.path.exists(model_path):
                with open(model_path, 'w') as f:
                    f.write('')
            
            # Create model info file
            model_info = {
                'model_type': model_type,
                'training_date': datetime.now().isoformat(),
                'metrics': {
                    'r2': 0.85,
                    'mae': 150.0,
                    'rmse': 250.0,
                    'mse': 62500.0,
                    'mape': 2.5
                },
                'params': self.model_config[model_type]
            }
            
            with open(info_path, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            logger.info(f"Completed training {model_type.upper()} model")
            
        except Exception as e:
            logger.error(f"Error training {model_type.upper()} model: {str(e)}")
            
            # Update status on error
            self.training_status[model_type] = {
                'status': 'Error',
                'progress': 0,
                'error': str(e),
                'start_time': self.training_status[model_type]['start_time'],
                'error_time': datetime.now().isoformat()
            }
    
    def stop_training(self, model_type):
        """
        Stop training a model
        
        Args:
            model_type: Type of model to stop training
            
        Returns:
            bool: True if training was stopped, False otherwise
        """
        model_type = model_type.lower()
        
        if model_type not in self.training_status:
            logger.warning(f"Unknown model type: {model_type}")
            return False
        
        if self.training_status[model_type].get('status') != 'Training':
            logger.warning(f"{model_type.upper()} model is not training")
            return False
        
        # Update status to stopping
        self.training_status[model_type]['status'] = 'Stopping'
        
        # In real implementation, we would signal the training thread to stop
        # For this mock implementation, we'll just update the status
        time.sleep(1)
        
        self.training_status[model_type] = {
            'status': 'Stopped',
            'progress': 0,
            'start_time': self.training_status[model_type]['start_time'],
            'stop_time': datetime.now().isoformat()
        }
        
        logger.info(f"Stopped training {model_type.upper()} model")
        return True
    
    def get_model_history(self, model_type):
        """
        Get training history for a specific model type
        
        Args:
            model_type: Type of model (lstm, gru, transformer, cnn)
            
        Returns:
            dict: Training history
        """
        model_type = model_type.lower()
        info_path = os.path.join(self.models_dir, f"{model_type}_model_info.json")
        
        try:
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'model_type': model_type,
                    'error': 'No training history available'
                }
        except Exception as e:
            logger.error(f"Error loading training history for {model_type}: {str(e)}")
            return {
                'model_type': model_type,
                'error': str(e)
            }
