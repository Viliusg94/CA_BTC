"""
Servisas užduočių valdymui
"""
import os
import json
import logging
from datetime import datetime

from app.models.task import TrainingTask, TaskStatus

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class TaskService:
    """Servisas, atsakingas už treniravimo užduočių valdymą"""
    
    def __init__(self, data_dir=None):
        """
        Inicializuojame TaskService
        
        Args:
            data_dir (str): Direktorija, kurioje saugomi užduočių duomenys
        """
        # Nustatome duomenų direktoriją
        self.data_dir = data_dir or os.path.join('data', 'tasks')
        
        # Sukuriame direktoriją, jei tokios nėra
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Nustatome failo kelią
        self.tasks_file = os.path.join(self.data_dir, 'training_tasks.json')
        
        # Užkrauname užduotis iš failo
        self.tasks = self._load_tasks()
        
        logger.info(f"TaskService inicializuotas. Užkrauta {len(self.tasks)} užduočių.")
    
    def _load_tasks(self):
        """
        Užkrauname užduotis iš failo
        
        Returns:
            list: Užduočių sąrašas
        """
        if not os.path.exists(self.tasks_file):
            logger.info(f"Užduočių failas nerastas: {self.tasks_file}")
            return []
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
                return [TrainingTask.from_dict(task_data) for task_data in tasks_data]
        except Exception as e:
            logger.error(f"Klaida užkraunant užduotis: {e}")
            return []
    
    def _save_tasks(self):
        """
        Išsaugome užduotis į failą
        
        Returns:
            bool: True, jei sėkmingai išsaugota, kitaip False
        """
        try:
            # Konvertuojame užduotis į žodynus
            tasks_data = [task.to_dict() for task in self.tasks]
            
            # Įrašome į failą JSON formatu
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Išsaugota {len(self.tasks)} užduočių į {self.tasks_file}")
            return True
        
        except Exception as e:
            logger.error(f"Klaida išsaugant užduotis: {e}")
            return False
    
    # CRUD operacijos
    
    def get_all_tasks(self):
        """
        Grąžiname visas užduotis
        
        Returns:
            list: Visų užduočių sąrašas
        """
        return self.tasks
    
    def get_task_by_id(self, task_id):
        """
        Grąžiname užduotį pagal ID
        
        Args:
            task_id (str): Užduoties ID
            
        Returns:
            TrainingTask: Užduoties objektas arba None, jei nerasta
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        
        logger.warning(f"Užduotis su ID {task_id} nerasta")
        return None
    
    def create_task(self, name, description, model_id, scheduled_time, training_params=None):
        """
        Sukuriame naują užduotį
        
        Args:
            name (str): Užduoties pavadinimas
            description (str): Užduoties aprašymas
            model_id (str): Modelio ID
            scheduled_time (datetime): Suplanuotas vykdymo laikas
            training_params (dict): Treniravimo parametrai
            
        Returns:
            TrainingTask: Sukurta užduotis
        """
        # Sukuriame naują užduotį
        task = TrainingTask(
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
        
        logger.info(f"Sukurta nauja užduotis: {name} (ID: {task.id})")
        return task
    
    def update_task(self, task_id, **kwargs):
        """
        Atnaujiname užduotį
        
        Args:
            task_id (str): Užduoties ID
            **kwargs: Atributai, kuriuos norime atnaujinti
            
        Returns:
            TrainingTask: Atnaujinta užduotis arba None, jei nerasta
        """
        # Randame užduotį
        task = self.get_task_by_id(task_id)
        if not task:
            logger.warning(f"Negalima atnaujinti: užduotis su ID {task_id} nerasta")
            return None
        
        # Atnaujiname atributus
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # Atnaujiname updated_at laiką
        task.updated_at = datetime.now()
        
        # Išsaugome pakeitimus
        self._save_tasks()
        
        logger.info(f"Atnaujinta užduotis: {task.name} (ID: {task.id})")
        return task
    
    def delete_task(self, task_id):
        """
        Ištriname užduotį
        
        Args:
            task_id (str): Užduoties ID
            
        Returns:
            bool: True, jei sėkmingai ištrinta, kitaip False
        """
        # Randame užduotį
        task = self.get_task_by_id(task_id)
        if not task:
            logger.warning(f"Negalima ištrinti: užduotis su ID {task_id} nerasta")
            return False
        
        # Pašaliname užduotį iš sąrašo
        self.tasks = [t for t in self.tasks if t.id != task_id]
        
        # Išsaugome pakeitimus
        self._save_tasks()
        
        logger.info(f"Ištrinta užduotis: {task.name} (ID: {task.id})")
        return True
    
    # Filtravimo metodai
    
    def get_tasks_by_status(self, status):
        """
        Grąžiname užduotis pagal būseną
        
        Args:
            status (TaskStatus): Užduoties būsena
            
        Returns:
            list: Užduočių sąrašas su nurodyta būsena
        """
        return [task for task in self.tasks if task.status == status]
    
    def get_pending_tasks(self):
        """
        Grąžiname laukiančias vykdymo užduotis
        
        Returns:
            list: Laukiančių užduočių sąrašas
        """
        return self.get_tasks_by_status(TaskStatus.PENDING)
    
    def get_running_tasks(self):
        """
        Grąžiname vykdomas užduotis
        
        Returns:
            list: Vykdomų užduočių sąrašas
        """
        return self.get_tasks_by_status(TaskStatus.RUNNING)
    
    def get_completed_tasks(self):
        """
        Grąžiname įvykdytas užduotis
        
        Returns:
            list: Įvykdytų užduočių sąrašas
        """
        return self.get_tasks_by_status(TaskStatus.COMPLETED)
    
    def get_tasks_for_date(self, date):
        """
        Grąžiname užduotis nurodytai datai
        
        Args:
            date (datetime.date): Data
            
        Returns:
            list: Užduočių sąrašas tai datai
        """
        tasks_for_date = []
        
        for task in self.tasks:
            # Jei užduotis turi suplanuotą laiką ir data sutampa
            if task.scheduled_time and task.scheduled_time.date() == date:
                tasks_for_date.append(task)
        
        return tasks_for_date
    
    def update_task_status(self, task_id, status, result=None, log_message=None):
        """
        Atnaujiname užduoties būseną
        
        Args:
            task_id (str): Užduoties ID
            status (TaskStatus): Nauja būsena
            result (dict): Rezultatai (jei yra)
            log_message (str): Žurnalo žinutė (jei yra)
            
        Returns:
            TrainingTask: Atnaujinta užduotis arba None, jei nerasta
        """
        # Randame užduotį
        task = self.get_task_by_id(task_id)
        if not task:
            logger.warning(f"Negalima atnaujinti būsenos: užduotis su ID {task_id} nerasta")
            return None
        
        # Atnaujiname būseną
        task.status = status
        
        # Pridedame rezultatus, jei jie yra
        if result:
            task.result = result
        
        # Pridedame žurnalo žinutę, jei ji yra
        if log_message:
            timestamp = datetime.now().isoformat()
            log_entry = {"timestamp": timestamp, "message": log_message}
            task.logs.append(log_entry)
        
        # Atnaujiname updated_at laiką
        task.updated_at = datetime.now()
        
        # Išsaugome pakeitimus
        self._save_tasks()
        
        logger.info(f"Atnaujinta užduoties {task.name} (ID: {task.id}) būsena į {status.value}")
        return task