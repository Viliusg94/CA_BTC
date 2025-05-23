"""
Flask aplikacijos inicijavimas
-----------------------------
Šis modulis inicijuoja Flask aplikaciją ir sukonfigūruoja
įvairius jos komponentus.
"""

import os
from datetime import datetime
from flask import Flask, redirect, url_for, current_app
from flask_socketio import SocketIO
import logging

# Importuojame WebSocket managerį
try:
    from app.services.websocket_service import websocket_manager
except ImportError:
    # Create a placeholder for the websocket_manager
    class DummyWebSocketManager:
        def setup_socketio(self, socketio): pass
        def start(self): pass
    websocket_manager = DummyWebSocketManager()

# Importuojame modelio validavimo maršrutus
try:
    from app.evaluation.evaluation_routes import model_evaluation
except ImportError:
    # Laikinas sprendimas
    from flask import Blueprint
    model_evaluation = Blueprint('model_evaluation', __name__, url_prefix='/evaluation')

from app.api.validation_routes import api_validation

# Importuojame užduočių maršrutus
try:
    from app.routes.task_routes import task_routes
except ImportError:
    # Create a temporary placeholder if module is not found
    from flask import Blueprint
    task_routes = Blueprint('tasks', __name__, url_prefix='/tasks')

# Užduočių vykdymo serviso įtraukimas į aplikaciją
try:
    from app.services.task_executor import task_executor
except ImportError:
    # Create a placeholder for task_executor
    task_executor = None

# Importuojame pranešimų maršrutus
try:
    from app.routes.notification_routes import notification_routes
except ImportError:
    # Create a placeholder if module is not found
    from flask import Blueprint
    notification_routes = Blueprint('notifications', __name__, url_prefix='/notifications')

# Importuojame dokumentacijos maršrutus
try:
    from app.routes.documentation_routes import documentation_routes
except ImportError:
    # Create a placeholder if module is not found
    from flask import Blueprint
    documentation_routes = Blueprint('documentation', __name__, url_prefix='/docs')

# Registruojame dashboard maršrutus
try:
    from app.dashboard.dashboard_routes import dashboard
except ImportError:
    # Create a placeholder if module is not found
    from flask import Blueprint
    dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Importuojame prekybos maršrutus
try:
    from app.trading.trading_routes import trading
except ImportError:
    # Create a placeholder if module is not found
    from flask import Blueprint
    trading = Blueprint('trading', __name__, url_prefix='/trading')

# Importuojame modelio treniravimo maršrutus
try:
    from app.training.training_routes import model_training
except ImportError:
    # Create a placeholder if module is not found
    from flask import Blueprint
    model_training = Blueprint('training', __name__, url_prefix='/training')

# Pridėkite šią importo eilutę
try:
    from app.training.template_routes import template_management
except ImportError:
    # Create a placeholder if module is not found
    from flask import Blueprint
    template_management = Blueprint('templates', __name__, url_prefix='/templates')

# Importuojame naują rezultatų modulį
try:
    from app.results.results_routes import results
except ImportError:
    # Create a placeholder if module is not found
    from flask import Blueprint
    results = Blueprint('results', __name__, url_prefix='/results')

# Sukuriame loggerį
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sukurkite SocketIO objektą
socketio = SocketIO()

# Inicializuojame duomenų bazę
from app.database import init_db

# Papildykite failą d:\CA_BTC\app\__init__.py

from app.db.init_results_db import init_results_tables

def create_app(config=None):
    """
    Sukuria ir sukonfigūruoja Flask aplikaciją
    
    Args:
        config: Konfigūracijos objektas arba failo kelias
        
    Returns:
        app: Flask aplikacijos objektas
    """
    # Sukuriame Flask aplikaciją
    app = Flask(__name__)
    
    # Nustatome pagrindinę konfigūraciją
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development_key')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    
    # Taikomos konfigūracijos
    app.config.from_mapping(
        SECRET_KEY='dev',  # Pakeiskite į saugesnį slaptažodį produkcinėje aplinkoje
        # Kitos konfigūracijos...
    )
    
    if config:
        app.config.from_mapping(config)
    
    # Inicializuojame SocketIO su aplikacija
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Nustatykite websocket_manager su socketio objektu
    websocket_manager.setup_socketio(socketio)
    
    # Registruojame modelio validavimo maršrutus
    app.register_blueprint(model_evaluation)
    app.register_blueprint(api_validation)
    
    # Registruojame užduočių maršrutus
    app.register_blueprint(task_routes)
    
    # Registruojame pranešimų maršrutus
    app.register_blueprint(notification_routes)
    
    # Registruojame dokumentacijos maršrutus
    app.register_blueprint(documentation_routes)
    
    # Registruojame dashboard maršrutus
    app.register_blueprint(dashboard)
    
    # Registruojame prekybos maršrutus
    app.register_blueprint(trading)
    
    # Registruojame modelio treniravimo maršrutus
    app.register_blueprint(model_training)
    
    # Pridėkite šią eilutę prie kitų app.register_blueprint() eilučių
    app.register_blueprint(template_management)
    
    # Registruojame rezultatų maršrutus
    app.register_blueprint(results)
    
    # Inicializuojame duomenų bazę
    init_db()
    
    # Inicializuojame rezultatų lenteles esamoje duomenų bazėje
    try:
        init_results_tables()
    except Exception as e:
        app.logger.error(f"Klaida inicializuojant rezultatų lenteles: {e}")
    
    # PASTABA: Schemos optimizavimo neįtraukiame į paleidimo procesą,
    # nes tai turėtų būti atlikta tik vieną kartą administratoriaus
    # naudojant app/db/migrate_to_optimized.py skriptą.
    
    # Pridedame konteksto procesorius datai
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    # Pridedame konteksto procesorių dabartinei aplikacijai
    @app.context_processor
    def inject_current_app():
        return {'current_app': current_app}
    
    # Paleidžiame užduočių vykdytoją
    task_executor.start()
    
    # Paleidžiame WebSocket serverį
    try:
        websocket_manager.start()
    except Exception as e:
        app.logger.error(f"Klaida paleidžiant WebSocket serverį: {e}")
    
    # Pridėtas pagrindinio puslapio maršrutas
    @app.route('/')
    def index():
        # Pakeiskite šį nukreipimą, jei jis neteisinga
        return redirect(url_for('model_evaluation.index'))
    
    # Grąžiname sukonfigūruotą aplikaciją
    return app