import datetime
import json
import os
import uuid

class TrainingSession:
    """
    Modelis, skirtas saugoti treniravimo sesijos duomenis
    """
    
    def __init__(self, name=None, model_architecture=None, hyperparameters=None, description=None):
        """
        Inicializuoja treniravimo sesiją
        
        Args:
            name (str): Sesijos pavadinimas
            model_architecture (str): Modelio architektūros aprašymas
            hyperparameters (dict): Hiperparametrų žodynas
            description (str): Sesijos aprašymas
        """
        # Generuojame unikalų ID
        self.session_id = str(uuid.uuid4())
        
        # Nustatome laukelius
        self.name = name or f"Sesija-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.model_architecture = model_architecture or "Nenurodyta"
        self.hyperparameters = hyperparameters or {}
        self.description = description or ""
        
        # Sesijos statusas: 'new', 'running', 'completed', 'failed', 'stopped'
        self.status = "new"
        
        # Sesijos laiko parametrai
        self.created_at = datetime.datetime.now()
        self.started_at = None
        self.completed_at = None
        
        # Metrikos
        self.epochs_total = 0
        self.epochs_completed = 0
        self.current_loss = None
        self.current_accuracy = None
        self.best_loss = None
        self.best_accuracy = None
        
        # Mokymosi istorija (visos metrikos per epochas)
        self.history = {
            "loss": [],
            "accuracy": [],
            "val_loss": [],
            "val_accuracy": []
        }
        
        # Išsaugoto galutinio modelio kelias
        self.model_path = None
    
    def to_dict(self):
        """
        Konvertuoja sesiją į žodyną
        
        Returns:
            dict: Sesijos duomenys žodyno pavidalu
        """
        return {
            "session_id": self.session_id,
            "name": self.name,
            "model_architecture": self.model_architecture,
            "hyperparameters": self.hyperparameters,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "epochs_total": self.epochs_total,
            "epochs_completed": self.epochs_completed,
            "current_loss": self.current_loss,
            "current_accuracy": self.current_accuracy,
            "best_loss": self.best_loss,
            "best_accuracy": self.best_accuracy,
            "history": self.history,
            "model_path": self.model_path
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Sukuria sesiją iš žodyno
        
        Args:
            data (dict): Sesijos duomenys žodyno pavidalu
            
        Returns:
            TrainingSession: Sukurtas sesijos objektas
        """
        session = cls()
        
        # Nustatome visus laukelius
        session.session_id = data.get("session_id", str(uuid.uuid4()))
        session.name = data.get("name", "")
        session.model_architecture = data.get("model_architecture", "")
        session.hyperparameters = data.get("hyperparameters", {})
        session.description = data.get("description", "")
        session.status = data.get("status", "new")
        
        # Konvertuojame datos ir laiko eilutes į datetime objektus
        if data.get("created_at"):
            session.created_at = datetime.datetime.fromisoformat(data["created_at"])
        
        if data.get("started_at"):
            session.started_at = datetime.datetime.fromisoformat(data["started_at"])
        
        if data.get("completed_at"):
            session.completed_at = datetime.datetime.fromisoformat(data["completed_at"])
        
        # Nustatome metrikas
        session.epochs_total = data.get("epochs_total", 0)
        session.epochs_completed = data.get("epochs_completed", 0)
        session.current_loss = data.get("current_loss")
        session.current_accuracy = data.get("current_accuracy")
        session.best_loss = data.get("best_loss")
        session.best_accuracy = data.get("best_accuracy")
        
        # Nustatome mokymosi istoriją
        session.history = data.get("history", {
            "loss": [],
            "accuracy": [],
            "val_loss": [],
            "val_accuracy": []
        })
        
        # Nustatome modelio kelią
        session.model_path = data.get("model_path")
        
        return session
