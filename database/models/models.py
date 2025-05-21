from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.db_utils import Base

class Model(Base):
    """
    Modelio klasė
    """
    __tablename__ = 'models'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100))
    description = Column(Text, nullable=True)
    type = Column(String(50))  # lstm, gru, transformer, t.t.
    hyperparameters = Column(JSON, nullable=True)
    input_features = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    # Ryšys su simuliacijomis
    simulations = relationship("Simulation", back_populates="model", cascade="all, delete-orphan")
    # Ryšys su prognozėmis
    predictions = relationship("Prediction", back_populates="model", cascade="all, delete-orphan")
    
    # Visiškai pašaliname ryšį su metrikomis
    # model_metrics = relationship("Metric", back_populates="model", cascade="all, delete-orphan", foreign_keys="Metric.model_id")
    
    @classmethod
    def from_dict(cls, data):
        """
        Sukuria objektą iš žodyno
        
        Args:
            data (dict): Objekto duomenys
            
        Returns:
            Model: Naujas objektas
        """
        return cls(**data)
    
    def to_dict(self):
        """
        Konvertuoja objektą į žodyną
        
        Returns:
            dict: Objekto atributai
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'hyperparameters': self.hyperparameters,
            'input_features': self.input_features,
            'performance_metrics': self.performance_metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }