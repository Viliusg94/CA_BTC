"""
Užduočių vykdymo mechanizmas - atsakingas už automatinį užduočių vykdymą
"""
import threading
import time
import logging
from datetime import datetime
import traceback

from app.services.task_service import TaskService
from app.models.task import TaskStatus
from app.services.model_service import train_model  # Importuojame treniravimo funkciją

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class TaskExecutor:
    """Klasė, atsakinga už užduočių vykdymą pagal tvarkaraštį"""
    
    def __init__(self):
        """Inicializuojame TaskExecutor"""
        self.task_service = TaskService()
        self.running = False
        self.thread = None
        self.check_interval = 60  # Tikrinimo intervalas sekundėmis
    
    def start(self):
        """Paleidžiame užduočių vykdytoją"""
        if self.running:
            logger.warning("Užduočių vykdytojas jau paleistas")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True  # Leidžia programai išeiti, net jei gija vis dar veikia
        self.thread.start()
        
        logger.info("Užduočių vykdytojas paleistas")
        return True
    
    def stop(self):
        """Sustabdome užduočių vykdytoją"""
        if not self.running:
            logger.warning("Užduočių vykdytojas jau sustabdytas")
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)  # Laukiame, kol gija baigsis (ne ilgiau kaip 5s)
        
        logger.info("Užduočių vykdytojas sustabdytas")
        return True
    
    def _run_loop(self):
        """Pagrindinė užduočių vykdymo ciklo funkcija"""
        while self.running:
            try:
                # Gauname laukiančias vykdymo užduotis
                pending_tasks = self.task_service.get_pending_tasks()
                
                # Tikriname, ar atėjo laikas vykdyti užduotis
                now = datetime.now()
                for task in pending_tasks:
                    # Jei užduoties vykdymo laikas atėjo arba jau praėjo
                    if task.scheduled_time and task.scheduled_time <= now:
                        # Paleiskime užduotį atskiroje gijoje
                        logger.info(f"Pradedama vykdyti užduotis: {task.name} (ID: {task.id})")
                        execution_thread = threading.Thread(
                            target=self._execute_task,
                            args=(task.id,)
                        )
                        execution_thread.daemon = True
                        execution_thread.start()
            
            except Exception as e:
                logger.error(f"Klaida užduočių vykdymo cikle: {e}")
                traceback.print_exc()
            
            # Laukiame iki kito tikrinimo
            time.sleep(self.check_interval)
    
    def _execute_task(self, task_id):
        """Vykdo konkrečią užduotį"""
        # Gauname užduoties informaciją
        task = self.task_service.get_task_by_id(task_id)
        if not task:
            logger.error(f"Užduotis nerasta: {task_id}")
            return
        
        try:
            # Atnaujiname užduoties būseną į "vykdoma"
            self.task_service.update_task_status(
                task_id, 
                TaskStatus.RUNNING,
                log_message=f"Pradėta vykdyti užduotį {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Gauname modelio informaciją ir treniravimo parametrus
            model_id = task.model_id
            training_params = task.training_params
            
            # Vykdome modelio treniravimą
            logger.info(f"Vykdomas modelio {model_id} treniravimas su parametrais: {training_params}")
            
            # Simuliuojame treniravimą (čia reikėtų iškviesti tikrą training funkciją)
            # Pavyzdys: 
            # results = train_model(model_id, **training_params)
            
            # Laikinas sprendimas - simuliuojame treniravimą
            time.sleep(5)  # Treniravimas užtrunka 5s
            results = {"success": True, "message": "Modelis sėkmingai apmokytas", "metrics": {"accuracy": 0.95, "loss": 0.05}}
            
            # Atnaujiname užduoties būseną į "įvykdyta" su rezultatais
            self.task_service.update_task_status(
                task_id, 
                TaskStatus.COMPLETED,
                result=results,
                log_message=f"Užduotis sėkmingai įvykdyta {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            logger.info(f"Užduotis {task_id} sėkmingai įvykdyta")
            
        except Exception as e:
            logger.error(f"Klaida vykdant užduotį {task_id}: {e}")
            traceback.print_exc()
            
            # Atnaujiname užduoties būseną į "nepavyko" su klaidos pranešimu
            self.task_service.update_task_status(
                task_id, 
                TaskStatus.FAILED,
                result={"error": str(e)},
                log_message=f"Klaida vykdant užduotį: {str(e)}"
            )

# Sukuriame globalų užduočių vykdytoją
task_executor = TaskExecutor()