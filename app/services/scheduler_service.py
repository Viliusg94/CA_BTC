import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
import traceback

# Sukuriame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pagrindinė SchedulerService klasė turėtų turėti šiuos metodus:
class SchedulerService:
    def __init__(self):
        """
        Scheduler servisas, kuris tvarko užduočių planavimą ir vykdymą fone
        """
        # Direktorija, kurioje saugomos užduotys
        self.tasks_dir = os.path.join('data', 'tasks')
        os.makedirs(self.tasks_dir, exist_ok=True)
        
        # Užduočių vykdymo istorijos direktorija
        self.history_dir = os.path.join('data', 'task_history')
        os.makedirs(self.history_dir, exist_ok=True)
        
        # Aktyviai vykdomos užduotys (task_id -> thread)
        self._active_tasks = {}
        
        # Užduočių vykdymo foninė gija
        self._scheduler_thread = None
        self._stop_scheduler = False
        
        # Paleisti background workerį
        self.start_scheduler()
    
    def start_scheduler(self):
        """
        Paleidžia foninį užduočių vykdytoją
        """
        if self._scheduler_thread is None:
            logger.info("Paleidžiamas užduočių planuoklis")
            self._stop_scheduler = False
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop)
            self._scheduler_thread.daemon = True  # Leidžia programai išsijungti net jei gija veikia
            self._scheduler_thread.start()
    
    def stop_scheduler(self):
        """
        Sustabdo foninį užduočių vykdytoją
        """
        if self._scheduler_thread is not None:
            logger.info("Stabdomas užduočių planuoklis")
            self._stop_scheduler = True
            self._scheduler_thread.join(timeout=10)  # Laukiame 10 sekundžių
            self._scheduler_thread = None
    
    def _scheduler_loop(self):
        """
        Pagrindinis planuoklio ciklas, kuris tikrina užduotis ir jas paleidžia
        """
        logger.info("Užduočių planuoklio ciklas pradėtas")
        
        while not self._stop_scheduler:
            try:
                # Gauname visas užduotis
                tasks = self.get_all_tasks()
                
                current_time = datetime.now()
                
                # Einame per visas užduotis ir tikriname, ar reikia jas vykdyti
                for task in tasks:
                    task_id = task.get('id')
                    
                    # Jei užduotis jau vykdoma, praleidžiame
                    if task_id in self._active_tasks:
                        continue
                    
                    # Tikriname, ar užduoties būsena leidžia ją vykdyti
                    if task.get('status') != 'pending':
                        continue
                    
                    # Tikriname, ar atėjo laikas vykdyti užduotį
                    next_run_time_str = task.get('next_run_time')
                    if not next_run_time_str:
                        continue
                    
                    # Konvertuojame į datetime objektą
                    try:
                        next_run_time = datetime.strptime(next_run_time_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        logger.error(f"Blogas datos formatas: {next_run_time_str}")
                        continue
                    
                    # Jei laikas atėjo arba jau praėjo, vykdome užduotį
                    if current_time >= next_run_time:
                        # Paleidžiame užduotį naujoje gijoje
                        self._run_task(task)
                
                # Miegame 10 sekundžių prieš kito ciklo iteraciją
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Klaida planuoklio cikle: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(30)  # Ilgesnė pauzė po klaidos
    
    def _run_task(self, task):
        """
        Paleidžia užduotį fone
        """
        task_id = task.get('id')
        logger.info(f"Paleidžiama užduotis: {task_id}")
        
        # Atnaujiname užduoties būseną
        task['status'] = 'running'
        task['start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        task['progress'] = 0
        self._save_task(task)
        
        # Sukuriame naują giją užduočiai vykdyti
        task_thread = threading.Thread(target=self._task_thread, args=(task,))
        task_thread.daemon = True
        
        # Įrašome į aktyvias užduotis
        self._active_tasks[task_id] = task_thread
        
        # Paleidžiame giją
        task_thread.start()
    
    def _task_thread(self, task):
        """
        Funkcija, kuri vykdoma atskiroje gijoje kiekvienai užduočiai
        """
        task_id = task.get('id')
        success = False
        error_message = None
        start_time = datetime.now()
        
        try:
            logger.info(f"Užduotis {task_id} pradėta vykdyti")
            
            # Pranešame apie užduoties pradžią
            self.notify_task_update(task)
            
            # Čia vykdome užduotį pagal jos tipą
            # Tai yra tik pavyzdys - tikroje sistemoje turėtumėte integruoti su modelio treniravimo kodu
            
            # Imituojame treniravimo procesą
            total_steps = 10
            for step in range(1, total_steps + 1):
                # Tikriname, ar nebuvo nurodyta sustabdyti
                if self._stop_scheduler:
                    raise Exception("Užduotis nutraukta")
                
                # Atnaujiname progresą
                progress = int(step * 100 / total_steps)
                task['progress'] = progress
                self._save_task(task)
                
                # Pranešame apie progreso pasikeitimą
                self.notify_task_update(task)
                
                # Pranešame apie progresą
                logger.info(f"Užduotis {task_id} progresas: {progress}%")
                
                # Imituojame darbą
                time.sleep(2)
            
            # Užduotis sėkmingai įvykdyta
            success = True
            logger.info(f"Užduotis {task_id} sėkmingai įvykdyta")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Klaida vykdant užduotį {task_id}: {error_message}")
            logger.error(traceback.format_exc())
        
        finally:
            # Užduotis baigta, tvarkome būsenas
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Atnaujiname užduoties būseną
            task['status'] = 'completed' if success else 'failed'
            task['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
            task['duration'] = round(duration, 2)
            
            # Pridedame paskutinio vykdymo rezultatus
            task['last_run'] = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': success,
                'duration': round(duration, 2)
            }
            
            if error_message:
                task['last_run']['error'] = error_message
            
            # Nustatome kitą vykdymo laiką, jei užduotis periodinė
            if task.get('frequency') != 'once' and success:
                task['next_run_time'] = self._schedule_next_run(task)
            else:
                task.pop('next_run_time', None)  # Pašaliname, jei vienkartinė arba nepavyko
            
            # Išsaugome užduotį
            self._save_task(task)
            
            # Pranešame apie užduoties pabaigą
            self.notify_task_update(task)
            
            # Pašaliname iš aktyvių užduočių
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
            
            logger.info(f"Užduotis {task_id} baigta")
    
    def _schedule_next_run(self, task):
        """
        Nustato kitą užduoties vykdymo laiką pagal dažnumą
        """
        frequency = task.get('frequency')
        now = datetime.now()
        
        if frequency == 'daily':
            next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            # Paprastas būdas, nors netikslus ilgesniam laikui
            next_run = now + timedelta(days=30)
        else:
            # Numatytasis - rytoj tuo pačiu laiku
            next_run = now + timedelta(days=1)
        
        return next_run.strftime('%Y-%m-%d %H:%M:%S')
    
    def _save_task(self, task):
        """
        Išsaugo užduotį į failą
        """
        task_id = task.get('id')
        if not task_id:
            logger.error("Neįmanoma išsaugoti užduoties be ID")
            return False
        
        task_path = os.path.join(self.tasks_dir, f"{task_id}.json")
        
        try:
            with open(task_path, 'w') as f:
                json.dump(task, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Klaida išsaugant užduotį {task_id}: {str(e)}")
            return False
    
    def get_all_tasks(self):
        """
        Grąžina visas užduotis iš failų sistemos
        """
        tasks = []
        
        try:
            for filename in os.listdir(self.tasks_dir):
                if filename.endswith('.json'):
                    task_path = os.path.join(self.tasks_dir, filename)
                    
                    try:
                        with open(task_path, 'r') as f:
                            task = json.load(f)
                            
                            # Įsitikinkim, kad užduotis turi ID
                            if 'id' not in task:
                                task['id'] = filename.replace('.json', '')
                            
                            tasks.append(task)
                    except Exception as e:
                        logger.error(f"Klaida skaitant užduotį {filename}: {str(e)}")
        except Exception as e:
            logger.error(f"Klaida gaunant užduočių sąrašą: {str(e)}")
        
        return tasks
    
    def get_tasks(self, page=1, per_page=10, status=None, frequency=None, priority=None):
        """
        Gauna užduočių sąrašą su filtravimu ir puslapiavimu
        """
        all_tasks = self.get_all_tasks()
        
        # Filtruojame pagal būseną
        if status:
            all_tasks = [task for task in all_tasks if task.get('status') == status]
        
        # Filtruojame pagal dažnumą
        if frequency:
            all_tasks = [task for task in all_tasks if task.get('frequency') == frequency]
        
        # Filtruojame pagal prioritetą
        if priority:
            if priority in ['high', 'medium', 'low']:
                # Konvertuojame tekstinį prioritetą į skaitinį
                if priority == 'high':
                    priority_val = 1
                elif priority == 'medium':
                    priority_val = 5
                else:  # low
                    priority_val = 10
                all_tasks = [task for task in all_tasks if task.get('priority') == priority_val]
            else:
                try:
                    priority_val = int(priority)
                    all_tasks = [task for task in all_tasks if task.get('priority') == priority_val]
                except (ValueError, TypeError):
                    pass
        
        # Rikiuojame pagal kitą vykdymo laiką (jei yra) ir sukūrimo laiką
        all_tasks.sort(key=lambda x: (
            x.get('next_run_time', '9999-12-31 23:59:59'),
            x.get('created_at', '9999-12-31 23:59:59')
        ))
        
        # Skaičiuojame viso užduočių kiekį
        total_count = len(all_tasks)
        
        # Išrenkame tik reikiamą puslapį
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_count)
        
        return all_tasks[start_idx:end_idx], total_count
    
    def get_task_by_id(self, task_id):
        """
        Gauna užduotį pagal ID
        """
        task_path = os.path.join(self.tasks_dir, f"{task_id}.json")
        
        if os.path.exists(task_path):
            try:
                with open(task_path, 'r') as f:
                    task = json.load(f)
                    
                    # Įsitikinkim, kad užduotis turi ID
                    if 'id' not in task:
                        task['id'] = task_id
                        
                    return task
            except Exception as e:
                logger.error(f"Klaida skaitant užduotį {task_id}: {str(e)}")
        
        return None
    
    def run_task(self, task_id):
        """
        Paleidžia užduotį vykdyti tuoj pat
        """
        # Gauname užduotį
        task = self.get_task_by_id(task_id)
        
        if not task:
            logger.error(f"Nerasta užduotis {task_id}")
            return False
        
        # Tikriname, ar užduotis jau vykdoma
        if task_id in self._active_tasks:
            logger.warning(f"Užduotis {task_id} jau vykdoma")
            return False
        
        # Atnaujiname užduoties laiką ir būseną
        task['status'] = 'pending'
        task['next_run_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Išsaugome užduotį
        self._save_task(task)
        
        logger.info(f"Užduotis {task_id} paruošta vykdymui")
        return True
    
    def delete_task(self, task_id):
        """
        Ištrina užduotį
        """
        task_path = os.path.join(self.tasks_dir, f"{task_id}.json")
        
        # Tikriname, ar užduotis egzistuoja
        if not os.path.exists(task_path):
            logger.warning(f"Nerasta užduotis {task_id}")
            return False
        
        # Tikriname, ar užduotis nėra vykdoma
        if task_id in self._active_tasks:
            logger.warning(f"Negalima ištrinti užduoties {task_id}, nes ji vykdoma")
            return False
        
        # Ištriname užduotį
        try:
            os.remove(task_path)
            logger.info(f"Užduotis {task_id} ištrinta")
            return True
        except Exception as e:
            logger.error(f"Klaida trinant užduotį {task_id}: {str(e)}")
            return False
    
    def notify_task_update(self, task):
        """
        Funkcija, kuri praneša apie užduoties pasikeitimą
        """
        try:
            from app import websocket_manager
            
            # Siunčiame pranešimą apie užduoties pasikeitimą
            task_id = task.get('id')
            status = task.get('status')
            progress = task.get('progress', 0)
            
            # Suformuojame pranešimą
            message = {
                'type': 'task_update',
                'task_id': task_id,
                'status': status,
                'progress': progress
            }
            
            # Siunčiame visiems klientams
            websocket_manager.broadcast(message)
        except Exception as e:
            logger.error(f"Klaida siunčiant pranešimą apie užduoties pasikeitimą: {str(e)}")

# Sukuriame globalų servisą, kurį galima naudoti visame projekte
scheduler_service = SchedulerService()