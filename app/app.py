"""
Bitcoin kainų prognozavimo web aplikacija

Ši aplikacija leidžia stebėti Bitcoin kainas, valdyti ir apmokyti prognozinius modelius
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import sys
import logging
import numpy as np
import json
import requests
from datetime import datetime, timedelta
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

# Įtraukiame direktoriją į importo kelius
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importuojame ModelManager
try:
    from model_manager import ModelManager
    
    # Nustatome modelių direktoriją
    models_dir = os.path.join(current_dir, 'models')
    
    # Sukuriame direktoriją, jei ji neegzistuoja
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"Sukurta modelių direktorija: {models_dir}")
    
    # Sukuriame ModelManager objektą
    model_manager = ModelManager(models_dir=models_dir)
    logger.info("ModelManager sėkmingai inicializuotas")
except Exception as e:
    logger.error(f"Klaida inicializuojant ModelManager: {str(e)}")
    model_manager = None

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
        
        if model_manager:
            success = model_manager.delete_model_history(model_type, model_id)
            if success:
                return jsonify({'success': True, 'message': 'Modelio įrašas ištrintas'})
        
        return jsonify({'success': False, 'error': 'Nepavyko ištrinti modelio įrašo'}), 500
    except Exception as e:
        app.logger.error(f"Klaida trinant modelio {model_type} įrašą (ID: {model_id}): {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/use_model/<model_type>/<model_id>', methods=['POST'])
def use_model(model_type, model_id):
    """API endpoint modelio aktyvavimui"""
    try:
        app.logger.info(f"Bandoma aktyvuoti modelį {model_type} (ID: {model_id})")
        
        if model_manager:
            success = model_manager.activate_model(model_type, model_id)
            if success:
                return jsonify({'success': True, 'message': 'Modelis aktyvuotas'})
        
        return jsonify({'success': False, 'error': 'Nepavyko aktyvuoti modelio'}), 500
    except Exception as e:
        app.logger.error(f"Klaida aktyvuojant modelį {model_type} (ID: {model_id}): {str(e)}")
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
        price_history = None
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
            else:
                logger.error(f"Klaida gaunant istorinę kainą: {response.status_code}")
                price_history = None
        except Exception as e:
            logger.error(f"Klaida gaunant istorinę kainą: {str(e)}")
            price_history = None
        
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
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

def get_real_bitcoin_price():
    """
    Gauna realią Bitcoin kainą iš Binance API
    """
    try:
        # Naudojame Binance API
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', 
                               headers={'User-Agent': 'Mozilla/5.0'}, 
                               timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current_price = float(data['price'])
            return current_price
        else:
            logger.error(f"Klaida gaunant Bitcoin kainą: {response.status_code}")
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

# Paleidimo kodas
if __name__ == '__main__':
    # Paleiskite aplikaciją režimu debug=True, kad matytumėte klaidas
    app.run(debug=True, host='0.0.0.0')