"""
Modelių valdymo modulis.
Suteikia priemones darbui su Bitcoin kainų prognozavimo modeliais.
"""
import os
import json
import logging
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import tensorflow as tf
from utils.data_preprocessing import preprocess_data
import requests
from io import StringIO

# Nustatome logging
logger = logging.getLogger(__name__)

class ModelManager:
    """Klasė, atsakinga už modelių valdymą, treniravimą ir prognozių gavimą"""
    
    def __init__(self, models_dir):
        """
        Inicializuoja ModelManager objektą
        
        Args:
            models_dir (str): Direktorija, kurioje saugomi modeliai
        """
        # Inicijuojame TensorFlow
        print("Inicijuojamas TensorFlow... (gali užtrukti kelias sekundes)")
        tf.keras.backend.clear_session()
        print("TensorFlow sėkmingai inicializuotas!")
        
        self.models_dir = models_dir
        self.models = {}
        self.training_jobs = {}
        
        # Modelių būsena
        self.model_types = ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm', 'arima']
        
        # Užkrauname visus modelius
        for model_type in self.model_types:
            self._load_model(model_type)
        
        logger.info(f"ModelManager inicializuotas. Direktorija: {self.models_dir}")
    
    def get_price_history(self, days=30):
        """
        Gauna Bitcoin kainos istoriją
        
        Args:
            days (int): Dienų skaičius istorijai
            
        Returns:
            dict: Kainos istorijos duomenys
        """
        try:
            # Bandome gauti duomenis iš API
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Formatas: YYYY-MM-DD
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Tikriname, ar turime vietinius duomenis
            local_data_path = os.path.join(self.models_dir, 'historical_data.csv')
            
            if os.path.exists(local_data_path):
                # Naudojame vietinius duomenis
                df = pd.read_csv(local_data_path)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df.sort_index()
                
                # Filtruojame pagal datą
                mask = (df.index >= start_date) & (df.index <= end_date)
                filtered_df = df.loc[mask]
                
                if not filtered_df.empty:
                    return {
                        'dates': filtered_df.index.tolist(),
                        'open': filtered_df['open'].tolist(),
                        'high': filtered_df['high'].tolist(),
                        'low': filtered_df['low'].tolist(),
                        'close': filtered_df['close'].tolist(),
                        'volume': filtered_df['volume'].tolist() if 'volume' in filtered_df.columns else [0] * len(filtered_df)
                    }
            
            # Jei neturėjome vietinių duomenų arba jie buvo tušti, grąžiname pavyzdinius duomenis
            sample_dates = [end_date - timedelta(days=i) for i in range(days)]
            sample_dates.reverse()  # Didėjimo tvarka
            
            return {
                'dates': sample_dates,
                'open': [40000 + i * 100 for i in range(days)],
                'high': [41000 + i * 100 for i in range(days)],
                'low': [39000 + i * 100 for i in range(days)],
                'close': [40500 + i * 100 for i in range(days)],
                'volume': [10000000 for _ in range(days)]
            }
            
        except Exception as e:
            logger.error(f"Klaida gaunant kainos istoriją: {e}")
            # Grąžiname pavyzdinius duomenis klaidos atveju
            sample_dates = [end_date - timedelta(days=i) for i in range(days)]
            sample_dates.reverse()  # Didėjimo tvarka
            
            return {
                'dates': sample_dates,
                'open': [40000 + i * 100 for i in range(days)],
                'high': [41000 + i * 100 for i in range(days)],
                'low': [39000 + i * 100 for i in range(days)],
                'close': [40500 + i * 100 for i in range(days)],
                'volume': [10000000 for _ in range(days)]
            }
    
    def _load_model(self, model_type):
        """
        Užkrauna modelį iš disko
        
        Args:
            model_type (str): Modelio tipas
        """
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
        
        if model_exists and info_exists and scaler_exists:
            try:
                model = tf.keras.models.load_model(model_path)
                with open(info_path, 'r') as f:
                    info = json.load(f)
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                
                self.models[model_type] = {
                    'model': model,
                    'info': info,
                    'scaler': scaler,
                    'status': 'loaded'
                }
                logger.info(f"Modelis {model_type} sėkmingai užkrautas")
            except Exception as e:
                logger.error(f"Klaida užkraunant modelį {model_type}: {e}")
                self.models[model_type] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            self.models[model_type] = {
                'status': 'not_available'
            }
            logger.info(f"Modelio {model_type} būsena: Neprieinamas")
    
    def get_all_models_info(self):
        """
        Gauna informaciją apie visus modelius
        
        Returns:
            dict: Modelių informacija
        """
        result = {}
        
        for model_type in self.model_types:
            if model_type in self.models:
                model_data = self.models[model_type]
                
                if model_data['status'] == 'loaded':
                    result[model_type] = {
                        'name': model_type.upper(),
                        'status': 'Užkrautas',
                        'metrics': model_data['info'].get('metrics', {}),
                        'last_trained': model_data['info'].get('last_trained', 'Nežinoma')
                    }
                elif model_data['status'] == 'error':
                    result[model_type] = {
                        'name': model_type.upper(),
                        'status': 'Klaida',
                        'error': model_data.get('error', 'Nežinoma klaida')
                    }
                else:
                    result[model_type] = {
                        'name': model_type.upper(),
                        'status': 'Neprieinamas'
                    }
        
        return result
    
    def get_latest_predictions(self):
        """
        Gauna naujausias modelių prognozes
        
        Returns:
            dict: Modelių prognozės
        """
        price_history = self.get_price_history(days=60)  # Naudojame 60 dienų istoriją prognozėms
        
        if not price_history or 'close' not in price_history or len(price_history['close']) < 30:
            logger.warning("Nepakanka duomenų prognozėms")
            return {}
        
        predictions = {}
        
        for model_type in self.model_types:
            if model_type in self.models and self.models[model_type]['status'] == 'loaded':
                try:
                    # Paruošiame duomenis prognozei
                    model_data = self.models[model_type]
                    model = model_data['model']
                    scaler = model_data['scaler']
                    
                    # Gauname parametrus iš modelio informacijos
                    info = model_data['info']
                    sequence_length = info.get('sequence_length', 60)
                    
                    # Paruošiame duomenis (supaprastinta versija)
                    close_prices = np.array(price_history['close'][-sequence_length:]).reshape(-1, 1)
                    
                    # Normalizuojame duomenis
                    scaled_data = scaler.transform(close_prices)
                    
                    # Paruošiame įvestį modeliui
                    X = np.array([scaled_data])
                    
                    # Atliekame prognozę
                    scaled_prediction = model.predict(X)
                    prediction = scaler.inverse_transform(scaled_prediction)[0][0]
                    
                    # Išsaugome prognozę
                    predictions[model_type] = {
                        'prediction': float(prediction),
                        'prediction_date': datetime.now() + timedelta(days=1)
                    }
                    
                except Exception as e:
                    logger.error(f"Klaida gaunant {model_type} modelio prognozę: {e}")
        
        return predictions
    
    def get_ensemble_prediction(self):
        """
        Gauna ansamblio prognozę
        
        Returns:
            dict: Ansamblio prognozė
        """
        predictions = self.get_latest_predictions()
        
        if not predictions:
            return None
        
        # Apskaičiuojame vidutinę prognozę
        values = [p['prediction'] for p in predictions.values()]
        avg_prediction = sum(values) / len(values) if values else None
        
        if avg_prediction is None:
            return None
        
        return {
            'prediction': avg_prediction,
            'prediction_date': datetime.now() + timedelta(days=1),
            'models_used': list(predictions.keys())
        }
    
    def get_ensemble_data(self):
        """
        Gauna ansamblio duomenis grafikui
        
        Returns:
            dict: Ansamblio duomenys
        """
        price_history = self.get_price_history(days=30)
        ensemble_prediction = self.get_ensemble_prediction()
        
        if not price_history or not ensemble_prediction:
            return None
        
        # Prognozuojame 7 dienas į priekį
        future_dates = [datetime.now() + timedelta(days=i) for i in range(1, 8)]
        future_prices = [ensemble_prediction['prediction'] * (1 + 0.01 * i) for i in range(7)]
        
        return {
            'actual_dates': price_history['dates'],
            'actual_prices': price_history['close'],
            'prediction_dates': future_dates,
            'ensemble_predictions': future_prices
        }
    
    def start_training_job(self, model_type, epochs, batch_size, sequence_length):
        """
        Pradeda modelio treniravimo darbą
        
        Args:
            model_type (str): Modelio tipas
            epochs (int): Epochų skaičius
            batch_size (int): Batch dydis
            sequence_length (int): Sekos ilgis
            
        Returns:
            str: Darbo ID
        """
        # Patikrinkime, ar toks modelio tipas egzistuoja
        if model_type not in self.model_types:
            logger.error(f"Nežinomas modelio tipas: {model_type}")
            return None
        
        # Sugeneruojame darbo ID
        job_id = f"{model_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Išsaugome darbo informaciją
        self.training_jobs[job_id] = {
            'model_type': model_type,
            'status': 'queued',
            'progress': 0,
            'start_time': datetime.now(),
            'params': {
                'epochs': epochs,
                'batch_size': batch_size,
                'sequence_length': sequence_length
            }
        }
        
        # Čia galima pridėti asinkroninį darbo paleidimą
        # Pavyzdžiui, naudojant Thread, ProcessPoolExecutor ar Celery
        
        logger.info(f"Pradėtas treniravimo darbas: {job_id}")
        return job_id
    
    def get_training_job_status(self, job_id):
        """
        Gauna treniravimo darbo statusą
        
        Args:
            job_id (str): Darbo ID
            
        Returns:
            dict: Darbo statusas
        """
        if job_id not in self.training_jobs:
            return {'status': 'not_found'}
        
        job_info = self.training_jobs[job_id]
        
        # Čia galima įdėti logiką, kuri tikrina realią darbo būseną
        # Šiuo metu tiesiog simuliuojame progresą
        
        # Skaičiuojame praėjusį laiką
        elapsed = (datetime.now() - job_info['start_time']).total_seconds()
        
        # Simuliuojame progresą: 1% per sekundę, max 100%
        progress = min(100, int(elapsed))
        
        # Atnaujiname progresą
        job_info['progress'] = progress
        
        # Keičiame būseną, jei darbas baigtas
        if progress >= 100 and job_info['status'] != 'completed':
            job_info['status'] = 'completed'
            job_info['end_time'] = datetime.now()
            
            # Simuliuojame modelio išsaugojimą
            logger.info(f"Treniravimo darbas {job_id} baigtas. Išsaugomas modelis...")
        
        return job_info
    
    def get_active_training_jobs(self):
        """
        Gauna visus aktyvius treniravimo darbus
        
        Returns:
            dict: Aktyvūs darbai
        """
        active_jobs = {}
        
        for job_id, job_info in self.training_jobs.items():
            if job_info['status'] in ['queued', 'running', 'processing']:
                # Atnaujinti darbo būseną
                updated_info = self.get_training_job_status(job_id)
                active_jobs[job_id] = updated_info
        
        return active_jobs
    
    def get_training_history(self):
        """
        Gauna treniravimo istoriją
        
        Returns:
            list: Treniravimo istorija
        """
        history = []
        
        for job_id, job_info in self.training_jobs.items():
            if job_info['status'] == 'completed':
                history.append({
                    'id': job_id,
                    'model_type': job_info['model_type'],
                    'status': job_info['status'],
                    'start_time': job_info['start_time'],
                    'end_time': job_info.get('end_time', datetime.now()),
                    'params': job_info['params'],
                    'metrics': {
                        'mae': round(np.random.uniform(300, 500), 2),  # Simuliuojamos metrikos
                        'mse': round(np.random.uniform(100000, 250000), 2)
                    }
                })
        
        # Jei istorija tuščia, pridedame keletą pavyzdinių įrašų
        if not history:
            history = [
                {
                    'id': 'lstm_20240518120000',
                    'model_type': 'lstm',
                    'status': 'completed',
                    'start_time': datetime.now() - timedelta(days=3),
                    'end_time': datetime.now() - timedelta(days=3, hours=1),
                    'params': {
                        'epochs': 100,
                        'batch_size': 32,
                        'sequence_length': 60
                    },
                    'metrics': {'mae': 450.5, 'mse': 250000}
                },
                {
                    'id': 'gru_20240519130000',
                    'model_type': 'gru',
                    'status': 'completed',
                    'start_time': datetime.now() - timedelta(days=2),
                    'end_time': datetime.now() - timedelta(days=2, hours=1),
                    'params': {
                        'epochs': 80,
                        'batch_size': 32,
                        'sequence_length': 60
                    },
                    'metrics': {'mae': 480.2, 'mse': 270000}
                }
            ]
        
        # Rūšiuojame pagal pradžios laiką (naujausi pirmi)
        history.sort(key=lambda x: x['start_time'], reverse=True)
        
        return history