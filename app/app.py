import os
import sys
import logging
import json
import requests
import datetime as dt
from datetime import datetime, timedelta
import random
import time
from flask import Flask, render_template, request, jsonify

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

# konfigūruojame logerį
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# pridedame startup laiką
# ir logerį
startup_start = time.time()
logger.info("=== APPLICATION STARTUP INITIATED ===")

try:
    from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
    logger.info("✓ Flask imported successfully")
except ImportError as e:
    logger.error(f"✗ Failed to import Flask: {e}")
    sys.exit(1)

# sukuriame Flask aplikaciją
app = Flask(__name__)
app.secret_key = 'bitcoin_lstm_secret_key'
logger.info("✓ Flask app created")

# pridedame app katalogą į Python kelią
# tai leidžia importuoti modulius iš to paties katalogo
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
logger.info(f"✓ Added {current_dir} to Python path")

# inicializuojame duomenų bazę
# Bandome inicializuoti duomenų bazę, bet leidžiame programai veikti ir be jos
database_enabled = False
try:
    logger.info("Attempting to initialize database...")
    from database import init_db, db, ModelHistory
    init_db(app)
    database_enabled = True
    logger.info("✓ Database initialized successfully")
except ImportError as e:
    logger.warning(f"Database modules not available: {e}")
    logger.info("Application will run without database functionality")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    logger.info("Application will run without database functionality")

# inicializuojame ModelManager
model_manager = None
try:
    logger.info("Attempting to initialize ModelManager...")
    
    # Check if TensorFlow is available
    try:
        import tensorflow as tf
        tf_version = tf.__version__
        logger.info(f"✓ TensorFlow {tf_version} available")
        tf_available = True
    except ImportError:
        logger.warning("TensorFlow not available - limited functionality")
        tf_available = False
    
    # Import and initialize ModelManager
    from model_manager import ModelManager
    
    models_dir = os.path.join(current_dir, 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"✓ Created models directory: {models_dir}")
    
    model_manager = ModelManager(models_dir=models_dir)
    logger.info("✓ ModelManager initialized successfully")
    
except ImportError as e:
    logger.error(f"Failed to import ModelManager: {e}")
    logger.info("Application will run with limited model functionality")
except Exception as e:
    logger.error(f"ModelManager initialization failed: {e}")
    logger.info("Application will run with limited model functionality")

# sukuriame funkciją, kuri gauna dabartinę Bitcoin kainą
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
    
    # gražiname fake kainą, jei nepavyko gauti realios
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

# Konfigūruojame logerį
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sukuriame Flask aplikaciją ir inicializuojame prieš importą
app = Flask(__name__)
app.secret_key = 'bitcoin_lstm_secret_key'

# Bandome inicializuoti duomenų bazę, bet leidžiame programai veikti ir be jos
try:
    from database import init_db, db, ModelHistory
    init_db(app)
    logger.info("Duomenų bazė sėkmingai inicializuota")
    database_enabled = True
except Exception as e:
    logger.error(f"Klaida inicializuojant duomenų bazę: {str(e)}")
    logger.info("Programa veiks be duomenų bazės funkcionalumo")
    database_enabled = False

# Importo sekcija (apie 10-60 eilutę)

import os
import sys
import logging
import json
import requests
import datetime as dt  
from datetime import datetime, timedelta  
import random

# Pridedame app katalogą į Python kelią
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importuojame ModelManager
try:
    from model_manager import ModelManager
    
    # Nustatome kelią į modelių direktoriją
    models_dir = os.path.join(current_dir, 'models')
    
    # Sukuriame direktoriją, jei ji neegzistuoja
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"Sukurta modelių direktorija: {models_dir}")
    
    # Inicializuojame ModelManager
    model_manager = ModelManager(models_dir=models_dir)
    logger.info("ModelManager sėkmingai inicializuotas")
    
except Exception as e:
    logger.error(f"Klaida inicializuojant ModelManager: {str(e)}", exc_info=True)
    model_manager = None  # Sukuriame tuščią objektą

# API endpoints
@app.route('/api/model/config', methods=['GET', 'POST'])
def model_config():
    """API endpoint modelių nustatymų valdymui"""
    # GET: grąžina modelio nustatymus
    if request.method == 'GET':
        model_type = request.args.get('model_type')
        if not model_type:
            return jsonify({'error': 'Nenurodytas modelio tipas'}), 400
        
        if not model_manager:
            return jsonify({'error': 'ModelManager neprieinamas'}), 500
        
        config = model_manager.get_model_config(model_type)
        return jsonify({'model_type': model_type, 'config': config})
    
    # POST: atnaujina modelio nustatymus
    elif request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'error': 'Nepateikti duomenys'}), 400
        
        model_type = data.get('model_type')
        config = data.get('config')
        
        if not model_type or not config:
            return jsonify({'error': 'Nenurodytas modelio tipas arba nustatymai'}), 400
        
        if not model_manager:
            return jsonify({'error': 'ModelManager neprieinamas'}), 500
        
        # Validuojame konfigūracijos parametrus
        valid_params = True
        validation_errors = []
        
        try:
            # Tikriname skaičių parametrus
            num_params = ['epochs', 'batch_size', 'lookback']
            for param in num_params:
                if param in config:
                    try:
                        config[param] = int(config[param])
                        if config[param] <= 0:
                            valid_params = False
                            validation_errors.append(f"Parametras {param} turi būti teigiamas skaičius")
                    except (ValueError, TypeError):
                        valid_params = False
                        validation_errors.append(f"Parametras {param} turi būti sveikasis skaičius")
            
            # Tikriname float parametrus
            float_params = ['learning_rate', 'dropout', 'recurrent_dropout', 'validation_split']
            for param in float_params:
                if param in config:
                    try:
                        config[param] = float(config[param])
                        if param == 'learning_rate' and (config[param] <= 0 or config[param] > 1):
                            valid_params = False
                            validation_errors.append(f"Parametras {param} turi būti tarp 0 ir 1")
                        elif (param == 'dropout' or param == 'recurrent_dropout' or param == 'validation_split') and (config[param] < 0 or config[param] >= 1):
                            valid_params = False
                            validation_errors.append(f"Parametras {param} turi būti tarp 0 ir 1")
                    except (ValueError, TypeError):
                        valid_params = False
                        validation_errors.append(f"Parametras {param} turi būti skaičius")
            
            # Tikriname transformerio parametrus
            if model_type == 'transformer':
                if 'num_heads' in config:
                    try:
                        config['num_heads'] = int(config['num_heads'])
                        if config['num_heads'] <= 0:
                            valid_params = False
                            validation_errors.append("Parametras num_heads turi būti teigiamas skaičius")
                    except (ValueError, TypeError):
                        valid_params = False
                        validation_errors.append("Parametras num_heads turi būti sveikasis skaičius")
                
                if 'd_model' in config:
                    try:
                        config['d_model'] = int(config['d_model'])
                        if config['d_model'] <= 0:
                            valid_params = False
                            validation_errors.append("Parametras d_model turi būti teigiamas skaičius")
                    except (ValueError, TypeError):
                        valid_params = False
                        validation_errors.append("Parametras d_model turi būti sveikasis skaičius")
        
        except Exception as e:
            logger.error(f"Klaida validuojant parametrus: {str(e)}")
            valid_params = False
            validation_errors.append(str(e))
        
        # Jei parametrai neteisingi, grąžiname klaidą
        if not valid_params:
            return jsonify({
                'status': 'error', 
                'message': 'Neteisingi parametrai',
                'errors': validation_errors
            }), 400
        
        # Atnaujiname nustatymus
        success = model_manager.update_model_config(model_type, config)
        
        if success:
            return jsonify({
                'status': 'success', 
                'message': f'Modelio {model_type} nustatymai atnaujinti',
                'config': config
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': f'Klaida atnaujinant modelio {model_type} nustatymus'
            }), 500

@app.route('/api/model/progress')
def model_progress():
    """API endpoint modelių apmokymo progreso stebėjimui"""
    model_type = request.args.get('model_type')
    if not model_type:
        return jsonify({'error': 'Nenurodytas modelio tipas'}), 400
    
    if not model_manager:
        return jsonify({'error': 'ModelManager neprieinamas'}), 500
    
    progress = model_manager.get_training_progress(model_type)
    return jsonify({'model_type': model_type, 'progress': progress})

@app.route('/api/model_history/<model_type>')
def model_history(model_type):
    """API endpoint modelio istorijos gavimui"""
    try:
        if not model_manager:
            return jsonify([])
        
        # Gauname modelio istorijos duomenis
        history = model_manager.get_model_history(model_type)
        return jsonify(history)
    except Exception as e:
        logger.error(f"Klaida gaunant modelio {model_type} istoriją: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_model_history/<model_type>/<model_id>', methods=['DELETE'])
def delete_model_history(model_type, model_id):
    """API endpoint modelio istorijos įrašo ištrynimui"""
    try:
        app.logger.info(f"Bandoma ištrinti modelio {model_type} įrašą (ID: {model_id})")
        
        # Pirmiausia bandome per model_manager (jei jis egzistuoja)
        if model_manager:
            try:
                success = model_manager.delete_model_history(model_type, model_id)
                if success:
                    return jsonify({'success': True, 'message': 'Modelio įrašas ištrintas'})
            except Exception as e:
                app.logger.error(f"Klaida trinant per ModelManager: {str(e)}")
        
        # Jei nepavyko per model_manager, bandome per duomenų bazę
        if database_enabled:
            try:
                # Konvertuojame ID į integer
                model_id_int = int(model_id)
                
                # Randam modelį pagal ID ir tipą
                model = ModelHistory.query.filter_by(id=model_id_int, model_type=model_type).first()
                if not model:
                    model = ModelHistory.query.get(model_id_int)  # Bandome tiesiog pagal ID, jei tipas neatitinka
                    if not model:
                        return jsonify({'success': False, 'error': 'Modelis duomenų bazėje nerastas'}), 404
                
                # Išsaugome informaciją apie aktyvumą
                is_active = model.is_active
                model_type = model.model_type  # Atnaujiname model_type, jei radome pagal ID
                
                # Ištriname modelį
                db.session.delete(model)
                db.session.commit()
                
                # Jei modelis buvo aktyvus ir turime model_manager, atnaujinkime jo statusą
                if is_active and model_manager:
                    model_status = model_manager.get_model_status(model_type)
                    model_status['status'] = 'Neaktyvus'
                    model_status['active_model_id'] = None
                    model_manager._save_model_status()
                
                return jsonify({'success': True, 'message': 'Modelis sėkmingai ištrintas'})
            except Exception as e:
                app.logger.error(f"Klaida trinant per DB: {str(e)}")
                if database_enabled:
                    db.session.rollback()
        
        # Jei abu būdai nepavyko
        return jsonify({'success': False, 'error': 'Nepavyko ištrinti modelio įrašo'}), 500
    except Exception as e:
        app.logger.error(f"Klaida trinant modelį: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/use_model/<model_type>/<model_id>', methods=['POST'])
def use_model(model_type, model_id):
    """API endpoint modelio aktyvavimui"""
    try:
        app.logger.info(f"Bandoma aktyvuoti modelį {model_type} (ID: {model_id})")
        
        # Pirmiausia bandome per model_manager
        if model_manager:
            try:
                success = model_manager.activate_model(model_type, model_id)
                if success:
                    return jsonify({'success': True, 'message': 'Modelis aktyvuotas'})
            except Exception as e:
                app.logger.error(f"Klaida aktyvuojant per ModelManager: {str(e)}")
        
        # Jei nepavyko per model_manager, bandome per duomenų bazę
        if database_enabled:
            try:
                # Konvertuojame ID į integer
                model_id_int = int(model_id)
                
                # Randam modelį pagal ID ir tipą
                model = ModelHistory.query.filter_by(id=model_id_int, model_type=model_type).first()
                if not model:
                    model = ModelHistory.query.get(model_id_int)  # Bandome tiesiog pagal ID
                    if not model:
                        return jsonify({'success': False, 'error': 'Modelis duomenų bazėje nerastas'}), 404
                
                model_type = model.model_type  # Atnaujiname model_type, jei radome pagal ID
                
                # Pažymime visus to tipo modelius kaip neaktyvius
                ModelHistory.query.filter_by(model_type=model_type).update({'is_active': False})
                
                # Nustatome pasirinktą modelį kaip aktyvų
                model.is_active = True
                db.session.commit()
                
                # Atnaujinkime ir ModelManager'io statusą, jei jis egzistuoja
                if model_manager:
                    model_status = model_manager.get_model_status(model_type)
                    model_status['status'] = 'Aktyvus'
                    model_status['last_trained'] = model.timestamp.strftime('%Y-%m-%d %H:%M:%S') if model.timestamp else 'Unknown'
                    model_status['performance'] = f"MAE: {model.mae:.4f}" if model.mae else 'Nežinoma'
                    model_status['active_model_id'] = model.id
                    model_manager._save_model_status()
                
                return jsonify({'success': True, 'message': 'Modelis sėkmingai aktyvuotas'})
            except Exception as e:
                app.logger.error(f"Klaida aktyvuojant per DB: {str(e)}")
                if database_enabled:
                    db.session.rollback()
        
        # Jei abu būdai nepavyko
        return jsonify({'success': False, 'error': 'Nepavyko aktyvuoti modelio'}), 500
    except Exception as e:
        app.logger.error(f"Klaida aktyvuojant modelį: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model_params/<int:model_id>')
def get_model_params(model_id):
    """API endpoint modelio parametrų gavimui"""
    try:
        # Tikriname, ar duomenų bazė inicializuota
        if not database_enabled:
            return jsonify({'success': False, 'error': 'Duomenų bazė nepasiekiama'}), 500
        
        # Randam modelį pagal ID
        model = ModelHistory.query.get(model_id)
        if not model:
            return jsonify({'success': False, 'error': 'Modelis nerastas'}), 404
        
        # Grąžiname modelio duomenis
        return jsonify({
            'success': True,
            'model': model.to_dict()
        })
    except Exception as e:
        logger.error(f"Klaida gaunant modelio parametrus: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export_models')
def export_models():
    """API endpoint modelių eksportavimui"""
    try:
        # Gauname parametrus
        model_format = request.args.get('format', 'json')
        ids = request.args.get('ids')
        
        # Formuojame užklausą
        query = ModelHistory.query
        
        # Jei nurodyti konkretūs ID
        if ids:
            id_list = [int(id) for id in ids.split(',')]
            query = query.filter(ModelHistory.id.in_(id_list))
        
        # Gauname duomenis
        models = query.all()
        
        # Konvertuojame į reikiamą formatą
        if model_format == 'json':
            data = [model.to_dict() for model in models]
            response = jsonify(data)
            response.headers["Content-Disposition"] = "attachment; filename=models_export.json"
            return response
        
        elif model_format == 'csv':
            # Sukuriame CSV stringą
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Antraštės
            writer.writerow(['id', 'model_type', 'timestamp', 'epochs', 'batch_size', 
                           'learning_rate', 'lookback', 'mae', 'mse', 'rmse', 'r2', 
                           'is_active', 'training_time'])
            
            # Duomenys
            for model in models:
                writer.writerow([
                    model.id,
                    model.model_type,
                    model.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    model.epochs,
                    model.batch_size,
                    model.learning_rate,
                    model.lookback,
                    model.mae,
                    model.mse,
                    model.rmse,
                    model.r2,
                    model.is_active,
                    model.training_time
                ])
            
            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=models_export.csv'
            }
        
        else:
            return jsonify({'success': False, 'error': 'Nepalaikomas formatas'}), 400
        
    except Exception as e:
        logger.error(f"Klaida eksportuojant modelius: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# Pagrindiniai maršrutai
@app.route('/')
def index():
    try:
        logger.info("Užkraunamas pagrindinis puslapis")
        
        # Get current Bitcoin price
        current_price = get_real_bitcoin_price()
        if current_price is None:
            current_price = 45000.0 + random.uniform(-1000, 1000)
            logger.warning(f"Using fallback Bitcoin price: {current_price}")
        
        # Get price history with proper fallback
        price_history = get_bitcoin_price_history(days=7)
        if not price_history or not isinstance(price_history, dict):
            # Ensure we have a properly structured price_history
            price_history = generate_mock_bitcoin_data(days=7)
        
        # Calculate price change
        price_change = calculate_price_change(current_price, price_history['prices'][-2] if len(price_history.get('prices', [])) > 1 else current_price * 0.99)
        
        # Market statistics with fallbacks
        circulating_supply = 19500000  
        market_cap = current_price * circulating_supply
        
        high_24h = current_price * 1.03
        low_24h = current_price * 0.97
        volume_24h = 25000000000
        
        if price_history and len(price_history.get('prices', [])) > 0:
            if 'high' in price_history and len(price_history['high']) > 0:
                high_24h = max(price_history['high'][-1], current_price)
            else:
                high_24h = max(price_history['prices']) if price_history.get('prices') else high_24h
            
            if 'low' in price_history and len(price_history['low']) > 0:
                low_24h = min(price_history['low'][-1], current_price)
            else:
                low_24h = min(price_history['prices']) if price_history.get('prices') else low_24h
            
            if 'volumes' in price_history and len(price_history['volumes']) > 0:
                volume_24h = price_history['volumes'][-1]
        
        formatted_market_cap = f"${int(market_cap):,}"
        formatted_volume = f"${int(volume_24h):,}"
        formatted_high = f"${int(high_24h):,}"
        formatted_low = f"${int(low_24h):,}"
        
        # Create fixed predictions
        fixed_predictions = {
            'dates': [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)],
            'values': [current_price * (1 + 0.01 * i) for i in range(1, 8)]
        }
        
        logger.info(f"Predictions object structure: {fixed_predictions}")
        logger.info(f"Pagrindinis puslapis užkrautas. BTC kaina: {current_price}")
        
        # Prepare all template data and serialize it
        template_data = {
            'latest_price': current_price,
            'predictions': fixed_predictions,
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
        
        # Serialize all data for the template
        serialized_template_data = serialize_for_template(template_data)
        
        # Pass serialized data to the template
        return render_template('index.html', **template_data)
                            
    except Exception as e:
        logger.error(f"Klaida index endpoint'e: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@app.route('/models')
def models_page():
    """Modelių valdymo puslapis"""
    try:
        # Tikriname, ar ModelManager egzistuoja
        if not model_manager:
            flash("ModelManager nepasiekiamas.", "error")
            return redirect('/')
        
        # Gauname modelių informaciją
        models_info = {}
        model_configs = {}
        model_history = {}
        
        # Safely get model types
        model_types = getattr(model_manager, 'model_types', ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm'])
        
        # Get training status for each model
        training_now = []
        
        # Tikriname, ar yra modelių info
        for model_type in model_types:
            try:
                # Gauname modelio būseną
                model_status = model_manager.get_model_status(model_type)
                
                # Get training progress safely with error handling
                try:
                    progress = model_manager.get_training_progress(model_type)
                    # Only add to training_now if it's actually training
                    if progress and progress.get('status') == 'Apmokomas':
                        training_now.append({
                            'model_type': model_type,
                            'name': model_type.upper(),
                            'progress': progress.get('progress', 0),
                            'current_epoch': progress.get('current_epoch', 0),
                            'total_epochs': progress.get('total_epochs', 0),
                            'time_remaining': progress.get('time_remaining', 'Nežinoma'),
                            'metrics': progress.get('metrics', {})
                        })
                except Exception as progress_error:
                    logger.error(f"Klaida gaunant modelio {model_type} progresą: {str(progress_error)}")
                
                # Kuriame modelio info objektą
                if model_type == 'lstm':
                    name = 'LSTM'
                    description = 'Long Short-Term Memory Neural Network'
                elif model_type == 'gru':
                    name = 'GRU'
                    description = 'Gated Recurrent Unit Neural Network'
                elif model_type == 'transformer':
                    name = 'Transformer'
                    description = 'Attention-based Transformer Network'
                elif model_type == 'cnn':
                    name = 'CNN'
                    description = 'Convolutional Neural Network'
                elif model_type == 'cnn_lstm':
                    name = 'CNN-LSTM'
                    description = 'Hybrid CNN-LSTM Network'
                else:
                    name = model_type.upper()
                    description = 'Custom Model'
                
                # Sukuriame modelio informacijos žodyną
                models_info[model_type] = {
                    'name': name,
                    'description': description,
                    'status': model_status.get('status', 'Neapmokytas'),
                    'last_trained': model_status.get('last_trained', 'Niekada'),
                    'performance': model_status.get('performance', 'Nežinoma'),
                    'active_model_id': model_status.get('active_model_id')
                }
                
                # Gauname modelio konfigūraciją
                try:
                    model_configs[model_type] = model_manager.get_model_config(model_type)
                except Exception as config_error:
                    logger.error(f"Klaida gaunant modelio {model_type} konfigūraciją: {str(config_error)}")
                    model_configs[model_type] = {}
                
                # Get model history for this model type
                try:
                    model_history[model_type] = model_manager.get_model_history(model_type)
                except Exception as history_error:
                    logger.error(f"Klaida gaunant modelio {model_type} istoriją: {str(history_error)}")
                    model_history[model_type] = []
                
            except Exception as model_error:
                logger.error(f"Klaida gaunant informaciją apie modelį {model_type}: {str(model_error)}")
                models_info[model_type] = {
                    'name': model_type.upper(),
                    'description': 'Nepavyko gauti informacijos',
                    'status': 'Klaida',
                    'last_trained': 'Niekada',
                    'performance': 'Nežinoma',
                    'active_model_id': None
                }
                model_configs[model_type] = {}
                model_history[model_type] = []
        
        # Add auto-refresh only if training is in progress
        auto_refresh = len(training_now) > 0
        
        # Rendiname šabloną su duomenimis
        return render_template('models.html', 
                              models_info=models_info,
                              model_configs=model_configs,
                              model_history=model_history,
                              training_now=training_now,
                              auto_refresh=auto_refresh,
                              refresh_interval=5)  # 5 seconds refresh interval
    
    except Exception as e:
        logger.error(f"Klaida modelių puslapyje: {str(e)}", exc_info=True)
        flash(f"Klaida: {str(e)}", "error")
        return redirect('/')

@app.route('/training_status')
def training_status_page():
    """Page to monitor training status of all models"""
    try:
        if not model_manager:
            flash("ModelManager nepasiekiamas", "error")
            return redirect('/')
            
        # Get status for all model types
        models_status = {}
        model_types = getattr(model_manager, 'model_types', ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm'])
        
        logger.info(f"Checking training status for models: {model_types}")
        
        any_training = False
        for model_type in model_types:
            try:
                # Get training progress
                training_progress = model_manager.get_training_progress(model_type)
                
                # Get model status
                model_status = model_manager.get_model_status(model_type)
                
                # Check if model is training
                is_training = training_progress.get('status') == 'Apmokomas'
                if is_training:
                    any_training = True
                
                # Store combined status
                models_status[model_type] = {
                    'training_progress': training_progress,
                    'model_status': model_status,
                    'is_training': is_training,
                    'name': model_type.upper()
                }
            except Exception as e:
                logger.error(f"Error getting status for {model_type}: {str(e)}")
                models_status[model_type] = {
                    'training_progress': {'status': 'Klaida', 'progress': 0},
                    'model_status': {'status': 'Klaida'},
                    'is_training': False,
                    'name': model_type.upper()
                }
        
        return render_template(
            'training_status.html',
            models_status=models_status,
            refresh_interval=5,
            any_training=any_training
        )
    except Exception as e:
        logger.error(f"Error in training status page: {str(e)}", exc_info=True)
        flash(f"Klaida: {str(e)}", "error")
        return redirect('/models')

@app.route('/train_model', methods=['POST'])
def train_model():
    """
    Apmoko pasirinktą modelį pagal pateiktą užklausą
    """
    try:
        # Get the model type from the form
        model_type = request.form.get('model_type', 'lstm')
        
        logger.info(f"Training request received for model: {model_type}")
        
        # Check if ModelManager exists
        if not model_manager:
            logger.error("ModelManager nepasiekiamas, negalima pradėti apmokymo")
            flash('Klaida: ModelManager nepasiekiamas', 'error')
            return redirect('/models')
        
        # Check if model type is valid
        if not hasattr(model_manager, 'model_types') or model_type not in model_manager.model_types:
            logger.error(f"Neteisingas modelio tipas: {model_type}")
            flash(f'Klaida: Neteisingas modelio tipas {model_type}', 'error')
            return redirect('/models')
            
        # Check if model is already training
        try:
            progress = model_manager.get_training_progress(model_type)
            if progress.get('status') == 'Apmokomas':
                logger.warning(f"Modelis {model_type} jau yra apmokomas")
                flash(f'Modelis {model_type.upper()} jau yra apmokomas.', 'info')
                return redirect('/training_status')
        except Exception as e:
            logger.error(f"Klaida tikrinant modelio būseną: {str(e)}")
            # Continue even if check fails
            
        # Clear any existing error status before starting
        try:
            if hasattr(model_manager, 'training_progress') and model_type in model_manager.training_progress:
                if model_manager.training_progress[model_type].get('status') == 'Klaida':
                    logger.info(f"Clearing previous error status for {model_type}")
                    model_manager.training_progress[model_type] = {
                        'status': 'Ruošiamasi',
                        'progress': 0,
                        'current_epoch': 0,
                        'total_epochs': 0,
                        'time_remaining': 'Ruošiamasi...',
                        'metrics': {},
                        'current_step': 'Inicializuojama...'
                    }
        except Exception as e:
            logger.error(f"Error clearing previous status: {str(e)}")
            
        # Start the training process
        try:
            logger.info(f"Starting training for model: {model_type}")
            success = model_manager.train_model(model_type)
            logger.info(f"Training initiated: {'Success' if success else 'Failed'}")
            
            if success:
                flash(f'Modelio {model_type.upper()} apmokymas pradėtas sėkmingai!', 'success')
                return redirect('/training_status')
            else:
                flash(f'Nepavyko pradėti {model_type.upper()} modelio apmokymo.', 'warning')
        except Exception as e:
            logger.error(f"Klaida pradedant apmokyti modelį: {str(e)}", exc_info=True)
            flash(f'Klaida pradedant apmokyti modelį: {str(e)}', 'error')
        
        return redirect('/models')
        
    except Exception as e:
        logger.error(f"Klaida apmokant modelį: {str(e)}", exc_info=True)
        flash(f'Klaida apmokant modelį: {str(e)}', 'error')
        return redirect('/models')

# API endpoint to check model training progress
@app.route('/api/training_progress/<model_type>')
def api_training_progress(model_type):
    """API endpoint for training progress"""
    try:
        if not model_manager:
            return jsonify({'success': False, 'error': 'ModelManager not available'}), 500
            
        # Get training progress
        progress = model_manager.get_training_progress(model_type)
        
        # Get model status
        status = model_manager.get_model_status(model_type)
        
        # Enhanced debug information
        debug_info = {
            'model_type': model_type,
            'has_training_progress': hasattr(model_manager, 'training_progress'),
            'has_running_trainings': hasattr(model_manager, 'running_trainings'),
            'training_thread_alive': False
        }
        
        # Check if training thread is alive
        if hasattr(model_manager, 'running_trainings') and model_type in model_manager.running_trainings:
            thread = model_manager.running_trainings[model_type]
            debug_info['training_thread_alive'] = thread.is_alive() if thread else False
        
        # Return as JSON
        return jsonify({
            'success': True,
            'model_type': model_type,
            'progress': progress,
            'model_status': status,
            'is_training': progress.get('status') == 'Apmokomas',
            'debug_info': debug_info,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Error in API training progress: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/status')
def get_model_status_api():
    """API endpoint to get model status"""
    try:
        model_type = request.args.get('model_type')
        if not model_type:
            return jsonify({'success': False, 'error': 'No model type specified'}), 400
            
        if not model_manager:
            return jsonify({'success': False, 'error': 'ModelManager not available'}), 500
            
        status = model_manager.get_model_status(model_type)
        return jsonify({
            'success': True,
            'model_type': model_type,
            'status': status.get('status', 'Unknown'),
            'last_trained': status.get('last_trained', 'Never'),
            'performance': status.get('performance', 'Unknown'),
            'active_model_id': status.get('active_model_id')
        })
    except Exception as e:
        logger.error(f"Error in get_model_status_api: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model_history_db')
def get_model_history_db():
    """API endpoint visų modelių istorijos gavimui iš duomenų bazės"""
    try:
        # Tikriname, ar duomenų bazė inicializuota
        if not 'database_enabled' in globals() or not database_enabled or not 'ModelHistory' in globals():
            return jsonify([])  # Grąžiname tuščią sąrašą, jei DB neprieinama
        
        # Filtravimo parametrai
        model_type = request.args.get('model_type')
        
        # Užklausa
        query = ModelHistory.query
        
        # Filtruojame pagal modelio tipą, jei pateiktas
        if model_type and model_type != 'all':
            query = query.filter_by(model_type=model_type)
        
        # Rikiuojame pagal laiką (naujausi viršuje)
        query = query.order_by(ModelHistory.timestamp.desc())
        
        # Gauname įrašus
        records = query.all()
        
        # Konvertuojame į JSON
        result = []
        for record in records:
            record_dict = {}
            
            # Bandome naudoti to_dict() metodą, jei jis egzistuoja
            if hasattr(record, 'to_dict'):
                record_dict = record.to_dict()
            else:
                # Pridedame pagrindinius laukus
                for field in ['id', 'model_type', 'epochs', 'batch_size', 'learning_rate', 
                             'lookback', 'dropout', 'mae', 'mse', 'rmse', 'r2', 'is_active']:
                    if hasattr(record, field):
                        record_dict[field] = getattr(record, field)
                
                # Konvertuojame timestamp į string
                if hasattr(record, 'timestamp') and record.timestamp:
                    record_dict['timestamp'] = record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # Pridedame training_time
                if hasattr(record, 'training_time'):
                    record_dict['training_time'] = record.training_time
            
            result.append(record_dict)
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Klaida gaunant modelių istoriją: {str(e)}", exc_info=True)
        return jsonify([])  # Saugiau grąžinti tuščią sąrašą nei 500 klaidą

@app.route('/api/model/history_config')
def model_history_config():
    """API endpoint modelio konfigūracijos gavimui iš istorijos"""
    try:
        model_type = request.args.get('model_type')
        model_id = request.args.get('model_id')
        
        app.logger.info(f"Gautas užklausimas modelio parametrams: model_type={model_type}, model_id={model_id}")
        
        if not model_type or not model_id:
            return jsonify({'success': False, 'error': 'Nenurodytas modelio tipas arba ID'}), 400
        
        # Bandome konvertuoti model_id į integer
        try:
            model_id_int = int(model_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Neteisingas modelio ID formatas'}), 400
        
        # Tikriname, ar duomenų bazė inicializuota
        if not database_enabled:
            return jsonify({'success': False, 'error': 'Duomenų bazė nepasiekiama'}), 500
        
        # Gauname modelio įrašą
        model = ModelHistory.query.get(model_id_int)
        if not model:
            return jsonify({'success': False, 'error': 'Modelis nerastas'}), 404
        
        # Sudarome konfigūracijos žodyną
        config = {}
        
        # Įtraukiame visus galimus parametrus
        for param in ['epochs', 'batch_size', 'learning_rate', 'lookback', 'dropout', 
                     'recurrent_dropout', 'validation_split', 'num_heads', 'd_model',
                     'filters', 'kernel_size', 'notes']:
            if hasattr(model, param):
                value = getattr(model, param)
                if value is not None:  # Neįtraukiame None reikšmių
                    config[param] = value
        
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        app.logger.error(f"Klaida gaunant modelio konfigūraciją: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/predict', methods=['GET', 'POST'])
def predict_page():
    try:
        if request.method == 'POST':
            model_name = request.form.get('model', 'transformer')
            logger.info(f"Bandoma gauti prognozę iš modelio {model_name}")
            
            if not model_manager:
                raise ValueError("Model manager not initialized")
                
            prediction = model_manager.predict(model_name)
            return jsonify(prediction)
            
        return render_template('predict.html')
        
    except Exception as e:
        logger.error(f"Klaida generuojant prognozes: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/btc_price/current')
def current_btc_price_api():
    """API endpoint dabartinei Bitcoin kainai gauti"""
    try:
        price = get_real_bitcoin_price()
        if price is None:
            return jsonify({
                'success': False,
                'error': 'Nepavyko gauti Bitcoin kainos'
            }), 500
        
        return jsonify({
            'success': True,
            'price': price,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Klaida gaunant dabartinę Bitcoin kainą: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/btc_price/history')
def btc_price_history():
    try:
        # Gauname dienų skaičių iš parametrų (numatytoji reikšmė 30)
        days = request.args.get('days', 30, type=int)
        
        # Apribojame dienų skaičių, kad išvengtume per didelių užklausų
        if days > 365:
            days = 365
        
        logger.info(f"Requesting Bitcoin price history for {days} days")
        
        # Gauname istorinius duomenis
        history_data = get_bitcoin_price_history(days)
        
        if not history_data:
            logger.error("Failed to get Bitcoin price history")
            return jsonify({
                'success': False,
                'error': 'Nepavyko gauti Bitcoin kainos istorijos'
            }), 500
        
        logger.info(f"Successfully retrieved {len(history_data.get('dates', []))} data points")
        return jsonify(history_data)
        
    except Exception as e:
        logger.error(f"Klaida gaunant Bitcoin kainos istoriją: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/candlestick-data')
def candlestick_data_alt():
    """Alternative API endpoint for candlestick chart data"""
    try:
        logger.info("Alternative candlestick data endpoint called")
        interval = request.args.get('interval', '1d')
        limit = int(request.args.get('limit', 100))
        
        # Just redirect to the working history endpoint
        return redirect(f'/api/btc_price/history?days={limit}')
        
    except Exception as e:
        logger.error(f"Error in alternative candlestick endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/price_history')
def api_price_history():
    """API endpoint for price history data"""
    try:
        days = request.args.get('days', 30, type=int)
        if days > 365:
            days = 365
            
        logger.info(f"API: Requesting Bitcoin price history for {days} days")
        
        # Get fresh price history data directly from Binance
        history_data = get_live_bitcoin_ohlc_data(days)
        
        if not history_data:
            logger.error("Failed to get Bitcoin price history")
            return jsonify({
                'status': 'error',
                'message': 'Nepavyko gauti Bitcoin kainos istorijos'
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': history_data
        })
        
    except Exception as e:
        logger.error(f"Error in API price history: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def get_live_bitcoin_ohlc_data(days=30):
    """
    Get live Bitcoin OHLC data directly from Binance API
    """
    try:
        logger.info(f"Fetching live Bitcoin OHLC data for {days} days")
        
        # Calculate time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days + 1)).timestamp() * 1000)
        
        # Use daily interval for OHLC data
        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime={start_time}&endTime={end_time}&limit={days + 5}"
        
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Binance API error: {response.status_code}")
            return generate_current_mock_bitcoin_data(days)
            
        klines = response.json()
        
        if not klines:
            logger.warning("Empty response from Binance API")
            return generate_current_mock_bitcoin_data(days)
        
        # Process the kline data
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        for kline in klines:
            # Binance kline format: [timestamp, open, high, low, close, volume, ...]
            timestamp = kline[0] / 1000
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            
            dates.append(date)
            opens.append(open_price)
            highs.append(high_price)
            lows.append(low_price)
            closes.append(close_price)
            volumes.append(volume)
        
        logger.info(f"Successfully processed {len(dates)} OHLC data points")
        
        return {
            'dates': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'prices': closes,  # Backward compatibility
            'volumes': volumes,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error getting live Bitcoin OHLC data: {str(e)}", exc_info=True)
        return generate_current_mock_bitcoin_data(days)

# Update the existing get_bitcoin_price_history function to include current data
def get_bitcoin_price_history(days=30):
    """
    Get current Bitcoin price history including today's data from Binance API
    
    Args:
        days (int): Number of days
        
    Returns:
        dict: Price history with formatted data
    """
    try:
        logger.info(f"Fetching Bitcoin price history for {days} days from Binance")
        
        # Get data from Binance API with proper time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days + 1)).timestamp() * 1000)
        
        # Use 1h interval for more recent data, 1d for longer periods
        interval = '1h' if days <= 7 else '1d'
        
        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&startTime={start_time}&endTime={end_time}&limit=1000"
        
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Binance API error: {response.status_code}")
            return generate_current_mock_bitcoin_data(days)
            
        klines = response.json()
        
        if not klines:
            logger.warning("Empty response from Binance API")
            return generate_current_mock_bitcoin_data(days)
        
        # Process the data
        dates = []
        prices = []
        volumes = []
        open_prices = []
        high_prices = []
        low_prices = []
        
        # Group by day if we're using hourly data
        if interval == '1h':
            daily_data = {}
            
            for kline in klines:
                timestamp = kline[0] / 1000
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                open_price = float(kline[1])
                high_price = float(kline[2])
                low_price = float(kline[3])
                close_price = float(kline[4])
                volume = float(kline[5])
                
                if date not in daily_data:
                    daily_data[date] = {
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume
                    }
                else:
                    # Update high/low and close
                    daily_data[date]['high'] = max(daily_data[date]['high'], high_price)
                    daily_data[date]['low'] = min(daily_data[date]['low'], low_price)
                    daily_data[date]['close'] = close_price  # Use latest close
                    daily_data[date]['volume'] += volume
            
            # Convert to arrays
            for date in sorted(daily_data.keys()):
                data = daily_data[date]
                dates.append(date)
                open_prices.append(data['open'])
                high_prices.append(data['high'])
                low_prices.append(data['low'])
                prices.append(data['close'])
                volumes.append(data['volume'])
                
        else:
            # Daily data processing
            for kline in klines:
                timestamp = kline[0] / 1000
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                open_price = float(kline[1])
                high_price = float(kline[2])
                low_price = float(kline[3])
                close_price = float(kline[4])
                volume = float(kline[5])
                
                dates.append(date)
                open_prices.append(open_price)
                high_prices.append(high_price)
                low_prices.append(low_price)
                prices.append(close_price)
                volumes.append(volume)
        
        # Add current price if today's data is missing
        today = datetime.now().strftime('%Y-%m-%d')
        if not dates or dates[-1] != today:
            current_price = get_real_bitcoin_price()
            if current_price:
                dates.append(today)
                prices.append(current_price)
                open_prices.append(current_price)
                high_prices.append(current_price)
                low_prices.append(current_price)
                volumes.append(0)  # No volume data for current price
        
        logger.info(f"Successfully processed {len(dates)} price data points")
        
        return {
            'dates': dates,
            'prices': prices,
            'close': prices,
            'volumes': volumes,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error getting Bitcoin price history: {str(e)}", exc_info=True)
        return generate_current_mock_bitcoin_data(days)

def generate_current_mock_bitcoin_data(days=30):
    """Generate mock Bitcoin data including today's price"""
    logger.info(f"Generating current mock Bitcoin data for {days} days")
    
    dates = []
    prices = []
    volumes = []
    open_prices = []
    high_prices = []
    low_prices = []
    
    # Get current real price as base
    current_price = get_real_bitcoin_price()
    if not current_price:
        current_price = 45000
    
    # Generate historical data working backwards from today
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i-1)).strftime('%Y-%m-%d')
        
        # Simulate price movement
        if i == 1:  # Today - use current price
            price = current_price
        else:
            # Generate price based on distance from today
            variation = random.uniform(-0.05, 0.05)  # 5% max variation
            price = current_price * (1 + variation * (i / days))
        
        open_price = price * (1 + random.uniform(-0.02, 0.02))
        high_price = price * (1 + random.uniform(0.01, 0.03))
        low_price = price * (1 - random.uniform(0.01, 0.03))
        volume = random.randint(1000, 10000)
        
        dates.append(date)
        open_prices.append(round(open_price, 2))
        high_prices.append(round(high_price, 2))
        low_prices.append(round(low_price, 2))
        prices.append(round(price, 2))
        volumes.append(volume)
    
    return {
        'dates': dates,
        'prices': prices,
        'close': prices,
        'volumes': volumes,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'success': True
    }

# Add a new endpoint to clear training errors
@app.route('/api/clear_training_error/<model_type>', methods=['POST'])
def clear_training_error(model_type):
    """Clear training error status for a model"""
    try:
        if not model_manager:
            return jsonify({'success': False, 'error': 'ModelManager not available'}), 500
            
        if model_type not in model_manager.model_types:
            return jsonify({'success': False, 'error': f'Invalid model type: {model_type}'}), 400
            
        # Clear the training progress error
        if hasattr(model_manager, 'training_progress') and model_type in model_manager.training_progress:
            model_manager.training_progress[model_type] = {
                'status': 'Neaktyvus',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'time_remaining': 'N/A',
                'metrics': {}
            }
            
        # Update model status
        if hasattr(model_manager, 'statuses') and model_type in model_manager.statuses:
            if model_manager.statuses[model_type]['status'] == 'Klaida':
                model_manager.statuses[model_type]['status'] = 'Neapmokytas'
                model_manager._save_model_status()
        
        logger.info(f"Cleared training error for model {model_type}")
        return jsonify({'success': True, 'message': 'Training error cleared'})
        
    except Exception as e:
        logger.error(f"Error clearing training error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# Add a health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'database': database_enabled,
            'model_manager': model_manager is not None,
            'tensorflow': 'tensorflow' in sys.modules
        }
    }
    return jsonify(health_status)

# Add startup completion logging
startup_time = time.time() - startup_start
logger.info(f"=== APPLICATION STARTUP COMPLETE in {startup_time:.2f} seconds ===")
logger.info(f"Database enabled: {database_enabled}")
logger.info(f"ModelManager available: {model_manager is not None}")
logger.info("Application ready to serve requests")

# Add main execution block with better error handling
if __name__ == '__main__':
    try:
        logger.info("Starting Flask development server...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to prevent double startup
        )
    except KeyboardInterrupt:
        logger.info("Application shutdown by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)