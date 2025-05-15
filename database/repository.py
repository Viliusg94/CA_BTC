# SUKURTI FAILĄ: d:\CA_BTC\database\repository.py
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, and_, or_, func
from datetime import datetime, timedelta
import pandas as pd
from database.models import BtcPriceData, TechnicalIndicator, AdvancedFeature, ModelPrediction

class BaseRepository:
    """
    Bazinė repozitorijos klasė CRUD operacijoms
    """
    def __init__(self, session, model):
        """
        Args:
            session: SQLAlchemy sesija
            model: SQLAlchemy modelio klasė
        """
        self.session = session
        self.model = model
    
    def add(self, entity):
        """Prideda naują įrašą į duomenų bazę"""
        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Klaida pridedant įrašą: {e}")
            return None
    
    def add_all(self, entities):
        """Prideda kelis įrašus į duomenų bazę"""
        try:
            self.session.add_all(entities)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Klaida pridedant įrašus: {e}")
            return False
    
    def get_by_id(self, id):
        """Gauna įrašą pagal ID"""
        return self.session.query(self.model).filter_by(id=id).first()
    
    def get_all(self):
        """Gauna visus įrašus"""
        return self.session.query(self.model).all()
    
    def update(self, entity):
        """Atnaujina įrašą"""
        try:
            self.session.merge(entity)
            self.session.commit()
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Klaida atnaujinant įrašą: {e}")
            return None
    
    def delete(self, entity):
        """Ištrina įrašą"""
        try:
            self.session.delete(entity)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Klaida ištrinant įrašą: {e}")
            return False
    
    def delete_by_id(self, id):
        """Ištrina įrašą pagal ID"""
        entity = self.get_by_id(id)
        if entity:
            return self.delete(entity)
        return False
    
    def count(self):
        """Suskaičiuoja įrašų skaičių"""
        return self.session.query(func.count(self.model.id)).scalar()


class BtcPriceRepository(BaseRepository):
    """
    Repozitorija BTC kainų duomenims
    """
    def __init__(self, session):
        """
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, BtcPriceData)
    
    def get_by_date_range(self, start_date, end_date):
        """
        Gauna BTC kainų duomenis pagal datų intervalą
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
            
        Returns:
            list: BtcPriceData objektų sąrašas
        """
        return self.session.query(self.model).filter(
            self.model.timestamp >= start_date,
            self.model.timestamp <= end_date
        ).order_by(self.model.timestamp).all()
    
    def get_latest(self, limit=1):
        """
        Gauna naujausius BTC kainų duomenis
        
        Args:
            limit: Įrašų kiekis
            
        Returns:
            list: BtcPriceData objektų sąrašas
        """
        return self.session.query(self.model).order_by(
            desc(self.model.timestamp)
        ).limit(limit).all()
    
    def to_dataframe(self, price_data_list):
        """
        Konvertuoja duomenų bazės įrašus į pandas DataFrame
        
        Args:
            price_data_list: BtcPriceData objektų sąrašas
            
        Returns:
            pandas.DataFrame: DataFrame su BTC kainų duomenimis
        """
        data = []
        for item in price_data_list:
            data.append({
                'timestamp': item.timestamp,
                'Open': item.open,
                'High': item.high,
                'Low': item.low,
                'Close': item.close,
                'Volume': item.volume
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    def get_dataframe_by_date_range(self, start_date, end_date):
        """
        Gauna BTC kainų duomenis kaip DataFrame pagal datų intervalą
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
            
        Returns:
            pandas.DataFrame: DataFrame su BTC kainų duomenimis
        """
        price_data_list = self.get_by_date_range(start_date, end_date)
        return self.to_dataframe(price_data_list)
    
    def get_all_as_dataframe(self):
        """
        Gauna visus BTC kainos duomenis kaip pandas DataFrame
        
        Returns:
            pandas.DataFrame: BTC kainų duomenys
        """
        import pandas as pd
        
        try:
            # Gauname visus duomenis
            all_data = self.get_all()
            
            if not all_data:
                print("Duomenų bazėje nėra kainų duomenų.")
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
            print(f"Klaida konvertuojant duomenis į DataFrame: {e}")
            return pd.DataFrame()
    
    def get_data_for_timeframe(self, timeframe='1d'):
        """
        Gauna duomenis pagal laiko intervalą (resampling)
        
        Args:
            timeframe: Laiko intervalas ('1h', '4h', '1d', '1w')
            
        Returns:
            list: BtcPriceData objektų sąrašas
        """
        # Čia reikėtų implementuoti specifinę logiką duomenų agregavimui
        # Tai galima padaryti su SQL užklausomis (GROUP BY) arba pandas resampling
        pass


class TechnicalIndicatorRepository(BaseRepository):
    """
    Repozitorija techniniams indikatoriams
    """
    def __init__(self, session):
        """
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, TechnicalIndicator)
    
    def get_by_price_id(self, price_id):
        """
        Gauna techninius indikatorius pagal kainos ID
        
        Args:
            price_id: BtcPriceData įrašo ID
            
        Returns:
            TechnicalIndicator: Techninio indikatoriaus objektas
        """
        return self.session.query(self.model).filter_by(price_id=price_id).first()
    
    def save_indicators(self, indicators_df, price_data_list):
        """
        Išsaugo techninius indikatorius duomenų bazėje
        
        Args:
            indicators_df: DataFrame su techniniais indikatoriais
            price_data_list: BtcPriceData objektų sąrašas
            
        Returns:
            bool: Ar pavyko išsaugoti
        """
        try:
            # Sukuriame žodyną su BtcPriceData objektais, indeksuotais pagal timestamp
            price_data_dict = {item.timestamp: item for item in price_data_list}
            
            # Sukuriame TechnicalIndicator objektus
            indicator_objects = []
            updated_count = 0
            created_count = 0
            
            for idx, row in indicators_df.iterrows():
                # Randame atitinkamą BtcPriceData objektą
                price_data = price_data_dict.get(idx)
                if not price_data:
                    continue
                
                # Patikriname, ar jau yra indikatorius šiam įrašui
                existing = self.get_by_price_id(price_data.id)
                if existing:
                    # Atnaujinti esamą
                    existing.sma7 = row.get('SMA_7') if 'SMA_7' in row else None
                    existing.sma25 = row.get('SMA_25') if 'SMA_25' in row else None
                    existing.sma99 = row.get('SMA_99') if 'SMA_99' in row else None
                    existing.rsi14 = row.get('RSI_14') if 'RSI_14' in row else None
                    existing.macd = row.get('MACD') if 'MACD' in row else None
                    existing.macd_signal = row.get('MACD_signal') if 'MACD_signal' in row else None
                    existing.macd_hist = row.get('MACD_hist') if 'MACD_hist' in row else None
                    existing.bollinger_upper = row.get('Bollinger_upper') if 'Bollinger_upper' in row else None
                    existing.bollinger_middle = row.get('Bollinger_middle') if 'Bollinger_middle' in row else None
                    existing.bollinger_lower = row.get('Bollinger_lower') if 'Bollinger_lower' in row else None
                    self.update(existing)
                    updated_count += 1
                else:
                    # Sukurti naują
                    indicator = TechnicalIndicator(
                        price_id=price_data.id,
                        timestamp=idx,
                        sma7=row.get('SMA_7') if 'SMA_7' in row else None,
                        sma25=row.get('SMA_25') if 'SMA_25' in row else None,
                        sma99=row.get('SMA_99') if 'SMA_99' in row else None,
                        rsi14=row.get('RSI_14') if 'RSI_14' in row else None,
                        macd=row.get('MACD') if 'MACD' in row else None,
                        macd_signal=row.get('MACD_signal') if 'MACD_signal' in row else None,
                        macd_hist=row.get('MACD_hist') if 'MACD_hist' in row else None,
                        bollinger_upper=row.get('Bollinger_upper') if 'Bollinger_upper' in row else None,
                        bollinger_middle=row.get('Bollinger_middle') if 'Bollinger_middle' in row else None,
                        bollinger_lower=row.get('Bollinger_lower') if 'Bollinger_lower' in row else None
                    )
                    indicator_objects.append(indicator)
                    created_count += 1
            
            # Išsaugome naujus indikatorius
            if indicator_objects:
                self.add_all(indicator_objects)
            
            print(f"Techninių indikatorių statistika: {created_count} nauji, {updated_count} atnaujinti")
            return True
        
        except Exception as e:
            print(f"Klaida išsaugant techninius indikatorius: {e}")
            return False
    
    def get_by_date_range(self, start_date, end_date):
        """
        Gauna techninius indikatorius pagal datų intervalą
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
            
        Returns:
            list: TechnicalIndicator objektų sąrašas
        """
        return self.session.query(self.model).filter(
            self.model.timestamp >= start_date,
            self.model.timestamp <= end_date
        ).order_by(self.model.timestamp).all()
    
    def get_with_price_data(self, limit=100):
        """
        Gauna techninius indikatorius kartu su kainų duomenimis (join)
        
        Args:
            limit: Įrašų kiekis
            
        Returns:
            list: Tuple objektų sąrašas (TechnicalIndicator, BtcPriceData)
        """
        return self.session.query(
            self.model, BtcPriceData
        ).join(
            BtcPriceData, self.model.price_id == BtcPriceData.id
        ).order_by(
            desc(self.model.timestamp)
        ).limit(limit).all()


class AdvancedFeatureRepository(BaseRepository):
    """
    Repozitorija pažangioms ypatybėms
    """
    def __init__(self, session):
        """
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, AdvancedFeature)
    
    def get_by_date_range(self, start_date, end_date):
        """
        Gauna pažangias ypatybes pagal datų intervalą
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
            
        Returns:
            list: AdvancedFeature objektų sąrašas
        """
        return self.session.query(self.model).filter(
            self.model.timestamp >= start_date,
            self.model.timestamp <= end_date
        ).order_by(self.model.timestamp).all()
    
    def get_with_price_data(self, limit=100):
        """
        Gauna pažangias ypatybes kartu su kainų duomenimis (join)
        
        Args:
            limit: Įrašų kiekis
            
        Returns:
            list: Tuple objektų sąrašas (AdvancedFeature, BtcPriceData)
        """
        return self.session.query(
            self.model, BtcPriceData
        ).join(
            BtcPriceData, self.model.price_id == BtcPriceData.id
        ).order_by(
            desc(self.model.timestamp)
        ).limit(limit).all()


class ModelPredictionRepository(BaseRepository):
    """
    Repozitorija modelio prognozėms
    """
    def __init__(self, session):
        """
        Args:
            session: SQLAlchemy sesija
        """
        super().__init__(session, ModelPrediction)
    
    def get_by_model(self, model_name, limit=100):
        """
        Gauna prognozes pagal modelio pavadinimą
        
        Args:
            model_name: Modelio pavadinimas
            limit: Įrašų kiekis
            
        Returns:
            list: ModelPrediction objektų sąrašas
        """
        return self.session.query(self.model).filter(
            self.model.model_name == model_name
        ).order_by(
            desc(self.model.prediction_time)
        ).limit(limit).all()
    
    def get_latest_by_horizon(self, horizon=1, limit=1):
        """
        Gauna naujausias prognozes pagal prognozės horizontą
        
        Args:
            horizon: Prognozės horizontas (kiek periodų į priekį)
            limit: Įrašų kiekis
            
        Returns:
            list: ModelPrediction objektų sąrašas
        """
        return self.session.query(self.model).filter(
            self.model.prediction_horizon == horizon
        ).order_by(
            desc(self.model.prediction_time)
        ).limit(limit).all()