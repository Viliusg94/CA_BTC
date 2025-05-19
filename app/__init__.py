"""
Flask aplikacijos inicijavimas
-----------------------------
Šis modulis inicijuoja Flask aplikaciją ir sukonfigūruoja
įvairius jos komponentus.
"""

import os
from datetime import datetime
from flask import Flask

# Importuojame WebSocket managerį
from app.services.websocket_manager import WebSocketManager
from app.utils.generate_sample_metrics import add_sample_models

# Sukuriame WebSocket managerio objektą
websocket_manager = WebSocketManager()

# Importuojame modelio validavimo maršrutus
from app.evaluation.evaluation_routes import model_evaluation
from app.api.validation_routes import api_validation

# Importuojame užduočių maršrutus
from app.routes.task_routes import task_routes

# Užduočių vykdymo serviso įtraukimas į aplikaciją

# Importuojame:
from app.services.task_executor import task_executor

def create_app(config=None):
    """
    Sukuria ir sukonfigūruoja Flask aplikaciją
    
    Returns:
        Flask: Sukonfigūruota Flask aplikacija
    """
    # Inicializuojame Flask
    app = Flask(__name__)
    
    # Nustatome slaptą raktą, naudojamą formų apsaugai ir sesijai
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'paslaptis_123456789')
    
    # Inicializuojame WebSocket managerį su mūsų aplikacija
    websocket_manager.init_app(app)
    
    # Importuojame ir registruojame blueprint'us
    from app.dashboard.routes import dashboard
    from app.trading.routes import trading, trading_scheduler
    from app.training.training_routes import model_training
    from app.routes.scheduler import scheduler
    from app.routes.models import models
    
    app.register_blueprint(dashboard)
    app.register_blueprint(trading)
    app.register_blueprint(trading_scheduler, url_prefix='/trading/scheduler')
    app.register_blueprint(model_training, url_prefix='/training')
    app.register_blueprint(scheduler, url_prefix='/scheduler')
    app.register_blueprint(models, url_prefix='/models')
    
    # Registruojame modelio įvertinimo maršrutus
    app.register_blueprint(model_evaluation)
    
    # Registruojame API validavimo maršrutus
    app.register_blueprint(api_validation)
    
    # Registruojame klaidų apdorojimo funkcijas
    register_error_handlers(app)
    
    # Perduodame dabarties laiką į visus šablonus
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    # Pridedame pavyzdinius modelius
    add_sample_models()
    
    # Registruojame užduočių maršrutus
    app.register_blueprint(task_routes)
    
    # Paleidžiame užduočių vykdytoją
    task_executor.start()
    
    return app

def register_error_handlers(app):
    """
    Registruoja klaidų apdorojimo maršrutus
    
    Args:
        app (Flask): Flask aplikacija
    """
    @app.errorhandler(404)
    def page_not_found(error):
        from flask import render_template
        return render_template('errors/404.html', title='Puslapis nerastas'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        from flask import render_template
        return render_template('errors/500.html', title='Serverio klaida'), 500