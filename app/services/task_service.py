"""
Servisas užduočių valdymui
"""
import os
import json
import uuid
from datetime import datetime
import logging

from app.models.task import TrainingTask, TaskStatus

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class TaskService:
    """Servisas, skirtas dirbti su treniravimo užduotimis"""
    
    def __init__(self):
        """Inicializuojame TaskService"""
        # Nustatome failo kelią užduočių saugojimui
        self.data_dir = os.path.join('data', 'tasks')
        os.makedirs(self.data_dir, exist_ok=True)
        self.tasks_file = os.path.join(self.data_dir, 'training_tasks.json')
        
        # Inicializuojame užduočių sąrašą
        self.tasks = self._load_tasks()
    
    def _load_tasks(self):
        """Užkrauna užduotis iš failo"""
        if not os.path.exists(self.tasks_file):
            # Jei failas neegzistuoja, grąžiname tuščią sąrašą
            return []
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
                return [TrainingTask.from_dict(task_data) for task_data in tasks_data]
        except Exception as e:
            logger.error(f"Klaida užkraunant užduotis: {e}")
            return []
    
    def _save_tasks(self):
        """Išsaugo užduotis į failą"""
        try:
            tasks_data = [task.to_dict() for task in self.tasks]
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Klaida išsaugant užduotis: {e}")
            return False
    
    def get_all_tasks(self):
        """Grąžina visas užduotis"""
        return self.tasks
    
    def get_task_by_id(self, task_id):
        """Grąžina užduotį pagal ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def create_task(self, name, description, model_id, scheduled_time, training_params=None):
        """Sukuria naują užduotį"""
        # Generuojame unikalų ID
        task_id = str(uuid.uuid4())
        
        # Konvertuojame scheduled_time į datetime, jei tai string
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
        
        # Sukuriame naują užduotį
        task = TrainingTask(
            id=task_id,
            name=name,
            description=description,
            model_id=model_id,
            scheduled_time=scheduled_time,
            training_params=training_params or {}
        )
        
        # Pridedame užduotį į sąrašą
        self.tasks.append(task)
        
        # Išsaugome pakeitimus
        self._save_tasks()
        
        return task
    
    def update_task(self, task_id, **kwargs):
        """Atnaujina egzistuojančią užduotį"""
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        # Atnaujina užduoties atributus
        for key, value in kwargs.items():
            if hasattr(task, key):
                # Jei tai scheduled_time ir tai string, konvertuojame į datetime
                if key == 'scheduled_time' and isinstance(value, str):
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                
                # Jei tai status ir tai string, konvertuojame į TaskStatus enum
                if key == 'status' and isinstance(value, str):
                    value = TaskStatus(value)
                
                setattr(task, key, value)
        
        # Atnaujina updated_at laiką
        task.updated_at = datetime.now()
        
        # Išsaugo pakeitimus
        self._save_tasks()
        
        return task
    
    def delete_task(self, task_id):
        """Ištrina užduotį pagal ID"""
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        
        # Pašaliname užduotį iš sąrašo
        self.tasks = [t for t in self.tasks if t.id != task_id]
        
        # Išsaugo pakeitimus
        self._save_tasks()
        
        return True
    
    def get_tasks_for_date(self, date):
        """Grąžina užduotis nurodytai datai"""
        # Konvertuojame į datetime.date, jei tai datetime objektas
        if isinstance(date, datetime):
            date = date.date()
        
        # Filtruojame užduotis pagal datą
        tasks_for_date = []
        for task in self.tasks:
            if task.scheduled_time and task.scheduled_time.date() == date:
                tasks_for_date.append(task)
        
        return tasks_for_date
    
    def get_pending_tasks(self):
        """Grąžina laukiančias vykdymo užduotis"""
        return [task for task in self.tasks if task.status == TaskStatus.PENDING]
    
    def update_task_status(self, task_id, status, result=None, log_message=None):
        """Atnaujina užduoties būseną"""
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        # Konvertuojame status į TaskStatus enum, jei tai string
        if isinstance(status, str):
            status = TaskStatus(status)
        
        # Atnaujina būseną
        task.status = status
        
        # Atnaujina rezultatus, jei jie pateikti
        if result:
            task.result = result
        
        # Prideda žurnalo žinutę, jei ji pateikta
        if log_message:
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': log_message
            }
            task.logs.append(log_entry)
        
        # Atnaujina updated_at laiką
        task.updated_at = datetime.now()
        
        # Išsaugo pakeitimus
        self._save_tasks()
        
        return task