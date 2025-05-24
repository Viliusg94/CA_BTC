import threading
import time
import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
import requests
import pickle

logger = logging.getLogger(__name__)

class RealTrainingService:
    """Real model training service with stop functionality"""
    
    def __init__(self):
        self.training_jobs = {}
        self.stop_flags = {}
        self.progress_callbacks = {}
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        
    def start_training(self, model_type: str, config: Dict[str, Any], 
                      progress_callback: Optional[Callable] = None) -> str:
        """Start real model training"""
        job_id = f"{model_type}_{int(time.time())}"
        
        # Initialize stop flag
        self.stop_flags[job_id] = threading.Event()
        
        # Store progress callback
        if progress_callback:
            self.progress_callbacks[job_id] = progress_callback
        
        # Create training thread
        training_thread = threading.Thread(
            target=self._train_model_real,
            args=(job_id, model_type, config),
            daemon=True
        )
        
        # Store job info
        self.training_jobs[job_id] = {
            'model_type': model_type,
            'status': 'initializing',
            'progress': 0,
            'start_time': datetime.now(),
            'config': config,
            'thread': training_thread,
            'current_epoch': 0,
            'total_epochs': config.get('epochs', 50),
            'metrics': {},
            'error': None
        }
        
        # Start training
        training_thread.start()
        logger.info(f"Started real training for {model_type} with job_id: {job_id}")
        
        return job_id
    
    def stop_training(self, job_id: str) -> bool:
        """Stop training for a specific job"""
        if job_id not in self.training_jobs:
            return False
        
        # Set stop flag
        if job_id in self.stop_flags:
            self.stop_flags[job_id].set()
            logger.info(f"Stop signal sent for job {job_id}")
        
        # Update job status
        if job_id in self.training_jobs:
            self.training_jobs[job_id]['status'] = 'stopping'
            self._update_progress(job_id, "Training stopped by user")
        
        return True
    
    def get_training_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current training status"""
        return self.training_jobs.get(job_id)
    
    def get_all_training_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all training jobs"""
        return self.training_jobs
    
    def _update_progress(self, job_id: str, message: str, progress: Optional[int] = None, 
                        metrics: Optional[Dict] = None):
        """Update training progress"""
        if job_id in self.training_jobs:
            job = self.training_jobs[job_id]
            job['last_update'] = datetime.now()
            job['message'] = message
            
            if progress is not None:
                job['progress'] = progress
            
            if metrics:
                job['metrics'].update(metrics)
            
            # Call progress callback if available
            if job_id in self.progress_callbacks:
                try:
                    self.progress_callbacks[job_id](job)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
    
    def _fetch_bitcoin_data(self, days: int = 365) -> pd.DataFrame:
        """Fetch Bitcoin price data from Binance API"""
        try:
            self._update_progress(None, "Fetching Bitcoin data from Binance API...")
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)
            
            url = "https://api.binance.com/api/v3/klines"
            all_klines = []
            current_start = start_ts
            
            while current_start < end_ts:
                params = {
                    'symbol': 'BTCUSDT',
                    'interval': '1h',
                    'startTime': current_start,
                    'endTime': end_ts,
                    'limit': 1000
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                klines = response.json()
                
                if not klines:
                    break
                
                all_klines.extend(klines)
                current_start = int(klines[-1][0]) + 1
                time.sleep(0.1)  # Rate limiting
            
            # Convert to DataFrame
            columns = ['time', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades',
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
            
            df = pd.DataFrame(all_klines, columns=columns)
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            logger.info(f"Fetched {len(df)} rows of Bitcoin data")
            return df[['time'] + numeric_columns].sort_values('time')
            
        except Exception as e:
            logger.error(f"Error fetching Bitcoin data: {e}")
            # Return sample data as fallback
            return self._generate_sample_data(days)
    
    def _generate_sample_data(self, days: int) -> pd.DataFrame:
        """Generate sample Bitcoin data for testing"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                             end=datetime.now(), freq='H')
        
        # Generate realistic Bitcoin price data
        np.random.seed(42)
        base_price = 45000
        prices = []
        current_price = base_price
        
        for i in range(len(dates)):
            change = np.random.normal(0, 0.02) * current_price
            current_price += change
            current_price = max(10000, min(100000, current_price))  # Reasonable bounds
            prices.append(current_price)
        
        df = pd.DataFrame({
            'time': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, len(dates))
        })
        
        return df
    
    def _prepare_data(self, df: pd.DataFrame, sequence_length: int = 24) -> tuple:
        """Prepare data for training"""
        from sklearn.preprocessing import MinMaxScaler
        
        # Feature columns
        feature_columns = ['open', 'high', 'low', 'close', 'volume']
        target_column = 'close'
        
        # Normalize data
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df[feature_columns])
        
        # Create sequences
        X, y = [], []
        target_idx = feature_columns.index(target_column)
        
        for i in range(len(scaled_data) - sequence_length):
            X.append(scaled_data[i:i + sequence_length])
            y.append(scaled_data[i + sequence_length, target_idx])
        
        X = np.array(X)
        y = np.array(y)
        
        # Train-test split
        split_index = int(len(X) * 0.8)
        X_train, X_test = X[:split_index], X[split_index:]
        y_train, y_test = y[:split_index], y[split_index:]
        
        return X_train, X_test, y_train, y_test, scaler, feature_columns
    
    def _create_model(self, model_type: str, input_shape: tuple, config: Dict[str, Any]):
        """Create model based on type"""
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, Conv1D, MaxPooling1D, Flatten
            from tensorflow.keras.layers import MultiHeadAttention, LayerNormalization, GlobalAveragePooling1D
            from tensorflow.keras.optimizers import Adam
            
            model = Sequential()
            
            if model_type.lower() == 'lstm':
                model.add(LSTM(config.get('units', 50), 
                              return_sequences=True, 
                              input_shape=input_shape,
                              dropout=config.get('dropout', 0.2)))
                model.add(LSTM(config.get('units', 50), 
                              dropout=config.get('dropout', 0.2)))
                model.add(Dense(25))
                model.add(Dense(1))
                
            elif model_type.lower() == 'gru':
                model.add(GRU(config.get('units', 50), 
                             return_sequences=True, 
                             input_shape=input_shape,
                             dropout=config.get('dropout', 0.2)))
                model.add(GRU(config.get('units', 50), 
                             dropout=config.get('dropout', 0.2)))
                model.add(Dense(25))
                model.add(Dense(1))
                
            elif model_type.lower() == 'cnn':
                model.add(Conv1D(filters=config.get('filters', 64), 
                                kernel_size=config.get('kernel_size', 3), 
                                activation='relu', 
                                input_shape=input_shape))
                model.add(MaxPooling1D(pool_size=2))
                model.add(Conv1D(filters=config.get('filters', 32), 
                                kernel_size=config.get('kernel_size', 3), 
                                activation='relu'))
                model.add(Dropout(config.get('dropout', 0.2)))
                model.add(Flatten())
                model.add(Dense(50, activation='relu'))
                model.add(Dense(1))
                
            elif model_type.lower() == 'transformer':
                # Simplified transformer implementation
                inputs = tf.keras.Input(shape=input_shape)
                
                # Multi-head attention
                attention = MultiHeadAttention(
                    num_heads=config.get('num_heads', 8),
                    key_dim=config.get('key_dim', 64)
                )(inputs, inputs)
                
                # Add & Norm
                attention = LayerNormalization()(inputs + attention)
                
                # Feed Forward
                ff = Dense(config.get('ff_dim', 256), activation='relu')(attention)
                ff = Dense(input_shape[-1])(ff)
                
                # Add & Norm
                outputs = LayerNormalization()(attention + ff)
                
                # Global pooling and output
                outputs = GlobalAveragePooling1D()(outputs)
                outputs = Dense(50, activation='relu')(outputs)
                outputs = Dropout(config.get('dropout', 0.2))(outputs)
                outputs = Dense(1)(outputs)
                
                model = tf.keras.Model(inputs=inputs, outputs=outputs)
            
            # Compile model
            model.compile(
                optimizer=Adam(learning_rate=config.get('learning_rate', 0.001)),
                loss='mse',
                metrics=['mae']
            )
            
            return model
            
        except ImportError as e:
            logger.error(f"TensorFlow not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating {model_type} model: {e}")
            return None
    
    def _train_model_real(self, job_id: str, model_type: str, config: Dict[str, Any]):
        """Real model training implementation"""
        try:
            # Update status
            self.training_jobs[job_id]['status'] = 'data_preparation'
            self._update_progress(job_id, "Preparing data...", 5)
            
            # Check for stop signal
            if self.stop_flags[job_id].is_set():
                self._handle_training_stop(job_id)
                return
            
            # Fetch and prepare data
            df = self._fetch_bitcoin_data(days=config.get('data_days', 365))
            self._update_progress(job_id, "Data fetched, preprocessing...", 10)
            
            sequence_length = config.get('sequence_length', 24)
            X_train, X_test, y_train, y_test, scaler, feature_columns = self._prepare_data(df, sequence_length)
            
            self._update_progress(job_id, "Data preprocessed, creating model...", 15)
            
            # Check for stop signal
            if self.stop_flags[job_id].is_set():
                self._handle_training_stop(job_id)
                return
            
            # Create model
            input_shape = (sequence_length, len(feature_columns))
            model = self._create_model(model_type, input_shape, config)
            
            if model is None:
                self._handle_training_error(job_id, "Failed to create model")
                return
            
            self._update_progress(job_id, "Model created, starting training...", 20)
            
            # Update status
            self.training_jobs[job_id]['status'] = 'training'
            
            # Training parameters
            epochs = config.get('epochs', 50)
            batch_size = config.get('batch_size', 32)
            
            # Custom training loop with stop checking
            import tensorflow as tf
            
            optimizer = tf.keras.optimizers.Adam(learning_rate=config.get('learning_rate', 0.001))
            loss_fn = tf.keras.losses.MeanSquaredError()
            
            train_dataset = tf.data.Dataset.from_tensor_slices((X_train, y_train))
            train_dataset = train_dataset.batch(batch_size).shuffle(1000)
            
            test_dataset = tf.data.Dataset.from_tensor_slices((X_test, y_test))
            test_dataset = test_dataset.batch(batch_size)
            
            training_history = []
            
            for epoch in range(epochs):
                # Check for stop signal
                if self.stop_flags[job_id].is_set():
                    self._handle_training_stop(job_id)
                    return
                
                # Update current epoch
                self.training_jobs[job_id]['current_epoch'] = epoch + 1
                
                # Training step
                epoch_loss = 0
                epoch_mae = 0
                num_batches = 0
                
                for batch_x, batch_y in train_dataset:
                    with tf.GradientTape() as tape:
                        predictions = model(batch_x, training=True)
                        loss = loss_fn(batch_y, predictions)
                    
                    gradients = tape.gradient(loss, model.trainable_variables)
                    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
                    
                    epoch_loss += loss
                    epoch_mae += tf.keras.metrics.mean_absolute_error(batch_y, predictions)
                    num_batches += 1
                
                # Validation step
                val_loss = 0
                val_mae = 0
                val_batches = 0
                
                for batch_x, batch_y in test_dataset:
                    predictions = model(batch_x, training=False)
                    val_loss += loss_fn(batch_y, predictions)
                    val_mae += tf.keras.metrics.mean_absolute_error(batch_y, predictions)
                    val_batches += 1
                
                # Calculate metrics
                avg_loss = float(epoch_loss / num_batches)
                avg_mae = float(epoch_mae / num_batches)
                avg_val_loss = float(val_loss / val_batches) if val_batches > 0 else 0
                avg_val_mae = float(val_mae / val_batches) if val_batches > 0 else 0
                
                training_history.append({
                    'epoch': epoch + 1,
                    'loss': avg_loss,
                    'mae': avg_mae,
                    'val_loss': avg_val_loss,
                    'val_mae': avg_val_mae
                })
                
                # Update progress
                progress = 20 + int((epoch + 1) / epochs * 70)
                metrics = {
                    'loss': avg_loss,
                    'mae': avg_mae,
                    'val_loss': avg_val_loss,
                    'val_mae': avg_val_mae
                }
                
                message = f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}, Val Loss: {avg_val_loss:.4f}"
                self._update_progress(job_id, message, progress, metrics)
                
                # Early stopping if loss is not improving
                if len(training_history) > 10:
                    recent_losses = [h['val_loss'] for h in training_history[-5:]]
                    if all(recent_losses[i] >= recent_losses[i+1] for i in range(len(recent_losses)-1)):
                        logger.info(f"Early stopping at epoch {epoch + 1}")
                        break
            
            # Check for stop signal before saving
            if self.stop_flags[job_id].is_set():
                self._handle_training_stop(job_id)
                return
            
            # Final evaluation
            self._update_progress(job_id, "Training completed, evaluating model...", 90)
            
            # Calculate final metrics
            y_pred = model.predict(X_test)
            
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Calculate MAPE
            mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            
            final_metrics = {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2),
                'mape': float(mape)
            }
            
            # Save model and scaler
            model_path = os.path.join(self.models_dir, f'{model_type.lower()}_model.h5')
            scaler_path = os.path.join(self.models_dir, f'{model_type.lower()}_scaler.pkl')
            info_path = os.path.join(self.models_dir, f'{model_type.lower()}_model_info.json')
            
            model.save(model_path)
            
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            # Save model info
            model_info = {
                'model_type': model_type,
                'timestamp': datetime.now().isoformat(),
                'config': config,
                'metrics': final_metrics,
                'training_history': training_history,
                'feature_columns': feature_columns,
                'sequence_length': sequence_length
            }
            
            with open(info_path, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            # Update database if available
            self._save_to_database(model_type, config, final_metrics, training_history)
            
            # Complete training
            self.training_jobs[job_id]['status'] = 'completed'
            self.training_jobs[job_id]['metrics'] = final_metrics
            self.training_jobs[job_id]['model_path'] = model_path
            self.training_jobs[job_id]['end_time'] = datetime.now()
            
            self._update_progress(job_id, "Training completed successfully!", 100, final_metrics)
            
            logger.info(f"Training completed for {model_type} (job_id: {job_id})")
            
        except Exception as e:
            logger.error(f"Training error for {model_type}: {e}")
            self._handle_training_error(job_id, str(e))
    
    def _handle_training_stop(self, job_id: str):
        """Handle training stop"""
        if job_id in self.training_jobs:
            self.training_jobs[job_id]['status'] = 'stopped'
            self.training_jobs[job_id]['end_time'] = datetime.now()
            self._update_progress(job_id, "Training stopped by user", None)
        
        logger.info(f"Training stopped for job {job_id}")
    
    def _handle_training_error(self, job_id: str, error_message: str):
        """Handle training error"""
        if job_id in self.training_jobs:
            self.training_jobs[job_id]['status'] = 'error'
            self.training_jobs[job_id]['error'] = error_message
            self.training_jobs[job_id]['end_time'] = datetime.now()
            self._update_progress(job_id, f"Training failed: {error_message}", None)
        
        logger.error(f"Training failed for job {job_id}: {error_message}")
    
    def _save_to_database(self, model_type: str, config: Dict[str, Any], 
                         metrics: Dict[str, Any], training_history: list):
        """Save model information to database"""
        try:
            from app import db, ModelHistory
            
            model_record = ModelHistory(
                model_type=model_type,
                timestamp=datetime.now(),
                epochs=config.get('epochs', 50),
                batch_size=config.get('batch_size', 32),
                learning_rate=config.get('learning_rate', 0.001),
                dropout=config.get('dropout', 0.2),
                validation_split=0.2,
                r2=metrics.get('r2'),
                mae=metrics.get('mae'),
                rmse=metrics.get('rmse'),
                training_loss=training_history[-1]['loss'] if training_history else None,
                validation_loss=training_history[-1]['val_loss'] if training_history else None,
                is_active=True,
                model_params=json.dumps(config)
            )
            
            # Deactivate previous models of the same type
            ModelHistory.query.filter_by(model_type=model_type, is_active=True).update({'is_active': False})
            
            db.session.add(model_record)
            db.session.commit()
            
            logger.info(f"Saved {model_type} model to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

# Global instance
real_training_service = RealTrainingService()
