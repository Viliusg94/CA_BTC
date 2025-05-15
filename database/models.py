# SUKURTI FAILĄ: d:\CA_BTC\database\models.py
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from database.config import DATABASE_URL, ECHO, POOL_SIZE, MAX_OVERFLOW

Base = declarative_base()

class BtcPriceData(Base):
    """Bitcoin kainos duomenų modelis"""
    __tablename__ = 'btc_price_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Pridedame indeksą greitai paieškai pagal datą
    __table_args__ = (
        Index('idx_timestamp', timestamp),
    )
    
    def __repr__(self):
        return f"<BtcPriceData(timestamp='{self.timestamp}', close='{self.close}')>"


class TechnicalIndicator(Base):
    """Techninių indikatorių modelis"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    price_id = Column(Integer, ForeignKey('btc_price_data.id'), nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # Slankieji vidurkiai
    sma7 = Column(Float)
    sma14 = Column(Float)
    sma30 = Column(Float)
    sma50 = Column(Float)
    sma200 = Column(Float)
    ema7 = Column(Float)
    ema14 = Column(Float)
    ema30 = Column(Float)
    
    # Momentumo indikatoriai
    rsi14 = Column(Float)
    rsi7 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_hist = Column(Float)
    
    # Kintamumo indikatoriai
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    atr14 = Column(Float)
    
    # Apimties indikatoriai
    obv = Column(Float)
    volume_sma20 = Column(Float)
    
    # Krypties indikatoriai
    adx14 = Column(Float)
    
    # Indeksai efektyviam paieškai
    __table_args__ = (
        Index('idx_tech_timestamp', timestamp),
        Index('idx_price_id', price_id),
    )
    
    # Ryšys su kainų duomenimis
    price_data = relationship("BtcPriceData")
    
    def __repr__(self):
        return f"<TechnicalIndicator(timestamp='{self.timestamp}')>"


class AdvancedFeature(Base):
    """Pažangių požymių modelis"""
    __tablename__ = 'advanced_features'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    price_id = Column(Integer, ForeignKey('btc_price_data.id'), nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # Lag požymiai
    close_lag1 = Column(Float)
    close_lag3 = Column(Float)
    close_lag7 = Column(Float)
    close_lag14 = Column(Float)
    close_lag30 = Column(Float)
    
    # Krypties požymiai
    trend_1d = Column(Integer)  # 1 (kyla), 0 (nekinta), -1 (krenta)
    trend_3d = Column(Integer)
    trend_7d = Column(Integer)
    
    # Sezoniniai požymiai
    day_of_week = Column(Integer)  # 0-6 (pirmadienis-sekmadienis)
    month = Column(Integer)  # 1-12
    quarter = Column(Integer)  # 1-4
    is_weekend = Column(Boolean)
    
    # Kintamumo požymiai
    volatility_7d = Column(Float)
    volatility_14d = Column(Float)
    volatility_30d = Column(Float)
    
    # Grąžos požymiai
    return_1d = Column(Float)
    return_3d = Column(Float)
    return_7d = Column(Float)
    
    # Indeksai
    __table_args__ = (
        Index('idx_adv_timestamp', timestamp),
        Index('idx_adv_price_id', price_id),
    )
    
    # Ryšys su kainų duomenimis
    price_data = relationship("BtcPriceData")
    
    def __repr__(self):
        return f"<AdvancedFeature(timestamp='{self.timestamp}')>"


class ModelPrediction(Base):
    """Modelio prognozių modelis"""
    __tablename__ = 'model_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Prognozės
    predicted_close = Column(Float)
    predicted_direction = Column(Integer)  # 1 (kils), 0 (kris)
    prediction_horizon = Column(Integer)  # Kiek periodų į priekį (1, 3, 7, etc.)
    
    # Įvertinimo metrikos
    confidence = Column(Float)
    
    # Prognozės laikas
    prediction_time = Column(DateTime, nullable=False)
    
    # Indeksai
    __table_args__ = (
        Index('idx_pred_timestamp', timestamp),
        Index('idx_model_name', model_name),
    )
    
    def __repr__(self):
        return f"<ModelPrediction(timestamp='{self.timestamp}', model='{self.model_name}')>"


def init_db():
    """Inicijuoja duomenų bazę su MySQL"""
    # Sukuriame engine objektą su MySQL
    engine = create_engine(
        DATABASE_URL,
        echo=ECHO,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW
    )
    
    # Sukuriame sesijų kūrimo objektą
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return engine, session