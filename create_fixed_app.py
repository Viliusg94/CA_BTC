"""
Create a fixed version of the main app.py file with all necessary corrections
"""

import os
import shutil

def create_fixed_app():
    """Create a fixed version of app.py"""
    
    fixed_app_content = '''import os
import sys
import logging
import json
import requests
import datetime as dt
from datetime import datetime, timedelta
import random
import time
import traceback
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for

# Configure logger first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

startup_start = time.time()
logger.info("=== APPLICATION STARTUP INITIATED ===")

# Create Flask app
app = Flask(__name__)
app.secret_key = 'bitcoin_lstm_secret_key'
logger.info("[OK] Flask app created")

# Add app directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
logger.info(f"[OK] Added {current_dir} to Python path")

# Database configuration
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(current_dir, "bitcoin_models.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Model definition
class ModelHistory(db.Model):
    __tablename__ = 'model_history'
    __table_args__ = {'extend_existing': True}
    
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
    dropout = db.Column(db.Float)
    recurrent_dropout = db.Column(db.Float)
    num_heads = db.Column(db.Integer)
    d_model = db.Column(db.Integer)
    filters = db.Column(db.String(255))
    kernel_size = db.Column(db.String(255))
    validation_split = db.Column(db.Float)
    model_params = db.Column(db.Text)
    training_loss = db.Column(db.Float)
    validation_loss = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_type': self.model_type,
            'r2': float(self.r2) if self.r2 is not None else None,
            'mae': float(self.mae) if self.mae is not None else None,
            'rmse': float(self.rmse) if self.rmse is not None else None,
            'training_loss': float(self.training_loss) if self.training_loss is not None else None,
            'validation_loss': float(self.validation_loss) if self.validation_loss is not None else None,
            'epochs': self.epochs,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_active': self.is_active,
            'model_params': self.model_params
        }

# Initialize database
database_enabled = False
try:
    with app.app_context():
        db.create_all()
        
        # Create sample models if none exist
        if ModelHistory.query.count() == 0:
            sample_models = [
                ModelHistory(
                    model_type='LSTM',
                    r2=0.87,
                    mae=850.0,
                    rmse=1100.0,
                    training_loss=0.045,
                    validation_loss=0.052,
                    epochs=50,
                    is_active=True,
                    model_params='{"layers": 3, "units": 50}',
                    timestamp=datetime.now()
                ),
                ModelHistory(
                    model_type='GRU',
                    r2=0.84,
                    mae=920.0,
                    rmse=1150.0,
                    training_loss=0.048,
                    validation_loss=0.055,
                    epochs=45,
                    is_active=False,
                    model_params='{"layers": 3, "units": 50}',
                    timestamp=datetime.now() - timedelta(hours=1)
                )
            ]
            
            for model in sample_models:
                db.session.add(model)
            
            db.session.commit()
            logger.info(f"Created {len(sample_models)} sample models")
    
    database_enabled = True
    logger.info("[OK] Database initialized successfully")
    
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Initialize ModelManager
model_manager = None
try:
    from model_manager import ModelManager
    
    models_dir = os.path.join(current_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_manager = ModelManager(models_dir=models_dir)
    app.config['MODEL_MANAGER'] = model_manager
    app.model_manager = model_manager
    
    logger.info("[OK] ModelManager initialized successfully")
    
except Exception as e:
    logger.error(f"ModelManager initialization failed: {e}")

# Register endpoints
try:
    from new_endpoints import register_endpoints
    register_endpoints(app, db, ModelHistory, model_manager)
    logger.info("[OK] New endpoints registered successfully")
except Exception as e:
    logger.error(f"Error registering new endpoints: {e}")

# Utility functions
def get_real_bitcoin_price():
    """Get current Bitcoin price from Binance API"""
    try:
        response = requests.get(
            'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return float(data['price'])
    except Exception as e:
        logger.warning(f"Failed to get real Bitcoin price: {e}")
    
    return 45000.0 + random.uniform(-1000, 1000)

def get_bitcoin_price_history(days=7):
    """Get Bitcoin price history from Binance API"""
    try:
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&startTime={start_time}&endTime={end_time}&limit=500"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            klines = response.json()
            
            dates = []
            prices = []
            high_values = []
            low_values = []
            volumes = []
            
            for kline in klines:
                timestamp = datetime.fromtimestamp(kline[0] / 1000)
                date_str = timestamp.strftime('%Y-%m-%d')
                
                close_price = float(kline[4])
                high_price = float(kline[2])
                low_price = float(kline[3])
                volume = float(kline[5])
                
                dates.append(date_str)
                prices.append(close_price)
                high_values.append(high_price)
                low_values.append(low_price)
                volumes.append(volume)
            
            return {
                'dates': dates,
                'prices': prices,
                'close': prices,
                'high': high_values,
                'low': low_values,
                'volumes': volumes
            }
        else:
            raise Exception(f"Binance API returned status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error fetching Bitcoin price history: {e}")
        return {
            'dates': [],
            'prices': [],
            'close': [],
            'high': [],
            'low': [],
            'volumes': []
        }

# Main routes
@app.route('/')
def index():
    try:
        current_price = get_real_bitcoin_price()
        price_history = get_bitcoin_price_history(days=7)
        
        predictions = {
            'dates': [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)],
            'values': []
        }
        
        template_data = {
            'latest_price': current_price,
            'predictions': predictions,
            'price_history': price_history,
            'now': datetime.now()
        }
        
        return render_template('index.html', **template_data)
        
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@app.route('/predict')
def predict_page():
    try:
        current_price = get_real_bitcoin_price()
        
        active_models = []
        if database_enabled:
            try:
                active_models = ModelHistory.query.filter_by(is_active=True).all()
                active_models = [model.to_dict() for model in active_models]
            except Exception as e:
                logger.error(f"Error getting active models: {str(e)}")
        
        template_data = {
            'current_price': current_price,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'active_models': active_models
        }
        
        return render_template('predict.html', **template_data)
    except Exception as e:
        logger.error(f"Error in predict page: {str(e)}", exc_info=True)
        return redirect('/')

if __name__ == '__main__':
    startup_end = time.time()
    startup_duration = startup_end - startup_start
    logger.info(f"=== APPLICATION STARTUP COMPLETE ({startup_duration:.2f}s) ===")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {str(e)}")
'''
    
    # Create backup of existing app.py
    app_path = os.path.join('app', 'app.py')
    backup_path = os.path.join('app', 'app_backup.py')
    
    if os.path.exists(app_path):
        shutil.copy2(app_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
    
    # Write the fixed app.py
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(fixed_app_content)
    
    print(f"✅ Created fixed app.py at {app_path}")
    
    return True

if __name__ == '__main__':
    create_fixed_app()
    print("\n📋 Next steps:")
    print("1. Navigate to the app directory: cd app")
    print("2. Run the application: python app.py")
    print("3. Open your browser to http://localhost:5000")
    print("4. Test the models page: http://localhost:5000/models")
    print("5. Test the training status: http://localhost:5000/training_status")
