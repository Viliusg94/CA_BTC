import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import plotly.graph_objects as go

class DataPreprocessor:
    def __init__(self, data_path=None):
        if data_path is None:
            self.data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                             'data', 'btc_data_1y_15m.csv')
        else:
            self.data_path = data_path
        
        self.feature_columns = ['open', 'high', 'low', 'close', 'volume']
        self.target_column = 'close'
        self.scaler = MinMaxScaler()
        
        # Įkeliame duomenis, jei jie egzistuoja
        self.df = self.load_data()
    
    def load_data(self):
        """Įkeliame Bitcoin duomenis"""
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                df['time'] = pd.to_datetime(df['time'])
                return df
            else:
                print(f"KLAIDA: Duomenų failas {self.data_path} nerastas")
                # Sukuriame dirbtinį duomenų rinkinį, jei originalių nėra
                return self._create_dummy_data()
        except Exception as e:
            print(f"Klaida įkeliant duomenis: {e}")
            return self._create_dummy_data()
    
    def _create_dummy_data(self):
        """Sukuriame dirbtinį duomenų rinkinį"""
        print("Sukuriami dirbtiniai duomenys testavimo tikslais")
        dates = pd.date_range(start="2023-01-01", periods=35040, freq="15min")  # ~1 metai 15min intervalais
        
        # Naudojame random walk procesą kainų generavimui
        np.random.seed(42)
        price = 30000
        prices = [price]
        for _ in range(35039):
            price = price * (1 + np.random.normal(0, 0.001))  # 0.1% kintamumas
            prices.append(price)
        
        return pd.DataFrame({
            'time': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.001))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.001))) for p in prices],
            'close': [p * (1 + np.random.normal(0, 0.0005)) for p in prices],
            'volume': [abs(np.random.normal(100, 20)) for _ in prices]
        })
    
    def prepare_data(self, test_size=0.2, sequence_length=24):
        """Paruošiame duomenis mokymui ir testavimui"""
        if self.df is None:
            self.df = self.load_data()
        
        # Normalizuojame duomenis
        df_normalized = self.df.copy()
        df_normalized[self.feature_columns] = self.scaler.fit_transform(self.df[self.feature_columns])
        
        # Sukuriame sekas
        X, y = self.create_sequences(df_normalized, sequence_length)
        
        # Padalijame į mokymosi ir testavimo rinkinius
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Testavimo datos
        test_dates = self.df['time'].iloc[sequence_length + split_idx:].reset_index(drop=True)
        
        return X_train, X_test, y_train, y_test, test_dates
    
    def create_sequences(self, data, sequence_length):
        """Sukuriame sekas iš laiko eilučių duomenų"""
        X, y = [], []
        data_array = data[self.feature_columns].values
        target_idx = self.feature_columns.index(self.target_column)
        
        for i in range(len(data) - sequence_length):
            X.append(data_array[i:i + sequence_length])
            y.append(data_array[i + sequence_length, target_idx])
            
        return np.array(X), np.array(y)
    
    def inverse_transform_predictions(self, predictions, target_idx=3):
        """Atstato normalizuotas prognozes į originalią skalę"""
        # target_idx 3 yra 'close' stulpelio indeksas feature_columns sąraše
        dummy = np.zeros((len(predictions), len(self.feature_columns)))
        dummy[:, target_idx] = predictions.flatten()
        return self.scaler.inverse_transform(dummy)[:, target_idx]
    
    def get_latest_data(self, sequence_length=24):
        """Grąžina naujausius duomenis prognozei"""
        if self.df is None:
            self.df = self.load_data()
        
        # Gauname paskutinius sequence_length įrašus
        latest_data = self.df[self.feature_columns].tail(sequence_length).values
        
        return latest_data
    
    def get_latest_price(self):
        """Grąžina naujausią Bitcoin kainą"""
        if self.df is None:
            self.df = self.load_data()
        
        return float(self.df['close'].iloc[-1])
    
    def get_price_change_24h(self):
        """Grąžina 24 valandų kainos pokytį"""
        if self.df is None:
            self.df = self.load_data()
        
        # 24 valandos = 96 15-minutiniai intervalai
        if len(self.df) >= 96:
            price_now = self.df['close'].iloc[-1]
            price_24h_ago = self.df['close'].iloc[-97]  # -97, nes indexavimas nuo 0
            
            change = price_now - price_24h_ago
            change_percent = (change / price_24h_ago) * 100
            
            return {
                'change': float(change),
                'change_percent': float(change_percent),
                'direction': 'up' if change > 0 else 'down'
            }
        else:
            return {
                'change': 0.0,
                'change_percent': 0.0,
                'direction': 'neutral'
            }
    
    def get_price_history(self, days=30):
        """Grąžina kainos istoriją nurodytam dienų skaičiui"""
        if self.df is None:
            self.df = self.load_data()
        
        # Paskutinis įrašas
        last_date = self.df['time'].iloc[-1]
        
        # Skaičiuojame, nuo kokios datos imti duomenis
        start_date = last_date - timedelta(days=days)
        
        # Filtruojame duomenis
        filtered_df = self.df[self.df['time'] >= start_date]
        
        return {
            'dates': filtered_df['time'].tolist(),
            'open': filtered_df['open'].tolist(),
            'high': filtered_df['high'].tolist(),
            'low': filtered_df['low'].tolist(),
            'close': filtered_df['close'].tolist(),
            'volume': filtered_df['volume'].tolist()
        }
    
def preprocess_data(data, sequence_length=60, test_size=0.2, target_column='close'):
    """
    Paruošia duomenis modelio apmokymui
    
    Args:
        data (pd.DataFrame/dict): Bitcoin kainos duomenys
        sequence_length (int): Sekos ilgis (kiek ankstesnių dienų naudoti prognozei)
        test_size (float): Testavimo duomenų dalis (0-1)
        target_column (str): Stulpelio pavadinimas, kurį norime prognozuoti
        
    Returns:
        tuple: (X_train, y_train, X_test, y_test, scaler) - paruošti duomenys ir normalizatorius
    """
    # Konvertuojame į DataFrame, jei tai žodynas
    if isinstance(data, dict):
        if 'date' in data and target_column in data:
            df = pd.DataFrame({
                'date': pd.to_datetime(data['date']),
                target_column: data[target_column]
            })
            df.set_index('date', inplace=True)
        else:
            # Grąžiname tuščius masyvus, jei duomenys netinkami
            return [], [], [], [], None
    else:
        df = data.copy()
    
    # Tikriname, ar yra pakankamai duomenų
    if df.empty or len(df) < sequence_length + 1:
        return [], [], [], [], None
    
    # Gauname reikalingą stulpelį
    data_values = df[target_column].values.reshape(-1, 1)
    
    # Naudojame paprastą normalizaciją (galima naudoti ir MinMaxScaler iš sklearn)
    data_min = np.min(data_values)
    data_max = np.max(data_values)
    data_range = data_max - data_min
    
    class SimpleScaler:
        def __init__(self, data_min, data_max):
            self.data_min = data_min
            self.data_range = data_max - data_min
        
        def transform(self, data):
            return (data - self.data_min) / self.data_range
        
        def inverse_transform(self, data):
            return data * self.data_range + self.data_min
    
    scaler = SimpleScaler(data_min, data_range)
    scaled_data = scaler.transform(data_values)
    
    # Kuriame sekas
    X, y = [], []
    for i in range(len(scaled_data) - sequence_length):
        X.append(scaled_data[i:i+sequence_length])
        y.append(scaled_data[i+sequence_length])
    
    X, y = np.array(X), np.array(y)
    
    # Skirstome į treniravimo ir testavimo rinkinius
    train_size = int(len(X) * (1 - test_size))
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    return X_train, y_train, X_test, y_test, scaler