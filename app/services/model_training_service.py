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
    """
    Servisas modelio kūrimui ir treniravimui.
    """
    def __init__(self):
        self.model = None
        self.training_id = None
    
    def create_model(self, parameters):
        """
        Sukuria naują modelį pagal nurodytus parametrus.
        
        Args:
            parameters (dict): Modelio parametrai
        """
        # Nustatome atsitiktinių skaičių generatorių pastovumui
        tf.random.set_seed(42)
        np.random.seed(42)
        
        model_type = parameters.get('model_type', 'LSTM')
        input_shape = (parameters.get('sequence_length', 60), parameters.get('features', 1))
        units = parameters.get('units', 64)
        layers = parameters.get('layers', 2)
        dropout = parameters.get('dropout', 0.2)
        
        # Sukuriame modelį pagal tipą
        model = Sequential()
        
        # Pirmasis sluoksnis su input shape
        if model_type == 'LSTM':
            model.add(LSTM(units=units, return_sequences=(layers > 1), input_shape=input_shape))
        elif model_type == 'GRU':
            model.add(GRU(units=units, return_sequences=(layers > 1), input_shape=input_shape))
        elif model_type == 'SimpleRNN':
            model.add(SimpleRNN(units=units, return_sequences=(layers > 1), input_shape=input_shape))
        elif model_type == 'Transformer':
            # Supaprastintas transformer modelis
            inputs = Input(shape=input_shape)
            x = Dense(units, activation='relu')(inputs)
            model = Model(inputs=inputs, outputs=x)
            layers = 1  # Transformeriui nustatome tik vieną sluoksnį paprastumui
        
        # Pridedame papildomus sluoksnius, jei reikia
        if model_type != 'Transformer':
            model.add(Dropout(dropout))
            
            # Vidiniai sluoksniai
            for i in range(1, layers):
                is_last_layer = (i == layers - 1)
                
                if model_type == 'LSTM':
                    model.add(LSTM(units=units, return_sequences=not is_last_layer))
                elif model_type == 'GRU':
                    model.add(GRU(units=units, return_sequences=not is_last_layer))
                elif model_type == 'SimpleRNN':
                    model.add(SimpleRNN(units=units, return_sequences=not is_last_layer))
                
                model.add(Dropout(dropout))
        
        # Išvesties sluoksnis
        model.add(Dense(units=1))
        
        # Optimizatoriaus pasirinkimas
        optimizer_type = parameters.get('optimizer', 'adam')
        learning_rate = parameters.get('learning_rate', 0.001)
        
        if optimizer_type == 'adam':
            optimizer = Adam(learning_rate=learning_rate)
        elif optimizer_type == 'rmsprop':
            optimizer = RMSprop(learning_rate=learning_rate)
        elif optimizer_type == 'sgd':
            optimizer = SGD(learning_rate=learning_rate)
        
        # Kompiliuojame modelį
        model.compile(
            optimizer=optimizer,
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def train_model(self, X_train, y_train, X_val, y_val, parameters):
        """
        Treniruoja modelį su nurodytais duomenimis ir parametrais.
        
        Args:
            X_train: Treniravimo duomenys
            y_train: Treniravimo tikslai
            X_val: Validavimo duomenys
            y_val: Validavimo tikslai
            parameters (dict): Treniravimo parametrai
        
        Returns:
            str: Treniravimo ID, kurį galima naudoti progreso stebėjimui
        """
        # Jei modelis dar nesukurtas, sukuriame jį
        if self.model is None:
            self.create_model(parameters)
        
        # Generuojame unikalų ID šiam treniravimui
        self.training_id = str(uuid.uuid4())
        
        # Treniravimo parametrai
        epochs = parameters.get('epochs', 50)
        batch_size = parameters.get('batch_size', 32)
        use_early_stopping = parameters.get('early_stopping', True)
        
        # Sukuriame callbacks
        callbacks = []
        
        # Progress callback
        progress_callback = TrainingProgressCallback(self.training_id, epochs)
        callbacks.append(progress_callback)
        
        # Model checkpoint
        checkpoint_path = os.path.join(MODEL_SAVE_DIR, f"{self.training_id}_best.h5")
        checkpoint = ModelCheckpoint(
            checkpoint_path,
            monitor='val_loss',
            save_best_only=True,
            mode='min',
            verbose=1
        )
        callbacks.append(checkpoint)
        
        # Early stopping, jei įjungta
        if use_early_stopping:
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                mode='min',
                verbose=1
            )
            callbacks.append(early_stopping)
        
        try:
            # Pradedame treniravimą
            history = self.model.fit(
                X_train,
                y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_val, y_val),
                callbacks=callbacks,
                verbose=1
            )
            
            # Išsaugome galutinį modelį
            self.save_model(parameters)
            
            return self.training_id
        
        except Exception as e:
            # Jei įvyksta klaida, pažymime treniravimą kaip nepavykusį
            logger.error(f"Treniravimo klaida: {str(e)}")
            progress_callback.training_log['status'] = 'failed'
            progress_callback.training_log['error'] = str(e)
            progress_callback._save_training_log()
            
            return self.training_id
    
    def save_model(self, parameters):
        """
        Išsaugo modelį ir jo metaduomenis.
        
        Args:
            parameters (dict): Modelio parametrai
        
        Returns:
            str: Modelio failo pavadinimas
        """
        if self.model is None or self.training_id is None:
            raise ValueError("Modelis turi būti sukurtas ir treniruotas prieš išsaugojimą")
        
        # Išsaugome modelį į .h5 failą
        model_path = os.path.join(MODEL_SAVE_DIR, f"{self.training_id}.h5")
        self.model.save(model_path)
        
        # Sukuriame metaduomenų failą
        metadata = {
            'id': self.training_id,
            'name': parameters.get('model_name', f"Model_{self.training_id[:8]}"),
            'parameters': parameters,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filename': f"{self.training_id}.h5"
        }
        
        metadata_path = os.path.join(MODEL_SAVE_DIR, f"{self.training_id}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        return f"{self.training_id}.h5"
    
    def load_model(self, filename):
        """
        Įkelia modelį iš failo.
        
        Args:
            filename (str): Modelio failo pavadinimas
        """
        model_path = os.path.join(MODEL_SAVE_DIR, filename)
        self.model = load_model(model_path)
        self.training_id = filename.split('.')[0]
        
        return self.model
    
    def get_training_status(self, training_id):
        """
        Gauna treniravimo būseną pagal ID.
        
        Args:
            training_id (str): Treniravimo ID
        
        Returns:
            dict: Treniravimo būsenos informacija
        """
        log_path = os.path.join(TRAINING_LOG_DIR, f"{training_id}.json")
        
        if not os.path.exists(log_path):
            return {
                'error': 'Treniravimo žurnalas nerastas'
            }
        
        with open(log_path, 'r') as f:
            status = json.load(f)
        
        return status