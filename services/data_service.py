"""
Duomenų servisas
-----------------------------
Šis modulis apibrėžia DataService klasę, kuri pateikia aukštesnio lygio funkcionalumą
duomenims gauti, apdoroti ir transformuoti. Jis taip pat įgyvendina duomenų versijų valdymą.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import os
from database.unit_of_work import UnitOfWork
from database.models import BtcPriceData, TechnicalIndicator, AdvancedFeature, ModelPrediction

# Sukuriame logerį
logger = logging.getLogger(__name__)

class DataService:
    """
    Duomenų servisas, kuris pateikia aukštesnio lygio funkcionalumą
    duomenims gauti, apdoroti ir transformuoti.
    """
    def __init__(self, session):
        """
        Inicializuoja duomenų servisą su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        self.session = session
        self.uow = UnitOfWork(session)
    
    def get_btc_data_with_indicators(self, start_date=None, end_date=None, interval='1d'):
        """
        Grąžina Bitcoin duomenis su techniniais indikatoriais ir savybėmis.
        
        Args:
            start_date: Pradžios data (pasirinktinai)
            end_date: Pabaigos data (pasirinktinai)
            interval: Laiko intervalas ('1h', '4h', '1d', '1w')
        
        Returns:
            pandas.DataFrame: BTC duomenys su indikatoriais
        """
        try:
            with self.uow:
                # Gauname kainos duomenis pagal laiko intervalą
                price_data = self.uow.btc_prices.get_time_interval(
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if price_data.empty:
                    logger.warning("Nerasta kainos duomenų pagal nurodytus parametrus.")
                    return pd.DataFrame()
                
                # Gauname indikatorius
                indicators_df = self.uow.indicators.get_all_as_dataframe()
                
                if indicators_df.empty:
                    logger.warning("Nerasta techninių indikatorių.")
                    return price_data  # Grąžiname bent kainos duomenis
                
                # Sujungiame duomenis pagal laiko žymas
                merged_df = pd.merge(
                    price_data,
                    indicators_df,
                    left_index=True,
                    right_index=True,
                    how='inner',
                    suffixes=('', '_ind')
                )
                
                # Pašaliname dubliuotus stulpelius
                columns_to_drop = [col for col in merged_df.columns if col.endswith('_ind')]
                merged_df.drop(columns=columns_to_drop, inplace=True)
                
                return merged_df
                
        except Exception as e:
            logger.error(f"Klaida gaunant BTC duomenis su indikatoriais: {e}")
            return pd.DataFrame()
    
    def get_latest_data_for_prediction(self, days=30):
        """
        Grąžina naujausius duomenis prognozavimui.
        
        Args:
            days: Kiek dienų duomenų grąžinti
        
        Returns:
            pandas.DataFrame: Naujausi duomenys su indikatoriais ir savybėmis
        """
        try:
            with self.uow:
                # Gauname naujausią datą
                latest_data = self.uow.btc_prices.get_latest(1)
                if not latest_data:
                    logger.warning("Nerasta kainos duomenų.")
                    return pd.DataFrame()
                
                latest_date = latest_data[0].timestamp
                start_date = latest_date - timedelta(days=days)
                
                # Gauname duomenis su indikatoriais
                return self.get_btc_data_with_indicators(
                    start_date=start_date,
                    end_date=latest_date
                )
                
        except Exception as e:
            logger.error(f"Klaida gaunant naujausius duomenis prognozavimui: {e}")
            return pd.DataFrame()
    
    def save_prediction(self, prediction_data):
        """
        Išsaugo modelio prognozę duomenų bazėje.
        
        Args:
            prediction_data: Slovaras su prognozės duomenimis:
                - timestamp: Prognozuojama data
                - model_name: Modelio pavadinimas
                - model_version: Modelio versija
                - predicted_close: Prognozuojama kaina
                - predicted_direction: Prognozuojama kryptis (1 - kils, 0 - kris)
                - prediction_horizon: Prognozės horizontas (dienomis)
                - confidence: Prognozės pasitikėjimo lygis (0-1)
        
        Returns:
            ModelPrediction: Išsaugota prognozė arba None, jei įvyko klaida
        """
        try:
            with self.uow:
                # Sukuriame naują prognozės objektą
                prediction = ModelPrediction(
                    timestamp=prediction_data.get('timestamp', datetime.now()),
                    model_name=prediction_data.get('model_name', 'unknown'),
                    model_version=prediction_data.get('model_version', '1.0'),
                    predicted_close=prediction_data.get('predicted_close'),
                    predicted_direction=prediction_data.get('predicted_direction'),
                    prediction_horizon=prediction_data.get('prediction_horizon', 1),
                    confidence=prediction_data.get('confidence', 0.5),
                    prediction_time=datetime.now()
                )
                
                # Išsaugome prognozę
                return self.uow.predictions.add(prediction)
                
        except Exception as e:
            logger.error(f"Klaida išsaugant prognozę: {e}")
            return None
    
    def get_data_for_analysis(self, use_versioning=True):
        """
        Grąžina duomenis signalų analizei su versijos kontrole.
        
        Args:
            use_versioning: Ar naudoti versijų kontrolę
        
        Returns:
            pandas.DataFrame: Duomenys signalų analizei
        """
        try:
            # Jei naudojame versijų kontrolę, pirmiausia bandome įkelti duomenis iš CSV failo
            if use_versioning:
                csv_path = "data/processed/btc_features.csv"
                
                if os.path.exists(csv_path):
                    # Gauname failo modifikavimo laiką
                    file_modified = datetime.fromtimestamp(os.path.getmtime(csv_path))
                    
                    # Gauname naujausią duomenų bazės įrašo laiką
                    with self.uow:
                        latest_data = self.uow.btc_prices.get_latest(1)
                        if not latest_data:
                            logger.warning("Nerasta kainos duomenų duomenų bazėje.")
                            # Naudojame CSV failą, jei jis egzistuoja
                            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                            logger.info(f"Duomenys įkelti iš CSV failo: {csv_path}")
                            return df
                        db_latest_date = latest_data[0].timestamp
                    
                    # Jei CSV failas naujesnis arba lygus DB datai, naudojame jį
                    if file_modified >= db_latest_date:
                        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                        logger.info(f"Duomenys įkelti iš CSV failo (naujesni): {csv_path}")
                        return df
            
            # Kitaip, gauname duomenis iš duomenų bazės
            with self.uow:
                return self.get_btc_data_with_indicators()
                
        except Exception as e:
            logger.error(f"Klaida gaunant duomenis analizei: {e}")
            return pd.DataFrame()
    
    def save_data_version(self, df, version_name=None):
        """
        Išsaugo duomenų versiją.
        
        Args:
            df: DataFrame su duomenimis
            version_name: Versijos pavadinimas
        
        Returns:
            bool: True, jei išsaugojimas sėkmingas, False - jei ne
        """
        try:
            # Sukuriame versijų katalogą, jei jo nėra
            os.makedirs('data/versions', exist_ok=True)
            
            # Jei versijos pavadinimas nenurodytas, naudojame datą ir laiką
            if version_name is None:
                version_name = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Išsaugome duomenis CSV formatu
            csv_path = f"data/versions/btc_features_{version_name}.csv"
            df.to_csv(csv_path)
            
            logger.info(f"Duomenų versija išsaugota: {csv_path}")
            return True
                
        except Exception as e:
            logger.error(f"Klaida išsaugant duomenų versiją: {e}")
            return False
    
    def load_data_version(self, version_name):
        """
        Įkelia duomenų versiją.
        
        Args:
            version_name: Versijos pavadinimas
        
        Returns:
            pandas.DataFrame: Duomenys iš nurodytos versijos
        """
        try:
            # Tikriname, ar versija egzistuoja
            csv_path = f"data/versions/btc_features_{version_name}.csv"
            if not os.path.exists(csv_path):
                logger.warning(f"Nerasta duomenų versija: {csv_path}")
                return pd.DataFrame()
            
            # Įkeliame duomenis
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            logger.info(f"Duomenų versija įkelta: {csv_path}")
            return df
                
        except Exception as e:
            logger.error(f"Klaida įkeliant duomenų versiją: {e}")
            return pd.DataFrame()
    
    def get_data_versions(self):
        """
        Grąžina visas egzistuojančias duomenų versijas.
        
        Returns:
            list: Versijų pavadinimai
        """
        try:
            versions_dir = 'data/versions'
            if not os.path.exists(versions_dir):
                return []
            
            # Ieškome visų CSV failų
            files = [f for f in os.listdir(versions_dir) if f.startswith('btc_features_') and f.endswith('.csv')]
            
            # Ištraukiame versijų pavadinimus
            versions = [f.replace('btc_features_', '').replace('.csv', '') for f in files]
            
            return sorted(versions, reverse=True)
                
        except Exception as e:
            logger.error(f"Klaida gaunant duomenų versijas: {e}")
            return []
    
    def aggregate_data_by_period(self, period='weekly'):
        """
        Agreguoja duomenis pagal periodą.
        
        Args:
            period: Agregavimo periodas ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
        
        Returns:
            pandas.DataFrame: Agreguoti duomenys
        """
        try:
            with self.uow:
                # Gauname visus duomenis
                df = self.uow.btc_prices.get_all_as_dataframe()
                
                if df.empty:
                    logger.warning("Nerasta duomenų agregavimui.")
                    return df
                
                # Nustatome agregavimo periodą
                if period == 'daily':
                    rule = 'D'
                elif period == 'weekly':
                    rule = 'W-MON'
                elif period == 'monthly':
                    rule = 'MS'
                elif period == 'quarterly':
                    rule = 'QS'
                elif period == 'yearly':
                    rule = 'YS'
                else:
                    logger.warning(f"Neteisingas agregavimo periodas: {period}. Naudojama 'weekly'.")
                    rule = 'W-MON'
                
                # Agreguojame duomenis
                aggregated = df.resample(rule).agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })
                
                return aggregated
                
        except Exception as e:
            logger.error(f"Klaida agreguojant duomenis: {e}")
            return pd.DataFrame()