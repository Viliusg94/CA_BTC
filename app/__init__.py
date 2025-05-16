"""
Flask aplikacijos inicijavimas
-----------------------------
Šis modulis inicijuoja Flask aplikaciją ir sukonfigūruoja
įvairius jos komponentus.
"""

import os
from datetime import datetime
from flask import Flask

def create_app():
    """
    Sukuria ir sukonfigūruoja Flask aplikaciją
    
    Returns:
        Flask: Sukonfigūruota Flask aplikacija
    """
    # Inicializuojame Flask
    app = Flask(__name__)
    
    # Nustatome slaptą raktą, naudojamą formų apsaugai ir sesijai
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'paslaptis_123456789')
    
    # Importuojame ir registruojame blueprint'us
    from app.dashboard.routes import dashboard
    from app.trading.routes import trading
    
    app.register_blueprint(dashboard)
    app.register_blueprint(trading)
    
    # Registruojame klaidų apdorojimo funkcijas
    register_error_handlers(app)
    
    # Perduodame dabarties laiką į visus šablonus
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
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