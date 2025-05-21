"""
Duomenų apdorojimo modulis.
Suteikia priemones Bitcoin kainų duomenų įkėlimui ir apdorojimui.
"""
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import plotly.graph_objects as go
import logging

# Konfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Klasė, atsakinga už Bitcoin kainų duomenų įkėlimą ir apdorojimą."""
    
    def __init__(self, data_path):
        """
        Inicializuojame duomenų procesorių.
        
        Args:
            data_path (str): Duomenų failo kelias
        """
        self.data_path = data_path
        self.feature_columns = ['open', 'high', 'low', 'close', 'volume']
        self.target_column = 'close'
        self.scaler = MinMaxScaler()
        self.df = None
        
        # Įkeliame duomenis
        self._load_data()
        
        logger.info(f"DataProcessor inicializuotas. Duomenų failas: {data_path}")
    
    def _load_data(self):
        """Įkelia Bitcoin kainų duomenis."""
        try:
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path)
                
                # Konvertuojame laiko stulpelį į datetime
                if 'time' in self.df.columns:
                    self.df['time'] = pd.to_datetime(self.df['time'])
                
                logger.info(f"Duomenys sėkmingai įkelti. Įrašų skaičius: {len(self.df)}")
                
                # Atnaujname scaler
                self.scaler.fit(self.df[self.feature_columns])
            else:
                logger.error(f"Duomenų failas nerastas: {self.data_path}")
                # Sukuriame dirbtinius duomenis, kad galėtume tęsti
                self._create_sample_data()
        except Exception as e:
            logger.error(f"Klaida įkeliant duomenis: {e}")
            # Sukuriame dirbtinius duomenis, kad galėtume tęsti
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Sukuria dirbtinius duomenis, jei nepavyksta įkelti iš failo."""
        logger.warning("Kuriami dirbtiniai duomenys demonstracijai")
        
        # Sukuriame dirbtines datas
        dates = pd.date_range(start="2023-01-01", periods=1000, freq="15min")
        
        # Sukuriame dirbtines kainas
        base_price = 30000
        noise = np.random.normal(0, 1000, 1000)
        trend = np.linspace(0, 5000, 1000)
        prices = base_price + trend + noise.cumsum()
        
        # Sukuriame dirbtines kainas ir apimtis
        self.df = pd.DataFrame({
            'time': dates,
            'open': prices - np.random.normal(0, 100, 1000),
            'high': prices + np.random.normal(200, 100, 1000),
            'low': prices - np.random.normal(200, 100, 1000),
            'close': prices,
            'volume': np.random.normal(100, 20, 1000)
        })
        
        # Atnaujname scaler
        self.scaler.fit(self.df[self.feature_columns])
        
        logger.warning(f"Sukurti dirbtiniai duomenys. Įrašų skaičius: {len(self.df)}")
    
    def get_data(self):
        """
        Grąžina DataFrame su duomenimis.
        
        Returns:
            pandas.DataFrame: Duomenų DataFrame
        """
        return self.df
    
    def get_normalized_data(self):
        """
        Grąžina normalizuotus duomenis.
        
        Returns:
            pandas.DataFrame: Normalizuotų duomenų DataFrame
        """
        if self.df is None:
            logger.error("Nėra įkeltų duomenų.")
            return None
        
        df_normalized = self.df.copy()
        df_normalized[self.feature_columns] = self.scaler.transform(self.df[self.feature_columns])
        
        return df_normalized
    
    def prepare_sequences(self, sequence_length=24, test_size=0.2):
        """
        Paruošia duomenų sekas modelio mokymui.
        
        Args:
            sequence_length (int): Sekos ilgis
            test_size (float): Testavimo duomenų dalis
            
        Returns:
            tuple: (X_train, X_test, y_train, y_test, test_dates) - mokymo ir testavimo duomenys
        """
        if self.df is None:
            logger.error("Nėra įkeltų duomenų.")
            return None, None, None, None, None
        
        # Normalizuojame duomenis
        df_normalized = self.get_normalized_data()
        
        # Sukuriame sekas
        X, y = self._create_sequences(df_normalized, sequence_length)
        
        # Padalijame į mokymo ir testavimo rinkinius
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Testavimo datos
        if 'time' in self.df.columns:
            test_dates = self.df['time'].iloc[sequence_length + split_idx:].reset_index(drop=True)
        else:
            test_dates = None
        
        return X_train, X_test, y_train, y_test, test_dates
    
    def _create_sequences(self, data, sequence_length):
        """
        Sukuria sekas iš laiko eilučių duomenų.
        
        Args:
            data (pandas.DataFrame): Duomenų DataFrame
            sequence_length (int): Sekos ilgis
            
        Returns:
            tuple: (X, y) - sekos ir tikslinės reikšmės
        """
        X, y = [], []
        
        data_array = data[self.feature_columns].values
        target_idx = self.feature_columns.index(self.target_column)
        
        for i in range(len(data) - sequence_length):
            X.append(data_array[i:i + sequence_length])
            y.append(data_array[i + sequence_length, target_idx])
            
        return np.array(X), np.array(y)
    
    def get_latest_data(self, sequence_length=24):
        """
        Grąžina naujausius duomenis prognozei.
        
        Args:
            sequence_length (int): Sekos ilgis
            
        Returns:
            numpy.ndarray: Naujausi duomenys
        """
        if self.df is None or len(self.df) < sequence_length:
            logger.error(f"Nepakanka duomenų. Turima: {0 if self.df is None else len(self.df)}, reikia: {sequence_length}")
            # Grąžiname dirbtinius duomenis
            return np.random.normal(30000, 1000, (sequence_length, len(self.feature_columns)))
        
        # Gauname paskutinius sequence_length įrašus
        latest_data = self.df[self.feature_columns].tail(sequence_length).values
        
        return latest_data
    
    def get_latest_price(self):
        """
        Grąžina naujausią Bitcoin kainą.
        
        Returns:
            float: Naujausia Bitcoin kaina
        """
        if self.df is None or len(self.df) == 0:
            logger.error("Nėra duomenų kainai gauti.")
            return 0.0
        
        return float(self.df['close'].iloc[-1])
    
    def get_price_change_24h(self):
        """
        Grąžina kainos pokytį per 24 valandas.
        
        Returns:
            dict: Kainos pokyčio informacija
        """
        if self.df is None or len(self.df) == 0:
            logger.error("Nėra duomenų pokyčiui skaičiuoti.")
            return {'change': 0.0, 'change_percent': 0.0, 'direction': 'neutral'}
        
        # Apskaičiuojame intervalo dydį 24 valandoms (96 = 24 val / 15 min)
        interval = 96
        
        if len(self.df) <= interval:
            current_price = float(self.df['close'].iloc[-1])
            previous_price = float(self.df['close'].iloc[0])
        else:
            current_price = float(self.df['close'].iloc[-1])
            previous_price = float(self.df['close'].iloc[-interval-1])
        
        change = current_price - previous_price
        change_percent = (change / previous_price) * 100 if previous_price != 0 else 0.0
        direction = 'up' if change > 0 else 'down' if change < 0 else 'neutral'
        
        return {
            'change': change,
            'change_percent': change_percent,
            'direction': direction
        }
    
    def get_price_chart(self, days=30):
        """
        Sukuria Bitcoin kainos grafiką.
        
        Args:
            days (int): Dienų skaičius
            
        Returns:
            plotly.graph_objects.Figure: Plotly grafikas
        """
        if self.df is None or len(self.df) == 0:
            logger.error("Nėra duomenų grafikui sukurti.")
            fig = go.Figure()
            fig.add_annotation(
                text="Nėra duomenų",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            return fig
        
        # Filtruojame pagal laikotarpį
        if 'time' in self.df.columns:
            end_date = self.df['time'].max()
            start_date = end_date - timedelta(days=days)
            df_filtered = self.df[self.df['time'] >= start_date].copy()
        else:
            # Jei nėra laiko stulpelio, imame paskutines N eilučių
            records_per_day = 96  # 24 val / 15 min = 96 įrašai per dieną
            df_filtered = self.df.tail(days * records_per_day).copy()
        
        # Sukuriame grafiką
        fig = go.Figure()
        
        # Pridedame kainų žvakutes
        if 'time' in self.df.columns:
            fig.add_trace(
                go.Candlestick(
                    x=df_filtered['time'],
                    open=df_filtered['open'],
                    high=df_filtered['high'],
                    low=df_filtered['low'],
                    close=df_filtered['close'],
                    name="Kainos"
                )
            )
        else:
            # Jei nėra laiko stulpelio, naudojame indeksus
            fig.add_trace(
                go.Candlestick(
                    x=df_filtered.index,
                    open=df_filtered['open'],
                    high=df_filtered['high'],
                    low=df_filtered['low'],
                    close=df_filtered['close'],
                    name="Kainos"
                )
            )
        
        # Atnaujina layoutą
        fig.update_layout(
            title="Bitcoin kainos istorija",
            xaxis_title="Data",
            yaxis_title="Kaina (USD)",
            template="plotly_white",
            xaxis_rangeslider_visible=False
        )
        
        return fig