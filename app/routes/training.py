"""
Modelių treniravimo maršrutai
---------------------------
Šis modulis apibrėžia Flask routes treniravimo funkcijai.
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, send_file, flash
from app.services.model_service import ModelService
import os
import json
import uuid
from datetime import datetime
import logging
from tensorflow.keras import backend as K

# Sukuriame loggerį
logger = logging.getLogger(__name__)

# Sukuriame blueprint
training_bp = Blueprint('training', __name__, url_prefix='/training')

# Inicializuojame modelio servisą
model_service = ModelService()

@training_bp.route('/')
def index():
    """Pagrindinis modelių treniravimo puslapis"""
    return redirect(url_for('training.models'))

@training_bp.route('/models')
def models():
    """Modelių sąrašo puslapis"""
    # Gauname visus modelius
    all_models = model_service.get_all_models()
    return render_template('training/models.html', models=all_models)

@training_bp.route('/model/<filename>')
def model_details(filename):
    """Modelio detalių puslapis"""
    # Gauname modelio informaciją
    model = model_service.get_model_details(filename)
    if not model:
        return redirect(url_for('training.models'))
    
    return render_template('training/model_details.html', model=model)

@training_bp.route('/train', methods=['GET', 'POST'])
def train():
    """Modelio treniravimo puslapis ir forma"""
    if request.method == 'POST':
        # Gauname formos duomenis
        training_params = {
            'model_name': request.form.get('model_name', f'Model_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
            'model_type': request.form.get('model_type', 'LSTM'),
            'layers': int(request.form.get('layers', 2)),
            'units': int(request.form.get('units', 64)),
            'dropout': float(request.form.get('dropout', 0.2)),
            'epochs': int(request.form.get('epochs', 50)),
            'batch_size': int(request.form.get('batch_size', 32)),
            'learning_rate': float(request.form.get('learning_rate', 0.001)),
            'sequence_length': int(request.form.get('sequence_length', 60)),
            'prediction_days': int(request.form.get('prediction_days', 1)),
            'test_size': float(request.form.get('test_size', 0.2)),
            'normalization': bool(request.form.get('normalization', True))
        }
        
        # Generuojame unikalų ID treniravimo sesijai
        training_id = str(uuid.uuid4())
        
        # Inicijuojame treniravimo procesą
        model_service.start_training(training_id, training_params)
        
        # Nukreipiame į treniravimo stebėjimo puslapį
        return redirect(url_for('training.monitor_training', training_id=training_id))
    
    # GET metodo atveju rodome formą
    # Gauname naujausius modelius
    recent_models = model_service.get_all_models()[:5]
    
    # Jei yra retraining parametras, užpildome formą su esamo modelio parametrais
    retrain_filename = request.args.get('retrain')
    model_params = {}
    if retrain_filename:
        model = model_service.get_model_details(retrain_filename)
        if model:
            model_params = model.parameters
    
    return render_template('training/train_model.html', recent_models=recent_models, model_params=model_params)

@training_bp.route('/monitor/<training_id>')
def monitor_training(training_id):
    """Modelio treniravimo stebėjimo puslapis"""
    # Gauname treniravimo būseną
    training_status = model_service.get_training_status(training_id)
    
    if not training_status:
        return redirect(url_for('training.train'))
    
    # Perduodame parametrus į šabloną
    return render_template('training/monitor.html', 
                         training_id=training_id,
                         model_name=training_status['model_name'],
                         start_time=training_status['start_time'],
                         epochs=training_status['parameters']['epochs'],
                         model_type=training_status['parameters']['model_type'],
                         layers=training_status['parameters']['layers'],
                         units=training_status['parameters']['units'],
                         dropout=training_status['parameters']['dropout'],
                         batch_size=training_status['parameters']['batch_size'],
                         learning_rate=training_status['parameters']['learning_rate'],
                         sequence_length=training_status['parameters']['sequence_length'],
                         prediction_days=training_status['parameters']['prediction_days'])

# Pridėti naują maršrutą modelio architektūrai
@training_bp.route('/model/<filename>/architecture')
def model_architecture(filename):
    """Modelio architektūros vizualizavimo puslapis"""
    # Gauname modelio informaciją
    model = model_service.get_model_details(filename)
    if not model:
        flash('Modelis nerastas.', 'error')
        return redirect(url_for('training.models'))
    
    # Gauname modelio architektūros informaciją
    model_config = model_service.get_model_architecture(filename)
    if not model_config:
        flash('Nepavyko gauti modelio architektūros.', 'error')
        return redirect(url_for('training.model_details', filename=filename))
    
    return render_template(
        'training/model_architektūra.html', 
        model=model,
        model_config=model_config
    )

# Pridėti naują maršrutą modelių palyginimui
@training_bp.route('/compare', methods=['GET', 'POST'])
def compare_models():
    """
    Modelių palyginimo puslapis
    GET: Atvaizduoja modelių pasirinkimo formą
    POST: Apdoroja pasirinktų modelių palyginimą
    """
    # Gauname visus turimus modelius
    models = model_service.get_all_models()
    
    # Jei metodas yra POST, vykdome palyginimą
    if request.method == 'POST':
        # Gauname pasirinktų modelių ID
        model_ids = request.form.getlist('model_ids[]')
        
        # Patikriname, ar pasirinkti bent 2 modeliai
        if len(model_ids) < 2:
            flash('Prašome pasirinkti bent 2 modelius palyginimui!', 'danger')
            return render_template('training/compare_models.html', models=models)
        
        # Gauname datos intervalą ir kainos stulpelį
        date_range = int(request.form.get('date_range', 30))
        price_column = request.form.get('price_column', 'close')
        
        try:
            # Atliekame modelių palyginimą naudodami modelio servisą
            comparison_result = model_service.compare_models(
                model_ids=model_ids,
                days=date_range,
                price_column=price_column
            )
            
            # Apdorojame rezultatus formatas tinkantis šablonui
            return render_template(
                'training/compare_models.html',
                models=models,
                comparison_result=comparison_result
            )
            
        except Exception as e:
            flash(f'Klaida lyginant modelius: {str(e)}', 'danger')
            return render_template('training/compare_models.html', models=models)
    
    # Jei GET metodas, tiesiog rodome formą
    return render_template('training/compare_models.html', models=models)

@training_bp.route('/api/compare_models', methods=['POST'])
def api_compare_models():
    """API maršrutas modelių palyginimui"""
    data = request.json
    
    if not data or 'model_filenames' not in data:
        return jsonify({'success': False, 'message': 'Nenurodyti modelių failų pavadinimai'})
    
    # Gauname parametrus
    model_filenames = data.get('model_filenames', [])
    date_range = data.get('date_range', 'all')
    price_type = data.get('price_type', 'close')
    
    # Tikriname, ar turime bent du modelius
    if len(model_filenames) < 2:
        return jsonify({'success': False, 'message': 'Palyginimui reikia bent dviejų modelių'})
    
    # Lyginame modelius
    comparison_result = model_service.compare_models(model_filenames, date_range, price_type)
    
    if comparison_result:
        return jsonify({'success': True, 'models': comparison_result['models'], 'predictions': comparison_result['predictions']})
    else:
        return jsonify({'success': False, 'message': 'Nepavyko palyginti modelių'})

# API maršrutai

@training_bp.route('/api/training_status/<training_id>')
def api_training_status(training_id):
    """API maršrutas gauti treniravimo būseną"""
    status = model_service.get_training_status(training_id)
    if not status:
        return jsonify({'error': 'Treniravimo sesija nerasta'}), 404
    return jsonify(status)

@training_bp.route('/api/cancel_training', methods=['POST'])
def api_cancel_training():
    """API maršrutas atšaukti treniravimo procesą"""
    data = request.json
    training_id = data.get('training_id')
    
    if not training_id:
        return jsonify({'success': False, 'message': 'Nenurodytas treniravimo ID'}), 400
    
    success = model_service.cancel_training(training_id)
    return jsonify({'success': success, 'message': 'Treniravimas nutrauktas' if success else 'Klaida nutraukiant treniravimą'})

@training_bp.route('/api/delete_model', methods=['POST'])
def api_delete_model():
    """API maršrutas ištrinti modelį"""
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'message': 'Nenurodytas modelio failas'}), 400
    
    success = model_service.delete_model(filename)
    return jsonify({'success': success, 'message': 'Modelis ištrintas' if success else 'Klaida trinant modelį'})

@training_bp.route('/api/export_model/<filename>')
def api_export_model(filename):
    """API maršrutas eksportuoti modelį"""
    file_path = model_service.get_model_path(filename)
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'Modelis nerastas'}), 404
    
    return send_file(file_path, 
                    mimetype='application/octet-stream',
                    as_attachment=True,
                    download_name=f"{filename}")

# Pridėti naują maršrutą modelio svoriams
@training_bp.route('/model/<filename>/weights')
def model_weights(filename):
    """Modelio svorių ir histogramų vizualizavimo puslapis"""
    # Gauname modelio informaciją
    model = model_service.get_model_details(filename)
    if not model:
        return redirect(url_for('training.models'))
    
    # Gauname modelio svorių analizę
    weights_data = model_service.get_model_weights_analysis(filename)
    if not weights_data:
        flash('Nepavyko gauti modelio svorių informacijos.', 'error')
        return redirect(url_for('training.model_details', filename=filename))
    
    # Konvertuojame į JSON duomenims į JavaScript
    weights_data_json = json.dumps(weights_data)
    
    return render_template(
        'training/model_weights.html', 
        model=model, 
        weights_data=weights_data,
        weights_data_json=weights_data_json
    )

# Pridėti naują maršrutą treniravimo istorijai
@training_bp.route('/history')
def training_history():
    """Treniravimo istorijos puslapis"""
    # Gauname filtravimo parametrus iš URL
    filters = {}
    
    # Data nuo
    date_from = request.args.get('date_from')
    if date_from:
        filters['date_from'] = date_from
    
    # Data iki
    date_to = request.args.get('date_to')
    if date_to:
        filters['date_to'] = date_to
    
    # Modelio tipai (gali būti keli)
    model_types = request.args.getlist('model_types')
    if model_types:
        filters['model_types'] = model_types
    
    # Būsenos (gali būti kelios)
    statuses = request.args.getlist('statuses')
    if statuses:
        filters['statuses'] = statuses
    
    # Rikiavimo parametrai
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Gauname treniravimo istoriją
    history = model_service.get_training_history(filters, sort_by, sort_order)
    
    # Gauname statistiką
    statistics = model_service.get_training_statistics()
    
    return render_template(
        'training/training_history.html',
        history=history,
        statistics=statistics,
        filters={
            'date_from': date_from or '',
            'date_to': date_to or '',
            'model_types': model_types or [],
            'statuses': statuses or [],
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    )

# Pridėkime naujus maršrutus hiperparametrų optimizavimui

@training_bp.route('/optimization')
def optimization():
    """Hiperparametrų optimizavimo puslapis"""
    return render_template('training/optimization.html')

@training_bp.route('/optimization/start', methods=['POST'])
def start_optimization():
    """Pradeda hiperparametrų optimizavimą"""
    try:
        # Gauname duomenis iš užklausos
        data = request.json
        
        data_params = data.get('data_params', {})
        optimization_params = data.get('optimization_params', {})
        
        # Tikriname, ar pateikti reikalingi parametrai
        if not data_params.get('file_path'):
            return jsonify({'success': False, 'message': 'Nenurodyta duomenų rinkmena'})
        
        # Pradedame optimizavimą
        optimization_id = model_service.start_hyperparameter_optimization(
            data_params, optimization_params
        )
        
        if not optimization_id:
            return jsonify({'success': False, 'message': 'Nepavyko pradėti optimizavimo'})
        
        return jsonify({
            'success': True, 
            'message': 'Optimizavimas pradėtas', 
            'optimization_id': optimization_id
        })
    except Exception as e:
        logger.error(f"Klaida pradedant optimizavimą: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Įvyko klaida: {str(e)}'})

@training_bp.route('/optimization/status/<optimization_id>')
def optimization_status(optimization_id):
    """Gauna optimizavimo būsenos informaciją"""
    status = model_service.get_optimization_status(optimization_id)
    
    if not status:
        return jsonify({'success': False, 'message': 'Optimizavimo sesija nerasta'})
    
    return jsonify({'success': True, 'status': status})

@training_bp.route('/optimization/cancel', methods=['POST'])
def cancel_optimization():
    """Nutraukia optimizavimo procesą"""
    try:
        # Gauname duomenis iš užklausos
        data = request.json
        optimization_id = data.get('optimization_id')
        
        if not optimization_id:
            return jsonify({'success': False, 'message': 'Nenurodytas optimizavimo ID'})
        
        # Nutraukiame optimizavimą
        result = model_service.cancel_optimization(optimization_id)
        
        if not result:
            return jsonify({'success': False, 'message': 'Nepavyko nutraukti optimizavimo'})
        
        return jsonify({'success': True, 'message': 'Optimizavimas nutrauktas'})
    except Exception as e:
        logger.error(f"Klaida nutraukiant optimizavimą: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Įvyko klaida: {str(e)}'})

@training_bp.route('/optimize')
def optimize():
    """Hiperparametrų optimizavimo puslapis"""
    return render_template('training/optimize.html')

@training_bp.route('/optimization_monitor/<optimization_id>')
def optimization_monitor(optimization_id):
    """Optimizavimo stebėjimo puslapis"""
    # Gauname optimizavimo būseną
    optimization = model_service.get_optimization_status(optimization_id)
    
    if not optimization:
        flash('Optimizavimas nerastas.', 'error')
        return redirect(url_for('training.optimize'))
    
    return render_template('training/optimization_monitor.html', optimization=optimization)

# Pridėti naują maršrutą puslapiui
@training_bp.route('/model/<filename>/validation')
def model_validation(filename):
    """Modelio validavimo grafikas"""
    # Gauname modelio informaciją
    model = model_service.get_model_details(filename)
    if not model:
        flash('Modelis nerastas.', 'error')
        return redirect(url_for('training.models'))
    
    # Gauname validavimo duomenis
    validation_data = model_service.get_model_validation_data(filename)
    if not validation_data:
        flash('Nepavyko gauti validavimo duomenų.', 'error')
        return redirect(url_for('training.model_details', filename=filename))
    
    return render_template(
        'training/model_validation.html', 
        model=model,
        validation_metrics=validation_data['metrics']
    )

# Pridėti API maršrutą duomenims gauti
@training_bp.route('/api/model_validation/<filename>')
def api_model_validation(filename):
    """API maršrutas modelio validavimo duomenims gauti"""
    # Gauname validavimo duomenis
    validation_data = model_service.get_model_validation_data(filename)
    if not validation_data:
        return jsonify({'success': False, 'message': 'Nepavyko gauti validavimo duomenų.'})
    
    return jsonify({
        'success': True,
        'validation_data': validation_data['validation_data'],
        'metrics': validation_data['metrics']
    })

# Pridėti naują maršrutą tarpinių modelių peržiūrai
@training_bp.route('/checkpoints')
def checkpoints():
    """Tarpinių modelių peržiūros puslapis"""
    # Gauname filtravimo parametrus
    model_name = request.args.get('model_name', '')
    training_id = request.args.get('training_id', '')
    sort_by = request.args.get('sort_by', 'timestamp')
    
    # Gauname visus tarpinius modelius
    all_checkpoints = model_service.get_checkpoints()
    
    # Filtruojame pagal pavadinimą
    filtered_checkpoints = all_checkpoints
    if model_name:
        filtered_checkpoints = [c for c in filtered_checkpoints if model_name.lower() in c.get('model_name', '').lower()]
    
    # Filtruojame pagal treniravimo ID
    if training_id:
        filtered_checkpoints = [c for c in filtered_checkpoints if training_id in c.get('training_id', '')]
    
    # Rikiuojame
    if sort_by == 'val_loss':
        filtered_checkpoints.sort(key=lambda x: x.get('metrics', {}).get('val_loss', float('inf')))
    elif sort_by == 'val_mae':
        filtered_checkpoints.sort(key=lambda x: x.get('metrics', {}).get('val_mae', float('inf')))
    elif sort_by == 'epoch':
        filtered_checkpoints.sort(key=lambda x: x.get('epoch', 0), reverse=True)
    else:  # timestamp (default)
        filtered_checkpoints.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Perduodame duomenis į šabloną
    return render_template(
        'training/checkpoints.html',
        checkpoints=filtered_checkpoints,
        filter_params={
            'model_name': model_name,
            'training_id': training_id,
            'sort_by': sort_by
        },
        os=os  # Perduodame os modulį, kad gautume failo pavadinimą šablone
    )

# Pridėti API maršrutus tarpinių modelių valdymui
@training_bp.route('/api/delete_checkpoint', methods=['POST'])
def api_delete_checkpoint():
    """API maršrutas tarpinio modelio trynimui"""
    data = request.json
    
    if not data or 'checkpoint_filename' not in data:
        return jsonify({'success': False, 'message': 'Nenurodytas tarpinio modelio failo pavadinimas'})
    
    # Triname tarpinį modelį
    success = model_service.delete_checkpoint(data['checkpoint_filename'])
    
    if success:
        return jsonify({'success': True, 'message': 'Tarpinis modelis sėkmingai ištrintas'})
    else:
        return jsonify({'success': False, 'message': 'Klaida trinant tarpinį modelį'})

@training_bp.route('/api/continue_from_checkpoint', methods=['POST'])
def api_continue_from_checkpoint():
    """API maršrutas treniravimo pratęsimui nuo tarpinio modelio"""
    data = request.json
    
    if not data or 'checkpoint_filename' not in data or 'additional_epochs' not in data:
        return jsonify({'success': False, 'message': 'Nenurodyti visi reikalingi parametrai'})
    
    # Pratęsiame treniravimą
    training_id = model_service.continue_training_from_checkpoint(
        data['checkpoint_filename'],
        data['additional_epochs']
    )
    
    if training_id:
        return jsonify({'success': True, 'message': 'Treniravimas sėkmingai pratęstas', 'training_id': training_id})
    else:
        return jsonify({'success': False, 'message': 'Klaida pratęsiant treniravimą'})

# Importuojame reikiamas bibliotekas, jei jų dar nėra importuota
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services.model_service import model_service
import numpy as np
import json

# ... jau egzistuojantis kodas ...

@training_bp.route('/validation-graph', methods=['GET'])
def validation_graph():
    """
    Rodo modelio validavimo grafiką
    GET: Atvaizduoja modelio validavimo metrikas
    """
    # Gauname visus modelius
    models = model_service.get_all_models()
    
    # Gauname modelio ID iš URL parametro
    model_id = request.args.get('model_id')
    
    # Jei modelio ID neperduotas, rodome tik modelių sąrašą
    if not model_id:
        return render_template('training/validation_graph.html', models=models)
    
    try:
        # Gauname pasirinkto modelio informaciją
        selected_model = model_service.get_model_info(model_id)
        
        if not selected_model:
            flash('Nepavyko rasti modelio.', 'danger')
            return render_template('training/validation_graph.html', models=models)
        
        # Gauname modelio metrikas
        metrics = selected_model.get('metrics', {})
        
        # Patikriname, ar turime visas reikalingas metrikas
        required_metrics = ['loss', 'val_loss', 'mae', 'val_mae']
        for metric in required_metrics:
            if metric not in metrics or not metrics[metric]:
                metrics[metric] = [0.0]  # Numatytoji reikšmė, jei metrika neegzistuoja
        
        # Tikriname, ar buvo naudojamas ankstyvasis sustojimas (early stopping)
        early_stopping = None
        if 'early_stopping' in selected_model.get('parameters', {}):
            # Ieškome geriausio validavimo metrikų taško
            val_losses = metrics.get('val_loss', [])
            if val_losses:
                best_epoch = np.argmin(val_losses) + 1  # Epochos indeksas prasideda nuo 1
                patience = selected_model['parameters'].get('early_stopping', {}).get('patience', 5)
                
                early_stopping = {
                    'epoch': len(val_losses),
                    'best_epoch': best_epoch,
                    'best_value': val_losses[best_epoch - 1],
                    'patience': patience
                }
        
        # Perduodame duomenis į šabloną
        return render_template(
            'training/validation_graph.html',
            models=models,
            selected_model=selected_model,
            metrics=metrics,
            early_stopping=early_stopping
        )
        
    except Exception as e:
        flash(f'Klaida gaunant modelio validavimo metrikas: {str(e)}', 'danger')
        return render_template('training/validation_graph.html', models=models)

@training_bp.route('/api/model/<model_id>/metrics', methods=['GET'])
def get_model_metrics(model_id):
    """
    API kelias, grąžinantis modelio metrikas JSON formatu
    """
    try:
        # Gauname modelio informaciją
        model_info = model_service.get_model_info(model_id)
        
        if not model_info:
            return jsonify({'error': 'Modelis nerastas'}), 404
        
        # Gauname modelio metrikas
        metrics = model_info.get('metrics', {})
        
        # Patikriname, ar turime visas reikalingas metrikas
        required_metrics = ['loss', 'val_loss', 'mae', 'val_mae']
        for metric in required_metrics:
            if metric not in metrics or not metrics[metric]:
                metrics[metric] = [0.0]  # Numatytoji reikšmė, jei metrika neegzistuoja
        
        # Grąžiname duomenis
        return jsonify({
            'name': model_info.get('name', 'Nežinomas modelis'),
            'metrics': metrics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500