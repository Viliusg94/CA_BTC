"""
Metrikų duomenų modeliai.
Apibrėžia metrikų lentelių struktūrą ir ryšius su kitomis lentelėmis.
"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

# Naudojame tą patį Base kaip ir kituose modeliuose
from database.models.base import Base

class UserMetric(Base):
    """
    Naudotojo metrikų duomenų modelis.
    Saugo įvairias naudotojo veiklos ir efektyvumo metrikas.
    """
    # Lentelės pavadinimas duomenų bazėje
    __tablename__ = "user_metrics"

    # Stulpeliai (lentelės laukai)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # accuracy, usage, performance, kt.
    metric_name = Column(String(100), nullable=False)  # average_prediction_accuracy, login_count, kt.
    numeric_value = Column(Float, nullable=True)  # Jei metrika yra skaitinė
    string_value = Column(String(255), nullable=True)  # Jei metrika yra tekstinė
    time_period = Column(String(20), nullable=True)  # daily, weekly, monthly, yearly
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    metadata = Column(Text, nullable=True)  # Papildoma informacija JSON formatu

    # Ryšiai su kitomis lentelėmis
    user = relationship("User", back_populates="metrics")

    def __repr__(self):
        """
        Grąžina objekto tekstinę reprezentaciją.
        """
        return f"<UserMetric(id='{self.id}', user_id='{self.user_id}', metric_type='{self.metric_type}', metric_name='{self.metric_name}')>"


class ModelMetric(Base):
    """
    Modelio metrikų duomenų modelis.
    Saugo įvairias modelio veikimo ir efektyvumo metrikas.
    """
    # Lentelės pavadinimas duomenų bazėje
    __tablename__ = "model_metrics"

    # Stulpeliai (lentelės laukai)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Naudotojas, atlikęs matavimą
    metric_type = Column(String(50), nullable=False)  # accuracy, training, testing, kt.
    metric_name = Column(String(100), nullable=False)  # prediction_accuracy, final_loss, rmse, kt.
    value = Column(Float, nullable=False)  # Metrikos reikšmė
    dataset_name = Column(String(100), nullable=True)  # Su kokiu duomenų rinkiniu atliktas matavimas
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    metadata = Column(Text, nullable=True)  # Papildoma informacija JSON formatu

    # Ryšiai su kitomis lentelėmis
    model = relationship("Model", back_populates="metrics")
    user = relationship("User")

    def __repr__(self):
        """
        Grąžina objekto tekstinę reprezentaciją.
        """
        return f"<ModelMetric(id='{self.id}', model_id='{self.model_id}', metric_type='{self.metric_type}', metric_name='{self.metric_name}')>"


class SessionMetric(Base):
    """
    Sesijos metrikų duomenų modelis.
    Saugo įvairias sesijų veikimo ir resursų metrikas.
    """
    # Lentelės pavadinimas duomenų bazėje
    __tablename__ = "session_metrics"

    # Stulpeliai (lentelės laukai)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # duration, resource, performance, kt.
    metric_name = Column(String(100), nullable=False)  # total_session_time, cpu_usage_percent, kt.
    numeric_value = Column(Float, nullable=True)  # Skaitinė metrikos reikšmė
    string_value = Column(String(255), nullable=True)  # Tekstinė metrikos reikšmė
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    metadata = Column(Text, nullable=True)  # Papildoma informacija JSON formatu

    # Ryšiai su kitomis lentelėmis
    session = relationship("UserSession", back_populates="metrics")

    def __repr__(self):
        """
        Grąžina objekto tekstinę reprezentaciją.
        """
        return f"<SessionMetric(id='{self.id}', session_id='{self.session_id}', metric_type='{self.metric_type}', metric_name='{self.metric_name}')>"