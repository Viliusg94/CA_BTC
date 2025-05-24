import logging
import json
from flask_socketio import SocketIO, emit, disconnect
from flask import request
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Klasė, skirta valdyti WebSocket komunikaciją tarp serverio ir kliento
    """
    
    def __init__(self):
        """
        Inicializuoja WebSocket managerį
        """
        self.socketio = None
        self.connected_clients = set()
        self.error_handlers = {}
        
    def setup_socketio(self, socketio):
        """
        Nustato SocketIO objektą
        
        Args:
            socketio (SocketIO): Flask-SocketIO objektas
        """
        self.socketio = socketio
        self._register_error_handlers()
        self._register_event_handlers()
        
    def _register_error_handlers(self):
        """Register comprehensive error handlers"""
        
        @self.socketio.on_error_default
        def default_error_handler(e):
            logger.error(f"WebSocket error: {str(e)}", exc_info=True)
            emit('error', {
                'message': 'An unexpected error occurred',
                'timestamp': datetime.now().isoformat(),
                'error_type': 'websocket_error'
            })
            
        @self.socketio.on_error('/training')
        def training_error_handler(e):
            logger.error(f"Training WebSocket error: {str(e)}", exc_info=True)
            emit('training_error', {
                'message': 'Training communication error',
                'timestamp': datetime.now().isoformat(),
                'suggested_action': 'Please refresh the page and try again'
            })
            
    def _register_event_handlers(self):
        """Register event handlers with error handling"""
        
        @self.socketio.on('connect')
        def handle_connect():
            try:
                client_id = request.sid
                self.connected_clients.add(client_id)
                logger.info(f"Client {client_id} connected")
                
                emit('connection_confirmed', {
                    'status': 'connected',
                    'client_id': client_id,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error handling connection: {e}")
                emit('error', {'message': 'Connection failed'})
                
        @self.socketio.on('disconnect')
        def handle_disconnect():
            try:
                client_id = request.sid
                self.connected_clients.discard(client_id)
                logger.info(f"Client {client_id} disconnected")
                
            except Exception as e:
                logger.error(f"Error handling disconnection: {e}")
                
        @self.socketio.on('request_training_status')
        def handle_training_status_request(data):
            try:
                model_type = data.get('model_type')
                if not model_type:
                    emit('error', {'message': 'Model type required'})
                    return
                    
                # Get training status from model service
                from app.services.model_service import ModelTrainingService
                service = ModelTrainingService()
                status = service.get_training_progress(model_type)
                
                emit('training_status', {
                    'model_type': model_type,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting training status: {e}")
                emit('training_error', {
                    'message': 'Failed to get training status',
                    'model_type': data.get('model_type', 'unknown')
                })
    
    def broadcast_training_progress(self, model_type, progress_data):
        """Broadcast training progress with error handling"""
        try:
            if not self.socketio:
                logger.warning("SocketIO not initialized")
                return False
                
            self.socketio.emit('training_progress', {
                'model_type': model_type,
                'progress': progress_data,
                'timestamp': datetime.now().isoformat()
            }, namespace='/training')
            
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting training progress: {e}")
            return False
    
    def broadcast_error(self, error_type, message, details=None):
        """Broadcast error to all connected clients"""
        try:
            if not self.socketio:
                return False
                
            error_data = {
                'error_type': error_type,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            if details:
                error_data['details'] = details
                
            self.socketio.emit('system_error', error_data)
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting error: {e}")
            return False
    
    def start(self):
        """Start WebSocket service with error handling"""
        try:
            if self.socketio:
                logger.info("WebSocket service started successfully")
                return True
            else:
                logger.error("SocketIO not initialized")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start WebSocket service: {e}")
            return False

# Sukuriame globalų WebSocketManager objektą
websocket_manager = WebSocketManager()