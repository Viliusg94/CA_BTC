import os
import json
import logging
import psutil
import threading
import numpy as np
import pandas as pd
from datetime import datetime
from tensorflow import keras
from keras.models import Sequential, load_model
from keras.layers import LSTM, Dense, Dropout, GRU, Conv1D, MaxPooling1D, Flatten
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import math
import matplotlib.pyplot as plt
import time
import uuid
import traceback
from app import websocket_manager  # Importuojame websocket managerį
import itertools
import random
from concurrent.futures import ThreadPoolExecutor
from keras.callbacks import ModelCheckpoint

logger = logging.getLogger(__name__)

class ModelService:
    """
    Serviso klasė, skirta modelių kūrimui, treniravimui ir valdymui
    """
    def __init__(self):
        """Inicializuoja modelio servisą"""
        # Kelias iki modelių direktorijos
        self.models_dir = os.path.join('app', 'static', 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Treniravimo būsenos, laikomos atmintyje
        self._trainings = {}
        
        # CPU profilaktika (threading limitas TensorFlow)
        os.environ['TF_NUM_INTEROP_THREADS'] = '1'
        os.environ['TF_NUM_INTRAOP_THREADS'] = '1'
        
        # Duomenų servisas duomenims gauti
        from app.services.data_service import DataService
        self.data_service = DataService()
    
        # Optimizavimo būsenos saugojimui
        self._optimizations = {}
    
    def get_all_models(self):
        """
        Gauna visų išsaugotų modelių sąrašą su papildoma informacija
        
        Returns:
            list: Modelių informacijos sąrašas
        """
        models = []
        
        try:
            # Patikriname, ar egzistuoja modelių katalogas
            if not os.path.exists(self.models_dir):
                logger.warning(f"Modelių katalogas nerastas: {self.models_dir}")
                return models
            
            # Randame visus .h5 failus
            for filename in os.listdir(self.models_dir):
                if filename.endswith(".h5"):
                    # Gauname modelio informaciją
                    model_info = self.get_model_info(filename)
                    
                    if model_info:
                        # Papildomi duomenys apie modelį
                        try:
                            # Bandome įkelti modelį, kad gautume daugiau informacijos
                            model = self.load_model(filename)
                            if model:
                                # Pridedame papildomą informaciją
                                model_info['layers_count'] = len(model.layers)
                                model_info['params_count'] = model.count_params()
                            else:
                                model_info['layers_count'] = "Nežinomas"
                                model_info['params_count'] = "Nežinomas"
                        except Exception as inner_e:
                            logger.error(f"Klaida gaunant išsamią modelio informaciją: {inner_e}")
                            model_info['layers_count'] = "Klaida"
                            model_info['params_count'] = "Klaida"
                        
                        # Įtraukiame failo pavadinimą
                        model_info['filename'] = filename
                        
                        # Pridedame modelio informaciją į sąrašą
                        models.append(model_info)
            
            # Surikiuojame modelius pagal sukūrimo datą (naujausi pirmi)
            models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Klaida gaunant modelių sąrašą: {e}")
            traceback.print_exc()
        
        return models
    
    def get_model_details(self, filename):
        """Gauna konkretaus modelio detalią informaciją"""
        return self._read_model_info(filename)
    
    def get_model_path(self, filename):
        """Gauna kelią iki modelio failo"""
        base_filename = os.path.splitext(filename)[0]
        model_path = os.path.join(self.models_dir, f"{base_filename}.h5")
        return model_path if os.path.exists(model_path) else None
    
    def delete_model(self, filename):
        """Ištrina modelį"""
        try:
            base_filename = os.path.splitext(filename)[0]
            
            # Ištriname info failą
            info_path = os.path.join(self.models_dir, f"{base_filename}.json")
            if os.path.exists(info_path):
                os.remove(info_path)
            
            # Ištriname modelio failą
            model_path = os.path.join(self.models_dir, f"{base_filename}.h5")
            if os.path.exists(model_path):
                os.remove(model_path)
            
            # Ištriname grafikų failą, jei yra
            plot_path = os.path.join(self.models_dir, f"{base_filename}_plot.png")
            if os.path.exists(plot_path):
                os.remove(plot_path)
            
            return True
        except Exception as e:
            logger.error(f"Klaida trinant modelį: {e}")
            return False
    
    def start_training(self, training_id, params, checkpoint_path=None):
        """
        Pradeda modelio treniravimo procesą
        
        Args:
            training_id (str): Treniravimo sesijos ID
            params (dict): Treniravimo parametrai
            checkpoint_path (str, optional): Tarpinio modelio kelias, jei pratęsiame treniravimą
        
        Returns:
            str: Treniravimo sesijos ID
        """
        # Išsaugome treniravimo būseną
        self._trainings[training_id] = {
            'model_name': params['model_name'],
            'parameters': params,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Initializing',
            'is_training': True,
            'current_epoch': params.get('initial_epoch', 0),  # Pradedame nuo nulio arba tarpinio modelio epochos
            'metrics': {
                'loss': [],
                'val_loss': [],
                'mae': [],
                'val_mae': []
            },
            'current_metrics': {},
            'final_metrics': {},
            'model_filename': '',
            'checkpoint_path': checkpoint_path,  # Išsaugome tarpinio modelio kelią
            'system_resources': {
                'cpu_usage': 0,
                'ram_usage': 0,
                'gpu_usage': 0
            }
        }
        
        # Paleidžiame treniravimą atskirame thread
        training_thread = threading.Thread(
            target=self._train_model_thread,
            args=(training_id, params, checkpoint_path)
        )
        training_thread.daemon = True
        training_thread.start()
        
        return training_id
    
    def get_training_status(self, training_id):
        """Gauna treniravimo būsenos informaciją"""
        return self._trainings.get(training_id)
    
    def cancel_training(self, training_id):
        """Atšaukia treniravimo procesą"""
        if training_id not in self._trainings:
            return False
        
        self._trainings[training_id]['is_training'] = False
        self._trainings[training_id]['status'] = 'Canceled'
        
        # Išsaugome treniravimo istoriją kaip atšauktą
        self.save_training_history(training_id, "Canceled")
        
        return True
    
    def _read_model_info(self, filename):
        """Skaito modelio informaciją iš JSON failo"""
        try:
            base_filename = os.path.splitext(filename)[0]
            info_path = os.path.join(self.models_dir, f"{base_filename}.json")
            
            if not os.path.exists(info_path):
                return None
            
            with open(info_path, 'r') as f:
                info = json.load(f)
            
            # Pridedame failų pavadinimus
            info['filename'] = base_filename + '.json'
            info['model_file'] = base_filename + '.h5'
            
            return info
        except Exception as e:
            logger.error(f"Klaida skaitant modelio informaciją: {e}")
            return None
    
    def _save_model_info(self, filename, info):
        """Išsaugo modelio informaciją į JSON failą"""
        try:
            with open(filename, 'w') as f:
                json.dump(info, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Klaida išsaugant modelio informaciją: {e}")
            return False
    
    def _update_system_resources(self, training_id):
        """Atnaujina sistemos resursų naudojimo informaciją"""
        try:
            # CPU naudojimas
            cpu_usage = psutil.cpu_percent()
            
            # RAM naudojimas
            memory = psutil.virtual_memory()
            ram_usage = memory.percent
            
            # GPU naudojimas (jei yra)
            gpu_usage = 0
            
            # Išsaugome informaciją
            self._trainings[training_id]['system_resources'] = {
                'cpu_usage': cpu_usage,
                'ram_usage': ram_usage,
                'gpu_usage': gpu_usage
            }
        except Exception as e:
            logger.error(f"Klaida gaunant sistemos resursų informaciją: {e}")
    
    def _train_model_thread(self, training_id, params, checkpoint_path=None):
        """Treniruoja modelį atskirame thread"""
        # Atnaujinti būseną
        self._trainings[training_id]['status'] = 'Loading data'
        
        try:
            # Gauname duomenis
            data = self.data_service.get_data_from_database()
            
            if data.empty:
                self._trainings[training_id]['status'] = 'Error: No data'
                self._trainings[training_id]['is_training'] = False
                return
            
            # Paruošiame duomenis LSTM modeliui
            X_train, X_test, y_train, y_test, scaler = self._prepare_data_for_lstm(
                data, 
                seq_length=params['sequence_length'],
                pred_days=params['prediction_days'],
                test_size=params['test_size']
            )
            
            # Kuriame modelį
            if checkpoint_path and os.path.exists(checkpoint_path):
                self._trainings[training_id]['status'] = 'Loading checkpoint'
                model = load_model(checkpoint_path)
                logger.info(f"Modelis užkrautas iš tarpinio failo: {checkpoint_path}")
            else:
                self._trainings[training_id]['status'] = 'Building model'
                model = self._build_model(params)
            
            # Callback funkcija, kuri bus iškviečiama po kiekvienos epochos
            class TrainingCallback(keras.callbacks.Callback):
                def __init__(self, training_service, training_id):
                    self.training_service = training_service
                    self.training_id = training_id
                
                def on_epoch_begin(self, epoch, logs=None):
                    """Iškviečiamas prieš kiekvieną epochą"""
                    # Siunčiame pranešimą apie epochos pradžią
                    update_data = {
                        'status': 'Training',
                        'message': f'Pradedama epocha {epoch+1}/{self.model.params["epochs"]}',
                        'current_epoch': epoch+1,
                        'total_epochs': self.model.params["epochs"],
                        'progress': int((epoch+1) / self.model.params["epochs"] * 100)
                    }
                    websocket_manager.send_update(self.training_id, update_data)
                
                def on_epoch_end(self, epoch, logs=None):
                    """Iškviečiamas po kiekvienos epochos"""
                    # Patikriname, ar treniravimas nebuvo atšauktas
                    if not self.training_service._trainings[self.training_id]['is_training']:
                        self.model.stop_training = True
                        return
                    
                    # Atnaujinti metrikos
                    self.training_service._trainings[self.training_id]['current_epoch'] = epoch + 1
                    self.training_service._trainings[self.training_id]['metrics']['loss'].append(logs['loss'])
                    self.training_service._trainings[self.training_id]['metrics']['val_loss'].append(logs['val_loss'])
                    self.training_service._trainings[self.training_id]['metrics']['mae'].append(logs['mae'])
                    self.training_service._trainings[self.training_id]['metrics']['val_mae'].append(logs['val_mae'])
                    
                    self.training_service._trainings[self.training_id]['current_metrics'] = {
                        'train_loss': logs['loss'],
                        'val_loss': logs['val_loss'],
                        'train_mae': logs['mae'],
                        'val_mae': logs['val_mae']
                    }
                    
                    # Atnaujinti resursų informaciją
                    self.training_service._update_system_resources(self.training_id)
                    
                    # Siunčiame realaus laiko atnaujinimą per WebSocket
                    progress = int((epoch+1) / self.model.params["epochs"] * 100)
                    update_data = {
                        'status': 'Training',
                        'current_epoch': epoch+1,
                        'total_epochs': self.model.params["epochs"],
                        'progress': progress,
                        'metrics': {
                            'loss': float(logs['loss']),
                            'val_loss': float(logs['val_loss']),
                            'mae': float(logs['mae']),
                            'val_mae': float(logs['val_mae'])
                        },
                        'history': {
                            'loss': [float(x) for x in self.training_service._trainings[self.training_id]['metrics']['loss']],
                            'val_loss': [float(x) for x in self.training_service._trainings[self.training_id]['metrics']['val_loss']],
                            'mae': [float(x) for x in self.training_service._trainings[self.training_id]['metrics']['mae']],
                            'val_mae': [float(x) for x in self.training_service._trainings[self.training_id]['metrics']['val_mae']]
                        },
                        'system_resources': self.training_service._trainings[self.training_id]['system_resources']
                    }
                    websocket_manager.send_update(self.training_id, update_data)
                
                def on_train_begin(self, logs=None):
                    """Iškviečiamas prieš pradedant treniravimą"""
                    update_data = {
                        'status': 'Started',
                        'message': 'Treniravimas pradėtas'
                    }
                    websocket_manager.send_update(self.training_id, update_data)
                
                def on_train_end(self, logs=None):
                    """Iškviečiamas baigus treniravimą"""
                    update_data = {
                        'status': 'Completed',
                        'message': 'Treniravimas baigtas'
                    }
                    websocket_manager.send_update(self.training_id, update_data)
            
            # Treniruojame modelį
            self._trainings[training_id]['status'] = 'Training'
            
            # Resursų monitoringo thread
            def monitor_resources():
                while self._trainings[training_id]['is_training']:
                    self._update_system_resources(training_id)
                    time.sleep(1)
            
            # Paleidžiame resursų monitoringą
            resources_thread = threading.Thread(target=monitor_resources)
            resources_thread.daemon = True
            resources_thread.start()
            
            # Sukuriame ModelCheckpoint callback
            checkpoint_callback = keras.callbacks.LambdaCallback(
                on_epoch_end=lambda epoch, logs: self.save_checkpoint(training_id, epoch + 1, model)
            )
            
            # Pradinis epochos indeksas
            initial_epoch = params.get('initial_epoch', 0)
            
            # Treniruojame modelį su checkpoint callback
            history = model.fit(
                X_train, y_train,
                epochs=params['epochs'],
                batch_size=params['batch_size'],
                validation_data=(X_test, y_test),
                callbacks=[TrainingCallback(self, training_id), checkpoint_callback],
                verbose=0,
                initial_epoch=initial_epoch  # Pradedame nuo nurodytos epochos
            )
            
            # Jei treniravimas buvo atšauktas, neišsaugome modelio
            if not self._trainings[training_id]['is_training']:
                self._trainings[training_id]['status'] = 'Canceled'
                return
            
            # Apskaičiuojame galutinius rezultatus
            y_pred = model.predict(X_test)
            
            # Atstatomos originalios reikšmės (jei buvo normalizuota)
            if params['normalization']:
                # Sukuriame dummy masyvą su reikiamomis dimensijomis
                dummy = np.zeros((len(y_test), data.shape[1]))
                # Įdedame prognozes į teisingą vietą (pirmas stulpelis - Close)
                dummy[:, 0] = y_pred.flatten()
                # Inversuojame normalizaciją
                y_pred_inv = scaler.inverse_transform(dummy)[:, 0]
                
                # Tas pats originaliai y_test
                dummy = np.zeros((len(y_test), data.shape[1]))
                dummy[:, 0] = y_test
                y_test_inv = scaler.inverse_transform(dummy)[:, 0]
            else:
                y_pred_inv = y_pred
                y_test_inv = y_test
            
            # Apskaičiuojame MAE
            test_mae = mean_absolute_error(y_test_inv, y_pred_inv)
            
            # Išsaugome galutines metrikas
            final_metrics = {
                'loss': float(history.history['loss'][-1]),
                'val_loss': float(history.history['val_loss'][-1]),
                'mae': float(history.history['mae'][-1]),
                'val_mae': float(history.history['val_mae'][-1]),
                'test_mae': float(test_mae)
            }
            
            self._trainings[training_id]['final_metrics'] = final_metrics
            
            # Išsaugome modelį
            model_filename = f"{params['model_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_filename = model_filename.replace(' ', '_')
            model_path = os.path.join(self.models_dir, f"{model_filename}.h5")
            model.save(model_path)
            
            # Išsaugome modelio informaciją
            model_info = {
                'name': params['model_name'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'parameters': params,
                'metrics': {
                    'loss': [float(x) for x in history.history['loss']],
                    'val_loss': [float(x) for x in history.history['val_loss']],
                    'mae': [float(x) for x in history.history['mae']],
                    'val_mae': [float(x) for x in history.history['val_mae']]
                },
                'final_metrics': final_metrics
            }
            
            info_path = os.path.join(self.models_dir, f"{model_filename}.json")
            self._save_model_info(info_path, model_info)
            
            # Atnaujinti būseną
            self._trainings[training_id]['status'] = 'Completed'
            self._trainings[training_id]['is_training'] = False
            self._trainings[training_id]['model_filename'] = model_filename
            
            # Siunčiame pranešimą apie treniravimo pabaigą
            update_data = {
                'status': 'Completed',
                'message': 'Treniravimas baigtas',
                'model_filename': model_filename
            }
            websocket_manager.send_update(training_id, update_data)
        except Exception as e:
            logger.error(f"Klaida treniruojant modelį: {e}")
            self._trainings[training_id]['status'] = f"Error: {str(e)}"
            self._trainings[training_id]['is_training'] = False
            
            # Siunčiame pranešimą apie klaidą
            update_data = {
                'status': 'Error',
                'message': str(e)
            }
            websocket_manager.send_update(training_id, update_data)
        
        # Išsaugome treniravimo istoriją
        self.save_training_history(training_id, "Completed")
    
    def _prepare_data_for_lstm(self, data, seq_length, pred_days, test_size):
        """Paruošia duomenis LSTM modeliui"""
        # Normalizuojame duomenis
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data)
        
        # Sukuriame sekų duomenis
        X, y = [], []
        for i in range(len(scaled_data) - seq_length - pred_days + 1):
            X.append(scaled_data[i:i+seq_length])
            y.append(scaled_data[i+seq_length+pred_days-1][0])  # Prognozuojame 'Close' reikšmę
        
        X = np.array(X)
        y = np.array(y)
        
        # Padalijame į treniravimo ir testavimo duomenis
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        return X_train, X_test, y_train, y_test, scaler
    
    def _build_model(self, params):
        """Kuria LSTM modelį pagal nurodytus parametrus"""
        model = Sequential()
        model.add(LSTM(params['lstm_units'], return_sequences=True, input_shape=(None, 1)))
        model.add(Dropout(params['dropout']))
        model.add(LSTM(params['lstm_units']))
        model.add(Dropout(params['dropout']))
        model.add(Dense(1))
        
        model.compile(optimizer=params['optimizer'], loss='mean_squared_error', metrics=['mae'])
        return model

    # Pridėti naują metodą, kuris grąžina modelio architektūros informaciją vizualizavimui
    def get_model_architecture(self, model_filename):
    """
    Gauna modelio architektūros informaciją
    
    Args:
        model_filename (str): Modelio failo pavadinimas
    
    Returns:
        dict: Modelio architektūros informacija
    """
    try:
        # Patikriname, ar modelis egzistuoja
        model_path = os.path.join(self.models_dir, model_filename)
        if not os.path.exists(model_path):
            logger.error(f"Modelio failas nerastas: {model_path}")
            return None
        
        # Įkraunama modelį
        model = self.load_model(model_filename)
        
        if model is None:
            logger.error(f"Nepavyko įkrauti modelio: {model_filename}")
            return None
        
        # Gauname modelio konfigūraciją
        model_config = model.get_config()
        
        # Sukuriame architektūros informacijos žodyną
        architecture = {
            'input_shape': str(model.input_shape),
            'output_shape': str(model.output_shape),
            'total_params': model.count_params(),
            'layers': []
        }
        
        # Gauname informaciją apie kiekvieną sluoksnį
        for layer in model.layers:
            layer_info = {
                'name': layer.name,
                'type': layer.__class__.__name__,
                'config': {},
                'params': layer.count_params()
            }
            
            # Išgauname sluoksnio konfigūraciją
            layer_config = layer.get_config()
            
            # Išsaugome tik svarbius konfigūracijos parametrus
            important_configs = ['units', 'activation', 'rate', 'filters', 'kernel_size', 'strides', 'padding']
            
            for key in important_configs:
                if key in layer_config:
                    layer_info['config'][key] = layer_config[key]
            
            # Pridedame sluoksnio informaciją į sąrašą
            architecture['layers'].append(layer_info)
        
        return architecture
        
    except Exception as e:
        logger.error(f"Klaida gaunant modelio architektūrą: {e}")
        traceback.print_exc()
        return None
    
    # Pridėti naują metodą, kuris analizuoja modelio svorius
    def get_model_weights_analysis(self, filename):
        """
        Analizuoja modelio svorius ir grąžina detalią informaciją
        
        Args:
            filename (str): Modelio failo pavadinimas
            
        Returns:
            dict: Modelio svorių analizės duomenys arba None, jei nepavyko
        """
        try:
            # Gauname modelio failo kelią
            model_path = self.get_model_path(filename)
            if not model_path:
                return None
            
            # Užkrauname modelį
            model = self.load_model(filename)
            
            if model is None:
                return None
            
            # Paruošiame rezultatų struktūrą
            from tensorflow.keras import backend as K
            
            results = {
                'total_params': model.count_params(),
                'trainable_params': sum([K.count_params(w) for w in model.trainable_weights]),
                'non_trainable_params': sum([K.count_params(w) for w in model.non_trainable_weights]),
                'layer_count': len(model.layers),
                'model_size_mb': os.path.getsize(model_path) / (1024 * 1024),  # Dydis megabaitais
                'layers': []
            }
            
            # Einame per kiekvieną sluoksnį ir analizuojame jo svorius
            for layer in model.layers:
                # Jei sluoksnis neturi svorių, tęsiame
                if not layer.weights:
                    continue
                
                # Analizuojame sluoksnio svorius
                layer_info = {
                    'name': layer.name,
                    'type': layer.__class__.__name__,
                    'params': layer.count_params(),
                    'shape': [str(w.shape.as_list()) for w in layer.weights],
                    'stats': {},
                    'histogram': {'bins': [], 'counts': []}
                }
                
                # Gauname svorių statistiką
                weights_flat = []
                for w in layer.weights:
                    # Gauname svorių reikšmes
                    w_values = K.batch_get_value([w])[0]
                    # Suplostiname masyvą
                    w_flat = w_values.flatten()
                    weights_flat.extend(w_flat)
                
                # Paverčiame į NumPy masyvą
                weights_np = np.array(weights_flat)
                
                # Apskaičiuojame statistikas
                layer_info['stats'] = {
                    'min': float(np.min(weights_np)),
                    'max': float(np.max(weights_np)),
                    'mean': float(np.mean(weights_np)),
                    'std': float(np.std(weights_np))
                }
                
                # Sukuriame histogramą (20 stulpelių)
                hist, bin_edges = np.histogram(weights_np, bins=20)
                layer_info['histogram'] = {
                    'bins': [float(x) for x in bin_edges[:-1]],  # Paskutinį praleidžiame
                    'counts': [int(x) for x in hist]
                }
                
                # Pridedame sluoksnio informaciją
                results['layers'].append(layer_info)
            
            return results
        except Exception as e:
            logger.error(f"Klaida analizuojant modelio svorius: {e}")
            traceback.print_exc()
            return None
    
    # Pridėti metodą, kuris grąžina treniravimo sesijų istoriją
    def get_training_history(self, filters=None):
        """
        Grąžina treniravimo sesijų istoriją su filtravimu
        
        Args:
            filters (dict): Filtravimo parametrai
                - date_from (str): Data nuo
                - date_to (str): Data iki
                - model_types (list): Modelių tipai
                - statuses (list): Sesijų būsenos
                - sort_by (str): Rikiavimo laukas
                - sort_order (str): Rikiavimo tvarka (asc, desc)
        
        Returns:
            list: Treniravimo sesijų sąrašas
        """
        try:
            # Istorijos failo kelias
            history_file = os.path.join(self.models_dir, 'training_history.json')
            
            # Jei failo nėra, grąžiname tuščią sąrašą
            if not os.path.exists(history_file):
                return []
            
            # Skaitome istorijos duomenis
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # Jei nėra filtrų, grąžiname visą istoriją
            if not filters:
                return history
            
            # Filtruojame pagal datą
            filtered_history = history
            if filters.get('date_from'):
                date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                filtered_history = [
                    session for session in filtered_history 
                    if datetime.strptime(session['start_time'].split()[0], '%Y-%m-%d') >= date_from
                ]
            
            if filters.get('date_to'):
                date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                filtered_history = [
                    session for session in filtered_history 
                    if datetime.strptime(session['start_time'].split()[0], '%Y-%m-%d') <= date_to
                ]
            
            # Filtruojame pagal modelio tipą
            if filters.get('model_types'):
                filtered_history = [
                    session for session in filtered_history 
                    if session['model_type'] in filters['model_types']
                ]
            
            # Filtruojame pagal būseną
            if filters.get('statuses'):
                filtered_history = [
                    session for session in filtered_history 
                    if session['status'] in filters['statuses']
                ]
            
            # Rikiuojame rezultatus
            sort_by = filters.get('sort_by', 'date')
            sort_order = filters.get('sort_order', 'desc')
            
            if sort_by == 'date':
                filtered_history.sort(key=lambda x: x['start_time'], reverse=(sort_order == 'desc'))
            elif sort_by == 'val_loss':
                # Ignoruojame sesijas be val_loss
                with_val_loss = [s for s in filtered_history if s.get('val_loss') is not None]
                without_val_loss = [s for s in filtered_history if s.get('val_loss') is None]
                
                with_val_loss.sort(key=lambda x: x['val_loss'], reverse=(sort_order == 'desc'))
                filtered_history = with_val_loss + without_val_loss if sort_order == 'asc' else without_val_loss + with_val_loss
            elif sort_by == 'val_mae':
                # Ignoruojame sesijas be val_mae
                with_val_mae = [s for s in filtered_history if s.get('val_mae') is not None]
                without_val_mae = [s for s in filtered_history if s.get('val_mae') is None]
                
                with_val_mae.sort(key=lambda x: x['val_mae'], reverse=(sort_order == 'desc'))
                filtered_history = with_val_mae + without_val_mae if sort_order == 'asc' else without_val_mae + with_val_mae
            elif sort_by == 'duration':
                # Ignoruojame sesijas be trukmės
                with_duration = [s for s in filtered_history if s.get('duration') is not None]
                without_duration = [s for s in filtered_history if s.get('duration') is None]
                
                with_duration.sort(key=lambda x: x['duration_seconds'], reverse=(sort_order == 'desc'))
                filtered_history = with_duration + without_duration if sort_order == 'asc' else without_duration + with_duration
            
            return filtered_history
        
        except Exception as e:
            logger.error(f"Klaida gaunant treniravimo istoriją: {e}")
            traceback.print_exc()
            return []

    # Pridėti metodą, kuris išsaugo treniravimo sesijos informaciją istorijoje
    def save_to_training_history(self, training_id):
        """
        Išsaugo treniravimo sesijos informaciją istorijos faile
        
        Args:
            training_id (str): Treniravimo sesijos ID
        
        Returns:
            bool: Ar pavyko išsaugoti
        """
        try:
            # Gauname sesijos informaciją
            session = self._trainings.get(training_id)
            if not session:
                logger.error(f"Nerasta treniravimo sesija su ID: {training_id}")
                return False
            
            # Istorijos failo kelias
            history_file = os.path.join(self.models_dir, 'training_history.json')
            
            # Skaitome esamą istoriją
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            # Apskaičiuojame treniravimo trukmę
            start_time = datetime.strptime(session['start_time'], '%Y-%m-%d %H:%M:%S')
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Formatuojame trukmę
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
            # Sukuriame sesijos informaciją
            session_info = {
                'id': training_id,
                'model_name': session['model_name'],
                'model_type': session['parameters']['model_type'],
                'start_time': session['start_time'],
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': duration,
                'duration_seconds': int(duration_seconds),
                'status': session['status'],
                'epochs': session['parameters']['epochs'],
                'completed_epochs': session['current_epoch'],
                'model_path': session.get('model_filename', None)
            }
            
            # Pridedame metrikos, jei yra
            if session.get('final_metrics'):
                session_info['val_loss'] = session['final_metrics'].get('val_loss')
                session_info['val_mae'] = session['final_metrics'].get('val_mae')
            
            # Pridedame sesijos informaciją į istoriją
            history.append(session_info)
            
            # Išsaugome istoriją
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=4)
            
            return True
        
        except Exception as e:
            logger.error(f"Klaida išsaugant treniravimo sesiją istorijoje: {e}")
            traceback.print_exc()
            return False

    # Pridėti metodą, kuris grąžina treniravimo statistiką
    def get_training_statistics(self):
        """
        Grąžina treniravimo sesijų statistiką
        
        Returns:
            dict: Statistikos duomenys
        """
        try:
            # Gauname visą istoriją
            history = self.get_training_history()
            
            # Inicializuojame statistiką
            stats = {
                'total': len(history),
                'completed': 0,
                'failed': 0,
                'canceled': 0,
                'in_progress': 0,
                'best_model': None
            }
            
            # Skaičiuojame statistiką
            best_val_mae = float('inf')
            
            for session in history:
                if session['status'] == 'Completed':
                    stats['completed'] += 1
                elif session['status'] == 'Failed':
                    stats['failed'] += 1
                elif session['status'] == 'Canceled':
                    stats['canceled'] += 1
                elif session['status'] == 'In Progress':
                    stats['in_progress'] += 1
                
                # Tikriname, ar šis modelis geresnis už dabartinius geriausius
                if session.get('val_mae') and session['status'] == 'Completed':
                    if session['val_mae'] < best_val_mae:
                        best_val_mae = session['val_mae']
                        stats['best_model'] = {
                            'name': session['model_name'],
                            'val_mae': session['val_mae'],
                            'model_path': session['model_path']
                        }
            
            return stats
        
        except Exception as e:
            logger.error(f"Klaida gaunant treniravimo statistiką: {e}")
            traceback.print_exc()
            return {
                'total': 0,
                'completed': 0,
                'failed': 0,
                'canceled': 0,
                'in_progress': 0,
                'best_model': None
            }

# Papildykime _train_model_thread metodą, kad išsaugotų istoriją kai treniravimas baigiasi
# Pakeitimas: Prieš grąžinant iš _train_model_thread metodo, išsaugome sesiją istorijoje

# Senoje kodo vietoje:
self._trainings[training_id]['model_filename'] = f"{model_filename}.json"
# Po to pridedame:
self.save_to_training_history(training_id)

    # Pridėti hiperparametrų optimizavimo metodus

    def start_optimization(self, optimization_id, params):
    """
    Pradeda hiperparametrų optimizavimo procesą
    
    Args:
        optimization_id (str): Optimizavimo sesijos ID
        params (dict): Optimizavimo parametrai
        
    Returns:
        bool: Ar pavyko pradėti optimizavimą
    """
    try:
        # Išgauname parametrus
        model_name = params.get('model_name', 'Optimizuotas modelis')
        optimization_method = params.get('optimization_method', 'grid')
        max_trials = params.get('max_trials', 10)
        epochs_per_trial = params.get('epochs_per_trial', 20)
        optimization_metric = params.get('optimization_metric', 'val_loss')
        parameter_values = params.get('parameter_values', {})
        fixed_parameters = params.get('fixed_parameters', {})
        
        # Sukuriame visas parametrų kombinacijas pagal pasirinktą metodą
        parameter_combinations = []
        
        if optimization_method == 'grid':
            # Grid search - visos galimos kombinacijos
            parameter_names = list(parameter_values.keys())
            parameter_values_list = [parameter_values[name] for name in parameter_names]
            
            for combination in itertools.product(*parameter_values_list):
                params_dict = {name: value for name, value in zip(parameter_names, combination)}
                parameter_combinations.append(params_dict)
        else:
            # Random search - atsitiktinės kombinacijos
            for _ in range(max_trials):
                params_dict = {}
                for name, values in parameter_values.items():
                    params_dict[name] = random.choice(values)
                parameter_combinations.append(params_dict)
        
        # Jei kombinacijų per daug, ribojame iki max_trials
        if len(parameter_combinations) > max_trials:
            parameter_combinations = random.sample(parameter_combinations, max_trials)
        
        # Išsaugome optimizavimo būseną
        self._optimizations[optimization_id] = {
            'optimization_id': optimization_id,
            'model_name': model_name,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Initializing',
            'optimization_method': optimization_method,
            'max_trials': len(parameter_combinations),
            'completed_trials': 0,
            'epochs_per_trial': epochs_per_trial,
            'optimization_metric': optimization_metric,
            'parameter_values': parameter_values,
            'fixed_parameters': fixed_parameters,
            'parameter_combinations': parameter_combinations,
            'trials': [],
            'best_trial_index': -1,
            'best_value': float('inf') if optimization_metric == 'val_loss' else -float('inf'),
            'is_running': True
        }
        
        # Paleidžiame optimizavimą atskirame thread
        optimization_thread = threading.Thread(
            target=self._run_optimization_thread,
            args=(optimization_id,)
        )
        optimization_thread.daemon = True
        optimization_thread.start()
        
        return True
    except Exception as e:
        logger.error(f"Klaida pradedant optimizavimą: {e}")
        traceback.print_exc()
        return False

def _run_optimization_thread(self, optimization_id):
    """
    Vykdo optimizavimą atskirame thread
    
    Args:
        optimization_id (str): Optimizavimo sesijos ID
    """
    try:
        # Gauname optimizavimo būseną
        optimization = self._optimizations.get(optimization_id)
        if not optimization:
            logger.error(f"Negalima vykdyti optimizavimo: nerasta sesija {optimization_id}")
            return
        
        # Atnaujiname būseną
        optimization['status'] = 'Running'
        
        # Gauname parametrus
        model_name = optimization['model_name']
        epochs_per_trial = optimization['epochs_per_trial']
        parameter_combinations = optimization['parameter_combinations']
        fixed_parameters = optimization['fixed_parameters']
        optimization_metric = optimization['optimization_metric']
        
        # Vykdome bandymus
        for i, params_combination in enumerate(parameter_combinations):
            # Tikriname, ar optimizavimas nebuvo nutrauktas
            if not optimization['is_running']:
                optimization['status'] = 'Canceled'
                return
            
            # Paruošiame modelio parametrus
            model_params = {**params_combination, **fixed_parameters}
            model_params['epochs'] = epochs_per_trial
            model_params['model_name'] = f"{model_name} (Trial {i+1})"
            
            # Paleidžiame treniravimą su šiais parametrais
            try:
                # Sukurti naują treniravimo sesiją
                training_id = str(uuid.uuid4())
                
                # Pradedame treniravimą
                self.start_training(training_id, model_params)
                
                # Laukiame, kol baigsis treniravimas
                while self._trainings.get(training_id, {}).get('is_training', False):
                    time.sleep(1)
                
                # Gauname treniravimo rezultatus
                training_result = self._trainings.get(training_id, {})
                final_metrics = training_result.get('final_metrics', {})
                
                # Išsaugome bandymo rezultatus
                trial_result = {
                    'trial_num': i + 1,
                    'parameters': params_combination,
                    'metrics': final_metrics,
                    'training_id': training_id
                }
                
                # Tikriname, ar tai geriausias rezultatas
                current_value = final_metrics.get(optimization_metric)
                if current_value is not None:
                    if optimization_metric == 'val_loss':
                        if current_value < optimization['best_value']:
                            optimization['best_value'] = current_value
                            optimization['best_trial_index'] = i
                    else:  # 'val_mae'
                        if current_value > optimization['best_value']:
                            optimization['best_value'] = current_value
                            optimization['best_trial_index'] = i
                
                # Pridedame rezultatą į sąrašą
                optimization['trials'].append(trial_result)
                
                # Atnaujiname baigtų bandymų skaičių
                optimization['completed_trials'] += 1
                
                # Siunčiame atnaujinimą per WebSocket
                self._send_optimization_update(optimization_id)
                
            except Exception as e:
                logger.error(f"Klaida vykdant bandymą {i+1}: {e}")
                traceback.print_exc()
        
        # Optimizavimas sėkmingai baigtas
        optimization['status'] = 'Completed'
        
        # Siunčiame galutinį atnaujinimą
        self._send_optimization_update(optimization_id)
        
    except Exception as e:
        # Klaida vykdant optimizavimą
        logger.error(f"Klaida vykdant optimizavimą: {e}")
        traceback.print_exc()
        
        # Atnaujiname būseną
        if optimization_id in self._optimizations:
            self._optimizations[optimization_id]['status'] = 'Failed'
            self._send_optimization_update(optimization_id)

def _send_optimization_update(self, optimization_id):
    """
    Siunčia optimizavimo būsenos atnaujinimą per WebSocket
    
    Args:
        optimization_id (str): Optimizavimo sesijos ID
    """
    try:
        optimization = self._optimizations.get(optimization_id)
        if not optimization:
            return
        
        # Paruošiame duomenis siuntimui
        update_data = {
            'type': 'optimization_update',
            'optimization_id': optimization_id,
            'status': optimization['status'],
            'completed_trials': optimization['completed_trials'],
            'max_trials': optimization['max_trials'],
            'trials': optimization['trials']
        }
        
        # Siunčiame per WebSocket
        websocket_manager.emit('optimization_update', update_data)
    except Exception as e:
        logger.error(f"Klaida siunčiant optimizavimo atnaujinimą: {e}")

def get_optimization_status(self, optimization_id):
    """
    Gauna optimizavimo būseną
    
    Args:
        optimization_id (str): Optimizavimo sesijos ID
        
    Returns:
        dict: Optimizavimo būsenos žodynas arba None, jei nerasta
    """
    return self._optimizations.get(optimization_id)

def cancel_optimization(self, optimization_id):
    """
    Nutraukia optimizavimo procesą
    
    Args:
        optimization_id (str): Optimizavimo sesijos ID
        
    Returns:
        bool: Ar pavyko nutraukti optimizavimą
    """
    try:
        optimization = self._optimizations.get(optimization_id)
        if not optimization:
            return False
        
        # Nustatome, kad optimizavimas nebevyksta
        optimization['is_running'] = False
        
        # Grąžiname sėkmės statusą
        return True
    except Exception as e:
        logger.error(f"Klaida nutraukiant optimizavimą: {e}")
        traceback.print_exc()
        return False
    
    # Pridėti naują metodą modelių palyginimui
def compare_models(self, model_ids, days=30, price_column='close'):
    """
    Palygina kelis modelius pagal jų prognozavimo tikslumą
    
    Args:
        model_ids (list): Modelių ID sąrašas palyginimui
        days (int): Dienų skaičius palyginimui (pastarųjų dienų)
        price_column (str): Kainos stulpelis (close, high, low)
    
    Returns:
        dict: Modelių palyginimo rezultatai
    """
    try:
        # Gauname duomenis iš duomenų bazės
        df = self.data_service.get_data_from_database()
        
        # Patikriname, ar turime pakankamai duomenų
        if len(df) < days:
            raise ValueError(f"Nepakankamai duomenų. Prašoma {days} dienų, bet turima tik {len(df)}")
        
        # Apribojame duomenis paskutinėms X dienų
        df = df.tail(days).reset_index(drop=True)
        
        # Saugosime kiekvieno modelio prognozes ir metrikas
        results = {
            'models': [],
            'predictions': [],
            'dates': df['date'].tolist(),
            'actual_prices': df[price_column].tolist(),
            'model_predictions': [],
            'model_errors': [],
            'days_count': days
        }
        
        # Sukuriame sąrašą modelių metrikoms saugoti
        model_metrics = []
        
        # Ciklas per kiekvieną modelį
        for model_id in model_ids:
            # Gauname modelio informaciją
            model_info = self.get_model_info(model_id)
            
            if not model_info:
                continue
            
            # Gauname modelį
            model = self.load_model(model_id)
            
            if model is None:
                continue
            
            # Paruošiame duomenis modeliui
            X_test, y_test, scaler = self._prepare_prediction_data(df, model_info['parameters'])
            
            # Atliekame prognozes
            predictions = model.predict(X_test)
            
            # Apdorojame prognozes (pašaliname papildomas dimensijas)
            if predictions.ndim > 1:
                predictions = predictions.reshape(-1)
            
            # Grąžiname prognozes į pradinę skalę (undo normalization)
            if hasattr(scaler, 'inverse_transform'):
                # Jei y_test ir predictions yra vektoriai, juos paverčiame į matricą
                if len(y_test.shape) == 1:
                    y_test = y_test.reshape(-1, 1)
                if len(predictions.shape) == 1:
                    predictions = predictions.reshape(-1, 1)
                
                # Invertuojame normalizavimą
                y_test = scaler.inverse_transform(y_test)
                predictions = scaler.inverse_transform(predictions)
                
                # Vėl paverčiame į vektorius
                y_test = y_test.flatten()
                predictions = predictions.flatten()
            
            # Apskaičiuojame metrikas
            mae = float(np.mean(np.abs(y_test - predictions)))
            rmse = float(np.sqrt(np.mean((y_test - predictions) ** 2)))
            r2 = float(1 - np.sum((y_test - predictions) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
            
            # Pridedame modelio metrikas
            model_metrics.append({
                'name': model_info['name'],
                'metrics': {
                    'mae': mae,
                    'rmse': rmse,
                    'r2': r2
                }
            })
            
            # Saugome prognozes
            results['model_predictions'].append(predictions.tolist())
            
            # Apskaičiuojame klaidas (skirtumas tarp prognozės ir tikros reikšmės)
            errors = predictions - y_test
            results['model_errors'].append(errors.tolist())
        
        # Surandame geriausias metrikas
        best_mae_idx = np.argmin([m['metrics']['mae'] for m in model_metrics])
        best_rmse_idx = np.argmin([m['metrics']['rmse'] for m in model_metrics])
        best_r2_idx = np.argmax([m['metrics']['r2'] for m in model_metrics])
        
        # Pažymime geriausius modelius
        for i, model_metric in enumerate(model_metrics):
            model_metric['is_best_mae'] = (i == best_mae_idx)
            model_metric['is_best_rmse'] = (i == best_rmse_idx)
            model_metric['is_best_r2'] = (i == best_r2_idx)
            
            results['models'].append(model_metric)
        
        # Paruošiame detalius prognozių duomenis lentelei
        for i in range(len(df)):
            row = {
                'date': df['date'].iloc[i],
                'actual': float(df[price_column].iloc[i]),
                'model_predictions': []
            }
            
            for j, model_id in enumerate(model_ids):
                if j < len(results['model_predictions']):
                    row['model_predictions'].append({
                        'predicted': float(results['model_predictions'][j][i]),
                        'error': float(results['model_errors'][j][i])
                    })
            
            results['predictions'].append(row)
        
        return results
    
    except Exception as e:
        logger.error(f"Klaida lyginant modelius: {e}")
        traceback.print_exc()
        raise

def _prepare_prediction_data(self, df, model_params):
    """
    Paruošia duomenis modelio prognozėms
    
    Args:
        df (DataFrame): Duomenų rinkinys
        model_params (dict): Modelio parametrai
    
    Returns:
        tuple: (X_test, y_test, scaler) - paruošti duomenys
    """
    # Nukopijuojame duomenis, kad nemodifikuotume originalių
    data = df.copy()
    
    # Gauname parametrus
    seq_length = model_params.get('sequence_length', 60)
    pred_days = model_params.get('prediction_days', 1)
    
    # Pasirenkame tik kainos stulpelį
    price_data = data[['close']].values
    
    # Sukuriame scaler objektą normalizavimui
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(price_data)
    
    # Paruošiame X ir y duomenis
    X, y = [], []
    
    for i in range(seq_length, len(scaled_data) - pred_days + 1):
        X.append(scaled_data[i-seq_length:i])
        y.append(scaled_data[i + pred_days - 1])
    
    # Konvertuojame į numpy masyvus
    X, y = np.array(X), np.array(y)
    
    return X, y, scaler

def get_model_validation_metrics(self, model_id):
    """
    Gauna modelio validavimo metrikas
    
    Args:
        model_id (str): Modelio ID
    
    Returns:
        dict: Modelio validavimo metrikos
    """
    try:
        # Gauname modelio informaciją
        model_info = self.get_model_info(model_id)
        
        if not model_info:
            return None
        
        # Gauname modelio metrikas
        metrics = model_info.get('metrics', {})
        
        # Patikriname, ar turime visas reikalingas metrikas
        required_metrics = ['loss', 'val_loss', 'mae', 'val_mae']
        for metric in required_metrics:
            if metric not in metrics or not metrics[metric]:
                metrics[metric] = [0.0]  # Numatytoji reikšmė, jei metrika neegzistuoja
        
        return metrics
    
    except Exception as e:
        logger.error(f"Klaida gaunant modelio validavimo metrikas: {e}")
        traceback.print_exc()
        return None
    
def schedule_training(self, params):
    """
    Suplanuoja modelio treniravimą
    
    Args:
        params (dict): Modelio parametrai
    
    Returns:
        str: Treniravimo ID arba None, jei įvyko klaida
    """
    try:
        # Sukuriame treniravimo ID
        training_id = str(uuid.uuid4())
        
        # Pradedame treniravimą
        self.start_training(training_id, params)
        
        # Grąžiname treniravimo ID
        return training_id
    except Exception as e:
        logger.error(f"Klaida planuojant treniravimą: {e}")
        traceback.print_exc()
        return None

def is_training(self, training_id):
    """
    Patikrina, ar vyksta treniravimas
    
    Args:
        training_id (str): Treniravimo ID
    
    Returns:
        bool: True, jei treniravimas vyksta, False kitu atveju
    """
    try:
        # Gauname treniravimo būseną
        training = self._trainings.get(training_id)
        
        # Jei treniravimas nerastas, grąžiname False
        if not training:
            return False
        
        # Grąžiname, ar treniravimas vyksta
        return training.get('is_training', False)
    except Exception as e:
        logger.error(f"Klaida tikrinant treniravimo būseną: {e}")
        traceback.print_exc()
        return False
