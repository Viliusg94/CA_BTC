"""
Modelio treniravimo servisas
---------------------------
Šis modulis yra atsakingas už TensorFlow/Keras modelių kūrimą,
treniravimą ir saugojimą.
"""

import os
import json
import uuid
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Dense, LSTM, GRU, SimpleRNN, Dropout, Input
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, Callback
from tensorflow.keras.optimizers import Adam, RMSprop, SGD
from datetime import datetime
import joblib
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import logging
import time
from pathlib import Path
from app.services.checkpoint_service import CheckpointService

logger = logging.getLogger(__name__)

MODEL_SAVE_DIR = 'app/static/models'
TRAINING_LOG_DIR = 'app/static/training_logs'

# Sukuriame reikalingus katalogus
os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
os.makedirs(TRAINING_LOG_DIR, exist_ok=True)

class TrainingProgressCallback(Callback):
    """
    Keras Callback klasė, kuri seka treniravimo progresą
    ir išsaugo metrikos į failą.
    """
    def __init__(self, training_id, total_epochs):
        super().__init__()
        self.training_id = training_id
        self.total_epochs = total_epochs
        self.current_epoch = 0
        self.training_log = {
            'id': training_id,
            'status': 'running',
            'total_epochs': total_epochs,
            'current_epoch': 0,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': {
                'loss': [],
                'val_loss': [],
                'mae': [],
                'val_mae': []
            }
        }
        self._save_training_log()
    
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        self.current_epoch = epoch + 1
        
        # Atnaujiname metrikas
        self.training_log['current_epoch'] = self.current_epoch
        self.training_log['metrics']['loss'].append(float(logs.get('loss', 0)))
        self.training_log['metrics']['val_loss'].append(float(logs.get('val_loss', 0)))
        self.training_log['metrics']['mae'].append(float(logs.get('mae', 0)))
        self.training_log['metrics']['val_mae'].append(float(logs.get('val_mae', 0)))
        
        # Išsaugome treniravimo būseną
        self._save_training_log()
    
    def on_train_end(self, logs=None):
        self.training_log['status'] = 'completed'
        self.training_log['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save_training_log()
    
    def _save_training_log(self):
        log_path = os.path.join(TRAINING_LOG_DIR, f"{self.training_id}.json")
        with open(log_path, 'w') as f:
            json.dump(self.training_log, f)


class ModelTrainingService:
    """Complete model training service with real TensorFlow model implementation"""
    
    def __init__(self):
        self.training_jobs = {}
        self.training_lock = threading.Lock()
        self.tensorflow_available = False
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        
        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Try to import TensorFlow
        try:
            import tensorflow as tf
            self.tf = tf
            self.tensorflow_available = True
            logger.info("TensorFlow successfully imported for model training")
        except ImportError:
            logger.error("TensorFlow not available - model training will not work")
    
    def fetch_bitcoin_data(self, days=365):
        """Fetch Bitcoin data from Binance API for training"""
        try:
            import requests
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # Convert to milliseconds
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            url = "https://api.binance.com/api/v3/klines"
            all_klines = []
            
            current_start = start_ms
            while current_start < end_ms:
                params = {
                    'symbol': 'BTCUSDT',
                    'interval': '15m',  # 15-minute intervals
                    'startTime': current_start,
                    'endTime': end_ms,
                    'limit': 1000
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code != 200:
                    break
                    
                klines = response.json()
                if not klines:
                    break
                    
                all_klines.extend(klines)
                current_start = int(klines[-1][0]) + 1
                
                # Rate limiting
                time.sleep(0.1)
            
            if not all_klines:
                raise Exception("No data received from Binance API")
            
            # Convert to DataFrame
            columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                      'close_time', 'quote_asset_volume', 'number_of_trades',
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
            
            df = pd.DataFrame(all_klines, columns=columns)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Convert numeric columns
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Fetched {len(df)} data points from {df['timestamp'].min()} to {df['timestamp'].max()}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Bitcoin data: {str(e)}")
            raise
    
    def prepare_data(self, df, sequence_length=24, target_column='close'):
        """Prepare data for training"""
        try:
            # Select features
            feature_columns = ['open', 'high', 'low', 'close', 'volume']
            
            # Normalize data
            scaler = MinMaxScaler()
            df_scaled = df.copy()
            df_scaled[feature_columns] = scaler.fit_transform(df[feature_columns])
            
            # Create sequences
            X, y = [], []
            for i in range(sequence_length, len(df_scaled)):
                X.append(df_scaled[feature_columns].iloc[i-sequence_length:i].values)
                y.append(df_scaled[target_column].iloc[i])
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            return {
                'X_train': X_train,
                'X_test': X_test,
                'y_train': y_train,
                'y_test': y_test,
                'scaler': scaler,
                'feature_columns': feature_columns
            }
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
    
    def create_lstm_model(self, input_shape, config):
        """Create LSTM model"""
        if not self.tensorflow_available:
            raise Exception("TensorFlow not available")
        
        model = self.tf.keras.Sequential([
            self.tf.keras.layers.LSTM(config.get('units', 50), 
                                     return_sequences=True, 
                                     input_shape=input_shape,
                                     dropout=config.get('dropout', 0.2)),
            self.tf.keras.layers.LSTM(config.get('units', 50), 
                                     return_sequences=True,
                                     dropout=config.get('dropout', 0.2)),
            self.tf.keras.layers.LSTM(config.get('units', 50),
                                     dropout=config.get('dropout', 0.2)),
            self.tf.keras.layers.Dense(25),
            self.tf.keras.layers.Dense(1)
        ])
        
        model.compile(
            optimizer=self.tf.keras.optimizers.Adam(learning_rate=config.get('learning_rate', 0.001)),
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        return model
    
    def create_gru_model(self, input_shape, config):
        """Create GRU model"""
        if not self.tensorflow_available:
            raise Exception("TensorFlow not available")
        
        model = self.tf.keras.Sequential([
            self.tf.keras.layers.GRU(config.get('units', 50), 
                                    return_sequences=True, 
                                    input_shape=input_shape,
                                    dropout=config.get('dropout', 0.2)),
            self.tf.keras.layers.GRU(config.get('units', 50), 
                                    return_sequences=True,
                                    dropout=config.get('dropout', 0.2)),
            self.tf.keras.layers.GRU(config.get('units', 50),
                                    dropout=config.get('dropout', 0.2)),
            self.tf.keras.layers.Dense(25),
            self.tf.keras.layers.Dense(1)
        ])
        
        model.compile(
            optimizer=self.tf.keras.optimizers.Adam(learning_rate=config.get('learning_rate', 0.001)),
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        return model
    
    def create_cnn_model(self, input_shape, config):
        """Create CNN model"""
        if not self.tensorflow_available:
            raise Exception("TensorFlow not available")
        
        model = self.tf.keras.Sequential([
            self.tf.keras.layers.Conv1D(filters=config.get('filters', 64), 
                                       kernel_size=config.get('kernel_size', 3),
                                       activation='relu', 
                                       input_shape=input_shape),
            self.tf.keras.layers.Conv1D(filters=config.get('filters', 64), 
                                       kernel_size=config.get('kernel_size', 3),
                                       activation='relu'),
            self.tf.keras.layers.Dropout(config.get('dropout', 0.2)),
            self.tf.keras.layers.MaxPooling1D(pool_size=2),
            self.tf.keras.layers.Flatten(),
            self.tf.keras.layers.Dense(50, activation='relu'),
            self.tf.keras.layers.Dense(1)
        ])
        
        model.compile(
            optimizer=self.tf.keras.optimizers.Adam(learning_rate=config.get('learning_rate', 0.001)),
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        return model
    
    def create_transformer_model(self, input_shape, config):
        """Create simple Transformer model"""
        if not self.tensorflow_available:
            raise Exception("TensorFlow not available")
        
        sequence_length, num_features = input_shape
        d_model = config.get('d_model', 64)
        
        inputs = self.tf.keras.layers.Input(shape=input_shape)
        
        # Simple multi-head attention
        attention_output = self.tf.keras.layers.MultiHeadAttention(
            num_heads=config.get('num_heads', 4),
            key_dim=d_model // config.get('num_heads', 4)
        )(inputs, inputs)
        
        # Add & Norm
        attention_output = self.tf.keras.layers.LayerNormalization()(inputs + attention_output)
        
        # Feed forward
        ffn_output = self.tf.keras.layers.Dense(d_model * 2, activation='relu')(attention_output)
        ffn_output = self.tf.keras.layers.Dense(d_model)(ffn_output)
        ffn_output = self.tf.keras.layers.Dropout(config.get('dropout', 0.1))(ffn_output)
        
        # Add & Norm
        output = self.tf.keras.layers.LayerNormalization()(attention_output + ffn_output)
        
        # Global average pooling and final layers
        output = self.tf.keras.layers.GlobalAveragePooling1D()(output)
        output = self.tf.keras.layers.Dense(50, activation='relu')(output)
        output = self.tf.keras.layers.Dense(1)(output)
        
        model = self.tf.keras.Model(inputs=inputs, outputs=output)
        
        model.compile(
            optimizer=self.tf.keras.optimizers.Adam(learning_rate=config.get('learning_rate', 0.001)),
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        return model
    
    def calculate_metrics(self, y_true, y_pred, scaler, feature_columns):
        """Calculate model performance metrics"""
        try:
            # Inverse transform predictions
            dummy_true = np.zeros((len(y_true), len(feature_columns)))
            dummy_pred = np.zeros((len(y_pred), len(feature_columns)))
            
            # Assuming 'close' is at index 3 (open, high, low, close, volume)
            close_idx = 3
            dummy_true[:, close_idx] = y_true.flatten()
            dummy_pred[:, close_idx] = y_pred.flatten()
            
            y_true_original = scaler.inverse_transform(dummy_true)[:, close_idx]
            y_pred_original = scaler.inverse_transform(dummy_pred)[:, close_idx]
            
            # Calculate metrics
            mse = mean_squared_error(y_true_original, y_pred_original)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_true_original, y_pred_original)
            r2 = r2_score(y_true_original, y_pred_original)
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((y_true_original - y_pred_original) / y_true_original)) * 100
            
            return {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2),
                'mape': float(mape)
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {
                'mse': 0.0,
                'rmse': 0.0,
                'mae': 0.0,
                'r2': 0.0,
                'mape': 0.0
            }
    
    def start_training(self, model_type, config):
        """Start training a model"""
        if not self.tensorflow_available:
            return {
                'success': False,
                'error': 'TensorFlow not available. Please install TensorFlow to train models.'
            }
        
        job_id = f"{model_type}_{int(datetime.now().timestamp())}"
        
        # Default configuration
        default_config = {
            'epochs': 50,
            'batch_size': 32,
            'learning_rate': 0.001,
            'sequence_length': 24,
            'units': 50,
            'dropout': 0.2,
            'filters': 64,
            'kernel_size': 3,
            'num_heads': 4,
            'd_model': 64
        }
        
        # Merge with user config
        training_config = {**default_config, **config}
        
        # Initialize job
        with self.training_lock:
            self.training_jobs[job_id] = {
                'model_type': model_type,
                'status': 'starting',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': training_config['epochs'],
                'start_time': datetime.now(),
                'config': training_config,
                'error': None,
                'metrics': {}
            }
        
        # Start training in a separate thread
        training_thread = threading.Thread(
            target=self._train_model_thread,
            args=(job_id, model_type, training_config)
        )
        training_thread.daemon = True
        training_thread.start()
        
        return {
            'success': True,
            'job_id': job_id,
            'message': f'Training started for {model_type} model'
        }
    
    def _train_model_thread(self, job_id, model_type, config):
        """Training thread function"""
        try:
            logger.info(f"Starting training for {model_type} (job {job_id})")
            
            # Update status
            with self.training_lock:
                self.training_jobs[job_id]['status'] = 'fetching_data'
                self.training_jobs[job_id]['progress'] = 5
            
            # Fetch data
            df = self.fetch_bitcoin_data(days=365)
            
            # Update status
            with self.training_lock:
                self.training_jobs[job_id]['status'] = 'preparing_data'
                self.training_jobs[job_id]['progress'] = 15
            
            # Prepare data
            data = self.prepare_data(df, sequence_length=config['sequence_length'])
            
            # Update status
            with self.training_lock:
                self.training_jobs[job_id]['status'] = 'creating_model'
                self.training_jobs[job_id]['progress'] = 25
            
            # Create model
            input_shape = (config['sequence_length'], len(data['feature_columns']))
            
            if model_type.lower() == 'lstm':
                model = self.create_lstm_model(input_shape, config)
            elif model_type.lower() == 'gru':
                model = self.create_gru_model(input_shape, config)
            elif model_type.lower() == 'cnn':
                model = self.create_cnn_model(input_shape, config)
            elif model_type.lower() == 'transformer':
                model = self.create_transformer_model(input_shape, config)
            else:
                raise Exception(f"Unknown model type: {model_type}")
            
            # Update status
            with self.training_lock:
                self.training_jobs[job_id]['status'] = 'training'
                self.training_jobs[job_id]['progress'] = 30
            
            # Create custom callback to update progress
            class ProgressCallback(self.tf.keras.callbacks.Callback):
                def __init__(self, job_id, training_service, total_epochs):
                    self.job_id = job_id
                    self.training_service = training_service
                    self.total_epochs = total_epochs
                
                def on_epoch_end(self, epoch, logs=None):
                    progress = 30 + int((epoch + 1) / self.total_epochs * 60)  # 30-90%
                    with self.training_service.training_lock:
                        if self.job_id in self.training_service.training_jobs:
                            self.training_service.training_jobs[self.job_id]['current_epoch'] = epoch + 1
                            self.training_service.training_jobs[self.job_id]['progress'] = progress
                            self.training_service.training_jobs[self.job_id]['training_loss'] = logs.get('loss', 0)
                            self.training_service.training_jobs[self.job_id]['validation_loss'] = logs.get('val_loss', 0)
            
            progress_callback = ProgressCallback(job_id, self, config['epochs'])
            
            # Train model
            history = model.fit(
                data['X_train'], data['y_train'],
                epochs=config['epochs'],
                batch_size=config['batch_size'],
                validation_data=(data['X_test'], data['y_test']),
                callbacks=[progress_callback],
                verbose=0
            )
            
            # Update status
            with self.training_lock:
                self.training_jobs[job_id]['status'] = 'evaluating'
                self.training_jobs[job_id]['progress'] = 90
            
            # Evaluate model
            y_pred = model.predict(data['X_test'])
            metrics = self.calculate_metrics(
                data['y_test'], y_pred, 
                data['scaler'], data['feature_columns']
            )
            
            # Save model
            model_path = os.path.join(self.models_dir, f'{model_type.lower()}_model.h5')
            model.save(model_path)
            
            # Save scaler
            scaler_path = os.path.join(self.models_dir, f'{model_type.lower()}_scaler.pkl')
            with open(scaler_path, 'wb') as f:
                pickle.dump(data['scaler'], f)
            
            # Save model info
            model_info = {
                'model_type': model_type,
                'timestamp': datetime.now().isoformat(),
                'config': config,
                'metrics': metrics,
                'training_history': {
                    'loss': history.history['loss'][-10:],  # Last 10 epochs
                    'val_loss': history.history['val_loss'][-10:] if 'val_loss' in history.history else []
                }
            }
            
            info_path = os.path.join(self.models_dir, f'{model_type.lower()}_model_info.json')
            with open(info_path, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            # Save to database if available
            try:
                from app.app import db, ModelHistory
                with db.session.begin():
                    # Deactivate other models of same type
                    ModelHistory.query.filter_by(model_type=model_type).update({'is_active': False})
                    
                    # Create new model record
                    new_model = ModelHistory(
                        model_type=model_type,
                        r2=metrics['r2'],
                        mae=metrics['mae'],
                        rmse=metrics['rmse'],
                        training_loss=history.history['loss'][-1],
                        validation_loss=history.history['val_loss'][-1] if 'val_loss' in history.history else None,
                        epochs=config['epochs'],
                        is_active=True,
                        model_params=json.dumps(config),
                        timestamp=datetime.now()
                    )
                    
                    db.session.add(new_model)
                    db.session.commit()
                    
                logger.info(f"Saved {model_type} model to database")
            except Exception as e:
                logger.warning(f"Could not save to database: {str(e)}")
            
            # Update status - completed
            with self.training_lock:
                self.training_jobs[job_id]['status'] = 'completed'
                self.training_jobs[job_id]['progress'] = 100
                self.training_jobs[job_id]['metrics'] = metrics
                self.training_jobs[job_id]['end_time'] = datetime.now()
            
            logger.info(f"Training completed for {model_type} (job {job_id})")
            logger.info(f"Final metrics: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.2f}, MAE={metrics['mae']:.2f}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Training failed for {model_type} (job {job_id}): {error_msg}")
            logger.error(traceback.format_exc())
            
            # Update status - failed
            with self.training_lock:
                self.training_jobs[job_id]['status'] = 'failed'
                self.training_jobs[job_id]['error'] = error_msg
                self.training_jobs[job_id]['end_time'] = datetime.now()
    
    def get_training_status(self, job_id):
        """Get training status for a specific job"""
        with self.training_lock:
            return self.training_jobs.get(job_id, {})
    
    def get_all_training_jobs(self):
        """Get all training jobs"""
        with self.training_lock:
            return dict(self.training_jobs)
    
    def stop_training(self, job_id):
        """Stop a training job"""
        with self.training_lock:
            if job_id in self.training_jobs:
                self.training_jobs[job_id]['status'] = 'stopped'
                self.training_jobs[job_id]['end_time'] = datetime.now()
                return True
        return False

# Global training service instance
training_service = ModelTrainingService()