import logging
from datetime import datetime
from app.services.websocket_manager import websocket_manager

# Sukuriame logerį
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        """
        Inicializuojame NotificationService
        """
        # Pranešimų tipai
        self.NOTIFICATION_TYPES = {
            'info': 'informacija',
            'warning': 'įspėjimas',
            'error': 'klaida',
            'success': 'sėkmė'
        }
    
    def send_notification(self, type, title, message, data=None):
        """
        Siunčia pranešimą per WebSocket
        
        Args:
            type (str): Pranešimo tipas (info, warning, error, success)
            title (str): Pranešimo antraštė
            message (str): Pranešimo tekstas
            data (dict, optional): Papildomi duomenys
            
        Returns:
            bool: Ar pavyko išsiųsti pranešimą
        """
        try:
            # Tikriname ar tipas teisingas
            if type not in self.NOTIFICATION_TYPES:
                logger.warning(f"Nežinomas pranešimo tipas: {type}")
                type = 'info'
            
            # Formuojame pranešimo duomenis
            notification = {
                'type': type,
                'title': title,
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Pridedame papildomus duomenis
            if data:
                notification['data'] = data
            
            # Siunčiame pranešimą
            websocket_manager.broadcast('notification', notification)
            
            logger.debug(f"Išsiųstas pranešimas: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Klaida siunčiant pranešimą: {str(e)}")
            return False
    
    def task_started(self, task):
        """
        Siunčia pranešimą apie užduoties pradžią
        
        Args:
            task (dict): Užduoties duomenys
            
        Returns:
            bool: Ar pavyko išsiųsti pranešimą
        """
        title = "Užduotis pradėta"
        message = f"Užduotis '{task.get('name')}' pradėta vykdyti."
        
        return self.send_notification('info', title, message, {
            'task_id': task.get('id'),
            'task_name': task.get('name')
        })
    
    def task_completed(self, task, duration):
        """
        Siunčia pranešimą apie sėkmingą užduoties pabaigą
        
        Args:
            task (dict): Užduoties duomenys
            duration (float): Vykdymo trukmė sekundėmis
            
        Returns:
            bool: Ar pavyko išsiųsti pranešimą
        """
        title = "Užduotis baigta"
        message = f"Užduotis '{task.get('name')}' sėkmingai baigta per {round(duration, 2)} s."
        
        return self.send_notification('success', title, message, {
            'task_id': task.get('id'),
            'task_name': task.get('name'),
            'duration': round(duration, 2)
        })
    
    def task_failed(self, task, error, duration):
        """
        Siunčia pranešimą apie nesėkmingą užduoties pabaigą
        
        Args:
            task (dict): Užduoties duomenys
            error (str): Klaidos pranešimas
            duration (float): Vykdymo trukmė sekundėmis
            
        Returns:
            bool: Ar pavyko išsiųsti pranešimą
        """
        title = "Užduotis nepavyko"
        message = f"Užduotis '{task.get('name')}' nepavyko: {error}"
        
        return self.send_notification('error', title, message, {
            'task_id': task.get('id'),
            'task_name': task.get('name'),
            'error': error,
            'duration': round(duration, 2)
        })

# Sukuriame globalų NotificationService objektą
notification_service = NotificationService()