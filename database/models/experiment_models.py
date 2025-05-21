"""
Eksperimentų duomenų bazės modeliai.
Šis modulis apibrėžia eksperimentų ir jų rezultatų duomenų struktūras.
"""
import uuid
from datetime import datetime
import json
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database.models.base import Base

class Experiment(Base):
    """
    Eksperimento duomenų modelis.
    Saugo pagrindinę informaciją apie mašininio mokymosi eksperimentą.
    """
    __tablename__ = "experiments"
    
    # Pagrindinis identifikatorius
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Eksperimento pavadinimas
    name = Column(String(255), nullable=False, index=True)
    
    # Eksperimento sukūrimo data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Paskutinio atnaujinimo data
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Eksperimento statusas (pvz., "naujas", "vykdomas", "baigtas", "nutrauktas")
    status = Column(String(50), default="naujas", nullable=False, index=True)
    
    # Papildoma metaduomenų informacija JSON formatu
    experiment_metadata = Column(JSON, nullable=True)
    
    # Sąsaja su vartotoju (eksperimento kūrėju)
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Eksperimento aprašymas
    description = Column(Text, nullable=True)
    
    # Ryšys su eksperimento rezultatais (vienas-su-daug)
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")
    
    def __repr__(self):
        """Gražina objekto tekstinę reprezentaciją"""
        return f"<Experiment(id='{self.id}', name='{self.name}', status='{self.status}')>"
    
    def get_metadata_dict(self) -> dict:
        """
        Grąžina metaduomenis kaip žodyną.
        
        Returns:
            dict: Metaduomenų žodynas arba tuščias žodynas, jei nėra metaduomenų
        """
        if not self.experiment_metadata:
            return {}
        
        try:
            return json.loads(self.experiment_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_hyperparameters(self) -> dict:
        """
        Grąžina eksperimento hiperparametrus.
        
        Returns:
            dict: Hiperparametrų žodynas arba tuščias žodynas, jei nėra hiperparametrų
        """
        metadata = self.get_metadata_dict()
        return metadata.get("hyperparameters", {})

class ExperimentResult(Base):
    """
    Eksperimento rezultatų modelis.
    Saugo eksperimento metu gautas metrikų reikšmes.
    """
    __tablename__ = "experiment_results"
    
    # Pagrindinis identifikatorius
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Išorinis raktas į eksperimentų lentelę
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metrikos pavadinimas
    metric_name = Column(String(100), nullable=False, index=True)
    
    # Metrikos reikšmė (skaičius)
    metric_value = Column(Text, nullable=False)  # Saugome kaip tekstą, bet validuojame, kad būtų skaičius
    
    # Rezultato įrašymo data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Etapas, kuriame metrika buvo išmatuota (pvz., "treniravimas", "validacija", "testavimas")
    stage = Column(String(50), nullable=True)
    
    # Komentaras arba papildoma informacija
    notes = Column(Text, nullable=True)
    
    # Ryšys su eksperimentu
    experiment = relationship("Experiment", back_populates="results")
    
    def __repr__(self):
        """Grąžina objekto tekstinę reprezentaciją"""
        return f"<ExperimentResult(experiment_id='{self.experiment_id}', metric='{self.metric_name}', value='{self.metric_value}')>"
    
    @property
    def numeric_value(self) -> float:
        """
        Grąžina metrikos reikšmę kaip skaičių.
        
        Returns:
            float: Metrikos reikšmė kaip skaičius
        """
        try:
            return float(self.metric_value)
        except (ValueError, TypeError):
            return 0.0