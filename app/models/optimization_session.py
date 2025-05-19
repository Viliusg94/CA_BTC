import json
import datetime
import uuid
import os

class OptimizationSession:
    """
    Modelis hiperparametrų optimizavimo sesijoms saugoti
    """
    
    def __init__(self, name=None, algorithm=None, model_type=None, parameters=None):
        """
        Inicializuoja optimizavimo sesiją
        
        Args:
            name (str): Sesijos pavadinimas
            algorithm (str): Optimizavimo algoritmas (grid_search, random_search, bayesian)
            model_type (str): Modelio tipas, kuriam atliekamas optimizavimas
            parameters (dict): Parametrų ribos ir nustatymai
        """
        # Generuojame unikalų ID
        self.session_id = str(uuid.uuid4())
        
        # Pagrindinė informacija
        self.name = name or f"Optimizavimas-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        self.algorithm = algorithm
        self.model_type = model_type
        self.parameters = parameters or {}
        
        # Laiko žymės
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        self.completed_at = None
        
        # Sesijos būsena
        self.status = "created"  # created, running, completed, failed
        
        # Optimizavimo rezultatai
        self.trials = []  # Visi atlikti bandymai
        self.best_params = {}  # Geriausi rasti parametrai
        self.best_score = None  # Geriausias rezultatas
        self.metrics = {}  # Įvairios metrikos
        
        # Pridedame archyvavimo būseną
        self.archived = False
        
    def add_trial(self, params, score, metrics=None):
        """
        Prideda naują bandymą į sesiją
        
        Args:
            params (dict): Bandymo parametrai
            score (float): Bandymo rezultatas
            metrics (dict): Papildomos metrikos
        """
        trial = {
            "trial_id": len(self.trials) + 1,
            "params": params,
            "score": score,
            "metrics": metrics or {},
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.trials.append(trial)
        self.updated_at = datetime.datetime.now()
        
        # Jei tai geriausias bandymas, atnaujiname geriausius parametrus
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            self.best_params = params.copy()
            
    def complete(self):
        """
        Pažymi sesiją kaip užbaigtą
        """
        self.status = "completed"
        self.completed_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        
    def fail(self, error_message=None):
        """
        Pažymi sesiją kaip nepavykusią
        
        Args:
            error_message (str): Klaidos pranešimas
        """
        self.status = "failed"
        if error_message:
            self.metrics["error"] = error_message
        self.updated_at = datetime.datetime.now()
        
    def to_dict(self):
        """
        Konvertuoja sesiją į žodyną
        
        Returns:
            dict: Sesijos duomenys
        """
        data = {
            "session_id": self.session_id,
            "name": self.name,
            "algorithm": self.algorithm,
            "model_type": self.model_type,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "trials": self.trials,
            "best_params": self.best_params,
            "best_score": self.best_score,
            "metrics": self.metrics,
            "archived": self.archived
        }
        return data
        
    @classmethod
    def from_dict(cls, data):
        """
        Sukuria sesiją iš žodyno
        
        Args:
            data (dict): Sesijos duomenys
            
        Returns:
            OptimizationSession: Sukurta sesija
        """
        session = cls()
        
        session.session_id = data.get("session_id", str(uuid.uuid4()))
        session.name = data.get("name", "")
        session.algorithm = data.get("algorithm", "")
        session.model_type = data.get("model_type", "")
        session.parameters = data.get("parameters", {})
        
        # Konvertuojame datos eilutes į datetime objektus
        session.created_at = datetime.datetime.fromisoformat(data.get("created_at", datetime.datetime.now().isoformat()))
        session.updated_at = datetime.datetime.fromisoformat(data.get("updated_at", datetime.datetime.now().isoformat()))
        
        if data.get("completed_at"):
            session.completed_at = datetime.datetime.fromisoformat(data["completed_at"])
        
        session.status = data.get("status", "created")
        session.trials = data.get("trials", [])
        session.best_params = data.get("best_params", {})
        session.best_score = data.get("best_score")
        session.metrics = data.get("metrics", {})
        
        # Pridedame archyvavimo būsenos užkrovimą
        session.archived = data.get("archived", False)
        
        return session