"""
Treniravimo užduočių duomenų modelis
"""
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    """Užduoties statuso tipai"""
    PENDING = "pending"      # Laukiama vykdymo
    RUNNING = "running"      # Vykdoma
    COMPLETED = "completed"  # Įvykdyta sėkmingai
    FAILED = "failed"        # Nepavyko įvykdyti
    CANCELED = "canceled"    # Atšaukta

class TrainingTask:
    """Modelio treniravimo užduotis"""
    
    def __init__(self, id, name, description, model_id, scheduled_time, 
                status=TaskStatus.PENDING, created_at=None, updated_at=None,
                training_params=None, result=None, logs=None):
        """Inicializuojame užduoties objektą su nurodytais parametrais"""
        self.id = id
        self.name = name
        self.description = description
        self.model_id = model_id
        self.scheduled_time = scheduled_time
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.training_params = training_params or {}
        self.result = result or {}
        self.logs = logs or []
    
    def to_dict(self):
        """Konvertuojame užduotį į žodyną saugojimui"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model_id': self.model_id,
            'scheduled_time': self.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if self.scheduled_time else None,
            'status': self.status.value,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'training_params': self.training_params,
            'result': self.result,
            'logs': self.logs
        }
    
    @classmethod
    def from_dict(cls, data):
        """Sukuria užduotį iš žodyno"""
        # Konvertuojame string į datetime
        scheduled_time = None
        if data.get('scheduled_time'):
            scheduled_time = datetime.strptime(data['scheduled_time'], '%Y-%m-%d %H:%M:%S')
        
        created_at = None
        if data.get('created_at'):
            created_at = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.strptime(data['updated_at'], '%Y-%m-%d %H:%M:%S')
        
        # Konvertuojame status string į TaskStatus enum
        status = TaskStatus.PENDING
        if data.get('status'):
            status = TaskStatus(data['status'])
        
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