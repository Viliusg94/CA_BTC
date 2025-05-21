"""
Prekybos rezultatų duomenų modeliai.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from database.models.base import Base  # Naudokite base.py importą

# Tikrinama, ar lentelė jau egzistuoja
simulation_exists = False
try:
    from sqlalchemy import inspect
    from database import engine
    inspector = inspect(engine)
    simulation_exists = 'simulations' in inspector.get_table_names()
except:
    pass

class Simulation(Base):
    """
    Prekybos simuliacijos modelis.
    Saugo informaciją apie modelio simuliaciją.
    """
    __tablename__ = "simulations"
    # Pridedame extend_existing=True, kad išvengtume konflikto
    __table_args__ = {'extend_existing': True} if simulation_exists else {}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(36), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    initial_balance = Column(Float, nullable=False, default=10000.0)
    final_balance = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)  # Return on Investment
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Ryšiai
    model = relationship("Model", back_populates="simulations")
    trades = relationship("Trade", back_populates="simulation", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="simulation", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="simulation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Simulation(id='{self.id}', name='{self.name}', roi={self.roi})>"

class Prediction(Base):
    """
    Modelio prognozės modelis.
    Saugo kiekvienos dienos prognozuojamus rezultatus.
    """
    __tablename__ = "predictions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulation_id = Column(String(36), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    prediction = Column(String(20), nullable=False)  # pvz., "kils", "kris"
    confidence = Column(Float, nullable=True)  # Pasitikėjimo lygis (0-1)
    actual = Column(String(20), nullable=True)  # Faktinis rezultatas
    price = Column(Float, nullable=True)  # Kaina prognozės metu
    
    # Ryšiai
    simulation = relationship("Simulation", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id='{self.id}', date='{self.date}', prediction='{self.prediction}')>"

class Trade(Base):
    """
    Prekybos sandorio modelis.
    Saugo informaciją apie atliktus pirkimo/pardavimo sandorius.
    """
    __tablename__ = "trades"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulation_id = Column(String(36), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    action = Column(String(10), nullable=False)  # "BUY" arba "SELL"
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # Perkamas/parduodamas kiekis
    value = Column(Float, nullable=False)  # Bendra sandorio vertė
    fee = Column(Float, nullable=False, default=0.0)  # Komisinis mokestis
    balance_after = Column(Float, nullable=False)  # Balansas po sandorio
    
    # Ryšiai
    simulation = relationship("Simulation", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(id='{self.id}', date='{self.date}', action='{self.action}', value={self.value})>"

# PRIDĖKITE ŠIĄ KLASĘ - Metric klasė, kuri buvo trūkstama
class Metric(Base):
    """
    Prekybos metrikos modelis.
    Saugo įvairias simuliacijos metrikos reikšmes.
    """
    __tablename__ = "metrics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulation_id = Column(String(36), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # Metrikos pavadinimas (pvz. "sharpe_ratio")
    value = Column(Float, nullable=True)  # Metrikos skaitinė reikšmė
    description = Column(String(255), nullable=True)  # Metrikos aprašymas
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Ryšiai
    simulation = relationship("Simulation", back_populates="metrics")
    
    def __repr__(self):
        return f"<Metric(id='{self.id}', name='{self.name}', value={self.value})>"