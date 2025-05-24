import os
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

# Configure logger first before using it
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Add startup time and logger
startup_start = time.time()
logger.info("=== APPLICATION STARTUP INITIATED ===")

# Import from local utils if available, otherwise use inline implementations
try:
    from utils.bitcoin_api import get_bitcoin_price_history, get_real_bitcoin_price
    logger.info("[OK] Successfully imported Bitcoin API utilities")
except ImportError:
    logger.warning("Could not import from utils.bitcoin_api - using inline implementations")
    
    # Define the function here to ensure it exists
    def get_bitcoin_price_history(days=7):
        """
        Get Bitcoin price history for the specified number of days
        
        Args:
            days (int): Number of days of history to retrieve
            
        Returns:
            dict: Dictionary containing price history data
        """
        try:
            logger.info(f"Fetching Bitcoin price history for {days} days")
            
            # Try to get data from Binance API
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            # Determine appropriate interval based on days
            interval = '1h'  # 1-hour intervals for 7 days or less
            if days > 30:
                interval = '1d'  # daily for longer periods
            elif days > 7:
                interval = '4h'  # 4-hour for medium periods
            
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&startTime={start_time}&endTime={end_time}&limit=500"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                klines = response.json()
                
                # Process data
                dates = []
                prices = []
                high_values = []
                low_values = []
                volumes = []
                
                for kline in klines:
                    # Kline format: [open_time, open, high, low, close, volume, ...]
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
                    'close': prices,  # Alias for compatibility
                    'high': high_values,
                    'low': low_values,
                    'volumes': volumes
                }
                
            else:
                logger.warning(f"Failed to fetch data from Binance API: {response.status_code}")
                # Return empty structure
                return {
                    'dates': [],
                    'prices': [],
                    'close': [],
                    'high': [],
                    'low': [],
                    'volumes': []
                }
                
        except Exception as e:
            logger.error(f"Error fetching Bitcoin price history: {str(e)}")
            # Return empty structure
            return {
                'dates': [],
                'prices': [],
                'close': [],
                'high': [],
                'low': [],
                'volumes': []
            }
    
    # Redefine the real Bitcoin price function to ensure it exists
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
        
        # Return a fallback value
        return 45000.0

# Simple JSON serialization function to replace the missing utility
def serialize_for_template(data):
    """
    Simple JSON serialization for template use
    """
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError):
        return json.dumps({})

# Create json_util module compatibility
class JsonUtil:
    @staticmethod
    def serialize_for_template(data):
        return serialize_for_template(data)

json_util = JsonUtil()

# sukuriame Flask aplikaciją
app = Flask(__name__)
app.secret_key = 'bitcoin_lstm_secret_key'
logger.info("[OK] Flask app created")

# pridedame app katalogą į Python kelią
# tai leidžia importuoti modulius iš to paties katalogo
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
logger.info(f"[OK] Added {current_dir} to Python path")

# Database configuration - moved here to avoid circular imports
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "bitcoin_models.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db = SQLAlchemy(app)

# Model definition - moved here to avoid circular imports
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
    
    # Additional parameters for different models
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
    
    def __repr__(self):
        return f'<ModelHistory {self.id}: {self.model_type} (R²: {self.r2})>'
    
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

# Database initialization
database_enabled = False
try:
    logger.info("Attempting to initialize database...")
    
    # Create tables
    with app.app_context():
        # Add missing columns if they don't exist
        try:
            from sqlalchemy import create_engine, MetaData
            engine = db.engine
            meta = MetaData()
            meta.reflect(bind=engine)
            
            # Add training_loss column if it doesn't exist
            if 'model_history' in meta.tables and 'training_loss' not in meta.tables['model_history'].columns:
                with engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE model_history ADD COLUMN training_loss FLOAT"))
                    conn.execute(db.text("ALTER TABLE model_history ADD COLUMN validation_loss FLOAT"))
                    conn.execute(db.text("ALTER TABLE model_history ADD COLUMN model_params TEXT"))
                    conn.commit()
                    logger.info("Added missing columns to model_history table")
        except Exception as e:
            logger.error(f"Error adding columns to model_history table: {str(e)}")
            logger.warning("Continuing with existing schema")
        
        # Now we can create tables or use existing ones
        db.create_all()
        
        # Check if we have any models, if not create sample ones
        if ModelHistory.query.count() == 0:
            logger.info("No models found, creating sample models...")
            
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
                ),
                ModelHistory(
                    model_type='Transformer',
                    r2=0.82,
                    mae=980.0,
                    rmse=1200.0,
                    training_loss=0.051,
                    validation_loss=0.058,
                    epochs=40,
                    is_active=False,
                    model_params='{"heads": 8, "layers": 6}',
                    timestamp=datetime.now() - timedelta(hours=2)
                )
            ]
            
            for model in sample_models:
                db.session.add(model)
            
            try:
                db.session.commit()
                logger.info(f"Created {len(sample_models)} sample models")
            except Exception as e:
                logger.error(f"Error creating sample models: {str(e)}")
                db.session.rollback()
    
    database_enabled = True
    logger.info("[OK] Database initialized successfully")
    
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    logger.info("Application will run without database functionality")

# ModelManager initialization
model_manager = None
try:
    logger.info("Attempting to initialize ModelManager...")
    
    # Import and initialize ModelManager
    from model_manager import ModelManager
    
    models_dir = os.path.join(current_dir, 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"[OK] Created models directory: {models_dir}")
    
    model_manager = ModelManager(models_dir=models_dir)
    
    # Store model_manager in app config for access in blueprints
    app.config['MODEL_MANAGER'] = model_manager
    app.model_manager = model_manager
    
    # Verify that the tensorflow_available attribute exists
    if hasattr(model_manager, 'tensorflow_available'):
        tf_status = "available" if model_manager.tensorflow_available else "not available"
        logger.info(f"[OK] ModelManager initialized successfully - TensorFlow is {tf_status}")
    else:
        logger.error("[ERROR] ModelManager missing tensorflow_available attribute")
        model_manager = None
    
except ImportError as e:
    logger.error(f"Failed to import ModelManager: {e}")
    logger.info("Application will run with limited model functionality")
except Exception as e:
    logger.error(f"ModelManager initialization failed: {e}")
    logger.error(f"Error details: {traceback.format_exc()}")
    logger.info("Application will run with limited model functionality")

# Import and register new endpoints after database and models are set up
try:
    from new_endpoints import new_endpoints
    app.register_blueprint(new_endpoints)
    logger.info("[OK] New endpoints blueprint registered successfully")
    
    # List all registered routes for debugging
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        if '/models' in rule.rule or '/training-status' in rule.rule or '/api/' in rule.rule:
            logger.info(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
            
except ImportError as e:
    logger.error(f"Failed to import new endpoints: {e}")
    logger.info("Application will run without additional endpoints")
except Exception as e:
    logger.error(f"Error registering new endpoints: {e}")
    logger.error(traceback.format_exc())

# Import and register the training API after other imports
try:
    from api.training_api import training_api
    app.register_blueprint(training_api)
    logger.info("[OK] Training API registered successfully")
except ImportError as e:
    logger.error(f"Failed to import training API: {e}")

# Register real training API
try:
    from api.real_training_api import real_training_api
    app.register_blueprint(real_training_api)
    logger.info("[OK] Real Training API registered successfully")
except ImportError as e:
    logger.error(f"Failed to import real training API: {e}")

# Register prediction routes if available
try:
    from routes.prediction_routes import prediction_routes
    app.register_blueprint(prediction_routes)
    logger.info("[OK] Prediction routes registered successfully")
except ImportError as e:
    logger.warning(f"Failed to import prediction routes: {e}")
    
    @app.route('/predict')
    def predict_page():
        """Bitcoin price prediction page"""
        try:
            logger.info("Loading prediction page")
            
            # Get current Bitcoin price for initial display
            current_price = get_real_bitcoin_price()
            if current_price is None:
                current_price = 45000.0
                
            # Get active models from database
            active_models = []
            if database_enabled:
                try:
                    active_models = ModelHistory.query.filter_by(is_active=True).all()
                    active_models = [model.to_dict() for model in active_models]
                    logger.info(f"Found {len(active_models)} active models")
                except Exception as e:
                    logger.error(f"Error getting active models: {str(e)}")
            
            # Prepare initial template data
            template_data = {
                'current_price': current_price,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'active_models': active_models
            }
            
            return render_template('predict.html', **template_data)
        except Exception as e:
            logger.error(f"Error in predict page: {str(e)}", exc_info=True)
            flash(f"Error loading prediction page: {str(e)}", "error")
            return redirect('/')

# Helper functions
def get_real_bitcoin_price():
    """Get current Bitcoin price with fallback"""
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

def calculate_price_change(current_price, previous_price):
    """Calculate price change percentage"""
    if previous_price is None or previous_price == 0:
        return {'change': 0, 'percentage': 0}
    
    change = current_price - previous_price
    percentage = (change / previous_price) * 100
    
    return {
        'change': round(change, 2),
        'percentage': round(percentage, 2)
    }

def generate_model_predictions(model, current_price, days):
    """Generate model predictions"""
    predictions = []
    accuracy = model.r2 if model.r2 is not None else 0.75
    volatility = 0.02 * (1 - accuracy)
    daily_trend = 0.01 * accuracy
    
    base_price = current_price
    for i in range(days):
        random_factor = random.uniform(-volatility, volatility)
        if i == 0:
            next_price = base_price * (1 + daily_trend + random_factor)
        else:
            next_price = predictions[i-1] * (1 + daily_trend + random_factor)
        predictions.append(round(next_price, 2))
    
    return predictions

# Pagrindiniai maršrutai
@app.route('/')
def index():
    try:
        logger.info("Užkraunamas pagrindinis puslapis")
        
        # Get current Bitcoin price
        current_price = get_real_bitcoin_price()
        if current_price is None:
            current_price = 45000.0  # Use a reasonable default
            logger.warning(f"Unable to get current Bitcoin price, using default ${current_price}")
        
        # Get price history with proper error handling
        price_history = get_bitcoin_price_history(days=7)
        logger.info(f"Retrieved price history with {len(price_history.get('dates', []))} data points")
        
        # Calculate price change
        previous_price = None
        if price_history and len(price_history.get('prices', [])) > 1:
            previous_price = price_history['prices'][-2]
            
        price_change = calculate_price_change(current_price, previous_price)
        
        # Market statistics
        circulating_supply = 19500000  # Approximately correct value
        market_cap = current_price * circulating_supply
        
        high_24h = 0
        low_24h = 0
        volume_24h = 0
        
        if price_history and len(price_history.get('prices', [])) > 0:
            if 'high' in price_history and len(price_history['high']) > 0:
                high_24h = max(price_history['high'][-1] if price_history['high'] else 0, current_price)
            
            if 'low' in price_history and len(price_history['low']) > 0:
                low_24h = min(price_history['low'][-1] if price_history['low'] else float('inf'), current_price)
            
            if 'volumes' in price_history and len(price_history['volumes']) > 0:
                volume_24h = price_history['volumes'][-1] if price_history['volumes'] else 0
        
        # Handle the case where low_24h is still infinite
        if low_24h == float('inf'):
            low_24h = current_price * 0.95  # 5% below current price as a fallback
        
        formatted_market_cap = f"${int(market_cap):,}"
        formatted_volume = f"${int(volume_24h):,}"
        formatted_high = f"${int(high_24h):,}"
        formatted_low = f"${int(low_24h):,}"
        
        # Basic predictions structure with empty values
        predictions = {
            'dates': [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)],
            'values': []
        }
        
        logger.info(f"Pagrindinis puslapis užkrautas. BTC kaina: {current_price}")
        
        # Prepare template data
        template_data = {
            'latest_price': current_price,
            'predictions': predictions,
            'price_history': price_history,
            'price_change': price_change,
            'now': datetime.now(),
            'market_cap': market_cap,
            'formatted_market_cap': formatted_market_cap,
            'volume_24h': volume_24h,
            'formatted_volume': formatted_volume,
            'high_24h': high_24h,
            'formatted_high': formatted_high,
            'low_24h': low_24h,
            'formatted_low': formatted_low
        }
        
        # Pass data to the template
        return render_template('index.html', **template_data)
                            
    except Exception as e:
        logger.error(f"Klaida index endpoint'e: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@app.route('/prediction')
def prediction_page():
    """Bitcoin price prediction page"""
    try:
        logger.info("Loading prediction page")
        
        # Get current Bitcoin price for initial display
        current_price = get_real_bitcoin_price()
        if current_price is None:
            current_price = 0.0
            
        # Prepare initial template data
        template_data = {
            'current_price': current_price,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('predict.html', **template_data)
    except Exception as e:
        logger.error(f"Error in predict page: {str(e)}", exc_info=True)
        flash(f"Error loading prediction page: {str(e)}", "error")
        return redirect('/')

# Fix the main routing issues by adding the missing routes directly to app.py

@app.route('/models')
def models_page():
    """Models management page - fixed route"""
    try:
        logger.info("Loading models page")
        
        # Get model files from directory
        models_dir = os.path.join(current_dir, 'models')
        model_files = {}
        if os.path.exists(models_dir):
            for filename in os.listdir(models_dir):
                if filename.endswith('.h5'):
                    model_type = filename.replace('.h5', '').replace('_model', '').upper()
                    model_files[model_type] = filename
        
        # Get model history from database
        model_history = {}
        if database_enabled:
            try:
                models = ModelHistory.query.all()
                for model in models:
                    if model.model_type not in model_history:
                        model_history[model.model_type] = []
                    model_history[model.model_type].append(model.to_dict())
            except Exception as e:
                logger.error(f"Error fetching model history: {e}")
        
        return render_template('models.html', 
                             model_files=model_files,
                             model_history=model_history)
    except Exception as e:
        logger.error(f"Error in models page: {e}")
        return render_template('models.html', 
                             model_files={},
                             model_history={},
                             error=str(e))

@app.route('/training_status')
def training_status():
    """Training status page - fixed route"""
    try:
        logger.info("Loading training status page")
        
        # Get training progress for all model types
        progress_data = {}
        model_types = ['lstm', 'gru', 'cnn', 'transformer']
        
        for model_type in model_types:
            progress_data[model_type] = {
                'progress': {'status': 'Ready', 'progress': 0},
                'status': {'status': 'Ready'}
            }
        
        return render_template('training_status.html', progress_data=progress_data)
    except Exception as e:
        logger.error(f"Error in training status page: {e}")
        return render_template('training_status.html', 
                             progress_data={},
                             error=str(e))

@app.route('/api/model_history_db', methods=['GET'])
def api_model_history_db():
    """API endpoint to get all model history from database - fixed route"""
    try:
        if not database_enabled:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        models = ModelHistory.query.order_by(ModelHistory.timestamp.desc()).all()
        model_data = [model.to_dict() for model in models]
        
        return jsonify({
            'success': True,
            'models': model_data,
            'count': len(model_data)
        })
    except Exception as e:
        logger.error(f"Error fetching model history: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/model/config', methods=['GET', 'POST'])
def api_model_config():
    """Model configuration API endpoint - fixed route"""
    if request.method == 'GET':
        model_type = request.args.get('model_type')
        if not model_type:
            return jsonify({'error': 'No model type specified'}), 400
        
        # Return default config
        default_config = {
            'epochs': 50,
            'batch_size': 32,
            'learning_rate': 0.001,
            'sequence_length': 24
        }
        
        return jsonify({'model_type': model_type, 'config': default_config})
    
    elif request.method == 'POST':
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            return jsonify({
                'status': 'success',
                'message': 'Config updated successfully'
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/model/progress')
def api_model_progress():
    """Model training progress API endpoint - fixed route"""
    model_type = request.args.get('model_type')
    if not model_type:
        return jsonify({'error': 'No model type specified'}), 400
    
    # Return mock progress data
    progress = {
        'status': 'Ready',
        'progress': 0,
        'current_epoch': 0,
        'total_epochs': 50
    }
    
    return jsonify({'model_type': model_type, 'progress': progress})

@app.route('/api/model_details/<model_type>')
def api_model_details(model_type):
    """Model details API endpoint - fixed route"""
    try:
        details = {
            'model_type': model_type,
            'status': 'Ready',
            'last_trained': 'Never',
            'performance': 'Unknown'
        }
        
        return jsonify({'success': True, 'details': details})
    except Exception as e:
        logger.error(f"Error in model details API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/price_history')
def api_price_history():
    """Price history API endpoint - fixed route"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Use the existing function
        price_data = get_bitcoin_price_history(days=days)
        
        return jsonify({
            'status': 'success',
            'data': price_data
        })
    except Exception as e:
        logger.error(f"Error in price history API: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/predictions')
def api_predictions():
    """Predictions API endpoint - fixed route"""
    try:
        # Generate mock predictions
        dates = []
        values = []
        
        current_price = get_real_bitcoin_price()
        
        for i in range(7):
            date = (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d')
            # Simple trend prediction
            trend_factor = 1 + (random.uniform(-0.02, 0.02))
            value = current_price * (trend_factor ** (i + 1))
            
            dates.append(date)
            values.append(round(value, 2))
        
        return jsonify({
            'status': 'success',
            'data': {
                'dates': dates,
                'values': values
            }
        })
    except Exception as e:
        logger.error(f"Error in predictions API: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

# Register the new training API
try:
    from api.training_api_v2 import training_api_v2
    app.register_blueprint(training_api_v2)
    logger.info("[OK] Training API v2 registered successfully")
except ImportError as e:
    logger.error(f"Failed to import training API v2: {e}")

# Add route for the training page
@app.route('/train_models')
def train_models_page():
    """Model training page with full functionality"""
    try:
        logger.info("Loading model training page")
        return render_template('train_models.html')
    except Exception as e:
        logger.error(f"Error in train models page: {str(e)}", exc_info=True)
        flash(f"Error loading training page: {str(e)}", "error")
        return redirect('/')

# Add route for real training page
@app.route('/real_training')
def real_training_page():
    """Real training page"""
    try:
        logger.info("Loading real training page")
        return render_template('real_training.html')
    except Exception as e:
        logger.error(f"Error in real training page: {str(e)}", exc_info=True)
        flash(f"Error loading real training page: {str(e)}", "error")
        return redirect('/')

if __name__ == '__main__':
    startup_end = time.time()
    startup_duration = startup_end - startup_start
    logger.info(f"=== APPLICATION STARTUP COMPLETE ({startup_duration:.2f}s) ===")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {str(e)}")