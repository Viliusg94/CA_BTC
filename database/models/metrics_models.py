"""
Metrikų duomenų modeliai.
Šis modulis apibrėžia metrikų lentelių struktūrą naudojant SQLAlchemy ORM.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

# Importuojame bazinę klasę iš projekto
from database.models.base import Base

class UserMetric(Base):
    """
    Naudotojų metrikų modelis.
    Saugo naudotojų veiklos ir efektyvumo metrikas.
    """
    # Nurodome lentelės pavadinimą duomenų bazėje
    __tablename__ = "user_metrics"
    
    # Apibrėžiame lentelės stulpelius
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # Metrikos tipas: accuracy, usage, performance
    metric_name = Column(String(100), nullable=False)  # Konkrečios metrikos pavadinimas
    numeric_value = Column(Float, nullable=True)  # Skaitinė reikšmė, jei taikoma
    string_value = Column(String(255), nullable=True)  # Tekstinė reikšmė, jei taikoma
    time_period = Column(String(20), nullable=True)  # Laikotarpis: daily, weekly, monthly, yearly
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    metric_metadata = Column(JSON)  # arba kitas duomenų tipas
    
    # Apibrėžiame ryšį su naudotoju
    user = relationship("User", back_populates="metrics")
    
    def __repr__(self):
        """
        Grąžina tekstinę objekto reprezentaciją.
        """
        return f"<UserMetric(id='{self.id}', user_id='{self.user_id}', metric_name='{self.metric_name}')>"


class ModelMetric(Base):
    """
    Modelių metrikų modelis.
    Saugo modelių veikimo ir efektyvumo metrikas.
    """
    # Nurodome lentelės pavadinimą duomenų bazėje
    __tablename__ = "model_metrics"
    
    # Apibrėžiame lentelės stulpelius
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Matavimą atlikęs naudotojas
    metric_type = Column(String(50), nullable=False)  # Metrikos tipas: accuracy, training, testing
    metric_name = Column(String(100), nullable=False)  # Konkrečios metrikos pavadinimas
    value = Column(Float, nullable=False)  # Metrikos reikšmė
    dataset_name = Column(String(100), nullable=True)  # Naudoto duomenų rinkinio pavadinimas
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    metric_metadata = Column(JSON)  # arba kitas duomenų tipas
    
    # Apibrėžiame ryšius
    model = relationship("Model", back_populates="metrics")
    user = relationship("User")
    
    def __repr__(self):
        """
        Grąžina tekstinę objekto reprezentaciją.
        """
        return f"<ModelMetric(id='{self.id}', model_id='{self.model_id}', metric_name='{self.metric_name}')>"


class SessionMetric(Base):
    """
    Sesijų metrikų modelis.
    Saugo sesijų veikimo ir resursų naudojimo metrikas.
    """
    # Nurodome lentelės pavadinimą duomenų bazėje
    __tablename__ = "session_metrics"
    
    # Apibrėžiame lentelės stulpelius
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # Metrikos tipas: duration, resource, performance
    metric_name = Column(String(100), nullable=False)  # Konkrečios metrikos pavadinimas
    numeric_value = Column(Float, nullable=True)  # Skaitinė reikšmė, jei taikoma
    string_value = Column(String(255), nullable=True)  # Tekstinė reikšmė, jei taikoma
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    metric_metadata = Column(JSON)  # arba kitas duomenų tipas
    
    # Apibrėžiame ryšį su sesija
    session = relationship("UserSession", back_populates="metrics")
    
    def __repr__(self):
        """
        Grąžina tekstinę objekto reprezentaciją.
        """
        return f"<SessionMetric(id='{self.id}', session_id='{self.session_id}', metric_name='{self.metric_name}')>"