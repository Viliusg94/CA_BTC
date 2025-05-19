"""
Duomenų servisas
---------------------------
Šis modulis yra atsakingas už duomenų gavimą, paruošimą ir transformavimą.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataService:
    """
    Servisas darbui su duomenimis
    """
    def __init__(self):
        self.scaler = None
    
    def get_data_from_database(self):
        """
        Gauna BTC kainų duomenis iš duomenų bazės
        
        Returns:
            pandas.DataFrame: DataFrame su kainų duomenimis
        """
        # Šiame etape tik simuliuosime duomenų gavimą
        # Realiame projekte čia būtų naudojama duomenų bazės užklausa
        
        try:
            # Patikriname, ar yra cached duomenys
            cached_path = 'app/static/data/cached_data.csv'
            if os.path.exists(cached_path):
                data = pd.read_csv(cached_path, index_col=0, parse_dates=True)
                logger.info(f"Duomenys įkelti iš kešo. Eilučių: {len(data)}")
                return data
            
            # Jeigu ne, bandome įkelti iš processed direktorijos
            processed_path = 'data/processed/btc_features.csv'
            if os.path.exists(processed_path):
                data = pd.read_csv(processed_path, index_col=0, parse_dates=True)
                
                # Išsaugome į kešą
                os.makedirs('app/static/data', exist_ok=True)
                data.to_csv(cached_path)
                
                logger.info(f"Duomenys įkelti iš apdorotų failų. Eilučių: {len(data)}")
                return data
            
            # Jeigu nerandame, generuojame sintetinius duomenis
            logger.warning("Nerasti BTC duomenys. Sugeneruoti sintetiniai duomenys.")
            return self._generate_synthetic_data()
        
        except Exception as e:
            logger.error(f"Klaida gaunant duomenis: {str(e)}")
            return self._generate_synthetic_data()
    
    def _generate_synthetic_data(self):
        """
        Generuoja sintetinius duomenis testavimui
        
        Returns:
            pandas.DataFrame: Sintetiniai duomenys
        """
        # Generuojame 1000 dienų duomenis
        dates = pd.date_range(end=datetime.now(), periods=1000, freq='D')
        
        # Pradedame nuo 1000 ir pridedame atsitiktinį pokytį
        close_prices = [1000]
        for i in range(1, 1000):
            # Atsitiktinis pokytis nuo -3% iki +3%
            change = close_prices[-1] * (1 + np.random.uniform(-0.03, 0.03))
            close_prices.append(change)
        
        # Sukuriame DataFrame
        data = pd.DataFrame({
            'Close': close_prices,
            'Open': [price * (1 - np.random.uniform(0, 0.01)) for price in close_prices],
            'High': [price * (1 + np.random.uniform(0, 0.02)) for price in close_prices],
            'Low': [price * (1 - np.random.uniform(0, 0.02)) for price in close_prices],
            'Volume': [np.random.randint(100000, 1000000) for _ in range(1000)]
        }, index=dates)
        
        return data
    
    def prepare_data_for_training(self, sequence_length=60, prediction_days=1, test_size=0.2):
        """
        Paruošia duomenis modelio treniravimui
        
        Args:
            sequence_length (int): Sekos ilgis (kiek dienų naudoti kaip įvestį)
            prediction_days (int): Kiek dienų į priekį prognozuoti
            test_size (float): Testavimo duomenų dalis (0-1)
        
        Returns:
            tuple: (X_train, X_val, y_train, y_val, scaler)
        """
        # Gauname duomenis
        data = self.get_data_from_database()
        
        # Naudosime tik 'Close' stulpelį
        close_data = data['Close'].values.reshape(-1, 1)
        
        # Normalizuojame duomenis
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = self.scaler.fit_transform(close_data)
        
        # Paruošiame sekas
        X, y = [], []
        
        for i in range(sequence"""
Duomenų servisas
---------------------------
Šis modulis yra atsakingas už duomenų gavimą, paruošimą ir transformavimą.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataService:
    """
    Servisas darbui su duomenimis
    """
    def __init__(self):
        self.scaler = None
    
    def get_data_from_database(self):
        """
        Gauna BTC kainų duomenis iš duomenų bazės
        
        Returns:
            pandas.DataFrame: DataFrame su kainų duomenimis
        """
        # Šiame etape tik simuliuosime duomenų gavimą
        # Realiame projekte čia būtų naudojama duomenų bazės užklausa
        
        try:
            # Patikriname, ar yra cached duomenys
            cached_path = 'app/static/data/cached_data.csv'
            if os.path.exists(cached_path):
                data = pd.read_csv(cached_path, index_col=0, parse_dates=True)
                logger.info(f"Duomenys įkelti iš kešo. Eilučių: {len(data)}")
                return data
            
            # Jeigu ne, bandome įkelti iš processed direktorijos
            processed_path = 'data/processed/btc_features.csv'
            if os.path.exists(processed_path):
                data = pd.read_csv(processed_path, index_col=0, parse_dates=True)
                
                # Išsaugome į kešą
                os.makedirs('app/static/data', exist_ok=True)
                data.to_csv(cached_path)
                
                logger.info(f"Duomenys įkelti iš apdorotų failų. Eilučių: {len(data)}")
                return data
            
            # Jeigu nerandame, generuojame sintetinius duomenis
            logger.warning("Nerasti BTC duomenys. Sugeneruoti sintetiniai duomenys.")
            return self._generate_synthetic_data()
        
        except Exception as e:
            logger.error(f"Klaida gaunant duomenis: {str(e)}")
            return self._generate_synthetic_data()
    
    def _generate_synthetic_data(self):
        """
        Generuoja sintetinius duomenis testavimui
        
        Returns:
            pandas.DataFrame: Sintetiniai duomenys
        """
        # Generuojame 1000 dienų duomenis
        dates = pd.date_range(end=datetime.now(), periods=1000, freq='D')
        
        # Pradedame nuo 1000 ir pridedame atsitiktinį pokytį
        close_prices = [1000]
        for i in range(1, 1000):
            # Atsitiktinis pokytis nuo -3% iki +3%
            change = close_prices[-1] * (1 + np.random.uniform(-0.03, 0.03))
            close_prices.append(change)
        
        # Sukuriame DataFrame
        data = pd.DataFrame({
            'Close': close_prices,
            'Open': [price * (1 - np.random.uniform(0, 0.01)) for price in close_prices],
            'High': [price * (1 + np.random.uniform(0, 0.02)) for price in close_prices],
            'Low': [price * (1 - np.random.uniform(0, 0.02)) for price in close_prices],
            'Volume': [np.random.randint(100000, 1000000) for _ in range(1000)]
        }, index=dates)
        
        return data
    
    def prepare_data_for_training(self, sequence_length=60, prediction_days=1, test_size=0.2):
        """
        Paruošia duomenis modelio treniravimui
        
        Args:
            sequence_length (int): Sekos ilgis (kiek dienų naudoti kaip įvestį)
            prediction_days (int): Kiek dienų į priekį prognozuoti
            test_size (float): Testavimo duomenų dalis (0-1)
        
        Returns:
            tuple: (X_train, X_val, y_train, y_val, scaler)
        """
        # Gauname duomenis
        data = self.get_data_from_database()
        
        # Naudosime tik 'Close' stulpelį
        close_data = data['Close'].values.reshape(-1, 1)
        
        # Normalizuojame duomenis
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = self.scaler.fit_transform(close_data)
        
        # Paruošiame sekas
        X, y = [], []
        
        for i in range(sequence