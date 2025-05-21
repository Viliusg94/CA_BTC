import pandas as pd
import numpy as np
from datetime import datetime

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