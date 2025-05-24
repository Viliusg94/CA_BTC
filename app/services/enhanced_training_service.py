import logging
import threading
import time
from datetime import datetime
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import pandas as pd

logger = logging.getLogger(__name__)

class EnhancedTrainingService:
    def __init__(self):
        self.training_jobs = {}
        self.lock = threading.Lock()
    
    def start_training(self, model_type, config, data_path):
        """Start enhanced model training with progress tracking"""
        job_id = f"{model_type}_{int(time.time())}"
        
        training_job = {
            'job_id': job_id,
            'model_type': model_type,
            'status': 'initializing',
            'progress': 0,
            'start_time': datetime.now(),
            'config': config,
            'metrics': {},
            'error': None
        }
        
        with self.lock:
            self.training_jobs[job_id] = training_job
        
        # Start training in separate thread
        thread = threading.Thread(
            target=self._train_model_thread,
            args=(job_id, model_type, config, data_path)
        )
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _train_model_thread(self, job_id, model_type, config, data_path):
        """Training thread with enhanced progress tracking"""
        try:
            # Update status
            self._update_job_status(job_id, 'loading_data', 5)
            
            # Load and preprocess data
            data = self._load_and_preprocess_data(data_path)
            self._update_job_status(job_id, 'preprocessing', 15)
            
            # Create sequences
            X, y = self._create_sequences(data, config.get('sequence_length', 24))
            self._update_job_status(job_id, 'creating_sequences', 25)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, shuffle=False
            )
            self._update_job_status(job_id, 'splitting_data', 30)
            
            # Build model
            model = self._build_model(model_type, X_train.shape, config)
            self._update_job_status(job_id, 'building_model', 35)
            
            # Custom callback for progress tracking
            progress_callback = ProgressCallback(job_id, self._update_job_progress)
            
            # Train model
            self._update_job_status(job_id, 'training', 40)
            history = model.fit(
                X_train, y_train,
                validation_data=(X_test, y_test),
                epochs=config.get('epochs', 50),
                batch_size=config.get('batch_size', 32),
                callbacks=[progress_callback],
                verbose=0
            )
            
            # Evaluate model
            self._update_job_status(job_id, 'evaluating', 90)
            metrics = self._evaluate_model(model, X_test, y_test)
            
            # Save model
            self._update_job_status(job_id, 'saving', 95)
            model_path = f"models/{model_type}_model_{job_id}.h5"
            model.save(model_path)
            
            # Update final status
            with self.lock:
                self.training_jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'end_time': datetime.now(),
                    'metrics': metrics,
                    'model_path': model_path,
                    'history': {
                        'loss': history.history['loss'],
                        'val_loss': history.history['val_loss']
                    }
                })
            
            logger.info(f"Training completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Training failed for job {job_id}: {str(e)}")
            with self.lock:
                self.training_jobs[job_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'end_time': datetime.now()
                })
    
    def _update_job_status(self, job_id, status, progress):
        """Update job status and progress"""
        with self.lock:
            if job_id in self.training_jobs:
                self.training_jobs[job_id]['status'] = status
                self.training_jobs[job_id]['progress'] = progress
    
    def _update_job_progress(self, job_id, epoch, total_epochs):
        """Update training progress"""
        base_progress = 40  # Training starts at 40%
        training_progress = 50  # Training takes 50% of total progress
        epoch_progress = (epoch / total_epochs) * training_progress
        total_progress = base_progress + epoch_progress
        
        with self.lock:
            if job_id in self.training_jobs:
                self.training_jobs[job_id]['progress'] = min(89, total_progress)
    
    def get_job_status(self, job_id):
        """Get training job status"""
        with self.lock:
            return self.training_jobs.get(job_id, {})
    
    def get_all_jobs(self):
        """Get all training jobs"""
        with self.lock:
            return dict(self.training_jobs)

class ProgressCallback(tf.keras.callbacks.Callback):
    def __init__(self, job_id, update_function):
        super().__init__()
        self.job_id = job_id
        self.update_function = update_function
        self.total_epochs = None
    
    def on_train_begin(self, logs=None):
        self.total_epochs = self.params['epochs']
    
    def on_epoch_end(self, epoch, logs=None):
        self.update_function(self.job_id, epoch + 1, self.total_epochs)

# Global instance
enhanced_training_service = EnhancedTrainingService()
