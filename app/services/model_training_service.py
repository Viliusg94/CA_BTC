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
    """
    Servisas skirtas modelio apmokymo procesui su automatiniu išsaugojimų valdymu.
    """
    
    def __init__(self, model_id, model=None):
        """
        Inicializuoja apmokymo servisą
        
        Args:
            model_id (str): Modelio ID
            model (object): Modelio objektas (pvz., Keras modelis)
        """
        self.model_id = model_id
        self.model = model
        
        # Apmokymo konfigūracija
        self.epochs = 50
        self.batch_size = 32
        self.validation_split = 0.2
        self.early_stopping = True
        self.patience = 5
        
        # Išsaugojimų konfigūracija
        self.checkpoint_service = CheckpointService(model_id)
        self.save_checkpoints = True
        self.checkpoint_interval = 5
        self.max_checkpoints = 10
        self.metric_to_monitor = 'val_loss'
        self.monitor_mode = 'min'
    
    def configure_training(self, epochs=50, batch_size=32, validation_split=0.2, early_stopping=True, patience=5):
        """
        Konfigūruoja apmokymo parametrus
        
        Args:
            epochs (int): Epochų skaičius
            batch_size (int): Batch dydis
            validation_split (float): Validavimo duomenų dalis
            early_stopping (bool): Ar naudoti ankstyvą sustabdymą
            patience (int): Kantrybės parametras ankstyvam sustabdymui
        """
        self.epochs = epochs
        self.batch_size = batch_size
        self.validation_split = validation_split
        self.early_stopping = early_stopping
        self.patience = patience
    
    def configure_checkpointing(self, save_checkpoints=True, checkpoint_interval=5, max_checkpoints=10, 
                                metric_to_monitor='val_loss', monitor_mode='min'):
        """
        Konfigūruoja išsaugojimų parametrus
        
        Args:
            save_checkpoints (bool): Ar išsaugoti tarpinius modelius
            checkpoint_interval (int): Kas kiek epochų atlikti išsaugojimą
            max_checkpoints (int): Maksimalus išsaugojimų skaičius
            metric_to_monitor (str): Metrika, pagal kurią nustatomas geriausias modelis
            monitor_mode (str): 'min' arba 'max' - ar mažesnė metrika geresnė, ar didesnė
        """
        self.save_checkpoints = save_checkpoints
        self.checkpoint_interval = checkpoint_interval
        self.max_checkpoints = max_checkpoints
        self.metric_to_monitor = metric_to_monitor
        self.monitor_mode = monitor_mode
        
        # Atnaujiname išsaugojimų servisą
        self.checkpoint_service.configure(
            save_interval=checkpoint_interval,
            max_checkpoints=max_checkpoints,
            metric_to_monitor=metric_to_monitor,
            monitor_mode=monitor_mode
        )
    
    def train(self, X_train, y_train, model_parameters=None):
        """
        Apmoko modelį su automatiniu išsaugojimų valdymu
        
        Args:
            X_train: Apmokymo duomenys
            y_train: Apmokymo etikečių duomenys
            model_parameters (dict): Modelio parametrai
            
        Returns:
            dict: Apmokymo rezultatai
        """
        try:
            # Tikriname, ar modelis yra inicializuotas
            if self.model is None:
                raise ValueError("Modelis nėra inicializuotas")
            
            # Nustatome pradines metrikas
            history = {
                'loss': [],
                'val_loss': [],
                'accuracy': [],
                'val_accuracy': []
            }
            
            # Skaidome duomenis į apmokymo ir validavimo
            if self.validation_split > 0:
                split_idx = int(len(X_train) * (1 - self.validation_split))
                X_val = X_train[split_idx:]
                y_val = y_train[split_idx:]
                X_train = X_train[:split_idx]
                y_train = y_train[:split_idx]
            
            # Inicializuojame ankstyvo sustabdymo parametrus
            best_val_loss = float('inf')
            patience_counter = 0
            
            # Pradedame apmokymo ciklą
            start_time = time.time()
            
            for epoch in range(self.epochs):
                epoch_start_time = time.time()
                
                # Apmokymo žingsnis
                train_loss, train_acc = self._train_epoch(X_train, y_train)
                
                # Validavimo žingsnis
                val_loss, val_acc = self._validate_epoch(X_val, y_val) if self.validation_split > 0 else (None, None)
                
                # Įrašome metrikas į istoriją
                history['loss'].append(train_loss)
                history['accuracy'].append(train_acc)
                
                if val_loss is not None:
                    history['val_loss'].append(val_loss)
                    history['val_accuracy'].append(val_acc)
                
                # Skaičiuojame epochos laiką
                epoch_time = time.time() - epoch_start_time
                
                # Spausdiname progresą
                self._print_progress(epoch, self.epochs, train_loss, train_acc, val_loss, val_acc, epoch_time)
                
                # Išsaugome tarpinį modelį, jei reikia
                if self.save_checkpoints and self.checkpoint_service.should_save_checkpoint(epoch):
                    # Sudarome metrikos žodyną
                    metrics = {
                        'loss': float(train_loss),
                        'accuracy': float(train_acc)
                    }
                    
                    if val_loss is not None:
                        metrics['val_loss'] = float(val_loss)
                        metrics['val_accuracy'] = float(val_acc)
                    
                    # Išgauname modelio svorius
                    weights_data = self._get_model_weights()
                    
                    # Išsaugome tarpinį modelį
                    self.checkpoint_service.save_checkpoint(
                        epoch=epoch,
                        metrics=metrics,
                        parameters=model_parameters or {},
                        weights_data=weights_data
                    )
                
                # Tikriname ankstyvą sustabdymą
                if self.early_stopping and val_loss is not None:
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        patience_counter = 0
                    else:
                        patience_counter += 1
                    
                    if patience_counter >= self.patience:
                        print(f"Ankstyvas sustabdymas po {epoch + 1} epochų")
                        break
            
            # Apmokymo pabaiga
            training_time = time.time() - start_time
            print(f"Apmokymas baigtas per {training_time:.2f} sekundžių")
            
            # Išsaugome galutinį modelį
            final_metrics = {
                'loss': float(history['loss'][-1]),
                'accuracy': float(history['accuracy'][-1])
            }
            
            if history.get('val_loss'):
                final_metrics['val_loss'] = float(history['val_loss'][-1])
                final_metrics['val_accuracy'] = float(history['val_accuracy'][-1])
            
            # Išgauname modelio svorius
            weights_data = self._get_model_weights()
            
            # Išsaugome galutinį modelį
            final_checkpoint = self.checkpoint_service.save_checkpoint(
                epoch=len(history['loss']) - 1,
                metrics=final_metrics,
                parameters=model_parameters or {},
                weights_data=weights_data
            )
            
            # Grąžiname apmokymo rezultatus
            return {
                'history': history,
                'training_time': training_time,
                'final_checkpoint_id': final_checkpoint.checkpoint_id if final_checkpoint else None,
                'best_checkpoint_id': self.checkpoint_service.best_checkpoint_id
            }
        
        except Exception as e:
            print(f"Klaida apmokant modelį: {str(e)}")
            return {
                'error': str(e),
                'history': history if 'history' in locals() else None
            }
    
    def _train_epoch(self, X_train, y_train):
        """
        Apmoko modelį vieną epochą
        
        Args:
            X_train: Apmokymo duomenys
            y_train: Apmokymo etikečių duomenys
            
        Returns:
            tuple: (loss, accuracy) - apmokymo nuostoliai ir tikslumas
        """
        # Čia turėtų būti realus modelio apmokymo kodas
        # Šis pavyzdys tik imituoja apmokymo procesą
        
        # Imituojame apmokymo žingsnį
        time.sleep(0.1)  # Imituojame apmokymo laiką
        
        # Grąžiname apsimestines metrikos (mažėjančius nuostolius, didėjantį tikslumą)
        epoch_idx = len(self._get_history_value('loss'))
        base_loss = 1.0 - 0.8 * min(1.0, epoch_idx / 30)
        loss = base_loss + np.random.normal(0, 0.05)
        accuracy = 0.5 + 0.4 * min(1.0, epoch_idx / 30) + np.random.normal(0, 0.02)
        
        return max(0.1, loss), min(0.99, max(0.5, accuracy))
    
    def _validate_epoch(self, X_val, y_val):
        """
        Validuoja modelį po epochos
        
        Args:
            X_val: Validavimo duomenys
            y_val: Validavimo etikečių duomenys
            
        Returns:
            tuple: (val_loss, val_accuracy) - validavimo nuostoliai ir tikslumas
        """
        # Čia turėtų būti realus modelio validavimo kodas
        # Šis pavyzdys tik imituoja validavimo procesą
        
        # Imituojame validavimo žingsnį
        time.sleep(0.05)  # Imituojame validavimo laiką
        
        # Grąžiname apsimestines metrikos (šiek tiek didesnes nei apmokymo)
        epoch_idx = len(self._get_history_value('loss'))
        
        # Apmokymo metrikos
        train_loss = self._get_history_value('loss')[-1] if self._get_history_value('loss') else 1.0
        train_acc = self._get_history_value('accuracy')[-1] if self._get_history_value('accuracy') else 0.5
        
        # Validavimo metrikos (šiek tiek blogesnės nei apmokymo)
        val_loss = train_loss * (1.0 + 0.1 * np.random.random())
        val_accuracy = train_acc * (1.0 - 0.05 * np.random.random())
        
        # Imituojame permokymą vėlesnėse epochose
        if epoch_idx > 20:
            overfitting_factor = min(1.0, (epoch_idx - 20) / 10) * 0.2
            val_loss = train_loss * (1.0 + 0.1 * np.random.random() + overfitting_factor)
            val_accuracy = train_acc * (1.0 - 0.05 * np.random.random() - overfitting_factor / 2)
        
        return max(0.1, val_loss), min(0.99, max(0.5, val_accuracy))
    
    def _get_history_value(self, key):
        """
        Grąžina metrikos istoriją pagal raktą
        
        Args:
            key (str): Metrikos raktas
            
        Returns:
            list: Metrikos istorija
        """
        # Ši funkcija yra pagalbinė apmokymo ir validavimo funkcijoms
        # Realiame kode ši istorija būtų saugoma modelio objekte
        
        # Grąžiname tuščią sąrašą, jei istorija dar nesukurta
        if not hasattr(self, '_history'):
            self._history = {'loss': [], 'accuracy': [], 'val_loss': [], 'val_accuracy': []}
        
        return self._history.get(key, [])
    
    def _get_model_weights(self):
        """
        Išgauna modelio svorius
        
        Returns:
            dict: Modelio svorių žodynas
        """
        # Čia turėtų būti realus svorių išgavimo kodas
        # Šis pavyzdys tik grąžina apsimestinius svorius
        
        # Imituojame modelio svorių gavimą
        # Realiame kode būtų naudojama model.get_weights() arba panašus metodas
        
        # Grąžiname apsimestinius svorius kaip numpy masyvus
        return {
            'layer1': np.random.rand(10, 10),
            'layer2': np.random.rand(10, 1)
        }
    
    def _print_progress(self, epoch, total_epochs, loss, accuracy, val_loss, val_acc, epoch_time):
        """
        Spausdina apmokymo progresą
        
        Args:
            epoch (int): Dabartinė epocha
            total_epochs (int): Bendras epochų skaičius
            loss (float): Apmokymo nuostoliai
            accuracy (float): Apmokymo tikslumas
            val_loss (float): Validavimo nuostoliai
            val_acc (float): Validavimo tikslumas
            epoch_time (float): Epochos trukmė sekundėmis
        """
        # Formuojame progreso pranešimą
        progress_str = f"Epocha {epoch + 1}/{total_epochs} - {epoch_time:.2f}s - loss: {loss:.4f} - accuracy: {accuracy:.4f}"
        
        if val_loss is not None:
            progress_str += f" - val_loss: {val_loss:.4f} - val_accuracy: {val_acc:.4f}"
        
        print(progress_str)
    
    def load_best_model(self):
        """
        Užkrauna geriausią modelį iš išsaugojimų
        
        Returns:
            tuple: (model, checkpoint) - modelio objektas ir išsaugojimo objektas
        """
        try:
            # Užkrauname geriausią išsaugojimą
            best_checkpoint = self.checkpoint_service.load_best_checkpoint()
            
            if best_checkpoint is None:
                print("Nerastas geriausias išsaugojimas")
                return None, None
            
            # Užkrauname modelio svorius
            weights_data = best_checkpoint.load_weights()
            
            if weights_data is None:
                print(f"Nerasti modelio svoriai išsaugojimui {best_checkpoint.checkpoint_id}")
                return None, best_checkpoint
            
            # Nustatome modelio svorius
            self._set_model_weights(weights_data)
            
            return self.model, best_checkpoint
        
        except Exception as e:
            print(f"Klaida užkraunant geriausią modelį: {str(e)}")
            return None, None
    
    def _set_model_weights(self, weights_data):
        """
        Nustato modelio svorius
        
        Args:
            weights_data (dict): Modelio svorių žodynas
        """
        # Čia turėtų būti realus svorių nustatymo kodas
        # Šis pavyzdys tik imituoja svorių nustatymą
        
        # Imituojame modelio svorių nustatymą
        # Realiame kode būtų naudojama model.set_weights() arba panašus metodas
        print(f"Nustatyti modelio svoriai su {len(weights_data)} sluoksniais")
        
        # Išspausdiname kiekvieno sluoksnio formą
        for layer_name, weights in weights_data.items():
            print(f"  {layer_name}: {weights.shape}")