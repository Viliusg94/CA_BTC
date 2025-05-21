from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey, Index, SmallInteger, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

def generate_uuid():
    """Generuoja unikalų ID"""
    return str(uuid.uuid4())

class Prediction(Base):
    """
    Prognozių lentelės modelis - optimizuota versija
    
    Optimizacijos:
    - Pakeisti duomenų tipai (DECIMAL vietoj Float tikslesniam saugojimui)
    - Pridėti papildomi indeksai greitesnei paieškai
    - Pridėtas komentarų stulpelis (metadata)
    """
    __tablename__ = 'predictions'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(36), nullable=False)
    prediction_date = Column(DateTime, nullable=False, default=datetime.now, index=True)
    target_date = Column(DateTime, nullable=False, index=True)
    predicted_value = Column(DECIMAL(20, 8), nullable=False)  # Naudojame DECIMAL tipą tikslesniam saugojimui
    actual_value = Column(DECIMAL(20, 8), nullable=True)  # Naudojame DECIMAL tipą tikslesniam saugojimui
    interval = Column(String(10), nullable=False, index=True)  # Indeksas greitesniam filtravimui pagal intervalą
    confidence = Column(DECIMAL(5, 4), nullable=True)  # Naudojame DECIMAL tipą tikslesniam saugojimui
    error_margin = Column(DECIMAL(10, 4), nullable=True)  # Naujas laukas - paklaidos riba
    metadata = Column(Text, nullable=True)  # Naujas laukas - papildomi duomenys JSON formatu
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Sukuriame sudėtinius indeksus dažnai naudojamiems filtravimams
    __table_args__ = (
        Index('idx_pred_model_target', model_id, target_date),  # Filtravimui pagal modelį ir datą
        Index('idx_pred_interval_date', interval, prediction_date),  # Filtravimui pagal intervalą ir datą
    )

class Simulation(Base):
    """
    Simuliacijų lentelės modelis - optimizuota versija
    
    Optimizacijos:
    - Pakeisti duomenų tipai (DECIMAL vietoj Float tikslesniam saugojimui)
    - SmallInteger vietoj Integer mažesniems skaičiams
    - Pridėta daugiau metaduomenų laukų
    """
    __tablename__ = 'simulations'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)  # Naujas laukas - aprašymas
    initial_capital = Column(DECIMAL(20, 8), nullable=False)
    fees = Column(DECIMAL(6, 5), nullable=False)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    strategy_type = Column(String(50), nullable=False, index=True)
    strategy_params = Column(Text, nullable=True)
    final_balance = Column(DECIMAL(20, 8), nullable=True)
    profit_loss = Column(DECIMAL(20, 8), nullable=True)
    roi = Column(DECIMAL(10, 4), nullable=True, index=True)  # Indeksas greičiau rasti pelningiausias strategijas
    max_drawdown = Column(DECIMAL(10, 4), nullable=True)
    total_trades = Column(SmallInteger, nullable=False, default=0)  # SmallInteger užima mažiau vietos
    winning_trades = Column(SmallInteger, nullable=False, default=0)  # SmallInteger užima mažiau vietos
    losing_trades = Column(SmallInteger, nullable=False, default=0)  # SmallInteger užima mažiau vietos
    win_rate = Column(DECIMAL(5, 2), nullable=True)  # Naujas laukas - laimėjimų santykis
    avg_profit = Column(DECIMAL(10, 4), nullable=True)  # Naujas laukas - vidutinis pelnas
    avg_loss = Column(DECIMAL(10, 4), nullable=True)  # Naujas laukas - vidutinis nuostolis
    is_completed = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Ryšys su sandoriais
    trades = relationship("Trade", back_populates="simulation", cascade="all, delete-orphan")
    
    # Sukuriame sudėtinius indeksus
    __table_args__ = (
        Index('idx_sim_strategy_roi', strategy_type, roi.desc()),  # Greičiau rasti pelningiausias strategijas
        Index('idx_sim_dates', start_date, end_date),  # Filtravimui pagal laikotarpį
    )

class Trade(Base):
    """
    Prekybos sandorių lentelės modelis - optimizuota versija
    
    Optimizacijos:
    - Pakeisti duomenų tipai į DECIMAL tikslesniam saugojimui
    - Pridėta daugiau indeksų
    - Pridėta papildomų metaduomenų laukų
    """
    __tablename__ = 'trades'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    simulation_id = Column(String(36), ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    type = Column(String(4), nullable=False, index=True)  # 'buy' arba 'sell'
    price = Column(DECIMAL(20, 8), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    value = Column(DECIMAL(20, 8), nullable=False)
    fee = Column(DECIMAL(20, 8), nullable=False)
    profit_loss = Column(DECIMAL(20, 8), nullable=True, index=True)  # Indeksas greičiau rasti pelningiausius sandorius
    position_id = Column(String(36), nullable=True)  # Naujas laukas - susieti pirkimo/pardavimo sandorius
    market_conditions = Column(Text, nullable=True)  # Naujas laukas - rinkos sąlygos sandorio metu
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Ryšys su simuliacija
    simulation = relationship("Simulation", back_populates="trades")
    
    # Sukuriame sudėtinius indeksus
    __table_args__ = (
        Index('idx_trade_date_type', date, type),  # Greičiau filtruoti pagal datą ir tipą
        Index('idx_trade_sim_date', simulation_id, date),  # Greičiau filtruoti sandorius tam tikrose simuliacijose
    )

class Metric(Base):
    """
    Metrikų lentelės modelis - optimizuota versija
    
    Optimizacijos:
    - Pakeisti duomenų tipai
    - Pridėta daugiau indeksų
    - Pridėta kategorizavimo sistema
    """
    __tablename__ = 'metrics'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False, index=True)
    category = Column(String(30), nullable=True, index=True)  # Naujas laukas - metrikos kategorija
    value = Column(DECIMAL(20, 8), nullable=False)
    model_id = Column(String(36), nullable=True, index=True)
    simulation_id = Column(String(36), ForeignKey('simulations.id', ondelete='SET NULL'), nullable=True, index=True)
    period = Column(String(20), nullable=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_benchmark = Column(Boolean, nullable=False, default=False)  # Naujas laukas - ar tai lyginamoji metrika
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Ryšys su simuliacija (opcionalus)
    simulation = relationship("Simulation")
    
    # Sukuriame sudėtinius indeksus
    __table_args__ = (
        Index('idx_metric_name_date', name, date),  # Greičiau rasti metrikos istoriją
        Index('idx_metric_category', category, name),  # Greičiau rasti susijusias metrikas
        # Užtikriname, kad bent vienas iš model_id arba simulation_id būtų ne NULL
        CheckConstraint('model_id IS NOT NULL OR simulation_id IS NOT NULL', name='chk_metric_relation'),
    )