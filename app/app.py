"""
Bitcoin kainų prognozavimo web aplikacija

Ši aplikacija leidžia stebėti Bitcoin kainas, valdyti ir apmokyti prognozinius modelius
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import sys
import logging
import json
import requests
# Pakeisti datetime importą
import datetime as dt  # Importuojame modulį kitu pavadinimu
from datetime import datetime, timedelta  # Importuojame konkrečias klases
import random

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
# Pakeisti datetime importą
import datetime as dt  # Importuojame modulį kitu pavadinimu
from datetime import datetime, timedelta  # Importuojame konkrečias klases
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
    """
    Pagrindinis puslapis su kainos grafiku ir prognozėmis
    """
    try:
        logger.info("Užkraunamas pagrindinis puslapis")
        
        # Gauname dabartinę Bitcoin kainą
        current_price = get_real_bitcoin_price()
        if current_price is None:
            current_price = 45000.0  # Numatytoji reikšmė jei nepavyksta gauti realios kainos
            
        # Bandome gauti Bitcoin kainos istoriją iš API
        price_history = {}  # Vietoj None naudojame tuščią žodyną
        try:
            # Naudojame Binance API gauti istoriniams duomenims
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime={start_time}&endTime={end_time}"
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            
            if response.status_code == 200:
                klines = response.json()
                
                # Formuojame duomenis grafikai
                dates = []
                close_prices = []
                volumes = []
                
                for kline in klines:
                    # Binance kline formatas: [Open time, Open, High, Low, Close, Volume, ...]
                    date = datetime.fromtimestamp(kline[0]/1000).strftime('%Y-%m-%d')
                    close_price = float(kline[4])
                    volume = float(kline[5])
                    
                    dates.append(date)
                    close_prices.append(close_price)
                    volumes.append(volume)
                
                price_history = {
                    'dates': dates,
                    'close': close_prices,
                    'volume': volumes
                }
        except Exception as e:
            logger.error(f"Klaida gaunant istorinę kainą: {str(e)}")
            price_history = {}  # Vietoj None naudojame tuščią žodyną
        
        # Jei nepavyko gauti duomenų iš API, pabandome iš duomenų bazės
        if price_history is None and database_enabled:
            try:
                # Čia galima įdėti kodą duomenų gavimui iš DB
                logger.info("Bandoma gauti istorinę kainą iš duomenų bazės")
                # ...
            except Exception as e:
                logger.error(f"Klaida gaunant kainą iš duomenų bazės: {str(e)}")
                price_history = None
        
        # Gauname prognozes iš aktyvių modelių
        predictions = []
        if model_manager:
            try:
                # Čia pridėkite kodą, kuris iškviečia modelį prognozei
                # Pavyzdys: prediction = model_manager.predict('lstm', days=7)
                logger.info("Bandoma gauti prognozes iš modelių")
                # ...
            except Exception as e:
                logger.error(f"Klaida gaunant prognozes: {str(e)}")
        
        # Jei nepavyko gauti prognozių, sukurkite tuščią masyvą
        if not predictions:
            predictions = []
            
        # Apskaičiuojame kainos pokytį
        previous_price = None
        if price_history and len(price_history['close']) > 1:
            previous_price = price_history['close'][-2]
            
        price_change = calculate_price_change(current_price, previous_price)
        
        # Pridedame dabartinę datą
        now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Pagrindinis puslapis užkrautas. BTC kaina: {current_price}")
        
        # Grąžiname HTML šabloną
        return render_template('index.html', 
                              latest_price=current_price,
                              price_history=price_history,
                              predictions=predictions,
                              price_change=price_change,
                              now=now)
    except Exception as e:
        logger.error(f"Klaida index endpoint'e: {str(e)}")
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
        
        # Tikriname, ar yra modelių info
        for model_type in model_manager.model_types:
            # Gauname modelio būseną
            model_status = model_manager.get_model_status(model_type)
            
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
            model_configs[model_type] = model_manager.get_model_config(model_type)
        
        # Rendiname šabloną su duomenimis
        return render_template('models.html', 
                              models_info=models_info,
                              model_configs=model_configs)
    
    except Exception as e:
        logger.error(f"Klaida modelių puslapyje: {str(e)}", exc_info=True)
        flash(f"Klaida: {str(e)}", "error")
        return redirect('/')

@app.route('/train_model', methods=['POST'])
def train_model():
    """
    Apmoko pasirinktą modelį pagal pateiktą užklausą
    """
    try:
        # Gauname modelio tipą iš užklausos parametrų (arba nustatome numatytąjį)
        model_type = request.form.get('model_type', 'lstm')
        
        logger.info(f"Pradedamas modelio {model_type.upper()} apmokymas")
        
        # Jei turime ModelManager, naudojame jį
        if model_manager:
            # Pradėkite apmokymo procesą
            success = model_manager.train_model(model_type)
            
            if success:
                # Rodome sėkmės pranešimą vartotojui
                flash(f'Modelio {model_type.upper()} apmokymas pradėtas sėkmingai!', 'success')
            else:
                flash(f'Modelio {model_type.upper()} apmokymas jau vyksta arba įvyko klaida.', 'warning')
        else:
            # Jei ModelManager nerastas, pranešame apie klaidą
            logger.error(f"ModelManager nerastas, negalima pradėti apmokymo")
            flash(f'Klaida: ModelManager nepasiekiamas', 'error')
        
        # Nukreipiame atgal į modelių puslapį
        return redirect('/models')
    except Exception as e:
        logger.error(f"Klaida apmokant modelį: {str(e)}")
        
        # Rodome klaidos pranešimą vartotojui
        flash(f'Klaida apmokant modelį: {str(e)}', 'error')
        
        # Nukreipiame atgal į modelių puslapį
        return redirect('/models')

# Pridėkite naują maršrutą istorijos puslapiui
@app.route('/history')
def history_page():
    """
    Modelių istorijos peržiūros puslapis
    """
    try:
        # Tikriname, ar duomenų bazė inicializuota
        if not database_enabled:
            flash("Duomenų bazė nepasiekiama. Modelių istorija negalima.", "error")
            return redirect('/')
        
        # Filtravimo parametrai
        model_type = request.args.get('model_type', 'all')
        sort_by = request.args.get('sort_by', 'timestamp')
        
        # Užklausa
        query = ModelHistory.query
        
        # Filtruojame pagal modelio tipą, jei pateiktas
        if model_type != 'all':
            query = query.filter_by(model_type=model_type)
        
        # Rikiuojame pagal pasirinktą stulpelį
        if sort_by == 'mae':
            query = query.order_by(ModelHistory.mae)
        elif sort_by == 'rmse':
            query = query.order_by(ModelHistory.rmse)
        elif sort_by == 'r2':
            query = query.order_by(ModelHistory.r2.desc())
        else:  # Default - by timestamp
            query = query.order_by(ModelHistory.timestamp.desc())
        
        # Gauname įrašus
        records = query.all()
        
        # Gauname unikalius modelių tipus filtravimui
        model_types = db.session.query(ModelHistory.model_type).distinct().all()
        model_types = [m[0] for m in model_types]
        
        # Rendiname šabloną
        return render_template('history.html',
                              records=records,
                              model_types=model_types,
                              selected_type=model_type)
    except Exception as e:
        logger.error(f"Klaida istorijos puslapyje: {str(e)}", exc_info=True)
        flash(f"Klaida: {str(e)}", "error")
        return redirect('/')

# Pridėkite API endpoint'ą, skirtą išsaugoti modelio istoriją į duomenų bazę
@app.route('/api/save_model_history', methods=['POST'])
def save_model_history():
    """API endpoint modelio istorijos įrašo išsaugojimui į duomenų bazę"""
    try:
        # Tikriname, ar duomenų bazė inicializuota
        if not database_enabled:
            return jsonify({'success': False, 'error': 'Duomenų bazė nepasiekiama'}), 500
        
        # Gauname duomenis iš užklausos
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Nepateikti duomenys'}), 400
        
        # Sukuriame naują istorijos įrašą
        history_entry = ModelHistory(
            model_type=data.get('model_type'),
            training_time=data.get('training_time'),
            epochs=data.get('epochs'),
            batch_size=data.get('batch_size'),
            learning_rate=data.get('learning_rate'),
            lookback=data.get('lookback'),
            layers=str(data.get('layers')),
            mae=data.get('metrics', {}).get('mae'),
            mse=data.get('metrics', {}).get('mse'),
            rmse=data.get('metrics', {}).get('rmse'),
            r2=data.get('metrics', {}).get('r2'),
            is_active=data.get('is_active', False),
            notes=data.get('notes'),
            dropout=data.get('parameters', {}).get('dropout'),
            recurrent_dropout=data.get('parameters', {}).get('recurrent_dropout'),
            num_heads=data.get('parameters', {}).get('num_heads'),
            d_model=data.get('parameters', {}).get('d_model'),
            filters=str(data.get('parameters', {}).get('filters')),
            kernel_size=str(data.get('parameters', {}).get('kernel_size')),
            validation_split=data.get('parameters', {}).get('validation_split')
        )
        
        # Pažymime kaip neaktyvius visus to tipo modelius
        if data.get('is_active', False):
            ModelHistory.query.filter_by(model_type=data.get('model_type')).update({'is_active': False})
        
        # Išsaugome į duomenų bazę
        db.session.add(history_entry)
        db.session.commit()
        
        # Grąžiname sėkmės atsakymą
        return jsonify({
            'success': True,
            'message': 'Modelio istorijos įrašas išsaugotas',
            'id': history_entry.id
        })
    except Exception as e:
        logger.error(f"Klaida išsaugant modelio istoriją: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# Pridėkite API endpoint'ą, skirtą aktyvuoti modelį duomenų bazėje
@app.route('/api/activate_model/<int:model_id>', methods=['POST'])
def activate_db_model(model_id):
    """API endpoint modelio aktyvavimui duomenų bazėje"""
    try:
        # Tikriname, ar duomenų bazė inicializuota
        if not database_enabled:
            return jsonify({'success': False, 'error': 'Duomenų bazė nepasiekiama'}), 500
        
        # Randam modelį pagal ID
        model = ModelHistory.query.get(model_id)
        if not model:
            return jsonify({'success': False, 'error': 'Modelis nerastas'}), 404
        
        # Pažymime visus to tipo modelius kaip neaktyvius
        ModelHistory.query.filter_by(model_type=model.model_type).update({'is_active': False})
        
        # Nustatome pasirinktą modelį kaip aktyvų
        model.is_active = True
        db.session.commit()
        
        # Atnaujinkime ir ModelManager'io statusą, jei jis egzistuoja
        if model_manager:
            model_status = model_manager.get_model_status(model.model_type)
            model_status['status'] = 'Aktyvus'
            model_status['last_trained'] = model.timestamp.strftime('%Y-%m-%d %H:%M:%S') if model.timestamp else 'Unknown'
            model_status['performance'] = f"MAE: {model.mae:.4f}" if model.mae else 'Nežinoma'
            model_status['active_model_id'] = model.id
            model_manager._save_model_status()
        
        return jsonify({'success': True, 'message': 'Modelis sėkmingai aktyvuotas'})
    except Exception as e:
        logger.error(f"Klaida aktyvuojant modelį: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete_db_model/<int:model_id>', methods=['DELETE'])
def delete_db_model(model_id):
    """API endpoint modelio ištrynimui iš duomenų bazės"""
    try:
        # Tikriname, ar duomenų bazė inicializuota
        if not database_enabled:
            return jsonify({'success': False, 'error': 'Duomenų bazė nepasiekiama'}), 500
        
        # Randam modelį pagal ID
        model = ModelHistory.query.get(model_id)
        if not model:
            return jsonify({'success': False, 'error': 'Modelis nerastas'}), 404
        
        # Išsaugome modelio tipą, jei reikės atnaujinti ModelManager
        model_type = model.model_type
        is_active = model.is_active
        
        # Ištriname modelį
        db.session.delete(model)
        db.session.commit()
        
        # Jei modelis buvo aktyvus, atnaujinkime ModelManager statusą
        if is_active and model_manager:
            model_status = model_manager.get_model_status(model_type)
            model_status['status'] = 'Neaktyvus'
            model_status['active_model_id'] = None
            model_manager._save_model_status()
        
        return jsonify({'success': True, 'message': 'Modelis sėkmingai ištrintas'})
    except Exception as e:
        logger.error(f"Klaida trinant modelį: {str(e)}", exc_info=True)
        # Atšaukiame transakcijos pakeitimus jei įvyko klaida
        if database_enabled:
            db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

def get_real_bitcoin_price():
    """
    Gauna realaus laiko Bitcoin kainą iš Binance API
    
    Returns:
        float: Dabartinė Bitcoin kaina
    """
    try:
        # Naudojame Binance API
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"Klaida gaunant Bitcoin kainą: {response.status_code}")
            return None
        
        data = response.json()
        if 'price' in data:
            return float(data['price'])
        else:
            logger.error(f"Netikėtas API atsakymo formatas: {data}")
            return None
    except Exception as e:
        logger.error(f"Klaida gaunant Bitcoin kainą: {str(e)}")
        return None

def calculate_price_change(current_price, previous_price):
    """
    Apskaičiuoja kainos pokytį ir grąžina duomenis apie jį
    """
    if not previous_price:
        return {
            'value': 0,
            'percent': 0,
            'direction': 'neutral'
        }
    
    # Apskaičiuojame pokytį
    change = current_price - previous_price
    percent_change = (change / previous_price) * 100
    
    # Nustatome krypties spalvą
    direction = 'up' if change > 0 else 'down' if change < 0 else 'neutral'
    
    return {
        'value': change,
        'percent': percent_change,
        'direction': direction
    }

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

@app.route('/predict')
def predict_page():
    """
    Bitcoin kainos prognozavimo puslapis
    """
    try:
        logger.info("Užkraunamas prognozavimo puslapis")
        
        # Gauname dabartinę kainą
        latest_price = None
        try:
            latest_price = get_real_bitcoin_price()
            if latest_price is None:
                latest_price = 45000.0
        except Exception as e:
            logger.error(f"Klaida gaunant kainą: {str(e)}")
            latest_price = 45000.0
        
        # SVARBU: tikriname ar model_manager egzistuoja
        if model_manager is None:
            logger.error("ModelManager nėra inicializuotas - negalima generuoti prognozių")
            return render_template('predict.html',
                active_menu='predict',
                predictions=[],
                active_models=[],
                selected_models=[],
                forecast_days=7,
                error_message="ModelManager neegzistuoja - prognozės negalimos",
                latest_price=latest_price,
                now=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        
        # Gauname aktyvius modelius
        active_models = []
        for model_type in model_manager.model_types:
            status = model_manager.get_model_status(model_type)
            if status.get('status') == 'Aktyvus':
                active_models.append({
                    'type': model_type,
                    'name': model_type.upper(),
                    'status': status
                })
        
        logger.info(f"Aktyvių modelių: {len(active_models)}")
        
        # Tikriname, ar vartotojas prašo prognozių
        predict = request.args.get('predict', 'false').lower() == 'true'
        
        # Modeliai, kuriuos vartotojas nori naudoti prognozei
        selected_models = request.args.getlist('models')
        logger.info(f"Pasirinkti modeliai: {selected_models}")
        
        # Dienų skaičius, kuriam prognozuoti
        forecast_days = int(request.args.get('days', 7))
        
        # Ar rodyti prognozes
        show_predictions = predict and (selected_models or active_models)
        logger.info(f"show_predictions: {show_predictions}")
        
        # Prognozių sąrašas
        predictions = []
        
        # Nurodome klaidos pranešimą
        error_message = None
        
        # Prognozavimo dalis
        if active_models and show_predictions:
            try:
                # Nusprendžiame, kuriuos modelius naudoti
                models_to_use = selected_models if selected_models else [m['type'] for m in active_models]
                logger.info(f"Bandoma generuoti prognozes su modeliais: {models_to_use}")
                
                # Gauname prognozes iš kiekvieno pasirinkto modelio
                for model_type in models_to_use:
                    logger.info(f"Bandoma gauti prognozę iš modelio {model_type}")
                    
                    # Jei ModelManager nėra None ir tipas palaikomas - generuojame prognozę
                    if model_manager and model_type in model_manager.model_types:
                        prediction_data = model_manager.predict(model_type, days=forecast_days)
                        if prediction_data:
                            predictions.append(prediction_data)
                            logger.info(f"Prognozė {len(predictions)}: modelis={prediction_data['model']}, {len(prediction_data['values'])} reikšmės")
                        else:
                            logger.warning(f"Modelio {model_type} prognozė grąžino None")
                    else:
                        logger.warning(f"Modelis {model_type} nėra prieinamas ModelManager'yje")
                        
                        # Generuojame atsarginę prognozę
                        if model_manager:
                            fallback = model_manager._generate_fallback_prediction(model_type, forecast_days)
                            predictions.append(fallback)
                            logger.info(f"Sugeneruota atsarginė prognozė modeliui {model_type}")
                        else:
                            # ModelManager neegzistuoja - generuojame prognozę su fiksuotais duomenimis
                            from datetime import datetime, timedelta
                            import random
                            
                            # Dabartinė kaina
                            current_price = 45000.0
                            try:
                                current_price = get_real_bitcoin_price()
                                if current_price is None:
                                    current_price = 45000.0
                            except:
                                pass
                            
                            # Generuojame datas ir kainas
                            dates = [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(forecast_days)]
                            values = [float(current_price)]
                            for i in range(1, forecast_days):
                                values.append(float(values[-1] * (1 + random.uniform(-0.01, 0.02))))
                            
                            # Pridedame prognozę
                            predictions.append({
                                'model': model_type.upper(),
                                'days': forecast_days,
                                'values': values,
                                'dates': dates,
                                'accuracy': 'ModelManager neegzistuoja'
                            })
                            logger.info(f"Sugeneruota atsarginė prognozė (ModelManager neegzistuoja) modeliui {model_type}")
                
                # Geras debugging prieš render_template
                logger.info("=== PROGNOZIŲ DUOMENYS ===")
                for i, pred in enumerate(predictions):
                    logger.info(f"Prognozė #{i} ({pred.get('model', 'nežinomas')}):")
                    logger.info(f"   - Values tipo: {type(pred.get('values', None))}")
                    logger.info(f"   - Values: {pred.get('values', [])[:3]}... (viso: {len(pred.get('values', []))})")
                    logger.info(f"   - Dates tipo: {type(pred.get('dates', None))}")
                    logger.info(f"   - Dates: {pred.get('dates', [])[:3]}... (viso: {len(pred.get('dates', []))})")
                logger.info("=========================")
                
            except Exception as e:
                logger.error(f"Klaida generuojant prognozes: {str(e)}", exc_info=True)
                error_message = f"Klaida generuojant prognozes: {str(e)}"
        else:
            logger.warning(f"Prognozės negeneruojamos: active_models={bool(active_models)}, show_predictions={show_predictions}")
        
        # Prieš render_template, išspausdinkime detalų debugging:
        for pred in predictions:
            logger.info(f"Modelis: {pred.get('model', 'nežinomas')}")
            logger.info(f"Datos: {pred.get('dates', [])[0:3]}... (viso: {len(pred.get('dates', []))})")
            logger.info(f"Reikšmės: {pred.get('values', [])[0:3]}... (viso: {len(pred.get('values', []))})")

        # Gauname istorinę kainos informaciją
        try:
            price_history = get_bitcoin_price_history(30)  # 30 dienų
            if not price_history or not isinstance(price_history, dict):
                logger.warning("Gauti netinkami price_history duomenys, naudojame tuščią objektą")
                price_history = {"dates": [], "prices": [], "close": [], "volumes": []}
            
            # Clean and validate price_history data for JSON serialization
            def clean_data_for_json(data):
                """Clean data to ensure it's JSON serializable"""
                if isinstance(data, dict):
                    cleaned = {}
                    for key, value in data.items():
                        cleaned[key] = clean_data_for_json(value)
                    return cleaned
                elif isinstance(data, list):
                    return [clean_data_for_json(item) for item in data]
                elif isinstance(data, (int, float)):
                    # Handle NaN and infinity values
                    if str(data).lower() in ['nan', 'inf', '-inf']:
                        return 0
                    return data
                elif isinstance(data, str):
                    # Escape any problematic characters
                    return data.replace('"', '\\"').replace("'", "\\'")
                else:
                    return data
            
            price_history = clean_data_for_json(price_history)
            
            # Ensure consistent structure - use 'close' as the main price field
            if "dates" not in price_history:
                price_history["dates"] = []
            if "prices" in price_history and "close" not in price_history:
                price_history["close"] = price_history["prices"]
            elif "close" in price_history and "prices" not in price_history:
                price_history["prices"] = price_history["close"]
            
            # Ensure we have both fields for compatibility
            if "prices" not in price_history:
                price_history["prices"] = []
            if "close" not in price_history:
                price_history["close"] = []
            
            logger.info(f"price_history final: {len(price_history.get('dates', []))} dates, {len(price_history.get('prices', []))} prices, {len(price_history.get('close', []))} close")
        except Exception as e:
            logger.error(f"Klaida gaunant kainos istoriją: {str(e)}")
            price_history = {"dates": [], "prices": [], "close": [], "volumes": []}
        
        # Clean predictions data for JSON serialization
        if predictions:
            try:
                # Clean predictions data
                cleaned_predictions = []
                for pred in predictions:
                    if isinstance(pred, dict):
                        cleaned_pred = {}
                        for key, value in pred.items():
                            if key == 'values' and isinstance(value, list):
                                # Ensure all values are valid numbers
                                cleaned_values = []
                                for v in value:
                                    try:
                                        num_val = float(v)
                                        if str(num_val).lower() in ['nan', 'inf', '-inf']:
                                            cleaned_values.append(0.0)
                                        else:
                                            cleaned_values.append(num_val)
                                    except (ValueError, TypeError):
                                        cleaned_values.append(0.0)
                                cleaned_pred[key] = cleaned_values
                            elif key == 'dates' and isinstance(value, list):
                                # Ensure dates are strings
                                cleaned_pred[key] = [str(d) for d in value]
                            elif key == 'model':
                                # Ensure model name is a clean string
                                cleaned_pred[key] = str(value).replace('"', '\\"').replace("'", "\\'")
                            else:
                                cleaned_pred[key] = value
                        cleaned_predictions.append(cleaned_pred)
                predictions = cleaned_predictions
                logger.info(f"Cleaned {len(predictions)} predictions for JSON serialization")
            except Exception as e:
                logger.error(f"Error cleaning predictions data: {str(e)}")
                predictions = []
        
        # Įsitikinkite, kad šablonui yra perduodami tinkami kintamieji
        return render_template('predict.html',
            active_menu='predict',
            show_predictions=True,
            predictions=predictions,
            active_models=active_models,
            selected_models=selected_models,
            forecast_days=forecast_days,
            error_message=error_message,
            latest_price=latest_price,
            price_history=price_history,
            now=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    except Exception as e:
        logger.error(f"Klaida prognozavimo puslapyje: {str(e)}", exc_info=True)
        # Grąžiname šabloną su klaidos pranešimu
        return render_template('predict.html',
            active_menu='predict',
            predictions=[],
            active_models=[],
            selected_models=[],
            forecast_days=7,
            error_message=f"Klaida: {str(e)}",
            latest_price=45000.0,
            price_history={"dates": [], "prices": [], "close": [], "volumes": []},
            now=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

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

def get_bitcoin_price_history(days=30):
    """
    Gauna tikslią Bitcoin kainos istoriją tiesiai iš Binance API
    
    Args:
        days (int): Dienų skaičius
        
    Returns:
        dict: Kainos istorija su formatuotais duomenimis
    """
    try:
        logger.info(f"Fetching Bitcoin price history for {days} days from Binance")
        
        # Tiesiogiai gauname duomenis iš Binance API
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime={start_time}&endTime={end_time}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Klaida Binance API užklausoje: {response.status_code}")
            # Return mock data instead of None
            return generate_mock_bitcoin_data(days)
            
        klines = response.json()
        
        if not klines:
            logger.warning("Empty response from Binance API")
            return generate_mock_bitcoin_data(days)
        
        # Formuojame duomenis grafikui
        dates = []
        prices = []
        volumes = []
        open_prices = []
        high_prices = []
        low_prices = []
        
        for kline in klines:
            # Binance kline formatas: [Open time, Open, High, Low, Close, Volume, ...]
            date = datetime.fromtimestamp(kline[0]/1000).strftime('%Y-%m-%d')
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
        
        logger.info(f"Successfully processed {len(dates)} price data points")
        
        # Grąžiname formatuotus duomenis
        return {
            'dates': dates,
            'prices': prices,
            'close': prices,  # Add close field for compatibility
            'volumes': volumes,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Klaida gaunant Bitcoin kainos istoriją: {str(e)}", exc_info=True)
        # Return mock data instead of None
        return generate_mock_bitcoin_data(days)

def generate_mock_bitcoin_data(days=30):
    """Generate mock Bitcoin data when API fails"""
    logger.info(f"Generating mock Bitcoin data for {days} days")
    
    dates = []
    prices = []
    volumes = []
    open_prices = []
    high_prices = []
    low_prices = []
    
    current_price = 45000
    
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Add some random variation
        current_price *= (1 + (random.random() - 0.5) * 0.02)
        
        open_price = current_price * (1 + (random.random() - 0.5) * 0.005)
        high_price = current_price * (1 + random.random() * 0.01)
        low_price = current_price * (1 - random.random() * 0.01)
        close_price = current_price
        volume = random.randint(1000, 10000)
        
        dates.append(date)
        open_prices.append(round(open_price, 2))
        high_prices.append(round(high_price, 2))
        low_prices.append(round(low_price, 2))
        prices.append(round(close_price, 2))
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

# ...existing code...
# Paleidimo kodas
if __name__ == '__main__':
    # Paleiskite aplikaciją režimu debug=True, kad matytumėte klaidas
    app.run(debug=True, host='0.0.0.0')