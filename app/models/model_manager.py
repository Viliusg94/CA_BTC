"""
Modelių valdymo modulis.
Suteikia priemones darbui su Bitcoin kainų prognozavimo modeliais.
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import LSTM, GRU, Dense, Conv1D, MaxPooling1D, Input, Flatten, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import uuid
import threading
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

# Konfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """Klasė, atsakinga už ML modelių valdymą Bitcoin kainų prognozavimui."""
    
    def __init__(self, models_dir):
        """
        Inicializuojame modelių valdytoją.
        
        Args:
            models_dir (str): Modelių direktorijos kelias
        """
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        
        # Žodynas modelių saugojimui atmintyje
        self.models = {}
        self.scalers = {}
        self.info = {}
        self.available = {}
        
        # Modelių mokymo užduočių žodynas
        self.training_jobs = {}
        
        # Užkrauname visus modelius
        self.load_all_models()
        
        logger.info(f"ModelManager inicializuotas. Direktorija: {models_dir}")
    
    def load_all_models(self):
        """Įkelia visus modelius iš modelių direktorijos."""
        model_types = ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm', 'arima']
        
        for model_type in model_types:
            self.load_model(model_type)
    
    def load_model(self, model_type):
        """
        Įkelia konkretų modelį pagal tipą.
        
        Args:
            model_type (str): Modelio tipas ('lstm', 'gru', ir t.t.)
        """
        model_path = os.path.join(self.models_dir, f'{model_type}_model.h5')
        info_path = os.path.join(self.models_dir, f'{model_type}_model_info.json')
        scaler_path = os.path.join(self.models_dir, f'{model_type}_scaler.pkl')
        
        model = None
        info = None
        scaler = None
        available = False
        
        # Įkeliame modelį
        if os.path.exists(model_path):
            try:
                # Tikriname ar tai tradicinis Keras modelis ar reikia custom objektų
                if model_type == 'transformer':
                    # Čia reikėtų importuoti custom objektus, jei naudojami
                    # Pvz., custom_objects={'TransformerBlock': TransformerBlock}
                    model = load_model(model_path)
                else:
                    model = load_model(model_path)
                
                # Kompiliuojame modelį
                model.compile(optimizer='adam', loss='mse', metrics=['mae'])
                available = True
                logger.info(f"Modelis {model_type} sėkmingai įkeltas")
            except Exception as e:
                logger.error(f"Klaida įkeliant modelį {model_type}: {e}")
        else:
            logger.warning(f"Modelio {model_type} failas nerastas: {model_path}")
        
        # Įkeliame modelio informaciją
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r') as f:
                    info = json.load(f)
                logger.info(f"Modelio {model_type} informacija įkelta")
            except Exception as e:
                logger.error(f"Klaida įkeliant modelio {model_type} informaciją: {e}")
                # Sukuriame numatytąją informaciją
                info = self._create_default_model_info(model_type)
        else:
            logger.warning(f"Modelio {model_type} informacijos failas nerastas: {info_path}")
            # Sukuriame numatytąją informaciją
            info = self._create_default_model_info(model_type)
        
        # Įkeliame scaler
        if os.path.exists(scaler_path):
            try:
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                logger.info(f"Modelio {model_type} scaler įkeltas")
            except Exception as e:
                logger.error(f"Klaida įkeliant modelio {model_type} scaler: {e}")
                scaler = MinMaxScaler()
        else:
            logger.warning(f"Modelio {model_type} scaler failas nerastas: {scaler_path}")
            scaler = MinMaxScaler()
        
        # Išsaugome modelio informaciją į atminties žodynus
        self.models[model_type] = model
        self.info[model_type] = info
        self.scalers[model_type] = scaler
        self.available[model_type] = available
        
        logger.info(f"Modelio {model_type} būsena: {'Prieinamas' if available else 'Neprieinamas'}")
    
    def _create_default_model_info(self, model_type, sequence_length=24):
        """
        Sukuria numatytąją modelio informaciją.
        
        Args:
            model_type (str): Modelio tipas
            sequence_length (int): Sekos ilgis
            
        Returns:
            dict: Modelio informacijos žodynas
        """
        return {
            'model_type': model_type,
            'sequence_length': sequence_length,
            'target_column': 'close',
            'features': ['open', 'high', 'low', 'close', 'volume'],
            'metrics': {
                'rmse': 0.0,
                'mae': 0.0,
                'mape': 0.0,
                'r2': 0.0
            },
            'training_date': None,
            'last_update': datetime.now().isoformat()
        }
    
    def get_all_models_info(self):
        """
        Grąžina informaciją apie visus modelius.
        
        Returns:
            dict: Modelių informacijos žodynas
        """
        models_info = {}
        
        for model_type in self.info:
            models_info[model_type] = {
                'info': self.info[model_type],
                'available': self.available[model_type]
            }
        
        return models_info
    
    def get_model_info(self, model_type):
        """
        Grąžina informaciją apie konkretų modelį.
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            dict: Modelio informacijos žodynas
        """
        if model_type not in self.info:
            return {'error': f'Modelis {model_type} nerastas'}
        
        return {
            'info': self.info[model_type],
            'available': self.available[model_type]
        }
    
    def get_metrics_comparison(self):
        """
        Grąžina DataFrame su modelių metrikomis palyginimui.
        
        Returns:
            pandas.DataFrame: Modelių metrikų DataFrame
        """
        model_names = []
        rmse_values = []
        mae_values = []
        mape_values = []
        r2_values = []
        
        for model_type, info in self.info.items():
            if self.available[model_type]:
                model_names.append(model_type.upper())
                metrics = info['metrics']
                rmse_values.append(metrics['rmse'])
                mae_values.append(metrics['mae'])
                mape_values.append(metrics['mape'])
                r2_values.append(metrics['r2'])
        
        metrics_df = pd.DataFrame({
            'Modelis': model_names,
            'RMSE': rmse_values,
            'MAE': mae_values,
            'MAPE (%)': mape_values,
            'R²': r2_values
        })
        
        # Rūšiuojame pagal RMSE
        return metrics_df.sort_values('RMSE')
    
    def get_prediction_chart(self, model_type):
        """
        Grąžina prognozės grafiką konkrečiam modeliui.
        
        Args:
            model_type (str): Modelio tipas
            
        Returns:
            plotly.graph_objects.Figure: Plotly grafikas
        """
        if model_type not in self.models or not self.available[model_type]:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Modelis {model_type} neprieinamas",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            return fig
        
        # Čia reikia implementuoti realių prognozės duomenų gavimą
        # Tai priklauso nuo to, kaip saugomi testiniai duomenys
        
        # Demonstraciniai duomenys
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        actual = np.random.normal(30000, 1000, 30)
        predicted = np.random.normal(30000, 1200, 30)
        
        fig = go.Figure()
        
        # Pridedame faktines reikšmes
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=actual,
                mode='lines',
                name='Faktinė kaina',
                line=dict(color='blue', width=2)
            )
        )
        
        # Pridedame prognozes
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=predicted,
                mode='lines',
                name=f'{model_type.upper()} prognozė',
                line=dict(color='red', width=2, dash='dash')
            )
        )
        
        # Atnaujina layoutą
        fig.update_layout(
            title=f"{model_type.upper()} modelio prognozė",
            xaxis_title="Data",
            yaxis_title="Bitcoin kaina (USD)",
            legend=dict(y=1.1, x=0.5, orientation="h"),
            template="plotly_white"
        )
        
        return fig
    
    def train_model(self, model_type, epochs=50, batch_size=32, sequence_length=24):
        """
        Inicijuoja modelio mokymą asynchroniškai.
        
        Args:
            model_type (str): Modelio tipas
            epochs (int): Epochų skaičius
            batch_size (int): Batch dydis
            sequence_length (int): Sekos ilgis
            
        Returns:
            str: Mokymo užduoties ID
        """
        job_id = str(uuid.uuid4())
        
        # Sukuriame naują gijį mokymo procesui
        training_thread = threading.Thread(
            target=self._train_model_thread,
            args=(job_id, model_type, epochs, batch_size, sequence_length)
        )
        
        # Inicializuojame mokymo būseną
        self.training_jobs[job_id] = {
            'status': 'starting',
            'model_type': model_type,
            'progress': 0,
            'current_epoch': 0,
            'total_epochs': epochs,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'metrics': None,
            'error': None
        }
        
        # Pradedame mokymo gijį
        training_thread.start()
        logger.info(f"Pradedamas modelio {model_type} mokymas. Užduoties ID: {job_id}")
        
        return job_id
    
    def _train_model_thread(self, job_id, model_type, epochs, batch_size, sequence_length):
        """
        Vykdo modelio mokymą atskirame gije.
        
        Args:
            job_id (str): Mokymo užduoties ID
            model_type (str): Modelio tipas
            epochs (int): Epochų skaičius
            batch_size (int): Batch dydis
            sequence_length (int): Sekos ilgis
        """
        try:
            # Atnaujinama būsena
            self.training_jobs[job_id]['status'] = 'data_loading'
            
            # Įkeliame duomenis
            # Šis funkcionalumas bus realizuotas data_processor.py faile
            # Čia galime naudoti placeholder duomenis demui
            
            # Imituojame duomenų įkėlimą
            import time
            time.sleep(2)
            
            # Atnaujinama būsena
            self.training_jobs[job_id]['status'] = 'preprocessing'
            self.training_jobs[job_id]['progress'] = 10
            
            # Imituojame duomenų apdorojimą
            time.sleep(2)
            
            # Atnaujinama būsena
            self.training_jobs[job_id]['status'] = 'model_creating'
            self.training_jobs[job_id]['progress'] = 20
            
            # Inicializuojame modelio architektūrą pagal tipą
            model = self._create_model(model_type, sequence_length)
            
            # Atnaujinama būsena
            self.training_jobs[job_id]['status'] = 'training'
            self.training_jobs[job_id]['progress'] = 30
            
            # Imituojame modelio mokymą
            for epoch in range(epochs):
                time.sleep(0.5)  # Imituojame mokymo laiką
                self.training_jobs[job_id]['current_epoch'] = epoch + 1
                self.training_jobs[job_id]['progress'] = 30 + int(70 * (epoch + 1) / epochs)
            
            # Imituojame metrikos
            metrics = {
                'rmse': np.random.uniform(800, 1200),
                'mae': np.random.uniform(400, 600),
                'mape': np.random.uniform(1.5, 3.5),
                'r2': np.random.uniform(0.75, 0.95)
            }
            
            # Atnaujinama būsena
            self.training_jobs[job_id]['status'] = 'completed'
            self.training_jobs[job_id]['progress'] = 100
            self.training_jobs[job_id]['end_time'] = datetime.now().isoformat()
            self.training_jobs[job_id]['metrics'] = metrics
            
            # Atnaujinama modelio informacija
            # Šiame demonstraciniame pavyzdyje tiesiog imituojame informaciją
            
            logger.info(f"Modelio {model_type} mokymas sėkmingai baigtas. Užduoties ID: {job_id}")
            
        except Exception as e:
            logger.error(f"Klaida mokant modelį {model_type}: {e}")
            # Klaidos atveju
            self.training_jobs[job_id]['status'] = 'failed'
            self.training_jobs[job_id]['error'] = str(e)
            self.training_jobs[job_id]['end_time'] = datetime.now().isoformat()
    
    def _create_model(self, model_type, sequence_length, features_count=5):
        """
        Sukuria modelio architektūrą pagal tipą.
        
        Args:
            model_type (str): Modelio tipas
            sequence_length (int): Sekos ilgis
            features_count (int): Požymių skaičius
            
        Returns:
            tf.keras.Model: Keras modelis
        """
        input_shape = (sequence_length, features_count)
        
        if model_type == 'lstm':
            model = tf.keras.Sequential([
                Input(shape=input_shape),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(50),
                Dropout(0.2),
                Dense(1)
            ])
        elif model_type == 'gru':
            model = tf.keras.Sequential([
                Input(shape=input_shape),
                GRU(50, return_sequences=True),
                Dropout(0.2),
                GRU(50),
                Dropout(0.2),
                Dense(1)
            ])
        elif model_type == 'cnn':
            model = tf.keras.Sequential([
                Input(shape=input_shape),
                Conv1D(filters=64, kernel_size=3, activation='relu'),
                MaxPooling1D(pool_size=2),
                Conv1D(filters=32, kernel_size=3, activation='relu'),
                Flatten(),
                Dense(50, activation='relu'),
                Dense(1)
            ])
        elif model_type == 'cnn_lstm':
            model = tf.keras.Sequential([
                Input(shape=input_shape),
                Conv1D(filters=64, kernel_size=3, activation='relu'),
                MaxPooling1D(pool_size=2),
                LSTM(50),
                Dense(1)
            ])
        elif model_type == 'transformer':
            # Supaprastinta transformer implementacija
            model = tf.keras.Sequential([
                Input(shape=input_shape),
                # Čia reikėtų pakeisti savo custom transformer implementacija
                Conv1D(filters=64, kernel_size=3, activation='relu'),
                Flatten(),
                Dense(50, activation='relu'),
                Dense(1)
            ])
        else:
            # Numatytasis modelis - paprastas LSTM
            model = tf.keras.Sequential([
                Input(shape=input_shape),
                LSTM(50),
                Dense(1)
            ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        return model
    
    def get_training_status(self, job_id):
        """
        Grąžina mokymo proceso būseną.
        
        Args:
            job_id (str): Mokymo užduoties ID
            
        Returns:
            dict: Mokymo būsenos žodynas
        """
        if job_id in self.training_jobs:
            return self.training_jobs[job_id]
        return {'status': 'not_found', 'error': f'Užduotis {job_id} nerasta'}
    
    def get_active_training_jobs(self):
        """
        Grąžina aktyvias mokymo užduotis.
        
        Returns:
            list: Aktyvių mokymo užduočių sąrašas
        """
        active_jobs = []
        
        for job_id, job_info in self.training_jobs.items():
            if job_info['status'] in ['starting', 'data_loading', 'preprocessing', 'model_creating', 'training']:
                active_jobs.append({
                    'job_id': job_id,
                    'model_type': job_info['model_type'],
                    'status': job_info['status'],
                    'progress': job_info['progress'],
                    'start_time': job_info['start_time']
                })
        
        return active_jobs
    
    def make_prediction(self, model_type, input_data):
        """
        Daro prognozę naudojant nurodytą modelį.
        
        Args:
            model_type (str): Modelio tipas
            input_data (numpy.ndarray): Įvesties duomenys
            
        Returns:
            dict: Prognozės rezultatai
        """
        if model_type not in self.models or not self.available[model_type]:
            return {"error": f"Modelis {model_type} neprieinamas"}
        
        try:
            model = self.models[model_type]
            scaler = self.scalers[model_type]
            sequence_length = self.info[model_type]['sequence_length']
            
            # Tikriname ar turime pakankamai duomenų
            if len(input_data) < sequence_length:
                return {"error": f"Nepakanka duomenų prognozei. Reikia bent {sequence_length} įrašų."}
            
            # Transformuojame duomenis
            normalized_data = scaler.transform(input_data)
            
            # Paruošiame įvesties seką
            input_sequence = normalized_data[-sequence_length:].reshape(1, sequence_length, normalized_data.shape[1])
            
            # Darome prognozę
            prediction = model.predict(input_sequence)[0][0]
            
            # Atstatome normalizaciją
            dummy = np.zeros((1, normalized_data.shape[1]))
            target_idx = 3  # 'close' indeksas
            dummy[0, target_idx] = prediction
            denormalized_prediction = scaler.inverse_transform(dummy)[0, target_idx]
            
            # Paskutinė faktinė kaina (denormalizuota)
            last_price = scaler.inverse_transform(normalized_data[-1:])[-1, target_idx]
            
            # Apskaičiuojame pokytį
            change = denormalized_prediction - last_price
            change_percent = (change / last_price) * 100
            
            return {
                "prediction": float(denormalized_prediction),
                "last_price": float(last_price),
                "change": float(change),
                "change_percent": float(change_percent),
                "direction": "up" if change > 0 else "down"
            }
            
        except Exception as e:
            logger.error(f"Klaida darant prognozę su modeliu {model_type}: {e}")
            return {"error": str(e)}
    
    def get_ensemble_predictions(self):
        """
        Grąžina ansamblio modelio prognozes.
        
        Returns:
            dict: Ansamblio prognozių duomenys
        """
        # Demonstraciniai duomenys
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        actual = np.random.normal(30000, 1000, 30)
        ensemble = np.random.normal(30000, 1200, 30)
        
        models_data = {
            'lstm': np.random.normal(30000, 1300, 30),
            'gru': np.random.normal(30000, 1250, 30),
            'transformer': np.random.normal(30000, 1400, 30),
            'cnn': np.random.normal(30000, 1350, 30),
            'cnn_lstm': np.random.normal(30000, 1320, 30)
        }
        
        return {
            'dates': [d.strftime("%Y-%m-%d") for d in dates],
            'actual': actual.tolist(),
            'ensemble': ensemble.tolist(),
            'models': models_data
        }
    
    def get_ensemble_metrics(self):
        """
        Grąžina ansamblio modelio metrikas.
        
        Returns:
            dict: Ansamblio metrikos
        """
        # Demonstracinės metrikos
        return {
            'rmse': np.random.uniform(700, 900),
            'mae': np.random.uniform(350, 450),
            'mape': np.random.uniform(1.2, 2.2),
            'r2': np.random.uniform(0.85, 0.95)
        }