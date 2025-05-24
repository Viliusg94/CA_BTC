from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class ModelHistory(db.Model):
    """Model to store training history and metrics"""
    __tablename__ = 'model_history'
    
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)  # LSTM, GRU, Transformer, etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    training_time = db.Column(db.Float)
    epochs = db.Column(db.Integer)
    batch_size = db.Column(db.Integer)
    learning_rate = db.Column(db.Float)
    lookback = db.Column(db.Integer)
    dropout = db.Column(db.Float)
    validation_split = db.Column(db.Float)
    r2 = db.Column(db.Float)  # R-squared score
    mae = db.Column(db.Float)  # Mean Absolute Error
    mse = db.Column(db.Float)  # Mean Squared Error
    rmse = db.Column(db.Float)  # Root Mean Square Error
    training_loss = db.Column(db.Float)
    validation_loss = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=False)  # Whether this model is currently active
    notes = db.Column(db.Text)  # Additional notes about the model
    
    # Model-specific parameters
    # Transformer specific parameters
    num_heads = db.Column(db.Integer)
    d_model = db.Column(db.Integer)
    
    # LSTM/GRU specific parameters
    lstm_units = db.Column(db.Integer)
    recurrent_dropout = db.Column(db.Float)
    
    # CNN specific parameters
    filters = db.Column(db.String(255))  # Stored as JSON string
    kernel_size = db.Column(db.String(255))  # Stored as JSON string
    
    # Model configuration JSON (for additional parameters)
    model_params = db.Column(db.Text)  # JSON string of model parameters
    
    def __repr__(self):
        return f'<ModelHistory {self.id}: {self.model_type} (R²: {self.r2})>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'model_type': self.model_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'training_time': self.training_time,
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'lookback': self.lookback,
            'dropout': self.dropout,
            'validation_split': self.validation_split,
            'r2': self.r2,
            'mae': self.mae,
            'mse': self.mse,
            'rmse': self.rmse,
            'training_loss': self.training_loss,
            'validation_loss': self.validation_loss,
            'is_active': self.is_active,
            'notes': self.notes,
            # Model-specific parameters
            'num_heads': self.num_heads,
            'd_model': self.d_model,
            'lstm_units': self.lstm_units,
            'recurrent_dropout': self.recurrent_dropout,
            'filters': self.filters,
            'kernel_size': self.kernel_size,
            'model_params': json.loads(self.model_params) if self.model_params else None
        }
    
    def get_specific_params(self):
        """Extract model-specific parameters based on model type"""
        params = {}
        
        if self.model_type.lower() in ['lstm', 'gru']:
            if self.lstm_units:
                params['lstm_units'] = self.lstm_units
            if self.recurrent_dropout:
                params['recurrent_dropout'] = self.recurrent_dropout
                
        elif self.model_type.lower() == 'transformer':
            if self.num_heads:
                params['num_heads'] = self.num_heads
            if self.d_model:
                params['d_model'] = self.d_model
                
        elif self.model_type.lower() in ['cnn', 'cnn_lstm']:
            if self.filters:
                try:
                    params['filters'] = json.loads(self.filters)
                except:
                    params['filters'] = self.filters
            if self.kernel_size:
                try:
                    params['kernel_size'] = json.loads(self.kernel_size)
                except:
                    params['kernel_size'] = self.kernel_size
        
        # Add additional params from model_params JSON
        if self.model_params:
            try:
                additional_params = json.loads(self.model_params)
                params.update(additional_params)
            except:
                pass
                
        return params


class PredictionHistory(db.Model):
    """Model to store prediction history"""
    __tablename__ = 'prediction_history'
    
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model_history.id'), nullable=False)
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_date = db.Column(db.Date, nullable=False)  # Date being predicted for
    predicted_price = db.Column(db.Float, nullable=False)
    actual_price = db.Column(db.Float)  # Filled in later when actual price is known
    days_ahead = db.Column(db.Integer, nullable=False)  # How many days ahead this prediction was for
    
    # Relationship
    model = db.relationship('ModelHistory', backref=db.backref('predictions', lazy=True))
    
    def __repr__(self):
        return f'<PredictionHistory {self.id}: {self.predicted_price} for {self.target_date}>'
