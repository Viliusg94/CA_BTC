"""
Modelių valdymo modulis

Šis modulis valdo neuroninių tinklų modelius, jų apmokymą ir prognozavimą
"""

import os
import json
import logging
import threading
import time
import numpy as np
from datetime import datetime, timedelta
import tensorflow as tf
import random
# Pridedame sklearn exceptions
import sklearn.exceptions
# Importuojame TensorFlow ir susijusius modulius
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model, Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU, Conv1D, MaxPooling1D, Flatten, Input, MultiHeadAttention, LayerNormalization
    from tensorflow.keras.layers import Layer
    
    # Pridedame TimeSeriesTransformer klasę
    @tf.keras.utils.register_keras_serializable(package="Custom")
    class TimeSeriesTransformer(Layer):
        """
        Transformerio sluoksnis laiko eilutėms
        """
        def __init__(self, d_model=64, num_heads=2, **kwargs):
            super(TimeSeriesTransformer, self).__init__(**kwargs)
            self.d_model = d_model 
            self.num_heads = num_heads
            self.mha = MultiHeadAttention(num_heads=num_heads, key_dim=d_model)
            self.layernorm1 = LayerNormalization(epsilon=1e-6)
            self.layernorm2 = LayerNormalization(epsilon=1e-6)
            self.ffn1 = Dense(d_model * 4, activation='relu')
            self.ffn2 = Dense(d_model)
            self.dropout1 = Dropout(0.1)
            self.dropout2 = Dropout(0.1)
            
        def call(self, inputs, training=False):
            attn_output = self.mha(inputs, inputs)
            attn_output = self.dropout1(attn_output, training=training)
            out1 = self.layernorm1(inputs + attn_output)
            
            ffn_output = self.ffn1(out1)
            ffn_output = self.ffn2(ffn_output)
            ffn_output = self.dropout2(ffn_output, training=training)
            return self.layernorm2(out1 + ffn_output)
            
        def get_config(self):
            config = super(TimeSeriesTransformer, self).get_config()
            config.update({
                "d_model": self.d_model,
                "num_heads": self.num_heads
            })
            return config
        
        @classmethod
        def from_config(cls, config):
            return cls(**config)
            
except ImportError:
    # Jei neužsikrautų tensorflow, užkraunam tik bazinius modulius
    pass
import joblib
import traceback
import pandas as pd

class ModelManager:
    """
    Klasė modelių valdymui ir apmokymui
    """
    def __init__(self, models_dir='models', data_processor=None):
        """
        Inicializuoja ModelManager klasę
        
        Args:
            models_dir (str): Direktorija, kurioje laikomi modeliai
            data_processor (object): Duomenų apdorojimo objektas (pvz., duomenų bazės ryšys)
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ModelManager...")
        
        # Check TensorFlow
        self.tensorflow_available = False
        try:
            import tensorflow as tf
            self.tensorflow_available = True
            self.logger.info(f"TensorFlow {tf.__version__} is available")
        except ImportError:
            self.logger.warning("TensorFlow not available - some features will be disabled")
        except Exception as e:
            self.logger.error(f"TensorFlow error: {e}")
        
        # kuriamos direktorijos
        self.models_dir = models_dir
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
            self.logger.info(f"Created models directory: {self.models_dir}")
        
        # Model types - include all even if TensorFlow isn't available
        self.model_types = ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm']
        
        # Create model subdirectories
        for model_type in self.model_types:
            model_dir = os.path.join(self.models_dir, model_type)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
                self.logger.info(f"Created directory for {model_type}: {model_dir}")
        
        # Initialize status tracking
        self.status_file = os.path.join(self.models_dir, 'model_status.json')
        self.statuses = {}
        self._load_model_status()
        
        # Initialize progress tracking
        self.training_progress = {}
        
        # Initialize training threads tracking
        self.running_trainings = {}
        
        self.logger.info("ModelManager initialization complete")

    def _load_model_status(self):
        """Užkrauna modelių statusus iš failo"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    self.statuses = json.load(f)
                
                # Užtikriname, kad yra visi modelių tipai
                for model_type in self.model_types:
                    if model_type not in self.statuses:
                        self.statuses[model_type] = {
                            'status': 'Neapmokytas',
                            'last_trained': 'Niekada',
                            'performance': 'Nežinoma',
                            'active_model_id': None
                        }
            else:
                # Inicializuojame statusus
                self.statuses = {}
                for model_type in self.model_types:
                    self.statuses[model_type] = {
                        'status': 'Neapmokytas',
                        'last_trained': 'Niekada',
                        'performance': 'Nežinoma',
                        'active_model_id': None
                    }
                
                # Išsaugome į failą
                self._save_model_status()
        except Exception as e:
            self.logger.error(f"Klaida užkraunant modelių statusus: {str(e)}")
            # Inicializuojame statusus
            self.statuses = {}
            for model_type in self.model_types:
                self.statuses[model_type] = {
                    'status': 'Neapmokytas',
                    'last_trained': 'Niekada',
                    'performance': 'Nežinoma',
                    'active_model_id': None
                }

    def _save_model_status(self):
        """Išsaugo modelių statusus į failą"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.statuses, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Klaida išsaugant modelių statusus: {str(e)}")
            return False
    
    def get_model_status(self, model_type):
        """
        Grąžina modelio statusą
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Modelio statuso žodynas
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return {
                'status': 'Nežinomas',
                'last_trained': 'Niekada',
                'performance': 'Nežinoma',
                'active_model_id': None
            }
        
        if model_type not in self.statuses:
            self.statuses[model_type] = {
                'status': 'Neapmokytas',
                'last_trained': 'Niekada',
                'performance': 'Nežinoma',
                'active_model_id': None
            }
        
        return self.statuses[model_type]
    
    def get_training_progress(self, model_type):
        """
        Grąžina modelio apmokymo progreso informaciją
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Apmokymo progreso informacija
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return {
                'status': 'Nežinomas',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'Nežinoma',
                'metrics': {}
            }
        
        if model_type not in self.training_progress:
            # Jei apmokymas nepradėtas, grąžiname numatytasias reikšmes
            return {
                'status': self.statuses.get(model_type, {}).get('status', 'Neapmokytas'),
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'Nežinoma',
                'metrics': {}
            }
        
        return self.training_progress[model_type]
    
    def get_model_config(self, model_type):
        """
        Grąžina modelio konfigūraciją
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Modelio konfigūracijos žodynas
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return {}
        
        # Kelias iki konfigūracijos failo
        config_file = os.path.join(self.models_dir, f"{model_type}_config.json")
        
        # Jei failas neegzistuoja, sukuriame numatytąją konfigūraciją
        if not os.path.exists(config_file):
            # Numatytieji parametrai pagal modelio tipą
            config = {
                'epochs': 50,
                'batch_size': 32,
                'learning_rate': 0.001,
                'lookback': 30,
                'dropout': 0.2,
                'validation_split': 0.2
            }
            
            # Papildomi parametrai atitinkamiems modeliams
            if model_type == 'lstm':
                config.update({
                    'recurrent_dropout': 0.2,
                    'layers': [50, 20]
                })
            elif model_type == 'gru':
                config.update({
                    'recurrent_dropout': 0.2,
                    'layers': [64, 32]
                })
            elif model_type == 'transformer':
                config.update({
                    'num_heads': 2,
                    'd_model': 64,
                    'layers': [64, 32]
                })
            elif model_type == 'cnn':
                config.update({
                    'filters': [64, 32],
                    'kernel_size': [3, 3],
                    'layers': [64, 32]
                })
            elif model_type == 'cnn_lstm':
                config.update({
                    'filters': [64, 32],
                    'kernel_size': [3, 3],
                    'recurrent_dropout': 0.2,
                    'layers': [64, 32]
                })
            
            # Išsaugome numatytąją konfigūraciją
            try:
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                self.logger.error(f"Klaida išsaugant numatytąją konfigūraciją: {str(e)}")
            
            return config
        
        # Užkrauname konfigūraciją iš failo
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            self.logger.error(f"Klaida užkraunant modelio konfigūraciją: {str(e)}")
            return {}
    
    def update_model_config(self, model_type, config):
        """
        Atnaujina modelio konfigūraciją
        
        Args:
            model_type (str): Modelio tipas
            config (dict): Nauji konfigūracijos parametrai
            
        Returns:
            bool: Ar sėkmingai atnaujinta konfigūracija
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return False
        
        # Kelias iki konfigūracijos failo
        config_file = os.path.join(self.models_dir, f"{model_type}_config.json")
        
        # Užkrauname esamą konfigūraciją
        current_config = self.get_model_config(model_type)
        
        # Atnaujiname konfigūraciją
        current_config.update(config)
        
        # Išsaugome atnaujintą konfigūraciją
        try:
            with open(config_file, 'w') as f:
                json.dump(current_config, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Klaida išsaugant modelio konfigūraciją: {str(e)}")
            return False
    
    def get_model_history(self, model_type):
        """
        Grąžina modelio apmokymo istoriją
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            list: Modelio apmokymo istorijos įrašų sąrašas
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return []
        
        # Kelias iki istorijos failo
        history_file = os.path.join(self.models_dir, f"{model_type}_history.json")
        
        # Jei failas neegzistuoja, grąžiname tuščią sąrašą
        if not os.path.exists(history_file):
            return []
        
        # Užkrauname istoriją iš failo
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            return history
        except Exception as e:
            self.logger.error(f"Klaida užkraunant modelio istoriją: {str(e)}")
            return []
    
    def save_model_history(self, model_type, history_entry):
        """
        Išsaugo modelio apmokymo istorijos įrašą
        
        Args:
            model_type (str): Modelio tipas
            history_entry (dict): Istorijos įrašas
            
        Returns:
            bool: Ar sėkmingai išsaugotas įrašas
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return False
        
        # Kelias iki istorijos failo
        history_file = os.path.join(self.models_dir, f"{model_type}_history.json")
        
        # Užkrauname esamą istoriją
        history = self.get_model_history(model_type)
        
        # Generuojame naują ID
        if history:
            max_id = max(entry.get('id', 0) for entry in history)
            new_id = max_id + 1
        else:
            new_id = 1
        
        # Pridedame ID į įrašą
        history_entry['id'] = new_id
        
        # Pridedame datą
        history_entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Pridedame modelio tipą (jei dar nėra)
        if 'model_type' not in history_entry:
            history_entry['model_type'] = model_type
        
        # Pridedame naują įrašą į istoriją
        history.append(history_entry)
        
        # Išsaugome atnaujintą istoriją
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Klaida išsaugant modelio istoriją: {str(e)}")
            return False
    
    def delete_model_history(self, model_type, model_id):
        """
        Ištrina modelio apmokymo istorijos įrašą
        
        Args:
            model_type (str): Modelio tipas
            model_id (int): Modelio ID
            
        Returns:
            bool: Ar sėkmingai ištrintas įrašas
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return False
        
        # Konvertuojame ID į stringą (jei jis nėra stringas)
        model_id = str(model_id)
        
        # Kelias iki istorijos failo
        history_file = os.path.join(self.models_dir, f"{model_type}_history.json")
        
        # Jei failas neegzistuoja, grąžiname klaidą
        if not os.path.exists(history_file):
            self.logger.warning(f"Istorijos failas neegzistuoja: {history_file}")
            return False
        
        # Užkrauname istoriją iš failo
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except Exception as e:
            self.logger.error(f"Klaida užkraunant modelio istoriją: {str(e)}")
            return False
        
        # Ieškome įrašo pagal ID
        entry_index = None
        for i, entry in enumerate(history):
            if str(entry.get('id')) == model_id:
                entry_index = i
                break
        
        # Jei įrašas nerastas, grąžiname klaidą
        if entry_index is None:
            self.logger.warning(f"Modelio įrašas (ID: {model_id}) nerastas")
            return False
        
        # Tikriname, ar įrašas yra aktyvus
        is_active = history[entry_index].get('is_active', False)
        
        # Ištriname įrašą
        del history[entry_index]
        
        # Jei įrašas buvo aktyvus, atnaujiname modelio statusą
        if is_active:
            self.statuses[model_type]['status'] = 'Neaktyvus'
            self.statuses[model_type]['active_model_id'] = None
            self._save_model_status()
        
        # Išsaugome atnaujintą istoriją
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Klaida išsaugant modelio istoriją: {str(e)}")
            return False
    
    def activate_model(self, model_type, model_id):
        """
        Aktyvuoja modelį
        
        Args:
            model_type (str): Modelio tipas
            model_id (int): Modelio ID
            
        Returns:
            bool: Ar sėkmingai aktyvuotas modelis
        """
        if model_type not in self.model_types:
            self.logger.warning(f"Nežinomas modelio tipas: {model_type}")
            return False
        
        # Konvertuojame ID į stringą (jei jis nėra stringas)
        model_id = str(model_id)
        
        # Kelias iki istorijos failo
        history_file = os.path.join(self.models_dir, f"{model_type}_history.json")
        
        # Jei failas neegzistuoja, grąžiname klaidą
        if not os.path.exists(history_file):
            self.logger.warning(f"Istorijos failas neegzistuoja: {history_file}")
            return False
        
        # Užkrauname istoriją iš failo
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except Exception as e:
            self.logger.error(f"Klaida užkraunant modelio istoriją: {str(e)}")
            return False
        
        # Ieškome įrašo pagal ID
        model_entry = None
        for entry in history:
            if str(entry.get('id')) == model_id:
                model_entry = entry
                break
        
        # Jei įrašas nerastas, grąžiname klaidą
        if model_entry is None:
            self.logger.warning(f"Modelio įrašas (ID: {model_id}) nerastas")
            return False
        
        # Pažymime visus modelius kaip neaktyvius
        for entry in history:
            entry['is_active'] = False
        
        # Pažymime pasirinktą modelį kaip aktyvų
        model_entry['is_active'] = True
        
        # Išsaugome atnaujintą istoriją
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            self.logger.error(f"Klaida išsaugant modelio istoriją: {str(e)}")
            return False
        
        # Atnaujiname modelio statusą
        self.statuses[model_type]['status'] = 'Aktyvus'
        self.statuses[model_type]['active_model_id'] = model_id
        
        # Atnaujiname performance ir last_trained
        if 'metrics' in model_entry and 'mae' in model_entry['metrics']:
            self.statuses[model_type]['performance'] = f"MAE: {model_entry['metrics']['mae']:.4f}"
        
        if 'timestamp' in model_entry:
            self.statuses[model_type]['last_trained'] = model_entry['timestamp']
        
        # Išsaugome statusus
        self._save_model_status()
        
        return True
    
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
        
        # tikrinam ar TensorFlow yra pasiekiamas
        if not self.tensorflow_available and model_type in ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm']:
            self.logger.error(f"TensorFlow neprieinamas - negalima apmokyti {model_type} modelio")
            
            # atnaujiname statusą
            self.training_progress[model_type] = {
                'status': 'Klaida',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'N/A',
                'metrics': {},
                'error': 'TensorFlow neprieinamas'
            }
            return False
        
        # tikrinam ar modelis jau apmokomas
        if model_type in self.running_trainings and self.running_trainings[model_type].is_alive():
            self.logger.warning(f"Modelis {model_type} jau apmokomas")
            return False
        
        try:
            # Atnaujiname statusą, kad modelis apmokomas
            self.statuses[model_type]['status'] = 'Apmokomas'
            self._save_model_status()
            
            # inicializuojame progreso informaciją
            self.training_progress[model_type] = {
                'status': 'Apmokomas',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'Skaičiuojama...',
                'metrics': {}
            }
            
            # pradedame apmokymą atskirame thread'e
            import threading
            training_thread = threading.Thread(
                target=self._train_model_thread,
                args=(model_type,),
                daemon=True,
                name=f'training_{model_type}'
            )
            
            training_thread.start()
            self.running_trainings[model_type] = training_thread
            
            self.logger.info(f"Modelio {model_type} apmokymas pradėtas sėkmingai")
            return True
            
        except Exception as e:
            self.logger.error(f"Klaida pradedant modelio apmokymą: {str(e)}")
            
            # atnaujiname statusą jei įvyko klaida
            self.statuses[model_type]['status'] = 'Klaida'
            self._save_model_status()
            
            self.training_progress[model_type] = {
                'status': 'Klaida',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'N/A',
                'metrics': {},
                'error': str(e)
            }
            
            return False

    def _prepare_data(self, lookback=30, validation_split=0.2):
        """
        Paruošia duomenis modelio apmokymui naudojant esamą CSV failą
        
        Args:
            lookback (int): Kiek ankstesnių dienų naudoti prognozei
            validation_split (float): Validacijos duomenų dalis
            
        Returns:
            tuple: (X_train, y_train, X_val, y_val, scaler)
        """
        try:
            # Kelias iki duomenų failo
            data_file = os.path.join(os.path.dirname(self.models_dir), 'data', 'btc_data_1y_15m.csv')
            
            if not os.path.exists(data_file):
                self.logger.error(f"Duomenų failas nerastas: {data_file}")
                raise FileNotFoundError(f"Duomenų failas nerastas: {data_file}")
            
            self.logger.info(f"Kraunami duomenys iš: {data_file}")
            
            # Įkrauname duomenis
            df = pd.read_csv(data_file)
            df['time'] = pd.to_datetime(df['time'])
            
            # Išrikiuojame pagal laiką
            df = df.sort_values('time')
            
            self.logger.info(f"Įkrauta {len(df)} įrašų nuo {df['time'].min()} iki {df['time'].max()}")
            
            # Paruošiame duomenis normalizavimui
            feature_columns = ['open', 'high', 'low', 'close', 'volume']
            
            # Konvertuojame stulpelius į skaičius (jei jie yra objekto tipo)
            for col in feature_columns:
                if df[col].dtype == 'object':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Pašaliname NaN reikšmes
            df = df.dropna(subset=feature_columns)
            
            if len(df) < lookback + 100:
                raise ValueError(f"Nepakanka duomenų: turime {len(df)}, reikia bent {lookback + 100}")
            
            # Normalizuojame duomenis
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            df_scaled = df.copy()
            df_scaled[feature_columns] = scaler.fit_transform(df[feature_columns])
            
            # Sukuriame sekų duomenis
            X, y = self._create_sequences(df_scaled, feature_columns, 'close', lookback)
            
            # Padalijame į mokymo ir validacijos rinkinius
            split_idx = int(len(X) * (1 - validation_split))
            X_train = X[:split_idx]
            y_train = y[:split_idx]
            X_val = X[split_idx:]
            y_val = y[split_idx:]
            
            self.logger.info(f"Duomenys paruošti: X_train={X_train.shape}, X_val={X_val.shape}")
            
            return X_train, y_train, X_val, y_val, scaler
            
        except Exception as e:
            self.logger.error(f"Klaida ruošiant duomenis: {str(e)}")
            raise

    def _create_sequences(self, df, feature_columns, target_column, sequence_length):
        """
        Sukuria laiko eilučių sekas mokymui
        
        Args:
            df: DataFrame su duomenimis
            feature_columns: Požymių stulpelių pavadinimai
            target_column: Tikslo stulpelio pavadinimas
            sequence_length: Sekos ilgis
            
        Returns:
            tuple: (X, y) masyvai
        """
        X, y = [], []
        
        data_array = df[feature_columns].values
        target_idx = feature_columns.index(target_column)
        
        for i in range(len(data_array) - sequence_length):
            X.append(data_array[i:i + sequence_length])
            y.append(data_array[i + sequence_length, target_idx])
        
        return np.array(X), np.array(y)

    def _train_model_thread(self, model_type):
        """
        Modelio apmokymo gijos funkcija
        
        Args:
            model_type (str): Modelio tipas
        """
        self.logger.info(f"Pradedamas modelio {model_type} apmokymas")
        
        try:
            # atnaujiname progreso informaciją
            self.training_progress[model_type] = {
                'status': 'Apmokomas',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'Ruošiamasi...',
                'metrics': {},
                'current_step': 'Inicializuojama...'
            }
            
            # Fiksuojame pradžios laiką
            start_time = time.time()
            
            # atnaujiname progreso informaciją
            self.training_progress[model_type]['current_step'] = 'Kraunama konfigūracija...'
            
            # Gauname modelio konfigūraciją
            config = self.get_model_config(model_type)
            self.logger.info(f"Config loaded for {model_type}: {config}")
            
            # Numatytieji parametrai, jei jų nėra konfigūracijoje
            epochs = config.get('epochs', 50) 
            batch_size = config.get('batch_size', 32)
            learning_rate = config.get('learning_rate', 0.001)
            lookback = config.get('lookback', 30) # sekos ilgis
            dropout = config.get('dropout', 0.2)
            validation_split = config.get('validation_split', 0.2)
            
            # Atnaujiname progreso informaciją
            self.training_progress[model_type]['total_epochs'] = epochs
            self.training_progress[model_type]['current_step'] = 'Ruošiami duomenys...'
            
            # tikriname ar TensorFlow yra pasiekiamas
            try:
                import tensorflow as tf
                self.logger.info(f"TensorFlow version: {tf.__version__}")
            except ImportError as tf_error:
                error_msg = f"TensorFlow nėra įdiegtas: {str(tf_error)}"
                self.logger.error(error_msg)
                self.training_progress[model_type]['status'] = 'Klaida'
                self.training_progress[model_type]['error'] = error_msg
                self.training_progress[model_type]['last_error_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return
            
            # paruošiame duomenis iš CSV failo
            try:
                self.logger.info(f"Ruošiami duomenys apmokymui (lookback={lookback}, validation_split={validation_split})")
                X_train, y_train, X_val, y_val, scaler = self._prepare_data(lookback=lookback, validation_split=validation_split)
                self.logger.info(f"Duomenys paruošti sėkmingai")
            except Exception as data_error:
                error_msg = f"Klaida ruošiant duomenis: {str(data_error)}"
                self.logger.error(error_msg)
                self.training_progress[model_type]['status'] = 'Klaida'
                self.training_progress[model_type]['error'] = error_msg
                self.training_progress[model_type]['last_error_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return
            
            self.logger.info(f"Duomenys paruošti: X_train.shape={X_train.shape}, y_train.shape={y_train.shape}")
            self.training_progress[model_type]['current_step'] = f'Kuriamas {model_type} modelis...'
            
            # aprašome TimeSeriesTransformer sluoksnį
            # tikriname ar modelis yra transformer
            if model_type == 'transformer':
                try:
                    # registruojame TimeSeriesTransformer sluoksnį
                    @tf.keras.utils.register_keras_serializable(package="Custom")
                    class TimeSeriesTransformer(tf.keras.layers.Layer):
                        """
                        Transformerio sluoksnis laiko eilutėms
                        """
                        def __init__(self, d_model=64, num_heads=2, **kwargs):
                            super(TimeSeriesTransformer, self).__init__(**kwargs)
                            self.d_model = d_model 
                            self.num_heads = num_heads
                            self.mha = tf.keras.layers.MultiHeadAttention(num_heads=num_heads, key_dim=d_model)
                            self.layernorm1 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
                            self.layernorm2 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
                            self.ffn1 = tf.keras.layers.Dense(d_model * 4, activation='relu')
                            self.ffn2 = tf.keras.layers.Dense(d_model)
                            self.dropout1 = tf.keras.layers.Dropout(0.1)
                            self.dropout2 = tf.keras.layers.Dropout(0.1)
                            
                        def call(self, inputs, training=False):
                            attn_output = self.mha(inputs, inputs)
                            attn_output = self.dropout1(attn_output, training=training)
                            out1 = self.layernorm1(inputs + attn_output)
                            
                            ffn_output = self.ffn1(out1)
                            ffn_output = self.ffn2(ffn_output)
                            ffn_output = self.dropout2(ffn_output, training=training)
                            return self.layernorm2(out1 + ffn_output)
                            
                        def get_config(self):
                            config = super(TimeSeriesTransformer, self).get_config()
                            config.update({
                                "d_model": self.d_model,
                                "num_heads": self.num_heads
                            })
                            return config
                        
                        @classmethod
                        def from_config(cls, config):
                            return cls(**config)
                    
                    # padarome sluoksnį pasiekiamą klasėje
                    self.TimeSeriesTransformer = TimeSeriesTransformer
                    self.logger.info("TimeSeriesTransformer class registered successfully")
                    
                except Exception as transformer_error:
                    self.logger.error(f"Error registering TimeSeriesTransformer: {str(transformer_error)}")
                    # We'll continue and handle this in the model creation step
            
            # Sukuriame modelį pagal tipą
            try:
                self.logger.info(f"Kuriamas {model_type} modelis")
                model = self.create_model(model_type, config, input_shape=(X_train.shape[1], X_train.shape[2]))
                self.logger.info(f"Modelis sukurtas sėkmingai")
            except Exception as model_error:
                error_msg = f"Klaida kuriant modelį: {str(model_error)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                self.training_progress[model_type]['status'] = 'Klaida'
                self.training_progress[model_type]['error'] = error_msg
                self.training_progress[model_type]['last_error_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return
            
            # pagerintas klaidų valdymas
            class ProgressCallback(tf.keras.callbacks.Callback):
                def __init__(self, manager, model_type):
                    super(ProgressCallback, self).__init__()
                    self.manager = manager
                    self.model_type = model_type
                    self.start_time = None
                    self.epoch_start_time = None
                    self.times_per_epoch = []
                
                def on_train_begin(self, logs=None):
                    self.start_time = time.time()
                    self.times_per_epoch = []
                    self.manager.logger.info(f"Apmokymas pradėtas modeliui {self.model_type}")
                    self.manager.training_progress[self.model_type]['current_step'] = 'Apmokomas modelis...'
                
                def on_epoch_begin(self, epoch, logs=None):
                    self.epoch_start_time = time.time()
                    self.manager.logger.info(f"Pradedama epocha {epoch+1}")
                    self.manager.training_progress[self.model_type]['current_step'] = f'Epocha {epoch+1}/{self.manager.training_progress[self.model_type]["total_epochs"]}'
                
                def on_epoch_end(self, epoch, logs=None):
                    try:
                        # Apskaičiuojame laiką, užtruktą šioje epochoje
                        epoch_time = time.time() - self.epoch_start_time
                        self.times_per_epoch.append(epoch_time)
                        
                        # Apskaičiuojame vidutinį laiką per epochą
                        avg_time_per_epoch = sum(self.times_per_epoch) / len(self.times_per_epoch)
                        
                        # Apskaičiuojame likusį laiką
                        remaining_epochs = self.manager.training_progress[self.model_type]['total_epochs'] - epoch - 1
                        remaining_time = remaining_epochs * avg_time_per_epoch
                        
                        # Konvertuojame likusį laiką į žmogui suprantamą formatą
                        if remaining_time < 60:
                            time_remaining = f"{int(remaining_time)} sek."
                        elif remaining_time < 3600:
                            time_remaining = f"{int(remaining_time / 60)} min."
                        else:
                            time_remaining = f"{int(remaining_time / 3600)} val. {int((remaining_time % 3600) / 60)} min."
                        
                        # Atnaujiname progreso informaciją
                        progress_percent = (epoch + 1) / self.manager.training_progress[self.model_type]['total_epochs'] * 100
                        self.manager.training_progress[self.model_type]['progress'] = progress_percent
                        self.manager.training_progress[self.model_type]['current_epoch'] = epoch + 1
                        self.manager.training_progress[self.model_type]['time_remaining'] = time_remaining
                        
                        # loginam progreso informaciją
                        self.manager.logger.info(f"Baigta epocha {epoch+1}/{self.manager.training_progress[self.model_type]['total_epochs']}, "
                                                 f"trukme: {epoch_time:.2f}s, progresas: {progress_percent:.1f}%")
                        
                        # Išsaugome metrikas
                        if logs is not None:
                            self.manager.training_progress[self.model_type]['metrics'] = {
                                'loss': float(logs.get('loss', 0)),
                                'val_loss': float(logs.get('val_loss', 0)),
                                'mae': float(logs.get('mae', 0)),
                                'val_mae': float(logs.get('val_mae', 0))
                            }
                            
                            self.manager.logger.info(f"Metrikos: loss={logs.get('loss', 0):.4f}, "
                                                     f"val_loss={logs.get('val_loss', 0):.4f}, "
                                                     f"mae={logs.get('mae', 0):.4f}, "
                                                     f"val_mae={logs.get('val_mae', 0):.4f}")
                    except Exception as callback_error:
                        self.manager.logger.error(f"Error in callback: {str(callback_error)}")
                     
            
            # mokome modelį su pagerintu klaidų valdymu
            progress_callback = ProgressCallback(self, model_type)
            
            self.logger.info(f"Pradedamas modelio {model_type} apmokymas (epochs={epochs}, batch_size={batch_size})")
            
            try:
                history = model.fit(
                    X_train, y_train,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_data=(X_val, y_val),
                    callbacks=[progress_callback],
                    verbose=1
                )
                
                self.logger.info(f"Modelio {model_type} apmokymas baigtas, vertinamas efektyvumas")
                self.training_progress[model_type]['current_step'] = 'Vertinamas modelio efektyvumas...'
                
            except Exception as fit_error:
                error_msg = f"Klaida apmokant modelį: {str(fit_error)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                
                self.training_progress[model_type]['status'] = 'Klaida'
                self.training_progress[model_type]['error'] = error_msg
                self.training_progress[model_type]['last_error_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.statuses[model_type]['status'] = 'Klaida'
                self._save_model_status()
                return
            
            # ivertinimas ir išsaugojimas
            try:
                # Įvertiname modelį
                evaluation = model.evaluate(X_val, y_val, verbose=0)
                val_loss = evaluation[0]
                val_mae = evaluation[1] if len(evaluation) > 1 else val_loss
                
                self.training_progress[model_type]['current_step'] = 'Išsaugomas modelis...'
                
                # Išsaugome modelį
                model_id = self._save_model(model, model_type, scaler)
                
                # Update progress to completion
                self.training_progress[model_type]['status'] = 'Baigtas'
                self.training_progress[model_type]['progress'] = 100
                self.training_progress[model_type]['current_step'] = 'Apmokymas baigtas sėkmingai'
                
                # Update model status
                self.statuses[model_type]['status'] = 'Aktyvus'
                self.statuses[model_type]['last_trained'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.statuses[model_type]['performance'] = f"MAE: {val_mae:.4f}"
                self.statuses[model_type]['active_model_id'] = model_id
                self._save_model_status()
                
                self.logger.info(f"Modelio {model_type} apmokymas baigtas sėkmingai. MAE: {val_mae:.4f}")
                
            except Exception as save_error:
                error_msg = f"Klaida išsaugant modelį: {str(save_error)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                
                self.training_progress[model_type]['status'] = 'Klaida'
                self.training_progress[model_type]['error'] = error_msg
                self.training_progress[model_type]['last_error_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        except Exception as e:
            error_msg = f"Bendroji klaida apmokant modelį {model_type}: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            # Atnaujiname modelio statusą
            self.statuses[model_type]['status'] = 'Klaida'
            self._save_model_status()
            
            # Atnaujiname progreso informaciją
            self.training_progress[model_type]['status'] = 'Klaida'
            self.training_progress[model_type]['error'] = error_msg
            self.training_progress[model_type]['last_error_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def create_model(self, model_type, config, input_shape):
        """
        Sukuria neuroninio tinklo modelį pagal nurodytą tipą
        
        Args:
            model_type (str): Modelio tipas (lstm, gru, transformer ir t.t.)
            config (dict): Konfigūracijos parametrai
            input_shape (tuple): Įvesties forma (sekos ilgis, požymių skaičius)
            
        Returns:
            tf.keras.Model: Sukurtas modelis
        """
        import tensorflow as tf
        self.logger.info(f"Kuriamas {model_type} modelis su įvesties forma {input_shape}")
        
        try:
            # Ištraukiame parametrus iš konfigūracijos su numatytosiomis reikšmėmis
            units = config.get('neurons_per_layer', 64)
            if isinstance(units, list):
                units = units[0] if units else 64
                
            dropout_rate = config.get('dropout_rate', 0.2)
            learning_rate = config.get('learning_rate', 0.001)
            
            # Sukuriame Sequential modelį
            if model_type in ['lstm', 'gru', 'cnn', 'cnn_lstm']:
                model = tf.keras.Sequential(name=f"{model_type}_model")
            
            # Pridedame sluoksnius pagal modelio tipą
            if model_type == 'lstm':
                # LSTM modelis
                model.add(tf.keras.layers.LSTM(
                    units=units,
                    input_shape=input_shape,
                    dropout=dropout_rate,
                    return_sequences=True
                ))
                model.add(tf.keras.layers.LSTM(units//2, dropout=dropout_rate))
                model.add(tf.keras.layers.Dense(units//2, activation='relu'))
                model.add(tf.keras.layers.Dense(1))
                
            elif model_type == 'gru':
                # GRU modelis
                model.add(tf.keras.layers.GRU(
                    units=units,
                    input_shape=input_shape,
                    dropout=dropout_rate,
                    return_sequences=True
                ))
                model.add(tf.keras.layers.GRU(units//2, dropout=dropout_rate))
                model.add(tf.keras.layers.Dense(units//2, activation='relu'))
                model.add(tf.keras.layers.Dense(1))
                
            elif model_type == 'transformer':
                # Transformer modelis
                seq_len, n_features = input_shape
                d_model = config.get('d_model', 64)
                num_heads = config.get('num_heads', 4)
                
                # Įvesties sluoksnis
                inputs = tf.keras.Input(shape=input_shape)
                
                # Projekcija į d_model dimensiją
                x = tf.keras.layers.Dense(d_model)(inputs)
                
                # Transformer sluoksnis
                if hasattr(self, 'TimeSeriesTransformer'):
                    self.logger.info("Naudojamas individualus TimeSeriesTransformer")
                    x = self.TimeSeriesTransformer(d_model=d_model, num_heads=num_heads)(x)
                else:
                    self.logger.info("Naudojamas MultiHeadAttention iš TensorFlow")
                    # Tiesioginis MultiHeadAttention naudojimas
                    # Vietoje to, kad modelis žiūrėtų į seką tik iš vieno kampo (vienos „galvos“),
                    #  jis sukuria kelias „galvas“ (heads) – kiekviena analizuoja seką skirtingu būdu. 
                    # Vėliau visos galvos sujungiamos, kad modelis gautų įvairesnį, turtingesnį kontekstą.
                    attn_output = tf.keras.layers.MultiHeadAttention(
                        num_heads=num_heads, key_dim=d_model//num_heads
                    )(x, x)
                    x = tf.keras.layers.LayerNormalization(epsilon=1e-6)(x + attn_output)
                    
                # Išvesties sluoksniai
                x = tf.keras.layers.Flatten()(x)
                x = tf.keras.layers.Dense(64, activation='relu')(x)
                x = tf.keras.layers.Dropout(dropout_rate)(x)
                outputs = tf.keras.layers.Dense(1)(x)
                
                # Sukuriame modelį
                model = tf.keras.Model(inputs=inputs, outputs=outputs, name='transformer_model')
                
            elif model_type == 'cnn':
                # CNN modelis
                model.add(tf.keras.layers.Conv1D(
                    filters=64,
                    kernel_size=3,
                    activation='relu',
                    input_shape=input_shape
                ))
                model.add(tf.keras.layers.MaxPooling1D(pool_size=2))
                model.add(tf.keras.layers.Conv1D(filters=32, kernel_size=3, activation='relu'))
                model.add(tf.keras.layers.MaxPooling1D(pool_size=2))
                model.add(tf.keras.layers.Flatten())
                model.add(tf.keras.layers.Dense(32, activation='relu'))
                model.add(tf.keras.layers.Dropout(dropout_rate))
                model.add(tf.keras.layers.Dense(1))
                
            elif model_type == 'cnn_lstm':
                # CNN-LSTM hibridinis modelis
                model.add(tf.keras.layers.Conv1D(
                    filters=64,
                    kernel_size=3,
                    activation='relu',
                    input_shape=input_shape
                ))
                model.add(tf.keras.layers.MaxPooling1D(pool_size=2))
                model.add(tf.keras.layers.Conv1D(filters=32, kernel_size=3, activation='relu'))
                model.add(tf.keras.layers.LSTM(units=50, dropout=dropout_rate))
                model.add(tf.keras.layers.Dense(25, activation='relu'))
                model.add(tf.keras.layers.Dropout(dropout_rate))
                model.add(tf.keras.layers.Dense(1))
                
            else:
                # Numatytasis: paprastas tankus modelis
                self.logger.warning(f"Nežinomas modelio tipas '{model_type}', naudojamas paprastas Dense modelis")
                model = tf.keras.Sequential(name=f"default_model")
                model.add(tf.keras.layers.Flatten(input_shape=input_shape))
                model.add(tf.keras.layers.Dense(64, activation='relu'))
                model.add(tf.keras.layers.Dropout(dropout_rate))
                model.add(tf.keras.layers.Dense(32, activation='relu'))
                model.add(tf.keras.layers.Dropout(dropout_rate))
                model.add(tf.keras.layers.Dense(1))
            
            # Kompiliuojame modelį
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                loss='mse',
                metrics=['mae']
            )
            
            # Atspausdiname modelio santrauką į logus
            model.summary(print_fn=lambda x: self.logger.info(x))
            
            self.logger.info(f"{model_type} modelis sukurtas sėkmingai")
            return model
            
        except Exception as e:
            self.logger.error(f"Klaida kuriant modelį: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def _save_model(self, model, model_type, scaler):
        """
        i6saugo modelį ir jo istoriją
        
        Args:
            model (tf.keras.Model): Apmokytas modelis
            model_type (str): modelio tipas
            scaler (object): scaleris, naudojamas duomenims normalizuoti
            
        Returns:
            str: Model ID
        """
        try:
            # Generate unique ID
            model_id = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create directory for this specific model
            model_dir = os.path.join(self.models_dir, model_type)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            
            # Save model
            model_path = os.path.join(model_dir, f"{model_id}.h5")
            model.save(model_path)
            self.logger.info(f"Model saved to {model_path}")
            
            # Save scaler
            scaler_path = os.path.join(model_dir, f"{model_id}_scaler.pkl")
            import joblib
            joblib.dump(scaler, scaler_path)
            self.logger.info(f"Scaler saved to {scaler_path}")
            
            # Get training metrics
            train_loss = None
            val_loss = None
            train_mae = None
            val_mae = None
            
            if hasattr(model, 'history') and model.history is not None:
                history = model.history.history
                if 'loss' in history and history['loss']:
                    train_loss = float(history['loss'][-1])
                if 'val_loss' in history and history['val_loss']:
                    val_loss = float(history['val_loss'][-1])
                if 'mae' in history and history['mae']:
                    train_mae = float(history['mae'][-1])
                if 'val_mae' in history and history['val_mae']:
                    val_mae = float(history['val_mae'][-1])
            
            # Create history entry
            history_entry = {
                'id': model_id,
                'model_type': model_type,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': True,
                'metrics': {
                    'loss': train_loss,
                    'val_loss': val_loss,
                    'mae': train_mae,
                    'val_mae': val_mae
                }
            }
            
            # Save to history
            self.save_model_history(model_type, history_entry)
            
            return model_id
            
        except Exception as e:
            self.logger.error(f"Error saving model: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
