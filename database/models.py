"""
Duomenų bazės modeliai
-----------------------------
Šis modulis apibrėžia SQLAlchemy ORM modelius, kurie naudojami duomenų 
saugojimui duomenų bazėje. Kiekvienas modelis atitinka duomenų bazės lentelę.
"""

from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Boolean, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os
from dotenv import load_dotenv
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
    """Modelio prognozių lentelė"""
    __tablename__ = 'model_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, nullable=False, comment="Data, kuriai pateikiama prognozė")
    model_name = Column(String(100), nullable=False, comment="Modelio pavadinimas")
    model_version = Column(String(50), nullable=False, comment="Modelio versija")
    predicted_close = Column(Float, nullable=True, comment="Prognozuojama uždarymo kaina")
    predicted_direction = Column(Integer, nullable=True, comment="Prognozuojama kryptis (1-aukštyn, 0-žemyn)")
    prediction_horizon = Column(Integer, default=1, comment="Prognozavimo horizontas dienomis")
    confidence = Column(Float, default=0.0, comment="Pasitikėjimo lygis (0-1)")
    prediction_time = Column(DateTime, default=datetime.utcnow, comment="Kada buvo atlikta prognozė")
    
    def __repr__(self):
        return f"<ModelPrediction(timestamp='{self.timestamp}', model='{self.model_name}')>"


class TradingSignal(Base):
    """Prekybos signalų lentelė"""
    __tablename__ = 'trading_signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, nullable=False, comment="Signalo data")
    price_id = Column(Integer, ForeignKey('btc_price_data.id'), nullable=False)
    signal_type = Column(String(50), nullable=False, comment="Signalo tipas (buy, sell, hold)")
    signal_strength = Column(Float, default=0.0, comment="Signalo stiprumas (0-1)")
    indicator_source = Column(String(100), nullable=True, comment="Indikatorius, sugeneravęs signalą")
    combined_signal = Column(Boolean, default=False, comment="Ar tai yra kombinuotas signalas")
    notes = Column(Text, nullable=True, comment="Papildoma informacija")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Signalai
    sma_signal = Column(Integer, default=0)  # 1=pirkti, -1=parduoti, 0=laikyti
    rsi_signal = Column(Integer, default=0)
    macd_signal = Column(Integer, default=0)
    bollinger_signal = Column(Integer, default=0)
    ml_signal = Column(Integer, default=0)
    
    # Metaduomenys
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Ryšys su kainų duomenimis
    price_data = relationship("BtcPriceData")


class Portfolio(Base):
    """Prekybos portfelio lentelė"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    balance = Column(Float, default=0.0)  # USD balansas
    btc_amount = Column(Float, default=0.0)  # BTC kiekis
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Ryšys su prekybos operacijomis
    trades = relationship("Trade", back_populates="portfolio")


class Trade(Base):
    """Prekybos operacijų lentelė"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    trade_type = Column(String(10), nullable=False)  # buy arba sell
    btc_amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)  # BTC kaina operacijos metu
    value = Column(Float, nullable=False)  # Operacijos vertė (btc_amount * price)
    
    # Nauja: mokesčių ir praslydimo stulpeliai
    fees = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.now)
    
    # Ryšys su portfeliu
    portfolio = relationship("Portfolio", back_populates="trades")


def init_db():
    """
    Inicializuoja duomenų bazės prisijungimą ir grąžina engine ir session objektus.
    
    Returns:
        tuple: (engine, session) - SQLAlchemy engine ir session objektai
    """
    load_dotenv()  # Užkrauname .env failą
    
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'btc_prediction')
    
    # Sukuriame prisijungimo URL
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Sukuriame SQLAlchemy engine
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv('SQLALCHEMY_ECHO', 'False').lower() in ('true', '1', 't'),
        pool_pre_ping=True
    )
    
    # Sukuriame lentelių struktūrą, jei ji dar neegzistuoja
    Base.metadata.create_all(engine)
    
    # Sukuriame Session klasę
    Session = sessionmaker(bind=engine)
    
    # Sukuriame sesijos objektą
    session = Session()
    
    return engine, session