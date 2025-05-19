from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, make_response
import datetime
import os
import json
import csv
from io import StringIO
from flask import Response

from app.services.model_architecture_service import ModelArchitectureService
from app.models.model_metrics import ModelMetrics
from app.utils.generate_sample_metrics import add_sample_models
from app.services.model_weights_service import ModelWeightsService
from app.services.training_history_service import TrainingHistoryService
from app.services.hyperparameter_optimization_service import HyperparameterOptimizationService
from app.services.checkpoint_service import CheckpointService

# SVARBU: kitas pavadinimas blueprint'ui!
model_training = Blueprint('model_training', __name__)

# Sukuriame modelio architektūros serviso objektą
model_architecture_service = ModelArchitectureService()
metrics = ModelMetrics()

# Sukuriame modelio svorių serviso objektą
weights_service = ModelWeightsService()

# Sukuriame treniravimo istorijos serviso objektą
history_service = TrainingHistoryService()

# Inicializuojame hiperparametrų optimizavimo paslaugą globaliai
optimization_service = HyperparameterOptimizationService()

@model_training.route('/')
@model_training.route('/index')
def index():
    """
    Pagrindinis treniravimo puslapis
    """
    return render_template('training/index.html', title='Modelio treniravimas')

@model_training.route('/train')
def train():
    """
    Modelio treniravimo puslapis
    """
    return render_template('training/train.html', title='Treniruoti modelį')

@model_training.route('/monitor')
def monitor():
    """
    Treniravimo progreso stebėjimo puslapis
    """
    return render_template('training/monitor.html', title='Stebėti treniravimą')

@model_training.route('/optimize')
def optimize():
    """
    Hiperparametrų optimizavimo puslapis
    """
    return render_template('training/optimize.html', title='Hiperparametrų optimizavimas')

@model_training.route('/history')
def view_history():
    """
    Treniravimo istorijos peržiūros puslapis
    """
    return render_template('training/history.html', title='Treniravimo istorija')

@model_training.route('/checkpoints')
def checkpoints():
    """
    Tarpinių modelių išsaugojimų puslapis
    """
    return render_template('training/checkpoints.html', title='Tarpiniai išsaugojimai')

@model_training.route('/compare_models', methods=['GET'])
def compare_models():
    """
    Atvaizduoja modelių palyginimo puslapį
    """
    # Įsitikiname, kad turime pavyzdinius modelius
    add_sample_models()
    
    # Gauname visus modelius
    models = metrics.get_all_models()
    
    return render_template('training/compare_models.html', 
                          title='Modelių palyginimas',
                          models=models)

@model_training.route('/model_architectures', methods=['GET'])
def model_architectures():
    """
    Atvaizduoja modelių architektūros vizualizacijos puslapį 
    su visų prieinamų modelių sąrašu
    """
    # Gauname visų prieinamų modelių sąrašą
    available_models = model_architecture_service.get_available_models()
    
    # Rodome šabloną su modelių sąrašu
    return render_template('training/model_architectures.html', 
                         title='Modelio architektūra',
                         available_models=available_models)

@model_training.route('/model_architectures/<model_name>', methods=['GET'])
def model_architecture_details(model_name):
    """
    Atvaizduoja konkretaus modelio architektūros detalią informaciją
    
    Args:
        model_name (str): Modelio failo pavadinimas
    """
    # Gauname modelio architektūros informaciją
    model_info = model_architecture_service.load_model_architecture(model_name)
    
    # Gauname modelio vizualizaciją
    model_visualization = model_architecture_service.generate_model_visualization(model_name)
    
    # Rodome detalų šabloną su modelio informacija
    return render_template('training/model_architecture_details.html', 
                         title='Modelio architektūros detalės',
                         model_info=model_info,
                         model_visualization=model_visualization,
                         model_name=model_name)

@model_training.route('/model_architecture/export/<model_name>/<format>', methods=['GET'])
def export_model_architecture(model_name, format):
    """
    Eksportuoja modelio architektūros vizualizaciją nurodytu formatu
    
    Args:
        model_name (str): Modelio failo pavadinimas
        format (str): Eksporto formatas (png arba svg)
    """
    # Tikriname ar formatas yra leistinas
    if format not in ['png', 'svg']:
        return jsonify({'error': 'Nepalaikomas formatas. Naudokite png arba svg'}), 400
    
    # Eksportuojame modelio vizualizaciją
    filename, binary_data = model_architecture_service.export_as_image(model_name, format)
    
    # Tikriname ar įvyko klaida
    if isinstance(binary_data, dict) and 'error' in binary_data:
        return jsonify(binary_data), 500
    
    # Sukuriame atsakymą su failu
    response = make_response(binary_data)
    response.headers.set('Content-Type', f'image/{format}')
    response.headers.set('Content-Disposition', f'attachment; filename={filename}')
    
    return response

@model_training.route('/validation_graph')
def validation_graph():
    """
    Validavimo grafiko puslapis
    """
    return render_template('training/validation_graph.html', title='Validavimo grafikas')

@model_training.route('/model_weights', methods=['GET'])
def model_weights():
    """
    Atvaizduoja modelių svorių puslapį
    """
    # Gauname visus modelius
    available_models = weights_service.get_available_models()
    
    return render_template('training/model_weights.html', 
                          title='Modelio svoriai',
                          available_models=available_models)

@model_training.route('/model_weights/<model_name>', methods=['GET'])
def model_weights_details(model_name):
    """
    Atvaizduoja modelio svorių detalų puslapį
    
    Args:
        model_name (str): Modelio failo pavadinimas
    """
    # Gauname modelio sluoksnių informaciją
    layers_info = weights_service.get_model_layers(model_name)
    
    # Jei įvyko klaida, grąžiname į sąrašą su klaidos pranešimu
    if isinstance(layers_info, dict) and 'error' in layers_info:
        flash(layers_info['error'], 'danger')
        return redirect(url_for('model_training.model_weights'))
    
    return render_template('training/model_weights_details.html',
                          title=f'Modelio {model_name} svoriai',
                          model_name=model_name,
                          layers_info=layers_info)

@model_training.route('/api/model_weights/histogram', methods=['GET'])
def get_weights_histogram():
    """
    Grąžina svorių histogramą
    """
    # Gauname parametrus iš URL
    model_name = request.args.get('model_name')
    layer_index = int(request.args.get('layer_index', 0))
    weight_index = int(request.args.get('weight_index', 0))
    
    # Tikrinama ar parametrai perduoti
    if not model_name:
        return jsonify({'error': 'Nenurodytas modelio pavadinimas'}), 400
    
    # Gauname histogramą
    histogram = weights_service.generate_weights_histogram(model_name, layer_index, weight_index)
    
    # Tikriname ar įvyko klaida
    if isinstance(histogram, dict) and 'error' in histogram:
        return jsonify(histogram), 400
    
    # Grąžiname histogramos paveikslėlį
    return jsonify({'histogram': histogram})

@model_training.route('/api/model_weights/activations', methods=['GET'])
def get_activations_heatmap():
    """
    Grąžina aktyvacijų šilumos žemėlapį
    """
    # Gauname parametrus iš URL
    model_name = request.args.get('model_name')
    layer_index = int(request.args.get('layer_index', 0))
    
    # Tikrinama ar parametrai perduoti
    if not model_name:
        return jsonify({'error': 'Nenurodytas modelio pavadinimas'}), 400
    
    # Gauname aktyvacijų žemėlapį
    heatmap = weights_service.generate_activations_heatmap(model_name, layer_index)
    
    # Tikriname ar įvyko klaida
    if isinstance(heatmap, dict) and 'error' in heatmap:
        return jsonify(heatmap), 400
    
    # Grąžiname aktyvacijų žemėlapį
    return jsonify({'heatmap': heatmap})

@model_training.route('/api/model_weights/analysis', methods=['GET'])
def get_weights_analysis():
    """
    Grąžina svorių analizės rezultatus
    """
    # Gauname parametrus iš URL
    model_name = request.args.get('model_name')
    layer_index = int(request.args.get('layer_index', 0))
    weight_index = int(request.args.get('weight_index', 0))
    
    # Tikrinama ar parametrai perduoti
    if not model_name:
        return jsonify({'error': 'Nenurodytas modelio pavadinimas'}), 400
    
    # Gauname svorių analizę
    analysis = weights_service.analyze_weights(model_name, layer_index, weight_index)
    
    # Tikriname ar įvyko klaida
    if isinstance(analysis, dict) and 'error' in analysis:
        return jsonify(analysis), 400
    
    # Grąžiname analizės rezultatus
    return jsonify(analysis)

@model_training.route('/compare_models/get', methods=['POST'])
def get_models_for_comparison():
    """
    Grąžina modelius, kuriuos reikia palyginti
    """
    # Gauname modelių ID iš POST duomenų
    data = request.get_json()
    model_ids = data.get('model_ids', [])
    
    # Kiekvieno modelio duomenys
    result = []
    
    # Gauname kiekvieno modelio informaciją
    for model_id in model_ids:
        model = metrics.get_model(int(model_id))
        if model:
            result.append(model)
    
    return jsonify(result)

@model_training.route('/compare_models/export_csv', methods=['POST'])
def export_models_csv():
    """
    Eksportuoja modelių duomenis CSV formatu
    """
    # Gauname modelių ID iš POST duomenų
    data = request.get_json()
    model_ids = data.get('model_ids', [])
    
    # Jei nėra modelių, grąžiname klaidą
    if not model_ids:
        return jsonify({'error': 'Nenurodyti modeliai eksportavimui'}), 400
    
    # Modelių duomenys
    models = []
    
    # Gauname kiekvieno modelio informaciją
    for model_id in model_ids:
        model = metrics.get_model(int(model_id))
        if model:
            models.append(model)
    
    # Jei nėra modelių, grąžiname klaidą
    if not models:
        return jsonify({'error': 'Nerasta modelių su nurodytais ID'}), 404
    
    # CSV antraštės
    headers = ['model_id', 'model_name', 'date_created', 'accuracy', 'loss', 
              'val_accuracy', 'val_loss', 'epochs', 'description']
    
    # Sukuriame CSV failą StringIO objekte
    import io
    import csv
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    
    # Įrašome antraštę
    writer.writerow(headers)
    
    # Įrašome modelių duomenis
    for model in models:
        writer.writerow([
            model.get('model_id', ''),
            model.get('model_name', ''),
            model.get('date_created', ''),
            model.get('accuracy', ''),
            model.get('loss', ''),
            model.get('val_accuracy', ''),
            model.get('val_loss', ''),
            model.get('epochs', ''),
            model.get('description', '')
        ])
    
    # Grąžiname CSV failą
    response = make_response(csv_data.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=model_comparison.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

@model_training.route('/history')
def history():
    """
    Treniravimo sesijų istorijos puslapis
    """
    # Gauname filtravimo parametrus iš URL
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    date_range = request.args.get('date_range', '')
    
    # Nustatome datų filtrus pagal pasirinktą laikotarpį
    date_from = None
    date_to = None
    
    if date_range == 'today':
        date_from = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'week':
        date_from = datetime.datetime.now() - datetime.timedelta(days=7)
    elif date_range == 'month':
        date_from = datetime.datetime.now() - datetime.timedelta(days=30)
    
    # Filtruojame sesijas
    sessions = history_service.get_filtered_sessions(keyword, status, date_from, date_to)
    
    return render_template('training/history.html', 
                         title='Treniravimo sesijų istorija',
                         sessions=sessions)

# Pridėkite šiuos maršrutus:

@model_training.route('/session/<session_id>', methods=['GET'])
def session_details(session_id):
    """
    Atvaizduoja treniravimo sesijos detalų puslapį
    
    Args:
        session_id (str): Sesijos ID
    """
    # Gauname sesiją
    session = history_service.get_session(session_id)
    
    # Jei sesija nerasta, grąžiname į istorijos puslapį
    if not session:
        flash('Sesija nerasta', 'danger')
        return redirect(url_for('model_training.history'))
    
    # Generuojame mokymosi istorijos grafikus
    loss_chart = history_service.generate_history_chart(session_id, 'loss')
    accuracy_chart = history_service.generate_history_chart(session_id, 'accuracy')
    
    return render_template('training/session_details.html',
                         title=f'Treniravimo sesija: {session.name}',
                         session=session,
                         loss_chart=loss_chart,
                         accuracy_chart=accuracy_chart)

@model_training.route('/session/<session_id>/delete', methods=['GET'])
def delete_session(session_id):
    """
    Ištrina treniravimo sesiją
    
    Args:
        session_id (str): Sesijos ID
    """
    # Ištriname sesiją
    if history_service.delete_session(session_id):
        flash('Sesija sėkmingai ištrinta', 'success')
    else:
        flash('Nepavyko ištrinti sesijos', 'danger')
    
    # Grįžtame į istorijos puslapį
    return redirect(url_for('model_training.history'))

@model_training.route('/session/<session_id>/start', methods=['GET'])
def start_session(session_id):
    """
    Pradeda treniravimo sesiją
    
    Args:
        session_id (str): Sesijos ID
    """
    # Gauname sesiją
    session = history_service.get_session(session_id)
    
    # Jei sesija nerasta, grąžiname į istorijos puslapį
    if not session:
        flash('Sesija nerasta', 'danger')
        return redirect(url_for('model_training.history'))
    
    # Patikriname ar sesijos statusas leidžia pradėti
    if session.status != 'new':
        flash(f'Negalima pradėti sesijos su statusu "{session.status}"', 'warning')
        return redirect(url_for('model_training.session_details', session_id=session_id))
    
    # Atnaujiname sesijos statusą
    session.status = 'running'
    session.started_at = datetime.datetime.now()
    
    # Išsaugome pakeitimus
    if history_service.update_session(session):
        flash('Sesija pradėta', 'success')
    else:
        flash('Nepavyko pradėti sesijos', 'danger')
    
    # Grįžtame į sesijos puslapį
    return redirect(url_for('model_training.session_details', session_id=session_id))

@model_training.route('/session/<session_id>/stop', methods=['GET'])
def stop_session(session_id):
    """
    Sustabdo treniravimo sesiją
    
    Args:
        session_id (str): Sesijos ID
    """
    # Gauname sesiją
    session = history_service.get_session(session_id)
    
    # Jei sesija nerasta, grąžiname į istorijos puslapį
    if not session:
        flash('Sesija nerasta', 'danger')
        return redirect(url_for('model_training.history'))
    
    # Patikriname ar sesijos statusas leidžia sustabdyti
    if session.status != 'running':
        flash(f'Negalima sustabdyti sesijos su statusu "{session.status}"', 'warning')
        return redirect(url_for('model_training.session_details', session_id=session_id))
    
    # Atnaujiname sesijos statusą
    session.status = 'stopped'
    
    # Išsaugome pakeitimus
    if history_service.update_session(session):
        flash('Sesija sustabdyta', 'success')
    else:
        flash('Nepavyko sustabdyti sesijos', 'danger')
    
    # Grįžtame į sesijos puslapį
    return redirect(url_for('model_training.session_details', session_id=session_id))

@model_training.route('/session/<session_id>/download', methods=['GET'])
def download_model(session_id):
    """
    Atsiunčia treniruotą modelį
    
    Args:
        session_id (str): Sesijos ID
    """
    # Gauname sesiją
    session = history_service.get_session(session_id)
    
    # Jei sesija nerasta, grąžiname į istorijos puslapį
    if not session:
        flash('Sesija nerasta', 'danger')
        return redirect(url_for('model_training.history'))
    
    # Patikriname ar yra modelio failas
    if not session.model_path or not os.path.exists(session.model_path):
        flash('Modelio failas nerastas', 'danger')
        return redirect(url_for('model_training.session_details', session_id=session_id))
    
    # Gauname modelio failo pavadinimą
    model_filename = os.path.basename(session.model_path)
    
    # Siunčiame modelio failą
    return send_file(session.model_path,
                   as_attachment=True,
                   download_name=model_filename)

@model_training.route('/api/sessions/comparison', methods=['POST'])
def compare_sessions():
    """
    Grąžina sesijų palyginimo grafiką
    """
    # Gauname sesijų ID ir metriką iš užklausos
    data = request.get_json()
    session_ids = data.get('session_ids', [])
    metric = data.get('metric', 'loss')
    
    # Patikriname ar yra sesijų
    if not session_ids:
        return jsonify({'error': 'Nenurodytos sesijos palyginimui'}), 400
    
    # Generuojame palyginimo grafiką
    chart = history_service.generate_comparison_chart(session_ids, metric)
    
    # Patikriname ar pavyko sugeneruoti grafiką
    if not chart:
        return jsonify({'error': f'Nepavyko sugeneruoti {metric} palyginimo grafiko'}), 500
    
    # Grąžiname grafiką
    return jsonify({'chart': chart})

# Pridėkite šį maršrutą:

@model_training.route('/compare_sessions', methods=['GET'])
def compare_sessions_page():
    """
    Atvaizduoja treniravimo sesijų palyginimo puslapį
    """
    # Gauname visas sesijas
    sessions = history_service.get_all_sessions()
    
    return render_template('training/compare_sessions.html',
                         title='Sesijų palyginimas',
                         sessions=sessions)

# Pridėkite šiuos maršrutus hiperparametrų optimizavimui:

@model_training.route('/optimization')
def optimization_index():
    """
    Hiperparametrų optimizavimo pagrindinis puslapis
    """
    # Gauname visas optimizavimo sesijas
    sessions = optimization_service.get_all_sessions()
    
    return render_template('training/optimization_index.html', 
                           title='Hiperparametrų optimizavimas',
                           sessions=sessions)

@model_training.route('/optimization/grid_search', methods=['GET', 'POST'])
def grid_search():
    """
    Grid Search optimizavimo puslapis
    """
    if request.method == 'POST':
        # Gauname formos duomenis
        model_type = request.form.get('model_type')
        name = request.form.get('name')
        
        # Gauname parametrų tinklelį iš formos
        param_grid = {}
        
        # Gauname X ir y treniravimui (čia reikėtų pritaikyti pagal jūsų duomenų gavimo logiką)
        X_train, y_train = load_training_data()
        
        # Funkcija modelio sukūrimui pagal parametrus
        def model_builder(**params):
            # Čia reikėtų pritaikyti pagal jūsų modelio kūrimo logiką
            if model_type == 'lstm':
                return create_lstm_model(**params)
            elif model_type == 'cnn':
                return create_cnn_model(**params)
            else:
                return create_default_model(**params)
        
        # Vykdome Grid Search
        try:
            session = optimization_service.grid_search(
                model_builder=model_builder,
                param_grid=param_grid,
                model_type=model_type,
                X_train=X_train,
                y_train=y_train,
                cv=3,
                name=name
            )
            
            # Nukreipiame į sesijos detalių puslapį
            flash('Grid Search optimizavimas sėkmingai pradėtas!', 'success')
            return redirect(url_for('model_training.optimization_session', session_id=session.session_id))
        
        except Exception as e:
            flash(f'Klaida vykdant Grid Search: {str(e)}', 'danger')
    
    return render_template('training/grid_search.html', 
                           title='Grid Search optimizavimas')

@model_training.route('/optimization/random_search', methods=['GET', 'POST'])
def random_search():
    """
    Random Search optimizavimo puslapis
    """
    if request.method == 'POST':
        # Gauname formos duomenis
        model_type = request.form.get('model_type')
        name = request.form.get('name')
        n_iter = int(request.form.get('n_iter', 10))
        
        # Gauname parametrų pasiskirstymus iš formos
        param_distributions = {}
        
        # Gauname X ir y treniravimui (čia reikėtų pritaikyti pagal jūsų duomenų gavimo logiką)
        X_train, y_train = load_training_data()
        
        # Funkcija modelio sukūrimui pagal parametrus
        def model_builder(**params):
            # Čia reikėtų pritaikyti pagal jūsų modelio kūrimo logiką
            if model_type == 'lstm':
                return create_lstm_model(**params)
            elif model_type == 'cnn':
                return create_cnn_model(**params)
            else:
                return create_default_model(**params)
        
        # Vykdome Random Search
        try:
            session = optimization_service.random_search(
                model_builder=model_builder,
                param_distributions=param_distributions,
                model_type=model_type,
                X_train=X_train,
                y_train=y_train,
                n_iter=n_iter,
                cv=3,
                name=name
            )
            
            # Nukreipiame į sesijos detalių puslapį
            flash('Random Search optimizavimas sėkmingai pradėtas!', 'success')
            return redirect(url_for('model_training.optimization_session', session_id=session.session_id))
        
        except Exception as e:
            flash(f'Klaida vykdant Random Search: {str(e)}', 'danger')
    
    return render_template('training/random_search.html', 
                           title='Random Search optimizavimas')

@model_training.route('/optimization/bayesian', methods=['GET', 'POST'])
def bayesian_optimization():
    """
    Bayesian optimizavimo puslapis
    """
    if request.method == 'POST':
        # Gauname formos duomenis
        model_type = request.form.get('model_type')
        name = request.form.get('name')
        n_iter = int(request.form.get('n_iter', 10))
        
        # Gauname parametrų ribas iš formos
        param_bounds = {}
        
        # Gauname X ir y treniravimui (čia reikėtų pritaikyti pagal jūsų duomenų gavimo logiką)
        X_train, y_train = load_training_data()
        
        # Funkcija modelio sukūrimui pagal parametrus
        def model_builder(**params):
            # Čia reikėtų pritaikyti pagal jūsų modelio kūrimo logiką
            if model_type == 'lstm':
                return create_lstm_model(**params)
            elif model_type == 'cnn':
                return create_cnn_model(**params)
            else:
                return create_default_model(**params)
        
        # Vykdome Bayesian optimizavimą
        try:
            session = optimization_service.bayesian_optimization(
                model_builder=model_builder,
                param_bounds=param_bounds,
                model_type=model_type,
                X_train=X_train,
                y_train=y_train,
                n_iter=n_iter,
                cv=3,
                name=name
            )
            
            # Nukreipiame į sesijos detalių puslapį
            flash('Bayesian optimizavimas sėkmingai pradėtas!', 'success')
            return redirect(url_for('model_training.optimization_session', session_id=session.session_id))
        
        except Exception as e:
            flash(f'Klaida vykdant Bayesian optimizavimą: {str(e)}', 'danger')
    
    return render_template('training/bayesian_optimization.html', 
                           title='Bayesian optimizavimas')

@model_training.route('/optimization/session/<session_id>')
def optimization_session(session_id):
    """
    Optimizavimo sesijos detalių puslapis
    
    Args:
        session_id (str): Sesijos ID
    """
    # Užkrauname sesiją
    session = optimization_service.load_session(session_id)
    
    if not session:
        flash('Nepavyko rasti optimizavimo sesijos', 'danger')
        return redirect(url_for('model_training.optimization_index'))
    
    return render_template('training/optimization_session.html',
                           title=f'Optimizavimo sesija: {session.name}',
                           session=session)

@model_training.route('/optimization/session/<session_id>/delete')
def delete_optimization_session(session_id):
    """
    Ištrina optimizavimo sesiją
    
    Args:
        session_id (str): Sesijos ID
    """
    # Ištriname sesiją
    success = optimization_service.delete_session(session_id)
    
    if success:
        flash('Optimizavimo sesija sėkmingai ištrinta', 'success')
    else:
        flash('Nepavyko ištrinti optimizavimo sesijos', 'danger')
    
    return redirect(url_for('model_training.optimization_index'))

@model_training.route('/optimization/session/<session_id>/apply')
def apply_best_params(session_id):
    """
    Pritaiko geriausius parametrus naujam modeliui
    
    Args:
        session_id (str): Sesijos ID
    """
    # Užkrauname sesiją
    session = optimization_service.load_session(session_id)
    
    if not session:
        flash('Nepavyko rasti optimizavimo sesijos', 'danger')
        return redirect(url_for('model_training.optimization_index'))
    
    # Patikriname, ar sesija užbaigta ir turi geriausius parametrus
    if session.status != "completed" or not session.best_params:
        flash('Sesija dar neužbaigta arba neturi geriausių parametrų', 'warning')
        return redirect(url_for('model_training.optimization_session', session_id=session_id))
    
    # Nustatome geriausius parametrus į sesiją (galite pritaikyti pagal savo logiką)
    # Pavyzdžiui, išsaugoti juos į naują formą, kur vartotojas gali sukurti naują modelį su šiais parametrais
    
    flash('Geriausi parametrai sėkmingai pritaikyti naujo modelio kūrimui', 'success')
    return redirect(url_for('model_training.train', best_params=json.dumps(session.best_params)))

# Pridedame naujus maršrutus egzistuojančiame faile

# Pridedame optimizavimo sesijų duomenų atnaujinimo maršrutą
@model_training.route('/optimization/session/<session_id>/data')
def optimization_session_data(session_id):
    """
    Grąžina optimizavimo sesijos duomenis JSON formatu
    Naudojamas realiu laiku progresu atnaujinimui
    
    Args:
        session_id (str): Sesijos ID
    """
    # Užkrauname sesiją
    session = optimization_service.load_session(session_id)
    
    if not session:
        return jsonify({'error': 'Sesija nerasta'}), 404
    
    # Paruošiame duomenis siuntimui
    data = {
        'session_id': session.session_id,
        'status': session.status,
        'trials_count': len(session.trials),
        'total_trials': session.parameters.get('n_iter', 0) if hasattr(session, 'parameters') else 0,
        'best_score': session.best_score,
        'latest_trial': session.trials[-1] if session.trials else None
    }
    
    return jsonify(data)

# Pridedame optimizavimo rezultatų eksportavimo maršrutą
@model_training.route('/optimization/session/<session_id>/export/<format>')
def export_optimization_session(session_id, format):
    """
    Eksportuoja optimizavimo sesijos rezultatus
    
    Args:
        session_id (str): Sesijos ID
        format (str): Eksporto formatas (json arba csv)
    """
    # Užkrauname sesiją
    session = optimization_service.load_session(session_id)
    
    if not session:
        flash('Nepavyko rasti optimizavimo sesijos', 'danger')
        return redirect(url_for('model_training.optimization_index'))
    
    # Sukuriame failo pavadinimą
    filename = f"optimizavimas_{session.session_id[:8]}_{session.algorithm}"
    
    if format == 'json':
        # Eksportuojame į JSON
        response = Response(
            json.dumps(session.to_dict(), indent=4, ensure_ascii=False),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename={filename}.json'
            }
        )
        return response
    
    elif format == 'csv':
        # Eksportuojame į CSV
        # Sukuriame CSV StringIO objektą
        csv_data = StringIO()
        writer = csv.writer(csv_data)
        
        # Rašome antraštę
        header = ['trial_id', 'score']
        
        # Pridedame visus parametrus į antraštę
        param_names = set()
        for trial in session.trials:
            param_names.update(trial['params'].keys())
        
        header.extend(sorted(param_names))
        header.append('timestamp')
        
        writer.writerow(header)
        
        # Rašome bandymus
        for trial in session.trials:
            row = [trial['trial_id'], trial['score']]
            
            # Pridedame parametrų reikšmes
            for param_name in sorted(param_names):
                row.append(trial['params'].get(param_name, ''))
            
            # Pridedame laiko žymę
            row.append(trial.get('timestamp', ''))
            
            writer.writerow(row)
        
        # Grąžiname CSV failą
        response = Response(
            csv_data.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename={filename}.csv'
            }
        )
        return response
    
    else:
        flash(f'Nežinomas eksporto formatas: {format}', 'danger')
        return redirect(url_for('model_training.optimization_session', session_id=session_id))

# Pridedame sesijų palyginimo maršrutą
@model_training.route('/optimization/compare')
def compare_sessions():
    """
    Palyginimo puslapis kelioms optimizavimo sesijoms
    """
    # Gauname sesijų ID iš URL parametrų
    sessions_param = request.args.get('sessions', '')
    session_ids = sessions_param.split(',') if sessions_param else []
    
    # Užkrauname sesijas
    sessions = []
    for session_id in session_ids:
        session = optimization_service.load_session(session_id)
        if session:
            sessions.append(session)
    
    # Jei nėra sesijų, nukreipiame į optimizavimo indeksą
    if not sessions:
        flash('Pasirinkite sesijas palyginimui', 'warning')
        return redirect(url_for('model_training.optimization_index'))
    
    return render_template('training/compare_sessions.html',
                           title='Optimizavimo sesijų palyginimas',
                           sessions=sessions)

# Pridedame sesijos archyvavimo maršrutą
@model_training.route('/optimization/session/<session_id>/archive')
def archive_session(session_id):
    """
    Archyvuoja optimizavimo sesiją
    
    Args:
        session_id (str): Sesijos ID
    """
    # Užkrauname sesiją
    session = optimization_service.load_session(session_id)
    
    if not session:
        flash('Nepavyko rasti optimizavimo sesijos', 'danger')
        return redirect(url_for('model_training.optimization_index'))
    
    # Pažymime sesiją kaip archyvuotą
    session.archived = True
    optimization_service.save_session(session)
    
    flash('Optimizavimo sesija sėkmingai archyvuota', 'success')
    return redirect(url_for('model_training.optimization_index'))

# Pridedame sesijos atkūrimo iš archyvo maršrutą
@model_training.route('/optimization/session/<session_id>/restore')
def restore_session(session_id):
    """
    Atkuria optimizavimo sesiją iš archyvo
    
    Args:
        session_id (str): Sesijos ID
    """
    # Užkrauname sesiją
    session = optimization_service.load_session(session_id)
    
    if not session:
        flash('Nepavyko rasti optimizavimo sesijos', 'danger')
        return redirect(url_for('model_training.optimization_index'))
    
    # Pažymime sesiją kaip nebeesančią archyve
    session.archived = False
    optimization_service.save_session(session)
    
    flash('Optimizavimo sesija sėkmingai atkurta iš archyvo', 'success')
    return redirect(url_for('model_training.optimization_index'))

# Pagalbinė funkcija duomenų užkrovimui (įgyvendinkite pagal savo duomenų struktūrą)
def load_training_data():
    """
    Užkrauna mokymo duomenis
    
    Returns:
        tuple: (X_train, y_train)
    """
    # Šią funkciją reikėtų pritaikyti pagal jūsų duomenų užkrovimo logiką
    # Tai tik pavyzdys
    import numpy as np
    
    # Pavyzdiniai duomenys
    X_train = np.random.rand(100, 10)
    y_train = np.random.randint(0, 2, 100)
    
    return X_train, y_train

# Pagalbinės funkcijos modelių kūrimui (įgyvendinkite pagal savo modelių struktūrą)
def create_lstm_model(**params):
    """
    Sukuria LSTM modelį
    
    Args:
        **params: Modelio parametrai
        
    Returns:
        object: LSTM modelis
    """
    # Šią funkciją reikėtų pritaikyti pagal jūsų modelių kūrimo logiką
    # Tai tik pavyzdys
    from keras.models import Sequential
    from keras.layers import LSTM, Dense
    
    model = Sequential()
    model.add(LSTM(units=params.get('units', 50), input_shape=(10, 1)))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer=params.get('optimizer', 'adam'), 
                 loss=params.get('loss', 'binary_crossentropy'),
                 metrics=['accuracy'])
    
    return model

def create_cnn_model(**params):
    """
    Sukuria CNN modelį
    
    Args:
        **params: Modelio parametrai
        
    Returns:
        object: CNN modelis
    """
    # Šią funkciją reikėtų pritaikyti pagal jūsų modelių kūrimo logiką
    # Tai tik pavyzdys
    from keras.models import Sequential
    from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense
    
    model = Sequential()
    model.add(Conv1D(filters=params.get('filters', 64), kernel_size=params.get('kernel_size', 3),
                    activation='relu', input_shape=(10, 1)))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(params.get('units', 50), activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer=params.get('optimizer', 'adam'),
                 loss=params.get('loss', 'binary_crossentropy'),
                 metrics=['accuracy'])
    
    return model

def create_default_model(**params):
    """
    Sukuria numatytąjį modelį
    
    Args:
        **params: Modelio parametrai
        
    Returns:
        object: Numatytasis modelis
    """
    # Šią funkciją reikėtų pritaikyti pagal jūsų modelių kūrimo logiką
    # Tai tik pavyzdys
    from keras.models import Sequential
    from keras.layers import Dense
    
    model = Sequential()
    model.add(Dense(params.get('units', 50), activation='relu', input_shape=(10,)))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer=params.get('optimizer', 'adam'),
                 loss=params.get('loss', 'binary_crossentropy'),
                 metrics=['accuracy'])
    
    return model

# Pridedame naujus maršrutus prie esamų

# Importuojame reikalingus modulius
from flask import flash, redirect, render_template, request, url_for
from app.models.parameter_template import ParameterTemplate
from app.services.parameter_template_service import ParameterTemplateService

# Inicializuojame parametrų šablonų servisą
parameter_template_service = ParameterTemplateService(os.path.join(app.config['DATA_DIR'], 'parameter_templates'))

# Maršrutas geriausių parametrų pritaikymui
@model_training.route('/optimization/session/<session_id>/apply_params', methods=['GET', 'POST'])
def apply_best_params(session_id):
    """
    Pritaiko geriausius parametrus iš optimizavimo sesijos
    
    Args:
        session_id (str): Optimizavimo sesijos ID
    """
    # Užkrauname optimizavimo sesiją
    session = optimization_service.load_session(session_id)
    
    if not session:
        flash('Nepavyko rasti optimizavimo sesijos', 'danger')
        return redirect(url_for('model_training.optimization_index'))
    
    # Jei sesija neturi geriausių parametrų, grąžiname klaidą
    if not session.best_params:
        flash('Optimizavimo sesija neturi geriausių parametrų', 'warning')
        return redirect(url_for('model_training.optimization_session', session_id=session_id))
    
    # Jei tai POST užklausa, apdorojame formą
    if request.method == 'POST':
        # Išgauname parametrus iš formos
        model_name = request.form.get('model_name')
        data_source = request.form.get('data_source')
        compare_with = request.form.get('compare_with')
        save_as_template = 'save_as_template' in request.form
        template_name = request.form.get('template_name')
        
        # Išgauname redaguotus parametrus
        params = {}
        for key, value in request.form.items():
            if key.startswith('params[') and key.endswith(']'):
                param_name = key[7:-1]  # Išgauname parametro pavadinimą
                params[param_name] = value
        
        # Išgauname papildomus parametrus
        additional_params = {}
        for key, value in request.form.items():
            if key.startswith('additional_params[') and key.endswith(']'):
                param_name = key[18:-1]  # Išgauname parametro pavadinimą
                additional_params[param_name] = value
        
        # Čia būtų modelio apmokymimo logika su parametrais
        # ...
        
        # Išsaugome parametrus kaip šabloną, jei reikia
        if save_as_template and template_name:
            # Sukuriame naują šabloną
            template = ParameterTemplate()
            template.name = template_name
            template.model_type = session.model_type
            template.parameters = params.copy()
            template.source_type = 'optimization'
            template.source_id = session.session_id
            template.best_score = session.best_score
            
            # Išsaugome šabloną
            if parameter_template_service.save_template(template):
                flash(f'Parametrų šablonas "{template_name}" sėkmingai išsaugotas', 'success')
            else:
                flash('Nepavyko išsaugoti parametrų šablono', 'danger')
        
        # Pranešame apie sėkmę
        flash(f'Modelis "{model_name}" sėkmingai apmokytas su optimizuotais parametrais', 'success')
        return redirect(url_for('model_training.optimization_session', session_id=session_id))
    
    # Jei tai GET užklausa, rodome formą
    return render_template('training/apply_parameters.html',
                           title='Pritaikyti geriausius parametrus',
                           session=session,
                           now=datetime.datetime.now())

# Maršrutas parametrų šablonų valdymui
@model_training.route('/parameter_templates', methods=['GET'])
def parameter_templates():
    """
    Rodo parametrų šablonų sąrašą
    """
    # Gauname visus šablonus
    templates = parameter_template_service.get_all_templates()
    
    return render_template('training/parameter_templates.html',
                           title='Parametrų šablonai',
                           templates=templates)

# Maršrutas naujo parametrų šablono sukūrimui
@model_training.route('/parameter_templates/create', methods=['POST'])
def create_parameter_template():
    """
    Sukuria naują parametrų šabloną
    """
    # Išgauname duomenis iš formos
    template_name = request.form.get('template_name')
    model_type = request.form.get('model_type')
    
    # Išgauname parametrų pavadinimus ir reikšmes
    param_names = request.form.getlist('param_names[]')
    param_values = request.form.getlist('param_values[]')
    
    # Sukuriame parametrų žodyną
    parameters = {}
    for i in range(len(param_names)):
        if i < len(param_values):
            # Bandome konvertuoti į skaičių, jei įmanoma
            try:
                value = float(param_values[i])
                # Jei reikšmė yra sveikasis skaičius, konvertuojame
                if value.is_integer():
                    value = int(value)
            except ValueError:
                value = param_values[i]
                
            parameters[param_names[i]] = value
    
    # Sukuriame naują šabloną
    template = ParameterTemplate(name=template_name, model_type=model_type, parameters=parameters)
    
    # Išsaugome šabloną
    if parameter_template_service.save_template(template):
        flash(f'Parametrų šablonas "{template_name}" sėkmingai sukurtas', 'success')
    else:
        flash('Nepavyko sukurti parametrų šablono', 'danger')
    
    return redirect(url_for('model_training.parameter_templates'))

# Maršrutas parametrų šablono ištrynimui
@model_training.route('/parameter_templates/<template_id>/delete', methods=['GET'])
def delete_parameter_template(template_id):
    """
    Ištrina parametrų šabloną
    
    Args:
        template_id (str): Šablono ID
    """
    # Ištriname šabloną
    if parameter_template_service.delete_template(template_id):
        flash('Parametrų šablonas sėkmingai ištrintas', 'success')
    else:
        flash('Nepavyko ištrinti parametrų šablono', 'danger')
    
    return redirect(url_for('model_training.parameter_templates'))

# Maršrutas parametrų šablono naudojimui
@model_training.route('/parameter_templates/<template_id>/use', methods=['GET'])
def use_parameter_template(template_id):
    """
    Naudoja parametrų šabloną naujam modeliui
    
    Args:
        template_id (str): Šablono ID
    """
    # Užkrauname šabloną
    template = parameter_template_service.load_template(template_id)
    
    if not template:
        flash('Nepavyko rasti parametrų šablono', 'danger')
        return redirect(url_for('model_training.parameter_templates'))
    
    # Čia būtų formos rodymas su užpildytais parametrais iš šablono
    # Pavyzdžiui, galima nukreipti į modelio kūrimo formą su užpildytais parametrais
    
    flash(f'Šablonas "{template.name}" pasirinktas. Galite tęsti modelio kūrimą.', 'success')
    return redirect(url_for('model_training.create_model', template_id=template_id))

# API maršrutas parametrų šablono duomenims gauti
@model_training.route('/api/parameter_templates/<template_id>', methods=['GET'])
def get_parameter_template(template_id):
    """
    Grąžina parametrų šablono duomenis JSON formatu
    
    Args:
        template_id (str): Šablono ID
    """
    # Užkrauname šabloną
    template = parameter_template_service.load_template(template_id)
    
    if not template:
        return jsonify({'error': 'Šablonas nerastas'}), 404
    
    # Grąžiname šablono duomenis
    return jsonify(template.to_dict())

@model_training.route('/model/<model_id>/checkpoints')
def model_checkpoints(model_id):
    """
    Rodo modelio išsaugojimų (checkpoints) sąrašą
    
    Args:
        model_id (str): Modelio ID
        
    Returns:
        Šablonas su išsaugojimų sąrašu
    """
    # Inicializuojame išsaugojimų servisą
    checkpoint_service = CheckpointService(model_id)
    
    # Gauname modelio informaciją
    model_info = weights_service.get_model_info(model_id)
    
    if not model_info:
        flash('Modelis nerastas', 'danger')
        return redirect(url_for('model_training.index'))
    
    # Gauname išsaugojimus
    checkpoints = checkpoint_service.get_checkpoints(model_id)
    
    return render_template(
        'training/checkpoints.html',
        model=model_info,
        checkpoints=checkpoints,
        title=f"Modelio '{model_info['name']}' išsaugojimai"
    )