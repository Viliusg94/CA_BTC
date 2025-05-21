"""
Pranešimų Valdymo Modulis
-----------------------
Šis modulis atsakingas už pranešimų valdymą tarp serverio ir kliento
naudojant Flask aplikaciją.
"""

# WebSocket ryšio valdymo servisas - atsakingas už realaus laiko pranešimų siuntimą
import asyncio
import json
import logging
import threading
import uuid
import websockets
from collections import defaultdict
from flask import Flask, redirect, url_for, render_template
from asyncio import run_coroutine_threadsafe

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Klasė WebSocket ryšių valdymui"""
    
    def __init__(self, host='localhost', port=8765):
        """
        Inicializuojame WebSocket managerį
        
        Args:
            host (str): Host adresas
            port (int): Prievado numeris
        """
        self.host = host
        self.port = port
        self.connections = set()
        self.user_connections = defaultdict(set)
        self.is_running = False
        self.server_thread = None
        
        # Pranešimų eilė
        self.message_queue = asyncio.Queue()
        
        logger.info(f"WebSocketManager inicializuotas (host: {host}, port: {port})")
        
        # Paleidžiame žinučių gavimo procesą atskirame thread su event loop
        self.consumer_thread = threading.Thread(target=self._run_async_consumer)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()

    def _run_async_consumer(self):
        """Paleidžia asinchroninę korutiną eventų cikle"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Paleidžiame message_consumer korutiną
            loop.run_until_complete(self.message_consumer())
        except Exception as e:
            logger.error(f"Klaida vykdant WebSocket korutiną: {e}")
        finally:
            loop.close()
    
    async def register(self, websocket, user_id=None):
        """
        Registruoja naują WebSocket ryšį
        
        Args:
            websocket: WebSocket ryšys
            user_id (str, optional): Vartotojo ID
        """
        # Pridedame ryšį į bendrą sąrašą
        self.connections.add(websocket)
        
        # Jei nurodytas vartotojo ID, pridedame į vartotojo ryšių sąrašą
        if user_id:
            self.user_connections[user_id].add(websocket)
            
        logger.info(f"Naujas WebSocket ryšys užregistruotas (vartotojas: {user_id if user_id else 'anonimas'})")
    
    async def unregister(self, websocket, user_id=None):
        """
        Išregistruoja WebSocket ryšį
        
        Args:
            websocket: WebSocket ryšys
            user_id (str, optional): Vartotojo ID
        """
        # Pašaliname ryšį iš bendro sąrašo
        if websocket in self.connections:
            self.connections.remove(websocket)
        
        # Jei nurodytas vartotojo ID, pašaliname iš vartotojo ryšių sąrašo
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
                
            # Jei vartotojo ryšių nebeliko, pašaliname vartotoją
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                
        logger.info(f"WebSocket ryšys išregistruotas (vartotojas: {user_id if user_id else 'anonimas'})")
    
    async def message_consumer(self):
        """
        Gauna pranešimus iš eilės ir siunčia juos klientams
        """
        while True:
            # Gauname pranešimą iš eilės
            message = await self.message_queue.get()
            
            try:
                # Tikriname, ar tai broadcast pranešimas
                if message.get('broadcast', False):
                    # Siunčiame visiems prisijungusiems klientams
                    websockets_list = list(self.connections)
                    for websocket in websockets_list:
                        try:
                            await websocket.send(json.dumps(message['data']))
                        except websockets.exceptions.ConnectionClosed:
                            pass  # Ryšys jau uždarytas
                else:
                    # Siunčiame konkrečiam vartotojui
                    user_id = message.get('user_id')
                    if user_id and user_id in self.user_connections:
                        websockets_list = list(self.user_connections[user_id])
                        for websocket in websockets_list:
                            try:
                                await websocket.send(json.dumps(message['data']))
                            except websockets.exceptions.ConnectionClosed:
                                pass  # Ryšys jau uždarytas
            except Exception as e:
                logger.error(f"Klaida siunčiant pranešimą: {e}")
            
            # Pažymime, kad pranešimas apdorotas
            self.message_queue.task_done()
    
    async def websocket_handler(self, websocket, path):
        """
        Tvarko WebSocket prisijungimus
        
        Args:
            websocket: WebSocket ryšys
            path (str): URL kelias
        """
        # Išgauti vartotojo ID iš URL
        user_id = None
        if '?' in path:
            query = path.split('?')[1]
            params = query.split('&')
            for param in params:
                if param.startswith('user_id='):
                    user_id = param.split('=')[1]
        
        # Užregistruoti WebSocket ryšį
        await self.register(websocket, user_id)
        
        try:
            # Laukti pranešimų iš kliento
            async for message in websocket:
                try:
                    # Apdoroti gautą pranešimą
                    data = json.loads(message)
                    
                    # Čia galite apdoroti gautus pranešimus
                    logger.info(f"Gautas pranešimas nuo kliento: {data}")
                    
                    # Pavyzdys: atsakyti į pranešimą
                    response = {
                        'type': 'response',
                        'message': f"Pranešimas gautas: {data.get('message', '')}"
                    }
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    logger.error(f"Gautas neteisingas JSON: {message}")
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Išregistruoti WebSocket ryšį
            await self.unregister(websocket, user_id)
    
    def broadcast_message(self, data):
        """
        Siunčia pranešimą visiems prisijungusiems klientams
        """
        try:
            # Įdedame pranešimą į eilę
            message = {
                'broadcast': True,
                'data': data
            }
            
            # Naudojame asyncio.new_event_loop() vietoj get_event_loop()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Vykdome eilės įdėjimo operaciją
                loop.run_until_complete(self.message_queue.put(message))
                return True
            finally:
                # Būtinai uždarome loop
                loop.close()
        
        except Exception as e:
            logger.error(f"Klaida įdedant pranešimą į eilę: {e}")
            return False
    
    def send_message_to_user(self, user_id, data):
        """
        Siunčia pranešimą konkrečiam vartotojui
        """
        try:
            # Įdedame pranešimą į eilę
            message = {
                'broadcast': False,
                'user_id': user_id,
                'data': data
            }
            
            # Naudojame asyncio.new_event_loop() vietoj get_event_loop()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Vykdome eilės įdėjimo operaciją
                loop.run_until_complete(self.message_queue.put(message))
                return True
            finally:
                # Būtinai uždarome loop
                loop.close()
        
        except Exception as e:
            logger.error(f"Klaida įdedant pranešimą į eilę: {e}")
            return False
    
    def _run_async_server(self):
        """
        Paleidžia WebSocket serverį asinchroniniame cikle
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Sukurti WebSocket serverį
            server = websockets.serve(
                self.websocket_handler, 
                self.host, 
                self.port
            )
            
            # Paleisti serverį
            self.is_running = True
            loop.run_until_complete(server)
            loop.run_forever()
        except Exception as e:
            logger.error(f"Klaida paleidžiant WebSocket serverį: {e}")
            self.is_running = False
        finally:
            loop.close()

    def start(self):
        """
        Paleidžia WebSocket serverį atskirame thread
        
        Returns:
            bool: True, jei pavyko paleisti, kitaip False
        """
        if self.is_running:
            logger.warning("WebSocket serveris jau paleistas")
            return False
        
        try:
            # Paleidžiame serverį atskirame thread
            self.server_thread = threading.Thread(target=self._run_async_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"WebSocket serveris paleistas adresu ws://{self.host}:{self.port}")
            return True
        
        except Exception as e:
            logger.error(f"Klaida paleidžiant WebSocket serverį: {e}")
            return False
    
    def stop(self):
        """
        Sustabdo WebSocket serverį
        
        Returns:
            bool: True, jei pavyko sustabdyti, kitaip False
        """
        if not self.is_running:
            logger.warning("WebSocket serveris nėra paleistas")
            return False
        
        try:
            # Žymime, kad serveris sustabdytas
            self.is_running = False
            
            # Uždarome asinchroninį ciklą saugiu būdu
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            logger.info("WebSocket serveris sustabdytas")
            return True
        
        except Exception as e:
            logger.error(f"Klaida stabdant WebSocket serverį: {e}")
            return False

# Globalus WebSocketManager objektas
websocket_manager = WebSocketManager()