# Pranešimų duomenų modelis - saugo informaciją apie sistemos pranešimus
import uuid
from datetime import datetime
from enum import Enum
import json
import os
from pathlib import Path

class NotificationType(Enum):
    """Pranešimo tipo enumeracija"""
    INFO = "info"           # Informacinis pranešimas
    SUCCESS = "success"     # Sėkmės pranešimas
    WARNING = "warning"     # Perspėjimo pranešimas
    ERROR = "error"         # Klaidos pranešimas
    PROCESS = "process"     # Proceso būsenos pranešimas

class NotificationStatus(Enum):
    """Pranešimo būsenos enumeracija"""
    UNREAD = "unread"       # Neperskaitytas
    READ = "read"           # Perskaitytas
    ARCHIVED = "archived"   # Archyvuotas

class Notification:
    """Pranešimų modelis"""
    
    def __init__(self, id=None, title=None, message=None, type=NotificationType.INFO, 
                 status=NotificationStatus.UNREAD, target_url=None, target_id=None, 
                 progress=None, user_id=None, created_at=None):
        """
        Inicializuoja pranešimo objektą
        
        Args:
            id (str): Pranešimo ID
            title (str): Pranešimo pavadinimas/antraštė
            message (str): Pranešimo tekstas
            type (NotificationType): Pranešimo tipas
            status (NotificationStatus): Pranešimo būsena (perskaitytas/neperskaitytas)
            target_url (str): URL, į kurį pranešimas nukreipia (jei yra)
            target_id (str): Susijusio objekto ID (pvz., užduoties ID)
            progress (int): Progreso procentas (0-100), jei tai proceso pranešimas
            user_id (str): Vartotojo, kuriam skirtas pranešimas, ID
            created_at (datetime): Pranešimo sukūrimo laikas
        """
        # Generuojame ID, jei jis nepateiktas
        self.id = id or str(uuid.uuid4())
        
        # Pagrindinė informacija
        self.title = title or "Pranešimas"
        self.message = message or ""
        self.type = type if isinstance(type, NotificationType) else NotificationType.INFO
        self.status = status if isinstance(status, NotificationStatus) else NotificationStatus.UNREAD
        
        # Papildoma informacija
        self.target_url = target_url
        self.target_id = target_id
        self.progress = progress
        self.user_id = user_id
        
        # Laiko informacija
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        """
        Konvertuoja pranešimą į žodyną (saugojimui JSON formatu)
        
        Returns:
            dict: Pranešimo duomenys žodyno formatu
        """
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'status': self.status.value,
            'target_url': self.target_url,
            'target_id': self.target_id,
            'progress': self.progress,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Sukuria pranešimo objektą iš žodyno
        
        Args:
            data (dict): Pranešimo duomenys žodyno formatu
            
        Returns:
            Notification: Sukurtas pranešimo objektas
        """
        # Konvertuojame date string į datetime
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        # Konvertuojame string į enum
        notification_type = NotificationType(data.get('type', 'info'))
        notification_status = NotificationStatus(data.get('status', 'unread'))
        
        # Sukuriame ir grąžiname naują objektą
        return cls(
            id=data.get('id'),
            title=data.get('title'),
            message=data.get('message'),
            type=notification_type,
            status=notification_status,
            target_url=data.get('target_url'),
            target_id=data.get('target_id'),
            progress=data.get('progress'),
            user_id=data.get('user_id'),
            created_at=created_at
        )