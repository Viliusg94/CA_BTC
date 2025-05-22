import os
import sqlite3
import uuid
from datetime import datetime
import json

# Pakeiskime importą, kad išvengtume ciklinio importo
# PRIEŠ: from database import db
# PO:
try:
    from database import db
except ImportError:
    # Jei nepavyksta importuoti, sukuriame fiktyvią klasę testavimui
    class MockDB:
        class Model:
            pass
        
        @staticmethod
        def Column(*args, **kwargs):
            return None
            
        Integer = String = DateTime = Text = Float = None
        
    db = MockDB()

"""
Rezultatų modeliai
"""

# Prognozės rezultato modelis
class PredictionResult(db.Model):
    """Prognozės rezultatų lentelė"""
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    prediction_horizon = db.Column(db.Integer)
    values = db.Column(db.Text)  # JSON stringas su prognozėmis
    
    def to_dict(self):
        """Konvertuoja modelį į žodyną"""
        return {
            'id': self.id,
            'model_type': self.model_type,
            'prediction_date': self.prediction_date.strftime('%Y-%m-%d %H:%M:%S'),
            'prediction_horizon': self.prediction_horizon,
            'values': self.values
        }

# Simuliacijos rezultato modelis
class SimulationResult(db.Model):
    """Simuliacijos rezultatų lentelė"""
    id = db.Column(db.Integer, primary_key=True)
    scenario_name = db.Column(db.String(100), nullable=False)
    simulation_date = db.Column(db.DateTime, default=datetime.utcnow)
    parameters = db.Column(db.Text)  # JSON stringas su parametrais
    results = db.Column(db.Text)  # JSON stringas su rezultatais
    
    def to_dict(self):
        """Konvertuoja modelį į žodyną"""
        return {
            'id': self.id,
            'scenario_name': self.scenario_name,
            'simulation_date': self.simulation_date.strftime('%Y-%m-%d %H:%M:%S'),
            'parameters': self.parameters,
            'results': self.results
        }

# Metrikos rezultato modelis
class MetricResult(db.Model):
    """Metrikų rezultatų lentelė"""
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    mae = db.Column(db.Float)
    mse = db.Column(db.Float)
    rmse = db.Column(db.Float)
    r2 = db.Column(db.Float)
    
    def to_dict(self):
        """Konvertuoja modelį į žodyną"""
        return {
            'id': self.id,
            'model_type': self.model_type,
            'evaluation_date': self.evaluation_date.strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': {
                'mae': self.mae,
                'mse': self.mse,
                'rmse': self.rmse,
                'r2': self.r2
            }
        }