"""
Pranešimų Valdymo Modulis
-----------------------
Šis modulis atsakingas už pranešimų valdymą tarp serverio ir kliento
naudojant Flask aplikaciją.
"""

import json
import logging
from flask import Flask
from flask_socketio import SocketIO  # Įsitikinkite, kad ši biblioteka įdiegta

# Sukuriame logerį
logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    WebSocket ryšių valdymo klasė
    """
    def __init__(self):
        """
        Inicializuojame WebSocket managerį
        """
        self.socketio = None  # Čia inicializuojame socketio kaip None
        self.initialized = False
    
    def init_app(self, app):
        """
        Inicializuojame WebSocket su Flask aplikacija
        """
        if not isinstance(app, Flask):
            raise TypeError("app turi būti Flask aplikacija")
        
        # Inicializuojame SocketIO
        self.socketio = SocketIO(app, cors_allowed_origins="*")
        self.initialized = True
        
        # Registruojame įvykių klausytojus
        self.register_event_handlers()
        
        logger.info("WebSocket manageris inicializuotas")
    
    def register_event_handlers(self):
        """
        Registruojame WebSocket įvykių klausytojus
        """
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Naujas klientas prisijungė")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Klientas atsijungė")
    
    def broadcast(self, message):
        """
        Siunčia pranešimą visiems prisijungusiems klientams
        """
        if not self.initialized:
            logger.warning("WebSocket manageris neinicializuotas")
            return
        
        try:
            # Jei pranešimas nėra string, konvertuojame į JSON
            if not isinstance(message, str):
                message = json.dumps(message)
            
            # Siunčiame pranešimą visiems klientams
            self.socketio.emit('message', message)
            logger.debug(f"Pranešimas išsiųstas visiems klientams: {message[:100]}...")
        except Exception as e:
            logger.error(f"Klaida siunčiant pranešimą: {str(e)}")