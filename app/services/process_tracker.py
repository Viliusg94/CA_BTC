# Ilgai trunkančių procesų sekimo servisas
import uuid
import logging
import threading
from datetime import datetime

from app.services.notification_service import notification_service, NotificationType
from app.services.websocket_manager import websocket_manager

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class ProcessStatus:
    """Proceso būsenos konstantes"""
    PENDING = "pending"      # Laukiantis vykdymo
    RUNNING = "running"      # Vykdomas
    COMPLETED = "completed"  # Sėkmingai įvykdytas
    FAILED = "failed"        # Nepavyko įvykdyti
    CANCELED = "canceled"    # Atšauktas

class ProcessTracker:
    """Klasė, atsakinga už ilgai trunkančių procesų sekimą"""
    
    def __init__(self):
        """Inicializuojame procesų sekimo servisą"""
        # Procesų informacijos saugojimas: process_id -> process_info
        self.processes = {}
        
        # Mutex thread-safe prieigai prie processes žodyno
        self.lock = threading.Lock()
        
        logger.info("ProcessTracker inicializuotas")
    
    def start_process(self, name, description=None, total_steps=None, data=None):
        """
        Pradedame sekti naują procesą
        
        Args:
            name (str): Proceso pavadinimas
            description (str): Proceso aprašymas
            total_steps (int): Bendras žingsnių skaičius (jei žinomas)
            data (dict): Papildomi duomenys apie procesą
            
        Returns:
            str: Proceso ID
        """
        # Generuojame unikalų proceso ID
        process_id = str(uuid.uuid4())
        
        # Sukuriame proceso informacijos objektą
        process_info = {
            'id': process_id,
            'name': name,
            'description': description or "",
            'status': ProcessStatus.PENDING,
            'progress': 0,  # 0-100 procentai
            'current_step': 0,
            'total_steps': total_steps,
            'start_time': datetime.now().isoformat(),
            'update_time': datetime.now().isoformat(),
            'end_time': None,
            'data': data or {},
            'logs': []
        }
        
        # Saugome proceso informaciją thread-safe būdu
        with self.lock:
            self.processes[process_id] = process_info
        
        # Siunčiame pranešimą apie naują procesą
        self._broadcast_process_update(process_id)
        
        # Sukuriame informacinį pranešimą
        notification_service.create_notification(
            title=f"Pradėtas procesas: {name}",
            message=f"Pradėtas naujas procesas: {description or name}",
            notification_type=NotificationType.INFO,
            data={'process_id': process_id},
            target_url=f"/processes/{process_id}",
            broadcast=True
        )
        
        logger.info(f"Pradėtas sekti naujas procesas: {name} (ID: {process_id})")
        return process_id
    
    def update_process(self, process_id, status=None, progress=None, current_step=None, 
                      message=None, increment_step=False):
        """
        Atnaujiname proceso informaciją
        
        Args:
            process_id (str): Proceso ID
            status (str): Nauja proceso būsena
            progress (int): Progreso procentas (0-100)
            current_step (int): Dabartinis žingsnis
            message (str): Žinutė apie proceso būseną
            increment_step (bool): Ar padidinti dabartinį žingsnį vienetu
            
        Returns:
            bool: True, jei sėkmingai atnaujinta, kitaip False
        """
        # Patikriname, ar procesas egzistuoja
        with self.lock:
            if process_id not in self.processes:
                logger.warning(f"Negalima atnaujinti: procesas su ID {process_id} nerastas")
                return False
            
            # Gauname proceso informaciją
            process_info = self.processes[process_id]
            
            # Atnaujiname proceso būseną (jei pateikta)
            if status:
                process_info['status'] = status
                
                # Jei procesas baigiasi, nustatome pabaigos laiką
                if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.CANCELED]:
                    process_info['end_time'] = datetime.now().isoformat()
            
            # Atnaujiname progresą (jei pateiktas)
            if progress is not None:
                process_info['progress'] = max(0, min(100, progress))  # Užtikriname, kad būtų 0-100 ribose
            
            # Atnaujiname dabartinį žingsnį
            if current_step is not None:
                process_info['current_step'] = current_step
            elif increment_step and process_info['total_steps']:
                # Jei nurodyta padidinti žingsnį ir yra žinomas bendras žingsnių skaičius
                process_info['current_step'] = min(
                    process_info['current_step'] + 1, 
                    process_info['total_steps']
                )
                
                # Automatiškai atnaujiname progresą pagal žingsnius
                if process_info['total_steps'] > 0:
                    process_info['progress'] = int(
                        (process_info['current_step'] / process_info['total_steps']) * 100
                    )
            
            # Atnaujiname atnaujinimo laiką
            process_info['update_time'] = datetime.now().isoformat()
            
            # Pridedame žinutę į procesų žurnalą (jei pateikta)
            if message:
                log_entry = {
                    'time': datetime.now().isoformat(),
                    'message': message
                }
                process_info['logs'].append(log_entry)
        
        # Siunčiame atnaujinimą per WebSocket
        self._broadcast_process_update(process_id)
        
        # Jei procesas baigėsi, sukuriame atitinkamą pranešimą
        if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED]:
            notification_type = NotificationType.SUCCESS if status == ProcessStatus.COMPLETED else NotificationType.ERROR
            notification_service.create_notification(
                title=f"Procesas {process_info['name']} {status}",
                message=message or f"Procesas {process_info['name']} baigtas su būsena: {status}",
                notification_type=notification_type,
                data={'process_id': process_id},
                target_url=f"/processes/{process_id}",
                broadcast=True
            )
        
        logger.info(f"Atnaujintas procesas: {process_info['name']} (ID: {process_id})")
        return True
    
    def complete_process(self, process_id, message=None):
        """
        Pažymime procesą kaip sėkmingai įvykdytą
        
        Args:
            process_id (str): Proceso ID
            message (str): Baigimo žinutė
            
        Returns:
            bool: True, jei sėkmingai atnaujinta, kitaip False
        """
        return self.update_process(
            process_id, 
            status=ProcessStatus.COMPLETED, 
            progress=100,
            message=message or "Procesas sėkmingai baigtas"
        )
    
    def fail_process(self, process_id, message=None):
        """
        Pažymime procesą kaip nepavykusį
        
        Args:
            process_id (str): Proceso ID
            message (str): Klaidos žinutė
            
        Returns:
            bool: True, jei sėkmingai atnaujinta, kitaip False
        """
        return self.update_process(
            process_id, 
            status=ProcessStatus.FAILED, 
            message=message or "Proceso vykdymas nepavyko"
        )
    
    def cancel_process(self, process_id, message=None):
        """
        Atšaukiame procesą
        
        Args:
            process_id (str): Proceso ID
            message (str): Atšaukimo priežastis
            
        Returns:
            bool: True, jei sėkmingai atnaujinta, kitaip False
        """
        return self.update_process(
            process_id, 
            status=ProcessStatus.CANCELED, 
            message=message or "Procesas atšauktas vartotojo"
        )
    
    def get_process(self, process_id):
        """
        Gauname proceso informaciją
        
        Args:
            process_id (str): Proceso ID
            
        Returns:
            dict: Proceso informacija arba None, jei nerasta
        """
        with self.lock:
            return self.processes.get(process_id)
    
    def get_all_processes(self):
        """
        Gauname visų procesų informaciją
        
        Returns:
            list: Procesų informacijos sąrašas
        """
        with self.lock:
            return list(self.processes.values())
    
    def get_active_processes(self):
        """
        Gauname aktyvių (vykdomų ir laukiančių) procesų informaciją
        
        Returns:
            list: Aktyvių procesų informacijos sąrašas
        """
        with self.lock:
            return [p for p in self.processes.values() 
                    if p['status'] in [ProcessStatus.PENDING, ProcessStatus.RUNNING]]
    
    def delete_process(self, process_id):
        """
        Ištriname proceso informaciją
        
        Args:
            process_id (str): Proceso ID
            
        Returns:
            bool: True, jei sėkmingai ištrinta, kitaip False
        """
        with self.lock:
            if process_id not in self.processes:
                logger.warning(f"Negalima ištrinti: procesas su ID {process_id} nerastas")
                return False
            
            # Gauname proceso informaciją prieš ištrinant
            process_info = self.processes[process_id]
            
            # Pašaliname procesą
            del self.processes[process_id]
        
        logger.info(f"Ištrintas procesas: {process_info['name']} (ID: {process_id})")
        return True
    
    def _broadcast_process_update(self, process_id):
        """
        Siunčiame proceso atnaujinimą per WebSocket
        
        Args:
            process_id (str): Proceso ID
        """
        try:
            # Gauname proceso informaciją
            process_info = self.get_process(process_id)
            if not process_info:
                return
            
            # Siunčiame atnaujinimą per WebSocket
            message = {
                'type': 'process_update',
                'data': process_info
            }
            websocket_manager.broadcast(message)
            
            logger.debug(f"Proceso atnaujinimas išsiųstas per WebSocket: {process_id}")
        except Exception as e:
            logger.error(f"Klaida siunčiant proceso atnaujinimą per WebSocket: {e}")


# Sukuriame globalų procesų sekimo serviso objektą
process_tracker = ProcessTracker()