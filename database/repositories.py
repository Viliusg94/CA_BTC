"""
Specializuotos repozitorijos
-----------------------------
Šis modulis apibrėžia specializuotas repozitorijas konkretiems duomenų modeliams.
Kiekviena repozitorija išplečia bazinę repozitoriją ir prideda specifines užklausas.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, and_, or_, func, text
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import pandas as pd
import logging
from database.models import BtcPriceData, TechnicalIndicator, AdvancedFeature, ModelPrediction, TradingSignal, Portfolio
from database.base_repository import BaseRepository

# Sukuriame logerį
logger = logging.getLogger(__name__)

class BtcPriceRepository(BaseRepository):
    """
    Repozitorija Bitcoin kainų duomenims.
    Išplečia bazinę repozitoriją specifinėmis užklausomis.
    """
    def __init__(self, session):
        """
        Inicializuoja repozitoriją su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, BtcPriceData)
    
    def get_by_date_range(self, start_date, end_date):
        """
        Grąžina kainos duomenis pagal datų intervalą.
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
        
        Returns:
            list: BtcPriceData objektų sąrašas
        """
        try:
            return self.session.query(self.model).filter(
                self.model.timestamp >= start_date,
                self.model.timestamp <= end_date
            ).order_by(self.model.timestamp).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant kainų pagal datų intervalą: {e}")
            return []
    
    def get_latest(self, limit=1):
        """
        Grąžina naujausius duomenis.
        
        Args:
            limit: Kiek naujausių įrašų grąžinti
        
        Returns:
            list: BtcPriceData objektų sąrašas
        """
        try:
            return self.session.query(self.model).order_by(
                desc(self.model.timestamp)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant naujausius kainos duomenis: {e}")
            return []
    
    def get_time_interval(self, interval='1d', start_date=None, end_date=None):
        """
        Grąžina duomenis agreguotus pagal laiko intervalą.
        
        Args:
            interval: Laiko intervalas ('1h', '4h', '1d', '1w')
            start_date: Pradžios data (pasirinktinai)
            end_date: Pabaigos data (pasirinktinai)
        
        Returns:
            pandas.DataFrame: Agreguoti duomenys
        """
        try:
            # Pradžiame užklausą
            query = self.session.query(self.model)
            
            # Pridedame datų filtrus, jei jie nurodyti
            if start_date:
                query = query.filter(self.model.timestamp >= start_date)
            if end_date:
                query = query.filter(self.model.timestamp <= end_date)
            
            # Vykdome užklausą ir gauname duomenis
            price_data = query.order_by(self.model.timestamp).all()
            
            # Konvertuojame į pandas DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': item.timestamp,
                    'open': item.open,
                    'high': item.high,
                    'low': item.low,
                    'close': item.close,
                    'volume': item.volume,
                    'id': item.id
                }
                for item in price_data
            ])
            
            if df.empty:
                return df
            
            # Nustatome timestamp kaip indeksą
            df.set_index('timestamp', inplace=True)
            
            # Agreguojame duomenis pagal interval
            if interval == '1h':
                # Jau turime valandinius duomenis, nereikia agreguoti
                return df
            elif interval == '4h':
                resampled = df.resample('4H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum',
                    'id': 'last'  # Išsaugome paskutinį ID
                })
            elif interval == '1d':
                resampled = df.resample('D').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum',
                    'id': 'last'
                })
            elif interval == '1w':
                resampled = df.resample('W-MON').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum',
                    'id': 'last'
                })
            else:
                logger.warning(f"Neteisingas laiko intervalas: {interval}. Grąžinami neagreguoti duomenys.")
                return df
            
            # Pašaliname eilutes su NaN reikšmėmis
            resampled.dropna(inplace=True)
            
            return resampled
            
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant duomenis pagal laiko intervalą: {e}")
            return pd.DataFrame()
    
    def get_all_as_dataframe(self):
        """
        Grąžina visus kainos duomenis kaip pandas DataFrame.
        
        Returns:
            pandas.DataFrame: Kainos duomenys
        """
        try:
            # Gauname visus duomenis
            all_data = self.get_all()
            
            if not all_data:
                logger.warning("Duomenų bazėje nėra kainos duomenų.")
                return pd.DataFrame()
            
            # Konvertuojame į DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': item.timestamp,
                    'Open': item.open,
                    'High': item.high,
                    'Low': item.low,
                    'Close': item.close,
                    'Volume': item.volume,
                    'id': item.id
                }
                for item in all_data
            ])
            
            # Nustatome timestamp kaip indeksą
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            return df
        
        except Exception as e:
            logger.error(f"Klaida konvertuojant duomenis į DataFrame: {e}")
            return pd.DataFrame()
    
    def check_duplicate_timestamp(self, timestamp):
        """
        Patikrina, ar jau yra duomenys su nurodytu laiko žyma.
        
        Args:
            timestamp: Laiko žyma
        
        Returns:
            bool: True, jei laiko žyma jau egzistuoja, False - jei ne
        """
        try:
            return self.exists(timestamp=timestamp)
        except SQLAlchemyError as e:
            logger.error(f"Klaida tikrinant dubliuotą laiko žymą: {e}")
            return False


class TechnicalIndicatorRepository(BaseRepository):
    """
    Repozitorija techniniams indikatoriams.
    """
    def __init__(self, session):
        """
        Inicializuoja repozitoriją su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, TechnicalIndicator)
    
    def get_by_date_range(self, start_date, end_date):
        """
        Grąžina indikatorius pagal datų intervalą.
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
        
        Returns:
            list: TechnicalIndicator objektų sąrašas
        """
        try:
            return self.session.query(self.model).filter(
                self.model.timestamp >= start_date,
                self.model.timestamp <= end_date
            ).order_by(self.model.timestamp).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant indikatorių pagal datų intervalą: {e}")
            return []
    
    def get_with_price_data(self, limit=100):
        """
        Grąžina indikatorius kartu su kainos duomenimis.
        
        Args:
            limit: Kiek įrašų grąžinti
        
        Returns:
            list: Tuple objektų sąrašas (TechnicalIndicator, BtcPriceData)
        """
        try:
            return self.session.query(
                self.model, BtcPriceData
            ).join(
                BtcPriceData, self.model.price_id == BtcPriceData.id
            ).order_by(
                desc(self.model.timestamp)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant indikatorius su kainos duomenimis: {e}")
            return []
    
    def get_all_as_dataframe(self):
        """
        Grąžina visus indikatorius kaip pandas DataFrame.
        
        Returns:
            pandas.DataFrame: Indikatorių duomenys
        """
        try:
            # Gauname visus duomenis su join
            results = self.session.query(
                self.model, BtcPriceData
            ).join(
                BtcPriceData, self.model.price_id == BtcPriceData.id
            ).order_by(
                self.model.timestamp
            ).all()
            
            if not results:
                logger.warning("Duomenų bazėje nėra indikatorių.")
                return pd.DataFrame()
            
            # Konvertuojame į DataFrame
            data = []
            for indicator, price in results:
                row = {
                    'timestamp': indicator.timestamp,
                    'price_id': indicator.price_id,
                    'Open': price.open,
                    'High': price.high,
                    'Low': price.low,
                    'Close': price.close,
                    'Volume': price.volume,
                    'SMA_7': indicator.sma7,
                    'SMA_14': indicator.sma14,
                    'SMA_30': indicator.sma30,
                    'SMA_50': indicator.sma50,
                    'SMA_200': indicator.sma200,
                    'EMA_7': indicator.ema7,
                    'EMA_14': indicator.ema14,
                    'EMA_30': indicator.ema30,
                    'RSI_7': indicator.rsi7,
                    'RSI_14': indicator.rsi14,
                    'MACD': indicator.macd,
                    'MACD_signal': indicator.macd_signal,
                    'MACD_hist': indicator.macd_hist,
                    'Bollinger_upper': indicator.bb_upper,
                    'Bollinger_middle': indicator.bb_middle,
                    'Bollinger_lower': indicator.bb_lower,
                    'ATR_14': indicator.atr14,
                    'OBV': indicator.obv,
                    'Volume_SMA20': indicator.volume_sma20,
                    'ADX_14': indicator.adx14
                }
                data.append(row)
            
            # Sukuriame DataFrame
            df = pd.DataFrame(data)
            
            # Nustatome timestamp kaip indeksą
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            return df
        
        except Exception as e:
            logger.error(f"Klaida konvertuojant indikatorius į DataFrame: {e}")
            return pd.DataFrame()


class AdvancedFeatureRepository(BaseRepository):
    """
    Repozitorija pažangioms savybėms.
    """
    def __init__(self, session):
        """
        Inicializuoja repozitoriją su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, AdvancedFeature)
    
    def get_by_date_range(self, start_date, end_date):
        """
        Grąžina savybes pagal datų intervalą.
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
        
        Returns:
            list: AdvancedFeature objektų sąrašas
        """
        try:
            return self.session.query(self.model).filter(
                self.model.timestamp >= start_date,
                self.model.timestamp <= end_date
            ).order_by(self.model.timestamp).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant pažangių savybių pagal datų intervalą: {e}")
            return []
    
    def get_with_price_data(self, limit=100):
        """
        Grąžina savybes kartu su kainos duomenimis.
        
        Args:
            limit: Kiek įrašų grąžinti
        
        Returns:
            list: Tuple objektų sąrašas (AdvancedFeature, BtcPriceData)
        """
        try:
            return self.session.query(
                self.model, BtcPriceData
            ).join(
                BtcPriceData, self.model.price_id == BtcPriceData.id
            ).order_by(
                desc(self.model.timestamp)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant pažangias savybes su kainos duomenimis: {e}")
            return []


class TradingRepository(BaseRepository):
    """
    Repozitorija prekybos operacijoms.
    """
    def __init__(self, session):
        """
        Inicializuoja repozitoriją su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, None)  # Šią repozitoriją reikia išplėsti su jūsų Trading modeliu
    
    # Čia pridėkite metodus prekybos operacijoms


class PredictionRepository(BaseRepository):
    """
    Repozitorija modelio prognozėms.
    """
    def __init__(self, session):
        """
        Inicializuoja repozitoriją su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, ModelPrediction)
    
    def get_by_model_name(self, model_name, limit=100):
        """
        Grąžina prognozes pagal modelio pavadinimą.
        
        Args:
            model_name: Modelio pavadinimas
            limit: Kiek įrašų grąžinti
        
        Returns:
            list: ModelPrediction objektų sąrašas
        """
        try:
            return self.session.query(self.model).filter(
                self.model.model_name == model_name
            ).order_by(
                desc(self.model.prediction_time)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant prognozių pagal modelio pavadinimą: {e}")
            return []
    
    def get_latest_predictions(self, horizon=1, limit=1):
        """
        Grąžina naujausias prognozes pagal prognozavimo horizontą.
        
        Args:
            horizon: Prognozavimo horizontas (dienos)
            limit: Kiek įrašų grąžinti
        
        Returns:
            list: ModelPrediction objektų sąrašas
        """
        try:
            return self.session.query(self.model).filter(
                self.model.prediction_horizon == horizon
            ).order_by(
                desc(self.model.prediction_time)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant naujausias prognozes: {e}")
            return []


class TradingSignalRepository(BaseRepository):
    """
    Repozitorija prekybos signalams.
    """
    def __init__(self, session):
        """
        Inicializuoja repozitoriją su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, TradingSignal)
    
    def get_latest_signals(self, limit=30):
        """
        Grąžina naujausius prekybos signalus.
        
        Args:
            limit: Kiek naujausių signalų grąžinti
        
        Returns:
            list: TradingSignal objektų sąrašas
        """
        try:
            return self.session.query(self.model).order_by(
                desc(self.model.timestamp)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant naujausius prekybos signalus: {e}")
            return []
    
    def get_signals_by_date_range(self, start_date, end_date):
        """
        Grąžina signalus pagal datų intervalą.
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
        
        Returns:
            list: TradingSignal objektų sąrašas
        """
        try:
            return self.session.query(self.model).filter(
                self.model.timestamp >= start_date,
                self.model.timestamp <= end_date
            ).order_by(self.model.timestamp).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant signalų pagal datų intervalą: {e}")
            return []


class PortfolioRepository(BaseRepository):
    """
    Repozitorija prekybos portfeliams.
    """
    def __init__(self, session):
        """
        Inicializuoja repozitoriją su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, Portfolio)
    
    def get_by_name(self, name):
        """
        Grąžina portfelį pagal pavadinimą.
        
        Args:
            name: Portfelio pavadinimas
        
        Returns:
            Portfolio: Portfelio objektas arba None, jei nerastas
        """
        try:
            return self.session.query(self.model).filter_by(name=name).first()
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant portfelio pagal pavadinimą: {e}")
            return None
    
    def get_with_trades(self, portfolio_id):
        """
        Grąžina portfelį su visomis prekybos operacijomis.
        
        Args:
            portfolio_id: Portfelio ID
        
        Returns:
            Portfolio: Portfelio objektas su prekybos operacijomis
        """
        try:
            return self.session.query(self.model).options(
                joinedload(self.model.trades)
            ).filter_by(id=portfolio_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant portfelį su prekybos operacijomis: {e}")
            return None
    
    def get_portfolio_history(self, portfolio_id):
        """
        Grąžina portfelio vertės istoriją.
        
        Args:
            portfolio_id: Portfelio ID
        
        Returns:
            pandas.DataFrame: Portfelio vertės istorija
        """
        try:
            # Gauname portfelį su prekybos operacijomis
            portfolio = self.get_with_trades(portfolio_id)
            
            if not portfolio or not portfolio.trades:
                logger.warning(f"Nerastas portfelis arba jo prekybos operacijos: {portfolio_id}")
                return pd.DataFrame()
            
            # Surikiuojame prekybos operacijas pagal laiką
            trades = sorted(portfolio.trades, key=lambda t: t.timestamp)
            
            # Gauname visus kainos duomenis
            price_data = self.session.query(BtcPriceData).all()
            
            if not price_data:
                logger.warning("Nerasta kainos duomenų portfelio istorijai.")
                return pd.DataFrame()
            
            # Konvertuojame kainos duomenis į DataFrame
            price_df = pd.DataFrame([
                {
                    'timestamp': item.timestamp,
                    'close': item.close
                }
                for item in price_data
            ])
            
            price_df.set_index('timestamp', inplace=True)
            price_df.sort_index(inplace=True)
            
            # Sukuriame portfelio DataFrame
            portfolio_data = []
            
            # Inicializuojame portfelio būseną
            balance = portfolio.balance
            btc_amount = portfolio.btc_amount
            
            # Einame per kiekvieną prekybos operaciją
            for trade in trades:
                # Atnaujiname portfelio būseną
                if trade.trade_type == 'buy':
                    balance += trade.value
                    btc_amount -= trade.btc_amount
                else:  # sell
                    balance -= trade.value
                    btc_amount += trade.btc_amount
                
                # Pridedame būseną prieš operaciją
                portfolio_data.append({
                    'timestamp': trade.timestamp,
                    'balance': balance,
                    'btc_amount': btc_amount,
                    'trade_type': trade.trade_type,
                    'trade_amount': trade.btc_amount,
                    'trade_price': trade.price,
                    'trade_value': trade.value
                })
                
                # Atnaujiname būseną po operacijos
                if trade.trade_type == 'buy':
                    balance -= trade.value
                    btc_amount += trade.btc_amount
                else:  # sell
                    balance += trade.value
                    btc_amount -= trade.btc_amount
                
                # Pridedame būseną po operacijos
                portfolio_data.append({
                    'timestamp': trade.timestamp,
                    'balance': balance,
                    'btc_amount': btc_amount,
                    'trade_type': None,
                    'trade_amount': None,
                    'trade_price': None,
                    'trade_value': None
                })
            
            # Sukuriame DataFrame
            portfolio_df = pd.DataFrame(portfolio_data)
            
            if portfolio_df.empty:
                return portfolio_df
            
            # Nustatome timestamp kaip indeksą
            portfolio_df.set_index('timestamp', inplace=True)
            portfolio_df.sort_index(inplace=True)
            
            # Sujungiame su kainos duomenimis
            result = pd.merge_asof(
                portfolio_df,
                price_df,
                left_index=True,
                right_index=True,
                direction='nearest'
            )
            
            # Apskaičiuojame portfelio vertę
            result['portfolio_value'] = result['balance'] + (result['btc_amount'] * result['close'])
            
            return result
            
        except Exception as e:
            logger.error(f"Klaida gaunant portfelio istoriją: {e}")
            return pd.DataFrame()