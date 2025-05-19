"""
Modelių modulis
--------------
Šis modulis apibrėžia neuroninius tinklus ir jų treniravimo logiką.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
import time
import random

# Čia imituojame TensorFlow/Keras biblioteką paprastam pavyzdžiui
# Realioje implementacijoje naudotumėte tikrą biblioteką

class Model:
    """Bazinė modelio klasė"""
    
    def __init__(self, config):
        """
        Inicializuoja modelį su nurodyta konfigūracija
        
        Args:
            config: Modelio konfigūracijos žodynas
        """
        self.config = config
        self.model_type = config.get('model_type', 'lstm')
        self.lookback = int(config.get('lookback', 60))
        self.prediction_steps = int(config.get('prediction_steps', 1))
        self.feature_count = int(config.get('feature_count', 5))
        self.epochs = int(config.get('epochs', 50))
        self.batch_size = int(config.get('batch_size', 32))
        self.learning_rate = float(config.get('learning_rate', 0.001))
        self.validation_split = float(config.get('validation_split', 0.2))
        self.hidden_layers = int(config.get('hidden_layers', 2))
        self.neurons_per_layer = int(config.get('neurons_per_layer', 64))
        self.dropout_rate = float(config.get('dropout_rate', 0.2))
        
        self.model = None
        self.history = None
        self.training_start_time = None
        self.training_end_time = None
        
        # Treniravimo būsena
        self.status = "Not started"
        self.progress = 0
        self.current_epoch = 0
        self.log_messages = []
        self.metrics = {
            'loss': [],
            'val_loss': [],
            'mae': [],
            'val_mae': []
        }
        
        self.add_log("Modelis inicializuotas su parametrais: " + str(config))
    
    def build_model(self):
        """Sukuria modelio architektūrą"""
        self.status = "Building model"
        self.progress = 10
        self.add_log(f"Kuriamas {self.model_type.upper()} modelis...")
        
        # Imituojame modelio kūrimą
        time.sleep(1)  # Imituojame, kad modelio kūrimas užtrunka
        
        # Imituojame modelio architektūrą
        architecture = {
            'type': self.model_type,
            'input_shape': (self.lookback, self.feature_count),
            'layers': []
        }
        
        # Pridedame sluoksnius
        for i in range(self.hidden_layers):
            architecture['layers'].append({
                'type': 'recurrent',
                'neurons': self.neurons_per_layer,
                'dropout': self.dropout_rate
            })
        
        # Pridedame išėjimo sluoksnį
        architecture['layers'].append({
            'type': 'dense',
            'neurons': self.prediction_steps
        })
        
        self.model = architecture  # Tikroje implementacijoje čia būtų Keras modelis
        self.add_log(f"Modelio architektūra sukurta: {self.hidden_layers} sluoksniai su {self.neurons_per_layer} neuronais")
        self.progress = 20
        
        return self.model
    
    def prepare_data(self):
        """Paruošia duomenis treniravimui"""
        self.status = "Preparing data"
        self.progress = 30
        self.add_log("Ruošiami duomenys treniravimui...")
        
        # Imituojame duomenų paruošimą
        time.sleep(2)  # Imituojame, kad duomenų paruošimas užtrunka
        
        # Imituojame duomenų formas
        data_info = {
            'X_train_shape': (1000, self.lookback, self.feature_count),
            'y_train_shape': (1000, self.prediction_steps),
            'X_val_shape': (200, self.lookback, self.feature_count),
            'y_val_shape': (200, self.prediction_steps)
        }
        
        self.add_log(f"Duomenys paruošti. Treniravimo pavyzdžių: 1000, Validacijos pavyzdžių: 200")
        self.progress = 40
        
        return data_info
    
    def train(self):
        """Treniruoja modelį"""
        self.status = "Training"
        self.progress = 45
        self.training_start_time = datetime.now()
        self.add_log(f"Pradedamas modelio treniravimas: {self.epochs} epochos, batch dydis: {self.batch_size}")
        
        # Imituojame modelio sukūrimą
        self.build_model()
        
        # Imituojame duomenų paruošimą
        self.prepare_data()
        
        # Imituojame treniravimo ciklą
        progress_per_epoch = 50 / self.epochs  # 50% progreso skirta treniravimui (nuo 40% iki 90%)
        
        for epoch in range(self.epochs):
            self.current_epoch = epoch + 1
            
            # Imituojame vieną epochą
            time.sleep(0.2)  # Imituojame, kad viena epocha užtrunka
            
            # Imituojame metrikos
            loss = 1.0 / (epoch + 1) + random.uniform(0, 0.1)
            val_loss = loss * (1 + random.uniform(0, 0.2))
            mae = loss * 10
            val_mae = val_loss * 10
            
            # Atnaujiname metrikas
            self.metrics['loss'].append(loss)
            self.metrics['val_loss'].append(val_loss)
            self.metrics['mae'].append(mae)
            self.metrics['val_mae'].append(val_mae)
            
            # Atnaujiname progresą
            self.progress = 40 + int((epoch + 1) * progress_per_epoch)
            
            # Pridedame žurnalo įrašą
            self.add_log(f"Epocha {epoch+1}/{self.epochs}: nuostolis = {loss:.4f}, val_nuostolis = {val_loss:.4f}, MAE = {mae:.4f}, val_MAE = {val_mae:.4f}")
        
        self.progress = 90
        self.status = "Evaluating"
        self.add_log("Modelio treniravimas baigtas. Vertinami rezultatai...")
        
        # Imituojame įvertinimą
        time.sleep(1)
        
        # Imituojame galutines metrikas
        final_metrics = {
            'loss': self.metrics['loss'][-1],
            'val_loss': self.metrics['val_loss'][-1],
            'mae': self.metrics['mae'][-1],
            'val_mae': self.metrics['val_mae'][-1],
            'accuracy': random.uniform(0.8, 0.95)
        }
        
        self.training_end_time = datetime.now()
        training_time = (self.training_end_time - self.training_start_time).total_seconds()
        
        self.add_log(f"Modelio įvertinimas: nuostolis = {final_metrics['loss']:.4f}, tikslumas = {final_metrics['accuracy']:.2f}")
        self.add_log(f"Treniravimas užtruko {training_time:.2f} sekundžių")
        
        self.progress = 100
        self.status = "Completed"
        
        return final_metrics
    
    def add_log(self, message):
        """Prideda žurnalo įrašą"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        print(log_entry)  # Taip pat spausdiname konsolėje
    
    def get_state(self):
        """Gauna dabartinę modelio būseną"""
        return {
            'status': self.status,
            'progress': self.progress,
            'current_epoch': self.current_epoch,
            'total_epochs': self.epochs,
            'metrics': self.metrics,
            'log_messages': self.log_messages,
            'config': self.config
        }
    
    def save(self, name=None):
        """
        Išsaugo modelio rezultatus
        
        Args:
            name: Modelio pavadinimas
            
        Returns:
            str: Išsaugojimo kelias
        """
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{self.model_type}_{timestamp}"
        
        # Sukuriame modelių katalogą, jei jo nėra
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
        
        # Sukuriame rezultatų objektą
        results = {
            'name': name,
            'config': self.config,
            'metrics': {
                'final_loss': self.metrics['loss'][-1] if self.metrics['loss'] else None,
                'final_val_loss': self.metrics['val_loss'][-1] if self.metrics['val_loss'] else None,
                'final_mae': self.metrics['mae'][-1] if self.metrics['mae'] else None,
                'final_val_mae': self.metrics['val_mae'][-1] if self.metrics['val_mae'] else None
            },
            'history': {
                'loss': self.metrics['loss'],
                'val_loss': self.metrics['val_loss'],
                'mae': self.metrics['mae'],
                'val_mae': self.metrics['val_mae']
            },
            'training_time': {
                'start': self.training_start_time.isoformat() if self.training_start_time else None,
                'end': self.training_end_time.isoformat() if self.training_end_time else None
            }
        }
        
        # Išsaugome rezultatus JSON faile
        file_path = os.path.join(models_dir, f"{name}.json")
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.add_log(f"Modelio rezultatai išsaugoti: {file_path}")
        
        return file_path


class LSTMModel(Model):
    """LSTM modelio klasė"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model_type = "lstm"


class GRUModel(Model):
    """GRU modelio klasė"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model_type = "gru"


class CNNModel(Model):
    """CNN modelio klasė"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model_type = "cnn"


def create_model(config):
    """
    Sukuria modelį pagal konfigūraciją
    
    Args:
        config: Modelio konfigūracijos žodynas
        
    Returns:
        Model: Sukurtas modelis
    """
    model_type = config.get('model_type', 'lstm').lower()
    
    if model_type == 'lstm':
        return LSTMModel(config)
    elif model_type == 'gru':
        return GRUModel(config)
    elif model_type == 'cnn':
        return CNNModel(config)
    else:
        raise ValueError(f"Nežinomas modelio tipas: {model_type}")