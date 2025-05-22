"""
Modelių valdymo modulis

Šis modulis valdo neuroninių tinklų modelius, jų apmokymą ir prognozavimą
"""

import os
import json
import logging
import pickle
from datetime import datetime
import threading
import time
import random
import numpy as np

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class ModelManager:
    """
    Klasė, valdanti neuroninius tinklus ir jų apmokymą
    """
    
    def __init__(self, models_dir='models'):
        """
        Inicializuoja ModelManager
        
        Args:
            models_dir (str): Direktorija, kurioje saugomi modeliai
        """
        self.models_dir = models_dir
        
        # Sukuriame direktoriją, jei jos nėra
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            
        # Modelių tipai, kuriuos palaiko sistema
        self.model_types = ['lstm', 'gru', 'transformer', 'cnn', 'arima']
        
        # Modelių būsenos
        self.models = {}
        self.running_trainings = {}
        
        # Modelių apmokymo progresas
        self.training_progress = {}
        
        # Modelių nustatymai (numatytosios reikšmės)
        self.model_configs = {
            'lstm': {
                'lookback': 30,
                'layers': [50, 100, 1],
                'batch_size': 32,
                'epochs': 100,
                'forecast_days': 7,
                'learning_rate': 0.001
            },
            'gru': {
                'lookback': 30,
                'layers': [60, 60, 1],
                'batch_size': 32,
                'epochs': 100,
                'forecast_days': 7,
                'learning_rate': 0.001
            },
            'transformer': {
                'lookback': 30,
                'attention_heads': 4,
                'batch_size': 32,
                'epochs': 100,
                'forecast_days': 7,
                'learning_rate': 0.001
            },
            'cnn': {
                'lookback': 30,
                'filters': [64, 128],
                'batch_size': 32,
                'epochs': 100,
                'forecast_days': 7,
                'learning_rate': 0.001
            },
            'arima': {
                'p': 5,
                'd': 1,
                'q': 0,
                'forecast_days': 7
            }
        }
        
        # Inicializuojame modelių būsenas
        self._initialize_models()
        
        # Įkeliame išsaugotus nustatymus, jei jie egzistuoja
        self._load_model_configs()
        
        logger.info(f"ModelManager inicializuotas. Direktorija: {os.path.abspath(models_dir)}")
    
    def _load_model_configs(self):
        """Įkelia modelių nustatymus iš failų"""
        config_path = os.path.join(self.models_dir, "model_configs.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    configs = json.load(f)
                
                # Atnaujiname nustatymus tik tiems modeliams, kurie egzistuoja faile
                for model_type, config in configs.items():
                    if model_type in self.model_configs:
                        self.model_configs[model_type].update(config)
                
                logger.info(f"Modelių nustatymai įkelti iš {config_path}")
            except Exception as e:
                logger.error(f"Klaida įkeliant modelių nustatymus: {str(e)}")
    
    def save_model_configs(self):
        """Išsaugo modelių nustatymus į failą"""
        config_path = os.path.join(self.models_dir, "model_configs.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.model_configs, f, indent=4)
            
            logger.info(f"Modelių nustatymai išsaugoti į {config_path}")
            return True
        except Exception as e:
            logger.error(f"Klaida išsaugant modelių nustatymus: {str(e)}")
            return False
    
    def _initialize_models(self):
        """Nuskaito modelių būsenas iš failų"""
        for model_type in self.model_types:
            model_path = os.path.join(self.models_dir, f"{model_type}_model.h5")
            info_path = os.path.join(self.models_dir, f"{model_type}_model_info.json")
            scaler_path = os.path.join(self.models_dir, f"{model_type}_scaler.pkl")
            
            model_exists = os.path.exists(model_path)
            info_exists = os.path.exists(info_path)
            scaler_exists = os.path.exists(scaler_path)
            
            if not model_exists:
                logger.warning(f"Modelio {model_type} failas nerastas: {model_path}")
            
            if not info_exists:
                logger.warning(f"Modelio {model_type} informacijos failas nerastas: {info_path}")
            
            if not scaler_exists:
                logger.warning(f"Modelio {model_type} scaler failas nerastas: {scaler_path}")
            
            # Modelio būsena
            if model_exists and info_exists and scaler_exists:
                # Nuskaitome info
                with open(info_path, 'r') as f:
                    info = json.load(f)
                
                self.models[model_type] = {
                    'path': model_path,
                    'info_path': info_path,
                    'scaler_path': scaler_path,
                    'status': 'Aktyvus',
                    'last_trained': info.get('last_trained', 'Nežinoma'),
                    'performance': info.get('performance', {}).get('mape', 'Nežinoma')
                }
            else:
                self.models[model_type] = {
                    'path': model_path,
                    'info_path': info_path,
                    'scaler_path': scaler_path,
                    'status': 'Neprieinamas',
                    'last_trained': None,
                    'performance': None
                }
            
            logger.info(f"Modelio {model_type} būsena: {self.models[model_type]['status']}")
    
    def get_model_status(self, model_type):
        """
        Grąžina modelio būseną
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Modelio būsenos informacija
        """
        if model_type not in self.models:
            return {
                'status': 'Neprieinamas',
                'last_trained': None,
                'performance': None
            }
        
        return self.models[model_type]
    
    def update_model_config(self, model_type, config):
        """
        Atnaujina modelio nustatymus
        
        Args:
            model_type (str): Modelio tipas
            config (dict): Nauji nustatymai
            
        Returns:
            bool: Ar pavyko atnaujinti nustatymus
        """
        if model_type not in self.model_types:
            logger.error(f"Nežinomas modelio tipas: {model_type}")
            return False
        
        try:
            # Atnaujiname tik tuos nustatymus, kurie jau egzistuoja
            for key, value in config.items():
                if key in self.model_configs[model_type]:
                    # Konvertuojame į tinkamą tipą
                    if key == 'layers' or key == 'filters':
                        # Konvertuojame sluoksnių sąrašą iš eilutės į skaičių sąrašą
                        if isinstance(value, str):
                            try:
                                value = [int(x.strip()) for x in value.split(',')]
                            except ValueError:
                                logger.error(f"Neteisingas sluoksnių sąrašas: {value}")
                                continue
                    elif key in ['lookback', 'batch_size', 'epochs', 'forecast_days', 'attention_heads', 'p', 'd', 'q']:
                        # Konvertuojame į sveikuosius skaičius
                        try:
                            value = int(value)
                        except ValueError:
                            logger.error(f"Neteisingas sveikasis skaičius: {value}")
                            continue
                    elif key == 'learning_rate':
                        # Konvertuojame į slankiojo kablelio skaičių
                        try:
                            value = float(value)
                        except ValueError:
                            logger.error(f"Neteisingas slankiojo kablelio skaičius: {value}")
                            continue
                    
                    # Priskiriame naują reikšmę
                    self.model_configs[model_type][key] = value
            
            # Išsaugome atnaujintus nustatymus
            self.save_model_configs()
            
            logger.info(f"Modelio {model_type} nustatymai atnaujinti: {config}")
            return True
        except Exception as e:
            logger.error(f"Klaida atnaujinant modelio {model_type} nustatymus: {str(e)}")
            return False
    
    def get_model_config(self, model_type):
        """
        Grąžina modelio nustatymus
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Modelio nustatymai
        """
        if model_type not in self.model_types:
            logger.error(f"Nežinomas modelio tipas: {model_type}")
            return {}
        
        return self.model_configs.get(model_type, {})
    
    def _simulate_training(self, model_type):
        """
        Simuliuoja modelio apmokymą (atskirame gije)
        
        Args:
            model_type (str): Modelio tipas
        """
        logger.info(f"Simuliuojamas modelio {model_type} apmokymas")
        
        # Pažymime, kad apmokymas prasidėjo
        self.models[model_type]['status'] = 'Apmokomas'
        
        # Gauname modelio nustatymus
        config = self.model_configs[model_type]
        epochs = config.get('epochs', 100)
        
        # Inicializuojame progresą
        self.training_progress[model_type] = {
            'current_epoch': 0,
            'total_epochs': epochs,
            'accuracy': 0,
            'loss': 0,
            'eta': f"{epochs * 2} sek."  # Apytiksliai 2 sekundės per epochą
        }
        
        # Simuliuojame apmokymo procesą per epochas
        for epoch in range(epochs):
            # Simuliuojame vieną epochą
            time.sleep(0.1)  # Pagreitiname simuliaciją demonstracijos tikslais
            
            # Atnaujiname progresą
            accuracy = min(0.5 + (epoch / epochs) * 0.45 + random.uniform(-0.02, 0.02), 0.99)
            loss = max(0.5 - (epoch / epochs) * 0.45 + random.uniform(-0.02, 0.02), 0.01)
            
            self.training_progress[model_type] = {
                'current_epoch': epoch + 1,
                'total_epochs': epochs,
                'accuracy': round(accuracy, 4),
                'loss': round(loss, 4),
                'eta': f"{(epochs - epoch - 1) * 2} sek."
            }
            
            logger.info(f"Modelio {model_type} apmokymas: Epocha {epoch+1}/{epochs}, "
                      f"Tikslumas: {accuracy:.4f}, Nuostolis: {loss:.4f}")
        
        # Generuojame atsitiktinį MAPE (vidutinė absoliutinė procentinė paklaida)
        mape = round(random.uniform(3.0, 8.0), 2)
        
        # Nustatome, kad apmokymas baigtas
        self.models[model_type]['status'] = 'Aktyvus'
        self.models[model_type]['last_trained'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.models[model_type]['performance'] = f"{mape}% MAPE"
        
        # Sukuriame modelio info failą
        info = {
            'model_type': model_type,
            'last_trained': self.models[model_type]['last_trained'],
            'performance': {
                'mape': mape,
                'rmse': round(random.uniform(100, 500), 2),
                'accuracy': self.training_progress[model_type]['accuracy']
            },
            'parameters': self.model_configs[model_type]
        }
        
        # Sukuriame direktoriją, jei jos nėra
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        
        # Įrašome informaciją į failą
        info_path = os.path.join(self.models_dir, f"{model_type}_model_info.json")
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=4)
        
        # Sukuriame fiktyvų modelio failą
        model_path = os.path.join(self.models_dir, f"{model_type}_model.h5")
        with open(model_path, 'w') as f:
            f.write(f"Fiktyvus {model_type} modelio failas")
        
        # Sukuriame fiktyvų scaler failą
        scaler_path = os.path.join(self.models_dir, f"{model_type}_scaler.pkl")
        with open(scaler_path, 'wb') as f:
            pickle.dump({'mean': 0, 'scale': 1}, f)
        
        logger.info(f"Modelio {model_type} apmokymas baigtas. MAPE: {mape}%")
        
        # Pašaliname iš einamųjų apmokymų sąrašo
        if model_type in self.running_trainings:
            del self.running_trainings[model_type]
        
        # Išvalome progreso informaciją
        if model_type in self.training_progress:
            del self.training_progress[model_type]
    
    def get_training_progress(self, model_type):
        """
        Grąžina modelio apmokymo progresą
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Apmokymo progreso informacija
        """
        if model_type not in self.model_types:
            logger.error(f"Nežinomas modelio tipas: {model_type}")
            return {}
        
        if model_type not in self.training_progress:
            return {
                'status': 'Inactive',
                'progress': 0,
                'message': 'Apmokymas nevyksta'
            }
        
        progress = self.training_progress[model_type]
        
        # Apskaičiuojame progreso procentą
        percent = int((progress['current_epoch'] / progress['total_epochs']) * 100)
        
        return {
            'status': 'Active',
            'progress': percent,
            'current_epoch': progress['current_epoch'],
            'total_epochs': progress['total_epochs'],
            'accuracy': progress['accuracy'],
            'loss': progress['loss'],
            'eta': progress['eta'],
            'message': f"Epocha {progress['current_epoch']}/{progress['total_epochs']}"
        }
    
    def train_model(self, model_type):
        """
        Apmoko modelį (paleidžia atskirame gije)
        
        Args:
            model_type (str): Modelio tipas
        """
        if model_type not in self.model_types:
            raise ValueError(f"Nežinomas modelio tipas: {model_type}")
        
        # Tikriname, ar modelis jau apmokomas
        if model_type in self.running_trainings and self.running_trainings[model_type].is_alive():
            logger.warning(f"Modelis {model_type} jau apmokomas")
            return False
        
        # Paleidžiame apmokymą atskirame gije
        self.running_trainings[model_type] = threading.Thread(
            target=self._simulate_training,
            args=(model_type,)
        )
        self.running_trainings[model_type].daemon = True
        self.running_trainings[model_type].start()
        
        logger.info(f"Modelio {model_type} apmokymas pradėtas atskirame gije")
        return True