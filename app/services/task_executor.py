"""
Užduočių vykdymo mechanizmas - atsakingas už automatinį užduočių vykdymą pagal tvarkaraštį
"""
import threading
import time
import logging
from datetime import datetime
import traceback

from app.services.task_service import TaskService
from app.models.task import TaskStatus

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class TaskExecutor:
    """Klasė, atsakinga už užduočių vykdymą pagal tvarkaraštį"""
    
    def __init__(self):
        """Inicializuojame užduočių vykdytoją"""
        # Sukuriame užduočių serviso objektą
        self.task_service = TaskService()
        
        # Žymė, ar vykdytojas paleistas
        self.running = False
        
        # Gija, kurioje veiks vykdytojas
        self.thread = None
        
        # Tikrinimo intervalas sekundėmis (kiek dažnai tikrinti užduotis)
        self.check_interval = 60
        
        logger.info("TaskExecutor inicializuotas")
    
    def start(self):
        """Paleidžiame užduočių vykdytoją"""
        # Jei jau paleistas, nereikia paleisti dar kartą
        if self.running:
            logger.warning("Užduočių vykdytojas jau paleistas")
            return False
        
        # Žymime, kad vykdytojas paleistas
        self.running = True
        
        # Kuriame naują giją, kurioje bus vykdomas pagrindinis ciklas
        self.thread = threading.Thread(target=self._run_loop)
        
        # Nustatome, kad gija būtų daemon (t.y., programa gali išeiti, net jei gija vis dar veikia)
        self.thread.daemon = True
        
        # Paleidžiame giją
        self.thread.start()
        
        logger.info("Užduočių vykdytojas paleistas")
        return True
    
    def stop(self):
        """Sustabdome užduočių vykdytoją"""
        # Jei nepaleistas, nereikia stabdyti
        if not self.running:
            logger.warning("Užduočių vykdytojas jau sustabdytas")
            return False
        
        # Žymime, kad vykdytojas sustabdytas
        self.running = False
        
        # Laukiame, kol gija baigsis (ne ilgiau kaip 5s)
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Užduočių vykdytojas sustabdytas")
        return True
    
    def _run_loop(self):
        """Pagrindinis užduočių vykdymo ciklas (veikia atskiroje gijoje)"""
        logger.info("Pradedamas užduočių vykdymo ciklas")
        
        while self.running:
            try:
                # Gauname laiką šiuo momentu
                now = datetime.now()
                
                # Loginame tikrinimo laiką
                logger.debug(f"Tikrinamos užduotys: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Gauname laukiančias vykdymo užduotis
                pending_tasks = self.task_service.get_pending_tasks()
                
                # Tikriname, ar atėjo laikas vykdyti kurią nors užduotį
                for task in pending_tasks:
                    # Jei užduoties vykdymo laikas atėjo arba jau praėjo
                    if task.scheduled_time and task.scheduled_time <= now:
                        logger.info(f"Rasta užduotis vykdymui: {task.name} (ID: {task.id})")
                        
                        # Paleiskime užduotį atskiroje gijoje
                        execution_thread = threading.Thread(
                            target=self._execute_task,
                            args=(task.id,)
                        )
                        execution_thread.daemon = True
                        execution_thread.start()
            
            except Exception as e:
                # Jei įvyko klaida cikle, loginame ją ir tęsiame darbą
                logger.error(f"Klaida užduočių vykdymo cikle: {str(e)}")
                traceback.print_exc()
            
            # Laukiame iki kito tikrinimo
            time.sleep(self.check_interval)
    
    def _execute_task(self, task_id):
        """Vykdo konkrečią užduotį"""
        try:
            # Gauname užduoties informaciją
            task = self.task_service.get_task_by_id(task_id)
            if not task:
                logger.error(f"Negalima vykdyti: užduotis su ID {task_id} nerasta")
                return
            
            # Užregistruojame, kad užduotis pradėta vykdyti
            self.task_service.update_task_status(
                task_id,
                TaskStatus.RUNNING,
                log_message=f"Pradėta vykdyti užduotį"
            )
            
            logger.info(f"Pradedama vykdyti užduotis: {task.name} (ID: {task.id})")
            
            # ŽINGSNIS 1: Paruošiame treniravimo parametrus
            model_id = task.model_id
            training_params = task.training_params
            
            logger.info(f"Treniravimo parametrai: modelis {model_id}, parametrai: {training_params}")
            
            # ŽINGSNIS 2: Čia būtų modelio treniravimo logika
            # Čia yra vieta, kur reikėtų integruoti su jūsų projekto treniravimo funkcijomis
            # Pavyzdžiui: result = train_model(model_id, **training_params)
            
            # Kol kas simuliuojame treniravimą, laukdami 5 sekundes
            logger.info(f"Vykdomas modelio {model_id} treniravimas...")
            time.sleep(5)
            
            # Simuliuojame sėkmingą rezultatą
            result = {
                "success": True,
                "accuracy": 0.95,
                "loss": 0.05,
                "epochs_completed": training_params.get("epochs", 10),
                "training_time": "00:05:00"
            }
            
            # ŽINGSNIS 3: Užregistruojame sėkmingą užduoties įvykdymą
            self.task_service.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result=result,
                log_message=f"Užduotis sėkmingai įvykdyta"
            )
            
            logger.info(f"Užduotis {task.name} (ID: {task.id}) sėkmingai įvykdyta")
            
        except Exception as e:
            # Jei įvyko klaida vykdant užduotį, užregistruojame klaidą
            error_message = f"Klaida vykdant užduotį: {str(e)}"
            logger.error(error_message)
            traceback.print_exc()
            
            # Atnaujiname užduoties būseną į "nepavyko"
            self.task_service.update_task_status(
                task_id,
                TaskStatus.FAILED,
                result={"error": str(e)},
                log_message=error_message
            )
    
    def execute_task_now(self, task_id):
        """Vykdo užduotį iš karto, nepriklausomai nuo suplanuoto laiko"""
        # Šis metodas leidžia vartotojui paleisti užduotį rankiniu būdu
        threading.Thread(target=self._execute_task, args=(task_id,)).start()
        return True


# Sukuriame globalų užduočių vykdytoją, kuris bus naudojamas visoje aplikacijoje
task_executor = TaskExecutor()