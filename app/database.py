"""
Duomenų bazės konfigūracija ir modeliai
"""
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Sukuriame SQLAlchemy objektą
db = SQLAlchemy()

# Modelių istorijos duomenų modelis
class ModelHistory(db.Model):
    """Modelių istorijos lentelė"""
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    training_time = db.Column(db.Float)
    epochs = db.Column(db.Integer)
    batch_size = db.Column(db.Integer)
    learning_rate = db.Column(db.Float)
    lookback = db.Column(db.Integer)
    layers = db.Column(db.String(255))
    mae = db.Column(db.Float)
    mse = db.Column(db.Float)
    rmse = db.Column(db.Float)
    r2 = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    # Papildomi parametrai skirtingiems modeliams
    # LSTM, GRU
    dropout = db.Column(db.Float)
    recurrent_dropout = db.Column(db.Float)
    
    # Transformer
    num_heads = db.Column(db.Integer)
    d_model = db.Column(db.Integer)
    
    # CNN
    filters = db.Column(db.String(255))
    kernel_size = db.Column(db.String(255))
    
    # Bendros metrikos
    validation_split = db.Column(db.Float)
    
    def to_dict(self):
        """Konvertuoja modelį į žodyną"""
        return {
            'id': self.id,
            'model_type': self.model_type,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'training_time': self.training_time,
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'lookback': self.lookback,
            'layers': self.layers,
            'metrics': {
                'mae': self.mae,
                'mse': self.mse,
                'rmse': self.rmse,
                'r2': self.r2
            },
            'is_active': self.is_active,
            'notes': self.notes,
            'parameters': {
                'dropout': self.dropout,
                'recurrent_dropout': self.recurrent_dropout,
                'num_heads': self.num_heads,
                'd_model': self.d_model,
                'filters': self.filters,
                'kernel_size': self.kernel_size,
                'validation_split': self.validation_split
            }
        }

def init_db(app):
    """Inicializuoja duomenų bazę"""
    # Nustatome duomenų bazės kelią
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'models.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Konfigūruojame duomenų bazę
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializuojame duomenų bazę
    db.init_app(app)
    
    # Sukuriame lenteles, jei jos neegzistuoja
    with app.app_context():
        db.create_all()