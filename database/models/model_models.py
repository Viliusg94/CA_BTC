"""
Modelių duomenų modeliai.
Šis modulis apibrėžia modelių (ML) lentelių struktūrą naudojant SQLAlchemy ORM.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship

# Importuojame bazinę klasę iš projekto
from database.models.user_models import Base

class Model(Base):
    """
    Mašininio mokymosi modelio duomenų modelis.
    Saugo informaciją apie sukurtus modelius.
    """
    # Nurodome lentelės pavadinimą duomenų bazėje
    __tablename__ = "models"
    
    # Apibrėžiame lentelės stulpelius
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)  # Modelio pavadinimas
    type = Column(String(50), nullable=False)  # Modelio tipas: lstm, rnn, arima, kt.
    description = Column(Text, nullable=True)  # Modelio aprašymas
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    creator_id = Column(String(36), nullable=True)  # Modelio kūrėjo ID (jei yra)
    is_active = Column(Boolean, nullable=False, default=True)  # Ar modelis aktyvus
    trained = Column(Boolean, nullable=False, default=False)  # Ar modelis apmokytas
    hyperparameters = Column(Text, nullable=True)  # Modelio hiperparametrai JSON formatu
    file_path = Column(String(255), nullable=True)  # Kelias iki modelio failo
    last_training = Column(DateTime, nullable=True)  # Paskutinio apmokymo data
    version = Column(String(20), nullable=True)  # Modelio versija
    accuracy = Column(Float, nullable=True)  # Bendras modelio tikslumas
    
    # Apibrėžiame ryšius su kitomis lentelėmis
    # Ryšys su modelio metrikomis
    metrics = relationship("ModelMetric", back_populates="model", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="model")
    
    def __repr__(self):
        """
        Grąžina tekstinę objekto reprezentaciją.
        """
        return f"<Model(id='{self.id}', name='{self.name}', type='{self.type}')>"


class ModelVersion(Base):
    """
    Modelio versijos duomenų modelis.
    Saugo informaciją apie skirtingas modelio versijas.
    """
    # Nurodome lentelės pavadinimą duomenų bazėje
    __tablename__ = "model_versions"
    
    # Apibrėžiame lentelės stulpelius
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(36), nullable=False)  # Susietas modelis
    version_number = Column(String(20), nullable=False)  # Versijos numeris (pvz., "1.0.0")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    creator_id = Column(String(36), nullable=True)  # Versijos kūrėjo ID
    description = Column(Text, nullable=True)  # Versijos aprašymas
    hyperparameters = Column(Text, nullable=True)  # Versijos hiperparametrai JSON formatu
    file_path = Column(String(255), nullable=True)  # Kelias iki versijos modelio failo
    accuracy = Column(Float, nullable=True)  # Versijos tikslumas
    is_production = Column(Boolean, nullable=False, default=False)  # Ar tai gamybinė versija
    
    def __repr__(self):
        """
        Grąžina tekstinę objekto reprezentaciją.
        """
        return f"<ModelVersion(id='{self.id}', model_id='{self.model_id}', version='{self.version_number}')>"