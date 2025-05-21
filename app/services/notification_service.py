# Pranešimų valdymo servisas - atsakingas už pranešimų CRUD operacijas ir siuntimą
import os
import json
import logging
from datetime import datetime

from app.models.notification import Notification, NotificationType, NotificationStatus
from app.services.websocket_manager import websocket_manager

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class NotificationService:
    """Servisas, atsakingas už pranešimų valdymą"""
    
    def __init__(self, data_dir=None):
        """
        Inicializuojame NotificationService
        
        Args:
            data_dir (str): Direktorija, kurioje saugomi pranešimų duomenys
        """
        # Nustatome duomenų direktoriją
        self.data_dir = data_dir or os.path.join('data', 'notifications')
        
        # Sukuriame direktoriją, jei tokios nėra
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Nustatome failo kelią
        self.notifications_file = os.path.join(self.data_dir, 'notifications.json')
        
        # Užkrauname pranešimus iš failo
        self.notifications = self._load_notifications()
        
        logger.info(f"NotificationService inicializuotas. Užkrauta {len(self.notifications)} pranešimų.")
    
    def _load_notifications(self):
        """
        Užkrauname pranešimus iš failo
        
        Returns:
            list: Pranešimų sąrašas
        """
        if not os.path.exists(self.notifications_file):
            logger.info(f"Pranešimų failas nerastas: {self.notifications_file}")
            return []
        
        try:
            with open(self.notifications_file, 'r', encoding='utf-8') as f:
                notifications_data = json.load(f)
                return [Notification.from_dict(notification_data) for notification_data in notifications_data]
        except Exception as e:
            logger.error(f"Klaida užkraunant pranešimus: {e}")
            return []
    
    def _save_notifications(self):
        """
        Išsaugome pranešimus į failą
        
        Returns:
            bool: True, jei sėkmingai išsaugota, kitaip False
        """
        try:
            # Konvertuojame pranešimus į žodynus
            notifications_data = [notification.to_dict() for notification in self.notifications]
            
            # Įrašome į failą JSON formatu
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump(notifications_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Išsaugota {len(self.notifications)} pranešimų į {self.notifications_file}")
            return True
        
        except Exception as e:
            logger.error(f"Klaida išsaugant pranešimus: {e}")
            return False
    
    # CRUD operacijos
    
    def get_all_notifications(self, user_id=None):
        """
        Grąžiname visus pranešimus (arba tik konkretaus vartotojo)
        
        Args:
            user_id (str, optional): Vartotojo ID
            
        Returns:
            list: Pranešimų sąrašas
        """
        if user_id:
            return [n for n in self.notifications if n.user_id == user_id]
        return self.notifications
    
    def get_notification_by_id(self, notification_id):
        """
        Grąžiname pranešimą pagal ID
        
        Args:
            notification_id (str): Pranešimo ID
            
        Returns:
            Notification: Pranešimo objektas arba None, jei nerasta
        """
        for notification in self.notifications:
            if notification.id == notification_id:
                return notification
        
        logger.warning(f"Pranešimas su ID {notification_id} nerastas")
        return None
    
    def get_unread_count(self, user_id=None):
        """
        Grąžina neperskaitytų pranešimų skaičių
        
        Args:
            user_id (str, optional): Vartotojo ID
            
        Returns:
            int: Neperskaitytų pranešimų skaičius
        """
        return len([n for n in self.notifications if n.status == NotificationStatus.UNREAD and (not user_id or n.user_id == user_id)])
    
    def create_notification(self, title, message, type=NotificationType.INFO, target_url=None, 
                           target_id=None, progress=None, user_id=None, send_websocket=True):
        """
        Sukuriame naują pranešimą
        
        Args:
            title (str): Pranešimo pavadinimas
            message (str): Pranešimo tekstas
            type (NotificationType): Pranešimo tipas
            target_url (str, optional): URL, į kurį pranešimas nukreipia
            target_id (str, optional): Susijusio objekto ID
            progress (int, optional): Progreso procentas (0-100)
            user_id (str, optional): Vartotojo ID, kuriam skirtas pranešimas
            send_websocket (bool): Ar siųsti per WebSocket
            
        Returns:
            Notification: Sukurtas pranešimas
        """
        # Sukuriame naują pranešimą
        notification = Notification(
            title=title,
            message=message,
            type=type,
            target_url=target_url,
            target_id=target_id,
            progress=progress,
            user_id=user_id
        )
        
        # Pridedame pranešimą į sąrašą
        self.notifications.append(notification)
        
        # Išsaugome pakeitimus
        self._save_notifications()
        
        # Siunčiame pranešimą per WebSocket, jei reikia
        if send_websocket:
            self._send_notification_websocket(notification)
        
        logger.info(f"Sukurtas naujas pranešimas: {title}")
        return notification
    
    def update_notification(self, notification_id, **kwargs):
        """
        Atnaujiname pranešimą
        
        Args:
            notification_id (str): Pranešimo ID
            **kwargs: Atributai, kuriuos norime atnaujinti
            
        Returns:
            Notification: Atnaujintas pranešimas arba None, jei nerasta
        """
        # Randame pranešimą
        notification = self.get_notification_by_id(notification_id)
        if not notification:
            logger.warning(f"Negalima atnaujinti: pranešimas su ID {notification_id} nerastas")
            return None
        
        # Atnaujiname atributus
        send_websocket = kwargs.pop('send_websocket', False)
        
        for key, value in kwargs.items():
            if hasattr(notification, key):
                setattr(notification, key, value)
        
        # Išsaugome pakeitimus
        self._save_notifications()
        
        # Siunčiame atnaujinimą per WebSocket, jei reikia
        if send_websocket:
            self._send_notification_websocket(notification, is_update=True)
        
        logger.info(f"Atnaujintas pranešimas: {notification.title} (ID: {notification.id})")
        return notification
    
    def mark_as_read(self, notification_id):
        """
        Pažymime pranešimą kaip perskaitytą
        
        Args:
            notification_id (str): Pranešimo ID
            
        Returns:
            Notification: Atnaujintas pranešimas arba None, jei nerasta
        """
        return self.update_notification(notification_id, status=NotificationStatus.READ)
    
    def mark_all_as_read(self, user_id=None):
        """
        Pažymime visus pranešimus kaip perskaitytus
        
        Args:
            user_id (str, optional): Vartotojo ID
            
        Returns:
            int: Pažymėtų pranešimų skaičius
        """
        count = 0
        for notification in self.notifications:
            if notification.status == NotificationStatus.UNREAD and (not user_id or notification.user_id == user_id):
                notification.status = NotificationStatus.READ
                count += 1
        
        if count > 0:
            self._save_notifications()
            logger.info(f"Pažymėta {count} pranešimų kaip perskaityti")
        
        return count
    
    def delete_notification(self, notification_id):
        """
        Ištriname pranešimą
        
        Args:
            notification_id (str): Pranešimo ID
            
        Returns:
            bool: True, jei sėkmingai ištrinta, kitaip False
        """
        # Randame pranešimą
        notification = self.get_notification_by_id(notification_id)
        if not notification:
            logger.warning(f"Negalima ištrinti: pranešimas su ID {notification_id} nerastas")
            return False
        
        # Pašaliname pranešimą iš sąrašo
        self.notifications = [n for n in self.notifications if n.id != notification_id]
        
        # Išsaugome pakeitimus
        self._save_notifications()
        
        logger.info(f"Ištrintas pranešimas: {notification.title} (ID: {notification.id})")
        return True
    
    def update_process_progress(self, target_id, progress, message=None, send_websocket=True):
        """
        Atnaujiname proceso progresą
        
        Args:
            target_id (str): Proceso ID
            progress (int): Progreso procentas (0-100)
            message (str, optional): Papildomas pranešimas
            send_websocket (bool): Ar siųsti per WebSocket
        
        Returns:
            Notification: Atnaujintas pranešimas arba None
        """
        # Ieškome egzistuojančio proceso pranešimo
        for notification in self.notifications:
            if notification.target_id == target_id and notification.type == NotificationType.PROCESS:
                # Atnaujiname progresą
                notification.progress = progress
                
                # Atnaujiname žinutę, jei pateikta
                if message:
                    notification.message = message
                
                # Išsaugome pakeitimus
                self._save_notifications()
                
                # Siunčiame atnaujinimą per WebSocket
                if send_websocket:
                    self._send_process_update_websocket(notification)
                
                logger.info(f"Atnaujintas proceso {target_id} progresas: {progress}%")
                return notification
        
        # Jei neradom proceso pranešimo, kuriam naują
        if message:
            return self.create_notification(
                title=f"Procesas vykdomas",
                message=message,
                type=NotificationType.PROCESS,
                target_id=target_id,
                progress=progress,
                send_websocket=send_websocket
            )
        
        return None
    
    def _send_notification_websocket(self, notification, is_update=False):
        """
        Siunčia pranešimą per WebSocket
        
        Args:
            notification (Notification): Pranešimo objektas
            is_update (bool): Ar tai atnaujinimas
        """
        try:
            # Konvertuojame pranešimą į žodyną
            notification_data = notification.to_dict()
            
            # Sukuriame WebSocket žinutę
            message = {
                'type': 'notification',
                'action': 'update' if is_update else 'create',
                'data': notification_data
            }
            
            # Siunčiame pranešimą (visiems arba tik konkrečiam vartotojui)
            if notification.user_id:
                websocket_manager.send_message_to_user(notification.user_id, message)
            else:
                websocket_manager.broadcast_message(message)
                
        except Exception as e:
            logger.error(f"Klaida siunčiant pranešimą per WebSocket: {e}")
    
    def _send_process_update_websocket(self, notification):
        """
        Siunčia proceso atnaujinimą per WebSocket
        
        Args:
            notification (Notification): Proceso pranešimo objektas
        """
        try:
            # Sukuriame WebSocket žinutę
            message = {
                'type': 'process_update',
                'data': {
                    'id': notification.id,
                    'target_id': notification.target_id,
                    'progress': notification.progress,
                    'message': notification.message
                }
            }
            
            # Siunčiame pranešimą (visiems arba tik konkrečiam vartotojui)
            if notification.user_id:
                websocket_manager.send_message_to_user(notification.user_id, message)
            else:
                websocket_manager.broadcast_message(message)
                
        except Exception as e:
            logger.error(f"Klaida siunčiant proceso atnaujinimą per WebSocket: {e}")


# Sukuriame globalų pranešimų serviso objektą
notification_service = NotificationService()