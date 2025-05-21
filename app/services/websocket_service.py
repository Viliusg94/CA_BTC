import logging
import json
from flask_socketio import SocketIO

class WebSocketManager:
    """
    Klasė, skirta valdyti WebSocket komunikaciją tarp serverio ir kliento
    """
    
    def __init__(self, socketio=None):
        """
        Inicializuoja WebSocket managerį
        
        Args:
            socketio (SocketIO, optional): Flask-SocketIO objektas
        """
        self.socketio = socketio
    
    def setup_socketio(self, socketio):
        """
        Nustato SocketIO objektą
        
        Args:
            socketio (SocketIO): Flask-SocketIO objektas
        """
        self.socketio = socketio
    
    def broadcast_message(self, data, event='message', namespace='/training'):
        """
        Siunčia pranešimą visiems prisijungusiems klientams
        
        Args:
            data (dict): Duomenų žodynas
            event (str, optional): Įvykio pavadinimas. Numatytoji reikšmė: 'message'
            namespace (str, optional): Vardų erdvė. Numatytoji reikšmė: '/training'
            
        Returns:
            bool: True, jei pranešimas išsiųstas sėkmingai, False kitu atveju
        """
        try:
            if self.socketio:
                self.socketio.emit(event, data, namespace=namespace)
                return True
            else:
                logging.warning("SocketIO objektas nenustatytas")
                return False
        except Exception as e:
            logging.error(f"Klaida siunčiant pranešimą per WebSocket: {str(e)}")
            return False
    
    def broadcast_training_update(self, training_id, epoch, metrics, progress, status='training', namespace='/training'):
        """
        Siunčia treniravimo atnaujinimą visiems prisijungusiems klientams
        
        Args:
            training_id (str): Treniravimo sesijos ID
            epoch (int): Dabartinė epocha
            metrics (dict): Metrikos (loss, accuracy, val_loss, val_accuracy)
            progress (float): Progreso procentas (0-100)
            status (str, optional): Treniravimo būsena. Numatytoji reikšmė: 'training'
            namespace (str, optional): Vardų erdvė. Numatytoji reikšmė: '/training'
            
        Returns:
            bool: True, jei pranešimas išsiųstas sėkmingai, False kitu atveju
        """
        data = {
            'training_id': training_id,
            'epoch': epoch,
            'metrics': metrics,
            'progress': progress,
            'status': status
        }
        
        return self.broadcast_message(data, event='training_update', namespace=namespace)
    
    def broadcast_training_complete(self, training_id, final_metrics, namespace='/training'):
        """
        Siunčia pranešimą apie baigtą treniravimą visiems prisijungusiems klientams
        
        Args:
            training_id (str): Treniravimo sesijos ID
            final_metrics (dict): Galutinės metrikos
            namespace (str, optional): Vardų erdvė. Numatytoji reikšmė: '/training'
            
        Returns:
            bool: True, jei pranešimas išsiųstas sėkmingai, False kitu atveju
        """
        data = {
            'training_id': training_id,
            'metrics': final_metrics,
            'progress': 100,
            'status': 'complete'
        }
        
        return self.broadcast_message(data, event='training_complete', namespace=namespace)
    
    def broadcast_training_error(self, training_id, error_message, namespace='/training'):
        """
        Siunčia pranešimą apie treniravimo klaidą visiems prisijungusiems klientams
        
        Args:
            training_id (str): Treniravimo sesijos ID
            error_message (str): Klaidos pranešimas
            namespace (str, optional): Vardų erdvė. Numatytoji reikšmė: '/training'
            
        Returns:
            bool: True, jei pranešimas išsiųstas sėkmingai, False kitu atveju
        """
        data = {
            'training_id': training_id,
            'error': error_message,
            'status': 'error'
        }
        
        return self.broadcast_message(data, event='training_error', namespace=namespace)
    
    def start(self):
        """
        Paleidžia WebSocket servisą (jei reikia)
        """
        logging.info("WebSocket servisas paleistas")
        # Šiame metode papildomos logikos nereikia, nes
        # SocketIO bus inicializuojamas ir paleidžiamas su Flask aplikacija
        pass

# Sukuriame globalų WebSocketManager objektą
websocket_manager = WebSocketManager()