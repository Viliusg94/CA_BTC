"""
Treniravimo užduočių duomenų modelis
"""
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(Enum):
    """Užduoties būsenų tipai"""
    PENDING = "pending"      # Laukianti vykdymo
    RUNNING = "running"      # Vykdoma šiuo metu
    COMPLETED = "completed"  # Sėkmingai įvykdyta
    FAILED = "failed"        # Įvykdymas nepavyko
    CANCELED = "canceled"    # Atšaukta vartotojo

class TrainingTask:
    """Modelio treniravimo užduotis"""
    
    def __init__(self, id=None, name=None, description=None, model_id=None, 
                 scheduled_time=None, status=TaskStatus.PENDING, created_at=None, 
                 updated_at=None, training_params=None, result=None, logs=None):
        """
        Inicializuojame užduoties objektą
        
        Args:
            id (str): Užduoties ID
            name (str): Užduoties pavadinimas
            description (str): Užduoties aprašymas
            model_id (str): Modelio, kurį reikia treniruoti, ID
            scheduled_time (datetime): Suplanuotas vykdymo laikas
            status (TaskStatus): Užduoties būsena
            created_at (datetime): Sukūrimo laikas
            updated_at (datetime): Paskutinio atnaujinimo laikas
            training_params (dict): Treniravimo parametrai
            result (dict): Užduoties rezultatai
            logs (list): Užduoties vykdymo žurnalas
        """
        # Generuojame ID, jei jis nepateiktas
        self.id = id or str(uuid.uuid4())
        
        # Pagrindinė informacija
        self.name = name or f"Užduotis-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        self.description = description or ""
        self.model_id = model_id
        
        # Laiko informacija
        self.scheduled_time = scheduled_time
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # Būsena ir rezultatai
        self.status = status
        self.training_params = training_params or {}
        self.result = result or {}
        self.logs = logs or []
    
    def to_dict(self):
        """
        Konvertuojame užduotį į žodyną (saugojimui JSON formatu)
        
        Returns:
            dict: Užduoties duomenys žodyno formatu
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model_id': self.model_id,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'training_params': self.training_params,
            'result': self.result,
            'logs': self.logs
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Sukuriame užduoties objektą iš žodyno
        
        Args:
            data (dict): Užduoties duomenys žodyno formatu
            
        Returns:
            TrainingTask: Sukurtas užduoties objektas
        """
        # Konvertuojame laiko žymes iš string į datetime
        scheduled_time = None
        if data.get('scheduled_time'):
            scheduled_time = datetime.fromisoformat(data['scheduled_time'])
        
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        # Konvertuojame status string į TaskStatus enum
        status = TaskStatus.PENDING
        if data.get('status'):
            status = TaskStatus(data['status'])
        
        # Sukuriame ir grąžiname naują objektą
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            model_id=data.get('model_id'),
            scheduled_time=scheduled_time,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            training_params=data.get('training_params', {}),
            result=data.get('result', {}),
            logs=data.get('logs', [])
        )