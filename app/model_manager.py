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
    
    def __init__(self, models_dir="models"):
        """
        Inicializuoja ModelManager klasę
        
        Args:
            models_dir (str): Modelių direktorija
        """
        self.logger = logging.getLogger(__name__)
        self.models_dir = models_dir
        
        # Palaikomi modelių tipai
        self.model_types = ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm']
        
        # Modelių būsenos
        self.statuses = {}
        
        # Modelių konfigūracijos
        self.model_configs = {}
        
        # Modelių objektai
        self.models = {}
        
        # Vykstančių apmokymų sekimas
        self.running_trainings = {}
        
        # Apmokymo progreso sekimas
        self.training_progress = {}
        
        # Inicializuojame progreso sekimą kiekvienam modelio tipui
        for model_type in self.model_types:
            self.training_progress[model_type] = {
                'progress': 0,
                'status': 'Neaktyvus',
                'history': []
            }
            # Inicializuojame modelio objektą
            self.models[model_type] = {
                'status': 'Neapmokytas',
                'last_trained': 'Niekada',
                'performance': 'Nežinoma'
            }
        
        # Sukuriame reikiamas direktorijas
        self._create_directories()
        
        # Įkrauname esamas modelių būsenas
        self._load_model_status()
        
        logger.info(f"ModelManager inicializuotas. Direktorija: {os.path.abspath(models_dir)}")
    
    def _create_directories(self):
        """Sukuria reikiamas direktorijas modelių saugojimui"""
        try:
            # Sukuriame pagrindinę modelių direktoriją
            os.makedirs(self.models_dir, exist_ok=True)
            
            # Sukuriame papildomas direktorijas
            subdirs = ['weights', 'history', 'config']
            for subdir in subdirs:
                os.makedirs(os.path.join(self.models_dir, subdir), exist_ok=True)
                
            self.logger.info(f"Modelių direktorijos sukurtos: {self.models_dir}")
        except Exception as e:
            self.logger.error(f"Klaida kuriant direktorijas: {str(e)}")

    def _load_model_status(self):
        """Įkrauna modelių būsenas iš failo"""
        try:
            status_path = os.path.join(self.models_dir, "status.json")
            
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    self.statuses = json.load(f)
                    
                self.logger.info(f"Modelių būsenos įkeltos iš {status_path}")
            else:
                # Inicializuojame tuščias būsenas
                self.statuses = {}
                for model_type in self.model_types:
                    self.statuses[model_type] = {
                        'status': 'Neapmokytas',
                        'last_trained': 'Niekada',
                        'performance': 'Nežinoma',
                        'active_model_id': None
                    }
                    
                # Išsaugome numatytąsias būsenas
                self._save_model_status()
                
                self.logger.info("Sukurtos numatytosios modelių būsenos")
        except Exception as e:
            self.logger.error(f"Klaida įkeliant modelių būsenas: {str(e)}")
            
            # Inicializuojame tuščias būsenas klaidos atveju
            self.statuses = {}
            for model_type in self.model_types:
                self.statuses[model_type] = {
                    'status': 'Klaida',
                    'last_trained': 'Nežinoma',
                    'performance': 'Nežinoma',
                    'active_model_id': None
                }

    def _save_model_status(self):
        """Išsaugo modelių būsenas į failą"""
        try:
            status_path = os.path.join(self.models_dir, "status.json")
            
            with open(status_path, 'w') as f:
                json.dump(self.statuses, f, indent=4)
                
            self.logger.info(f"Modelių būsenos išsaugotos į {status_path}")
        except Exception as e:
            self.logger.error(f"Klaida išsaugant modelių būsenas: {str(e)}")
    
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
        Gauna modelio būseną
    
        Args:
            model_type (str): Modelio tipas
        
        Returns:
            dict: Modelio būsena
        """
      
            # Tikriname, ar modelio tipas palaikomas
        if model_type not in self.model_types:
            self.logger.error(f"Modelio tipas {model_type} nepalaikomas")
            return {}
        
        # Nustatome statusų failo kelią
        status_path = os.path.join(self.models_dir, "status.json")
        
        # Jei statusų failas egzistuoja, grąžiname modelio būseną
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                statuses = json.load(f)
            
            if model_type in statuses:
                return statuses[model_type]
        
        # Jei statusų failas neegzistuoja arba modelio tipo nėra jame,
        # grąžiname numatytąją modelio būseną
        return {
            'status': 'Neapmokytas',
            'last_trained': 'Niekada',
            'performance': 'Nežinoma',
            'active_model_id': None
        }
   
    def update_model_config(self, model_type, config):
        """
        Atnaujina modelio konfigūraciją
        
        Args:
            model_type (str): Modelio tipas
            config (dict): Modelio konfigūracija
            
        Returns:
            bool: Ar pavyko atnaujinti konfigūraciją
        """
        try:
            # Tikriname, ar modelio tipas palaikomas
            if model_type not in self.model_types:
                self.logger.error(f"Modelio tipas {model_type} nepalaikomas")
                return False
            
            # Gauname dabartinę konfigūraciją
            current_config = self.get_model_config(model_type)
            
            # Atnaujiname tik tuos parametrus, kurie pateikti
            for key, value in config.items():
                current_config[key] = value
            
            # Išsaugome atnaujintą konfigūraciją
            config_path = os.path.join(self.models_dir, "config", f"{model_type}_config.json")
            
            # Sukuriame direktoriją, jei ji neegzistuoja
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(current_config, f, indent=4)
            
            self.logger.info(f"Modelio {model_type} konfigūracija atnaujinta: {current_config}")
            return True
        except Exception as e:
            self.logger.error(f"Klaida atnaujinant modelio {model_type} konfigūraciją: {str(e)}")
            return False
    
    def get_model_config(self, model_type):
        """
        Gauna modelio konfigūraciją
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Modelio konfigūracija
        """
        try:
            # Tikriname, ar modelio tipas palaikomas
            if model_type not in self.model_types:
                self.logger.error(f"Modelio tipas {model_type} nepalaikomas")
                return {}
            
            # Nustatome konfigūracijos failo kelią
            config_path = os.path.join(self.models_dir, "config", f"{model_type}_config.json")
            
            # Jei konfigūracijos failas egzistuoja, grąžiname jo turinį
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                return config
            
            # Jei konfigūracijos failas neegzistuoja, grąžiname numatytąją konfigūraciją
            else:
                # Numatytosios konfigūracijos skirtingiems modeliams
                default_configs = {
                    'lstm': {
                        'epochs': 50,
                        'batch_size': 32,
                        'learning_rate': 0.001,
                        'lookback': 14,
                        'dropout': 0.2,
                        'recurrent_dropout': 0.0,
                        'validation_split': 0.2
                    },
                    'gru': {
                        'epochs': 50,
                        'batch_size': 32,
                        'learning_rate': 0.001,
                        'lookback': 14,
                        'dropout': 0.2,
                        'recurrent_dropout': 0.0,
                        'validation_split': 0.2
                    },
                    'transformer': {
                        'epochs': 50,
                        'batch_size': 32,
                        'learning_rate': 0.001,
                        'lookback': 14,
                        'num_heads': 8,
                        'd_model': 64,
                        'validation_split': 0.2
                    },
                    'cnn': {
                        'epochs': 50,
                        'batch_size': 32,
                        'learning_rate': 0.001,
                        'lookback': 14,
                        'filters': '32,64,128',
                        'kernel_size': '3,3,3',
                        'validation_split': 0.2
                    },
                    'cnn_lstm': {
                        'epochs': 50,
                        'batch_size': 32,
                        'learning_rate': 0.001,
                        'lookback': 14,
                        'filters': '32,64',
                        'kernel_size': '3,3',
                        'dropout': 0.2,
                        'validation_split': 0.2
                    }
                }
                
                # Grąžiname numatytąją konfigūraciją pagal modelio tipą
                config = default_configs.get(model_type, {
                    'epochs': 50,
                    'batch_size': 32,
                    'learning_rate': 0.001,
                    'lookback': 14,
                    'validation_split': 0.2
                })
                
                # Išsaugome numatytąją konfigūraciją į failą
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                
                return config
        except Exception as e:
            self.logger.error(f"Klaida gaunant modelio {model_type} konfigūraciją: {str(e)}")
            return {}
    
    def _simulate_training(self, model_type):
        """
        Simuliuoja modelio apmokymą (atskirame gije)
        
        Args:
            model_type (str): Modelio tipas
        """
        self.logger.info(f"Simuliuojamas modelio {model_type} apmokymas")
        
        # Pažymime, kad apmokymas prasidėjo
        if model_type in self.models:
            self.models[model_type]['status'] = 'Apmokomas'
        
        # Gauname modelio nustatymus
        config = self.get_model_config(model_type)
        epochs = config.get('epochs', 50)
        
        # Simuliuojame apmokymo procesą
        for epoch in range(epochs):
            # Simuliuojame vieną epochą
            time.sleep(0.1)  # Pagreitiname simuliaciją demonstracijos tikslais
            
            # Atnaujiname progresą
            accuracy = min(0.5 + (epoch / epochs) * 0.45 + random.uniform(-0.02, 0.02), 0.99)
            loss = max(0.5 - (epoch / epochs) * 0.45 + random.uniform(-0.02, 0.02), 0.01)
            progress = int((epoch + 1) / epochs * 100)
            
            self.training_progress[model_type] = {
                'progress': progress,
                'status': 'Vykdoma',
                'message': f"Epocha {epoch+1}/{epochs}",
                'current_epoch': epoch + 1,
                'total_epochs': epochs,
                'accuracy': round(accuracy, 4),
                'loss': round(loss, 4),
                'eta': f"{(epochs - epoch - 1) * 2} sek.",
                'history': self.training_progress[model_type].get('history', [])
            }
            
            # Įrašome progreso informaciją į istoriją
            history_entry = {
                'epoch': epoch + 1,
                'accuracy': round(accuracy, 4),
                'loss': round(loss, 4),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.training_progress[model_type]['history'].append(history_entry)
            
            self.logger.info(f"Modelio {model_type} apmokymas: Epocha {epoch+1}/{epochs}, "
                          f"Tikslumas: {accuracy:.4f}, Nuostolis: {loss:.4f}")
        
        # Generuojame atsitiktines metrikas
        metrics = {
            'mae': round(random.uniform(100, 500), 2),
            'mse': round(random.uniform(10000, 50000), 2),
            'rmse': round(random.uniform(100, 500), 2),
            'r2': round(random.uniform(0.7, 0.95), 4),
            'mape': round(random.uniform(3.0, 8.0), 2)
        }
        
        # Gauname modelio parametrus
        params = self.get_model_config(model_type)
        
        # Baigiame apmokymo procesą
        self.end_training(model_type, metrics=metrics, duration=epochs * 2, params=params)
        
        self.logger.info(f"Modelio {model_type} apmokymas baigtas. MAE: {metrics['mae']}")
    
    def get_training_progress(self, model_type):
        """
        Grąžina modelio apmokymo progresą
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Apmokymo progreso informacija
        """
        if model_type not in self.model_types:
            self.logger.error(f"Nežinomas modelio tipas: {model_type}")
            return {'status': 'Neaktyvus', 'progress': 0}
        
        if model_type not in self.training_progress:
            return {'status': 'Neaktyvus', 'progress': 0}
        
        progress_data = self.training_progress[model_type]
        
        # Jei status nėra, nustatome 'Neaktyvus'
        if 'status' not in progress_data:
            progress_data['status'] = 'Neaktyvus'
        
        # Jei progress nėra, nustatome 0
        if 'progress' not in progress_data:
            progress_data['progress'] = 0
        
        return progress_data
    
    def train_model(self, model_type):
        """
        Apmoko modelį (paleidžia atskirame gije)
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            bool: Ar sėkmingai pradėtas apmokymas
        """
        if model_type not in self.model_types:
            self.logger.error(f"Nežinomas modelio tipas: {model_type}")
            return False
        
        # Inicializuojame running_trainings žodyną, jei jis neegzistuoja
        if not hasattr(self, 'running_trainings'):
            self.running_trainings = {}
        
        # Tikriname, ar modelis jau apmokomas
        if model_type in self.running_trainings and self.running_trainings[model_type].is_alive():
            self.logger.warning(f"Modelis {model_type} jau apmokomas")
            return False
        
        # Atnaujiname modelio būseną
        model_status = self.get_model_status(model_type)
        model_status['status'] = 'Apmokomas'
        self.statuses[model_type] = model_status
        self._save_model_status()
        
        # Inicializuojame progreso stebėjimą
        self.training_progress[model_type] = {
            'progress': 0,
            'status': 'Pradėta',
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'history': []
        }
        
        # Paleidžiame apmokymą atskirame gije
        self.running_trainings[model_type] = threading.Thread(
            target=self._simulate_training,
            args=(model_type,)
        )
        self.running_trainings[model_type].daemon = True
        self.running_trainings[model_type].start()
        
        self.logger.info(f"Modelio {model_type} apmokymas pradėtas atskirame gije")
        return True
    
    def end_training(self, model_type, metrics=None, duration=None, params=None):
        """
        Baigia modelio apmokymo procesą ir išsaugo rezultatus
        
        Args:
            model_type (str): Modelio tipas
            metrics (dict): Apmokymo metrikos
            duration (float): Apmokymo trukmė
            params (dict): Apmokymo parametrai
        """
        try:
            # Atnaujinti modelio statusą
            model_status = self.get_model_status(model_type)
            model_status['status'] = 'Aktyvus'
            model_status['last_trained'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Nustatome našumo metriką (jei pateikta)
            if metrics and 'mae' in metrics:
                model_status['performance'] = f"MAE: {metrics['mae']:.4f}"
            
            # Išsaugome statusą
            self._save_model_status()
            
            # Išsaugome progresą
            self.training_progress[model_type] = {
                'progress': 100,
                'status': 'Baigta',
                'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'history': self.training_progress[model_type].get('history', [])
            }
            
            # Išsaugome istoriją
            self.save_training_history(model_type, metrics, duration, params)
            
            # Bandome išsaugoti į duomenų bazę, jei ji prieinama
            try:
                import requests
                db_data = {
                    'model_type': model_type,
                    'training_time': duration,
                    'epochs': params.get('epochs', 0) if params else 0,
                    'batch_size': params.get('batch_size', 0) if params else 0,
                    'learning_rate': params.get('learning_rate', 0) if params else 0,
                    'lookback': params.get('lookback', 0) if params else 0,
                    'layers': params.get('layers', []) if params else [],
                    'metrics': metrics if metrics else {},
                    'is_active': True,
                    'notes': params.get('notes', '') if params else '',
                    'parameters': {
                        'dropout': params.get('dropout', 0) if params else 0,
                        'recurrent_dropout': params.get('recurrent_dropout', 0) if params else 0,
                        'num_heads': params.get('num_heads', 0) if params else 0,
                        'd_model': params.get('d_model', 0) if params else 0,
                        'filters': params.get('filters', []) if params else [],
                        'kernel_size': params.get('kernel_size', []) if params else [],
                        'validation_split': params.get('validation_split', 0) if params else 0
                    }
                }
                
                # Siunčiame duomenis į API endpoint'ą
                requests.post('http://localhost:5000/api/save_model_history', 
                             json=db_data, 
                             headers={'Content-Type': 'application/json'})
            except Exception as e:
                self.logger.error(f"Klaida išsaugant modelio istoriją į duomenų bazę: {str(e)}")
            
            self.logger.info(f"Modelio {model_type} apmokymas baigtas")
        except Exception as e:
            self.logger.error(f"Klaida baigiant modelio {model_type} apmokymą: {str(e)}")
    
    def get_model_history(self, model_type):
        """
        Gauna modelio istorijos duomenis
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            list: Modelio istorijos įrašai
        """
        try:  
            history_path = os.path.join(self.models_dir, "history", f"{model_type}_history.json")
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history = json.load(f)
                return history
            return []
        except Exception as e:
            self.logger.error(f"Klaida gaunant modelio {model_type} istoriją: {str(e)}")
            return []
    
    def save_training_history(self, model_type, metrics=None, duration=None, params=None):
        """
        Išsaugo modelio apmokymo istoriją
    
        Args:
            model_type (str): Modelio tipas
            metrics (dict): Apmokymo metrikos
            duration (float): Apmokymo trukmė
            params (dict): Apmokymo parametrai
        """
        try:
            # Sukuriame istorijos įrašą
            history_entry = {
                'id': datetime.now().strftime('%Y%m%d%H%M%S'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'model_type': model_type,
                'training_time': duration,
                'metrics': metrics or {},
                'parameters': params or {},
                'is_active': True
            }
            
            # Gauname esamą istoriją
            history = self.get_model_history(model_type)
            
            # Įtraukiame naują įrašą
            history.append(history_entry)
            
            # Išsaugome į failą
            history_path = os.path.join(self.models_dir, "history", f"{model_type}_history.json")
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=4)
            
            self.logger.info(f"Modelio {model_type} apmokymo istorija išsaugota: {history_path}")
        except Exception as e:
            self.logger.error(f"Klaida išsaugant modelio {model_type} apmokymo istoriją: {str(e)}")