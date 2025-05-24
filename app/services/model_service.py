"""
Model training service for handling training tasks
"""
import os
import json
import time
import logging
import threading
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import requests

# Set up logging
logger = logging.getLogger(__name__)

class ModelTrainingService:
    """Service for training machine learning models with user parameters"""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        self.training_status = {}  # Dictionary to track training status
        self.active_trainings = {}  # Dictionary to track active training threads
        self.stopping = set()  # Set to track models that should stop training
          # Create data and models directories if they don't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        
    def init_app(self, app, db):
        """Initialize with Flask app and database instances"""
        self.app = app
        self.db = db
        
    def get_training_status(self, model_type):
        """Get training status for a specific model"""
        if model_type not in self.training_status:
            self.training_status[model_type] = {
                'status': 'Neapmokytas',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'N/A',
                'metrics': {},
                'error': None
            }
        return self.training_status[model_type]
        
    def train_model(self, model_type, params):
        """Start model training with the specified parameters"""
        try:
            logger.info(f"Starting training for model type: {model_type}")
            
            # Check if model_type is valid
            if model_type not in ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm']:
                return False, "Neteisingas modelio tipas"
            
            # Check if model is already training
            if model_type in self.active_trainings and self.active_trainings[model_type] is not None:
                is_alive = self.active_trainings[model_type].is_alive()
                if is_alive:
                    return False, "Modelis jau yra apmokomas"
            
            # Reset training status
            self.training_status[model_type] = {
                'status': 'Inicializuojama',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': int(params.get('epochs', 50)),
                'time_remaining': 'Apskaičiuojama...',
                'metrics': {},
                'error': None,
                'start_time': time.time(),
                'training_id': str(uuid.uuid4())
            }
            
            # Remove model from stopping set if it's there
            if model_type in self.stopping:
                self.stopping.remove(model_type)
            
            # Start training in a separate thread
            training_thread = threading.Thread(
                target=self._train_model_thread,
                args=(model_type, params),
                daemon=True
            )
            
            self.active_trainings[model_type] = training_thread
            training_thread.start()
            
            logger.info(f"Training thread started for {model_type}")
            
            return True, self.training_status[model_type]['training_id']
            
        except Exception as e:
            logger.error(f"Error starting training: {str(e)}", exc_info=True)
            self.training_status[model_type] = {
                'status': 'Klaida',
                'progress': 0,
                'error': str(e),
                'metrics': {}
            }
            return False, str(e)
    
    def stop_training(self, model_type):
        """Stop training for a specific model"""
        if model_type not in self.training_status:
            return False, "Modelis nesimoko"
        
        # Add model to stopping set
        self.stopping.add(model_type)
        
        # Update status
        self.training_status[model_type]['status'] = 'Stabdoma'
        
        logger.info(f"Requested to stop training for {model_type}")
        return True, "Apmokymas bus sustabdytas"
    
    def _train_model_thread(self, model_type, params):
        """Training function that runs in a separate thread"""
        try:
            with self.app.app_context():
                logger.info(f"Training thread is running for {model_type}")
                
                # Update status
                self.training_status[model_type]['status'] = 'Ruošiami duomenys'
                self.training_status[model_type]['progress'] = 5
                
                # Get historical data
                try:
                    df = self._get_historical_data()
                    if df is None or df.empty:
                        raise ValueError("Nepavyko gauti istorinių duomenų")
                    
                    logger.info(f"Historical data loaded, shape: {df.shape}")
                    self.training_status[model_type]['progress'] = 10
                except Exception as e:
                    logger.error(f"Error getting historical data: {str(e)}", exc_info=True)
                    self.training_status[model_type]['status'] = 'Klaida'
                    self.training_status[model_type]['error'] = f"Klaida gaunant duomenis: {str(e)}"
                    return
                
                # Prepare data
                try:
                    self.training_status[model_type]['status'] = 'Ruošiami duomenys'
                    X_train, X_test, y_train, y_test, scaler, feature_columns = self._prepare_data(df, params)
                    logger.info(f"Data prepared, X_train shape: {X_train.shape}")
                    self.training_status[model_type]['progress'] = 15
                except Exception as e:
                    logger.error(f"Error preparing data: {str(e)}", exc_info=True)
                    self.training_status[model_type]['status'] = 'Klaida'
                    self.training_status[model_type]['error'] = f"Klaida ruošiant duomenis: {str(e)}"
                    return
                
                # Create model
                try:
                    self.training_status[model_type]['status'] = 'Kuriamas modelis'
                    model = self._create_model(model_type, X_train.shape, params)
                    logger.info(f"Model created: {model_type}")
                    self.training_status[model_type]['progress'] = 20
                except Exception as e:
                    logger.error(f"Error creating model: {str(e)}", exc_info=True)
                    self.training_status[model_type]['status'] = 'Klaida'
                    self.training_status[model_type]['error'] = f"Klaida kuriant modelį: {str(e)}"
                    return
                
                # Train model
                try:
                    self.training_status[model_type]['status'] = 'Apmokomas'
                    history = self._train_model(model, X_train, y_train, X_test, y_test, model_type, params)
                    logger.info(f"Model training completed for {model_type}")
                except Exception as e:
                    logger.error(f"Error during model training: {str(e)}", exc_info=True)
                    self.training_status[model_type]['status'] = 'Klaida'
                    self.training_status[model_type]['error'] = f"Klaida apmokant modelį: {str(e)}"
                    return
                
                # If training was stopped, update status and return
                if model_type in self.stopping:
                    self.stopping.remove(model_type)
                    self.training_status[model_type]['status'] = 'Nutraukta'
                    logger.info(f"Training for {model_type} was stopped by user")
                    return
                
                # Evaluate model
                try:
                    self.training_status[model_type]['status'] = 'Vertinama'
                    self.training_status[model_type]['progress'] = 95
                    
                    # Use test data for evaluation
                    y_pred = model.predict(X_test)
                    
                    # Transform back to original scale
                    target_idx = feature_columns.index('close')
                    y_pred_original = self._inverse_transform_predictions(y_pred, scaler, target_idx, feature_columns)
                    y_test_original = self._inverse_transform_predictions(y_test.reshape(-1, 1), scaler, target_idx, feature_columns)
                    
                    # Calculate metrics
                    mse = mean_squared_error(y_test_original, y_pred_original)
                    rmse = np.sqrt(mse)
                    mae = mean_absolute_error(y_test_original, y_pred_original)
                    r2 = r2_score(y_test_original, y_pred_original)
                    mape = np.mean(np.abs((y_test_original - y_pred_original) / y_test_original)) * 100
                    
                    # Get training metrics from history
                    training_loss = history.history['loss'][-1] if history and 'loss' in history.history else None
                    validation_loss = history.history['val_loss'][-1] if history and 'val_loss' in history.history else None
                    
                    metrics = {
                        'rmse': float(rmse),
                        'mae': float(mae),
                        'r2': float(r2),
                        'mape': float(mape),
                        'mse': float(mse),
                        'training_loss': float(training_loss) if training_loss is not None else None,
                        'validation_loss': float(validation_loss) if validation_loss is not None else None
                    }
                    
                    logger.info(f"Model evaluation metrics: {metrics}")
                    self.training_status[model_type]['metrics'] = metrics
                except Exception as e:
                    logger.error(f"Error evaluating model: {str(e)}", exc_info=True)
                    self.training_status[model_type]['status'] = 'Klaida'
                    self.training_status[model_type]['error'] = f"Klaida vertinant modelį: {str(e)}"
                    return
                
                # Save model
                try:
                    self.training_status[model_type]['status'] = 'Saugoma'
                    
                    # Save model to file
                    model_filename = f"{model_type}_model.h5"
                    model_path = os.path.join(self.models_dir, model_filename)
                    model.save(model_path)
                    
                    # Save scaler
                    scaler_filename = f"{model_type}_scaler.pkl"
                    scaler_path = os.path.join(self.models_dir, scaler_filename)
                    with open(scaler_path, 'wb') as f:
                        pickle.dump(scaler, f)
                    
                    # Save model info
                    model_info = {
                        'model_type': model_type,
                        'timestamp': datetime.now().isoformat(),
                        'sequence_length': int(params.get('lookback', 30)),
                        'target_column': 'close',
                        'metrics': metrics
                    }
                    
                    info_filename = f"{model_type}_model_info.json"
                    info_path = os.path.join(self.models_dir, info_filename)
                    with open(info_path, 'w') as f:
                        json.dump(model_info, f, indent=4)
                    
                    logger.info(f"Model saved to {model_path}")
                    
                    # Save to database
                    model_params_json = json.dumps(params)
                    self._save_to_database(model_type, metrics, params, model_params_json)
                    
                    self.training_status[model_type]['progress'] = 100
                    self.training_status[model_type]['status'] = 'Baigtas'
                    logger.info(f"Training for {model_type} completed successfully")
                    
                except Exception as e:
                    logger.error(f"Error saving model: {str(e)}", exc_info=True)
                    self.training_status[model_type]['status'] = 'Klaida'
                    self.training_status[model_type]['error'] = f"Klaida išsaugant modelį: {str(e)}"
                    return
                
        except Exception as e:
            logger.error(f"Unexpected error in training thread: {str(e)}", exc_info=True)
            self.training_status[model_type]['status'] = 'Klaida'
            self.training_status[model_type]['error'] = f"Netikėta klaida: {str(e)}"
    
    def _get_historical_data(self, days=365):
        """Get historical BTC price data"""
        try:
            # First try to load cached data
            cached_data_path = os.path.join(self.data_dir, 'btc_data_1y_15m.csv')
            if os.path.exists(cached_data_path):
                logger.info(f"Loading cached data from {cached_data_path}")
                df = pd.read_csv(cached_data_path)
                df['time'] = pd.to_datetime(df['time'])
                return df
            
            # If no cached data, fetch from API
            logger.info(f"Fetching historical data for {days} days")
            
            # Attempt to fetch from Binance API
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
            symbol = "BTCUSDT"
            interval = "15m"  # 15-minute intervals
            
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)
            all_klines = []
            
            # Fetch data in chunks (Binance limits to 1000 results per request)
            current_start = start_ts
            while current_start < end_ts:
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'startTime': current_start,
                    'endTime': end_ts,
                    'limit': 1000
                }
                
                response = requests.get(BINANCE_API_URL, params=params, timeout=10)
                response.raise_for_status()
                klines = response.json()
                
                if not klines:
                    break
                    
                all_klines.extend(klines)
                current_start = int(klines[-1][0]) + 1
                
                # Sleep to avoid hitting API rate limits
                time.sleep(0.5)
            
            if not all_klines:
                raise ValueError("No data received from Binance API")
            
            # Process the data
            columns = ['time', 'open', 'high', 'low', 'close', 'volume', 
                       'close_time', 'quote_asset_volume', 'number_of_trades',
                       'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
            
            df = pd.DataFrame(all_klines, columns=columns)
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            # Convert numeric columns to float
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            # Save to cache
            os.makedirs(os.path.dirname(cached_data_path), exist_ok=True)
            df.to_csv(cached_data_path, index=False)
            
            logger.info(f"Historical data fetched and cached, shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}", exc_info=True)
            raise
    
    def _prepare_data(self, df, params):
        """Prepare data for model training"""
        try:
            # Get parameters
            sequence_length = int(params.get('lookback', 30))
            validation_split = float(params.get('validation_split', 0.2))
            
            # Define columns to normalize
            feature_columns = ['open', 'high', 'low', 'close', 'volume']
            target_column = 'close'
            
            # Sort data by time
            df = df.sort_values('time')
            
            # Create scaler and normalize data
            scaler = MinMaxScaler()
            df_normalized = df.copy()
            df_normalized[feature_columns] = scaler.fit_transform(df[feature_columns])
            
            # Create sequences for training
            X, y = self._create_sequences(df_normalized, target_column, sequence_length, feature_columns)
            
            # Split data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=validation_split, shuffle=False)
            
            logger.info(f"Data prepared: X_train: {X_train.shape}, X_test: {X_test.shape}")
            return X_train, X_test, y_train, y_test, scaler, feature_columns
        
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}", exc_info=True)
            raise
    
    def _create_sequences(self, data, target_column, sequence_length, feature_columns):
        """Create input sequences and target values for time series data"""
        X, y = [], []
        data_array = data[feature_columns].values
        target_idx = feature_columns.index(target_column)
        
        for i in range(len(data) - sequence_length):
            X.append(data_array[i:i + sequence_length])
            y.append(data_array[i + sequence_length, target_idx])
            
        return np.array(X), np.array(y)
    
    def _create_model(self, model_type, input_shape, params):
        """Create model based on model type and parameters"""
        logger.info(f"Creating model: {model_type}, input shape: {input_shape}")
        
        # Get parameters
        learning_rate = float(params.get('learning_rate', 0.001))
        dropout_rate = float(params.get('dropout', 0.2))
        
        if model_type == 'lstm':
            lstm_units = int(params.get('lstm_units', 50))
            
            model = models.Sequential()
            model.add(layers.LSTM(lstm_units, input_shape=(input_shape[1], input_shape[2]), return_sequences=True))
            model.add(layers.Dropout(dropout_rate))
            model.add(layers.LSTM(lstm_units // 2, return_sequences=False))
            model.add(layers.Dropout(dropout_rate))
            model.add(layers.Dense(20, activation='relu'))
            model.add(layers.Dense(1))
            
        elif model_type == 'gru':
            gru_units = int(params.get('lstm_units', 50))  # Can reuse lstm_units parameter
            
            model = models.Sequential()
            model.add(layers.GRU(gru_units, input_shape=(input_shape[1], input_shape[2]), return_sequences=True))
            model.add(layers.Dropout(dropout_rate))
            model.add(layers.GRU(gru_units // 2, return_sequences=False))
            model.add(layers.Dropout(dropout_rate))
            model.add(layers.Dense(20, activation='relu'))
            model.add(layers.Dense(1))
            
        elif model_type == 'cnn':
            cnn_filters = int(params.get('lstm_units', 64))  # Can reuse lstm_units parameter
            
            model = models.Sequential()
            model.add(layers.Conv1D(filters=cnn_filters, kernel_size=3, activation='relu', 
                               input_shape=(input_shape[1], input_shape[2])))
            model.add(layers.MaxPooling1D(pool_size=2))
            model.add(layers.Conv1D(filters=cnn_filters//2, kernel_size=3, activation='relu'))
            model.add(layers.MaxPooling1D(pool_size=2))
            model.add(layers.Flatten())
            model.add(layers.Dense(50, activation='relu'))
            model.add(layers.Dropout(dropout_rate))
            model.add(layers.Dense(1))
            
        elif model_type == 'cnn_lstm':
            cnn_lstm_filters = int(params.get('lstm_units', 64))  # Can reuse lstm_units parameter
            
            model = models.Sequential()
            model.add(layers.Conv1D(filters=cnn_lstm_filters, kernel_size=3, activation='relu', 
                               input_shape=(input_shape[1], input_shape[2])))
            model.add(layers.MaxPooling1D(pool_size=2))
            model.add(layers.LSTM(cnn_lstm_filters, return_sequences=False))
            model.add(layers.Dropout(dropout_rate))
            model.add(layers.Dense(20, activation='relu'))
            model.add(layers.Dense(1))
            
        elif model_type == 'transformer':
            # Get transformer-specific parameters
            num_heads = int(params.get('num_heads', 4))
            d_model = int(params.get('d_model', 64))
            
            # Input layer
            inputs = tf.keras.Input(shape=(input_shape[1], input_shape[2]))
            
            # Embedding layer
            x = layers.Dense(d_model)(inputs)
            
            # Add positional encoding
            positions = np.arange(input_shape[1])[:, np.newaxis]
            indices = np.arange(d_model)[np.newaxis, :]
            pos_encoding = np.zeros((1, input_shape[1], d_model))
            pos_encoding[0, :, 0::2] = np.sin(positions * 10000 ** (-2 * indices[0, 0::2] / d_model))
            pos_encoding[0, :, 1::2] = np.cos(positions * 10000 ** (-2 * indices[0, 1::2] / d_model))
            x = layers.Add()([x, tf.constant(pos_encoding, dtype=tf.float32)])
            
            # Transformer block
            attn_output = layers.MultiHeadAttention(num_heads=num_heads, key_dim=d_model)(x, x)
            x = layers.LayerNormalization(epsilon=1e-6)(x + attn_output)
            
            # Feed-forward layer
            ffn_output = layers.Dense(d_model*4, activation='relu')(x)
            ffn_output = layers.Dense(d_model)(ffn_output)
            x = layers.LayerNormalization(epsilon=1e-6)(x + ffn_output)
            
            # Global average pooling and output layer
            x = layers.GlobalAveragePooling1D()(x)
            x = layers.Dropout(dropout_rate)(x)
            outputs = layers.Dense(1)(x)
            
            # Create model
            model = tf.keras.Model(inputs=inputs, outputs=outputs)
        
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Compile model
        optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        model.compile(optimizer=optimizer, loss='mse')
        
        return model
    
    def _train_model(self, model, X_train, y_train, X_test, y_test, model_type, params):
        """Train the model with early stopping and progress updates"""
        # Get parameters
        epochs = int(params.get('epochs', 50))
        batch_size = int(params.get('batch_size', 32))
        
        # Create custom callback to update training progress
        class ProgressCallback(callbacks.Callback):
            def __init__(self, training_service, model_type, epochs):
                super().__init__()
                self.training_service = training_service
                self.model_type = model_type
                self.total_epochs = epochs
                self.start_time = time.time()
                
            def on_epoch_begin(self, epoch, logs=None):
                status = self.training_service.training_status[self.model_type]
                status['current_epoch'] = epoch + 1
                status['progress'] = 20 + int((epoch / self.total_epochs) * 75)  # Progress from 20% to 95%
                
                # Check if training should be stopped
                if self.model_type in self.training_service.stopping:
                    self.model.stop_training = True
                    logger.info(f"Training stopped for {self.model_type} at epoch {epoch+1}")
                
            def on_epoch_end(self, epoch, logs=None):
                logs = logs or {}
                status = self.training_service.training_status[self.model_type]
                
                # Store metrics
                status['metrics'] = {
                    'loss': logs.get('loss'),
                    'val_loss': logs.get('val_loss')
                }
                
                # Calculate time remaining
                elapsed_time = time.time() - self.start_time
                epochs_remaining = self.total_epochs - (epoch + 1)
                if epochs_remaining > 0 and epoch > 0:
                    time_per_epoch = elapsed_time / (epoch + 1)
                    remaining_time = time_per_epoch * epochs_remaining
                    hours, remainder = divmod(remaining_time, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    status['time_remaining'] = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
                
                # Update current step
                status['current_step'] = f"Epocha {epoch+1}/{self.total_epochs} - loss: {logs.get('loss', 0):.6f}, val_loss: {logs.get('val_loss', 0):.6f}"
                
        # Create callbacks
        progress_callback = ProgressCallback(self, model_type, epochs)
        early_stopping = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train model
        logger.info(f"Starting training for {model_type} model with {epochs} epochs")
        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            callbacks=[progress_callback, early_stopping],
            verbose=0
        )
        
        return history
    
    def _inverse_transform_predictions(self, predictions, scaler, target_idx, feature_columns):
        """Transform predictions back to original scale"""
        dummy = np.zeros((len(predictions), len(feature_columns)))
        dummy[:, target_idx] = predictions.flatten()
        inverse_predicted = scaler.inverse_transform(dummy)
        return inverse_predicted[:, target_idx]
    
    def _save_to_database(self, model_type, metrics, params, model_params_json):
        """Save model to database"""
        try:
            if not self.db:
                logger.warning("Database not available, skipping database save")
                return
            
            from app.database import ModelHistory
            
            # Create new model history entry
            model_history = ModelHistory(
                model_type=model_type.upper(),
                r2=metrics.get('r2'),
                mae=metrics.get('mae'),
                mse=metrics.get('mse'),
                rmse=metrics.get('rmse'),
                training_time=time.time() - self.training_status[model_type].get('start_time', time.time()),
                epochs=int(params.get('epochs', 50)),
                batch_size=int(params.get('batch_size', 32)),
                learning_rate=float(params.get('learning_rate', 0.001)),
                lookback=int(params.get('lookback', 30)),
                dropout=float(params.get('dropout', 0.2)),
                validation_split=float(params.get('validation_split', 0.2)),
                num_heads=int(params.get('num_heads', 4)) if model_type == 'transformer' else None,
                d_model=int(params.get('d_model', 64)) if model_type == 'transformer' else None,
                notes=params.get('notes', '')
            )
            
            # Set all models of this type to inactive
            with self.db.session.begin_nested():
                self.db.session.query(ModelHistory).filter_by(model_type=model_type.upper()).update({'is_active': False})
            
            # Set this model to active
            model_history.is_active = True
            
            # Add and commit
            self.db.session.add(model_history)
            self.db.session.commit()
            
            logger.info(f"Model saved to database with ID: {model_history.id}")
            
        except Exception as e:
            logger.error(f"Error saving model to database: {str(e)}", exc_info=True)
            if self.db and hasattr(self.db, 'session'):
                self.db.session.rollback()
