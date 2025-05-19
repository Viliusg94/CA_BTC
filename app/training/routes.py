"""
Modelio treniravimo maršrutai
---------------------------
Šis modulis apibrėžia modelio treniravimo, stebėjimo ir valdymo maršrutus.
"""

import os
import json
import uuid
import time
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Sukurti treniravimo Blueprint
training = Blueprint('training', __name__)

# Keliai iki modelių saugojimo katalogų
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')

# Globali kintamoji treniravimo progresui sekti
training_progress = {
    'status': 'Not started',
    'progress': 0,
    'current_epoch': 0,
    'total_epochs': 0,
    'metrics': {
        'loss': [],
        'val_loss': [],
        'mae': [],
        'val_mae': []
    },
    'log_messages': [],
    'model_results': None
}

@training.route('/')
@training.route('/index')
def index():
    """Pagrindinis treniravimo puslapis"""
    return render_template('training/index.html', title='Modelio treniravimas')

@training.route('/train')
def train():
    """Modelio parametrų forma"""
    return render_template('training/train.html', title='Treniruoti modelį')

@training.route('/monitor')
def monitor():
    """Treniravimo progreso stebėjimas"""
    return render_template('training/monitor.html', title='Treniravimo progresas')

@training.route('/optimize')
def optimize():
    """
    Hiperparametrų optimizavimo puslapis
    """
    return render_template('training/optimize.html', title='Hiperparametrų optimizavimas')

# Pakeistas pavadinimas - dabar tai history funkcija
@training.route('/training_history')
def view_history():  # naujas funkcijos pavadinimas
    """
    Treniravimo istorijos peržiūros puslapis
    """
    return render_template('training/history.html', title='Treniravimo istorija')

@training.route('/checkpoints')
def checkpoints():
    """
    Tarpinių modelių išsaugojimų puslapis
    """
    return render_template('training/checkpoints.html', title='Tarpiniai išsaugojimai')

@training.route('/compare_models')
def compare_models():
    """
    Modelių palyginimo puslapis
    """
    return render_template('training/compare_models.html', title='Modelių palyginimas')

@training.route('/model_architectures')
def model_architectures():
    """
    Modelio architektūros vizualizacijos puslapis
    """
    return render_template('training/model_architectures.html', title='Modelio architektūra')

@training.route('/model_weights')
def model_weights():
    """
    Modelio svorių vizualizacijos puslapis
    """
    return render_template('training/model_weights.html', title='Modelio svoriai')

@training.route('/validation_graph')
def validation_graph():
    """
    Validavimo grafiko puslapis
    """
    return render_template('training/validation_graph.html', title='Validavimo grafikas')

@training.route('/models')
def models():
    """Išsaugotų modelių sąrašas"""
    # Gauname išsaugotų modelių sąrašą
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    
    models_list = []
    
    for filename in os.listdir(MODELS_DIR):
        if filename.endswith('.json'):
            # Skaitome modelio metaduomenis
            try:
                with open(os.path.join(MODELS_DIR, filename), 'r') as f:
                    model_data = json.load(f)
                
                # Pridedame į sąrašą
                models_list.append({
                    'name': model_data.get('name', 'Nežinomas'),
                    'created_at': model_data.get('created_at', 'Nežinoma'),
                    'metrics': model_data.get('metrics', {}),
                    'parameters': model_data.get('parameters', {}),
                    'filename': filename
                })
            except:
                continue
    
    # Rikiuojame pagal sukūrimo datą (naujausi viršuje)
    models_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('training/models.html', models=models_list, title='Modelių sąrašas')

@training.route('/model/<filename>')
def model_details(filename):
    """Modelio detalių peržiūra"""
    # Patikriname ar failas egzistuoja
    file_path = os.path.join(MODELS_DIR, filename)
    
    if not os.path.exists(file_path):
        return render_template('errors/404.html', title='Modelis nerastas'), 404
    
    # Skaitome modelio metaduomenis
    with open(file_path, 'r') as f:
        model_data = json.load(f)
    
    return render_template('training/model_details.html', model=model_data, title=f'Modelio detalės - {model_data.get("name", "Nežinomas")}')

# API endpoint'ai

@training.route('/api/start_training', methods=['POST'])
def api_start_training():
    """API endpoint treniravimo pradėjimui"""
    global training_progress
    
    # Gauname parametrus
    parameters = request.json
    
    # Resetuojame progresą
    training_progress = {
        'status': 'Preparing data',
        'progress': 10,
        'current_epoch': 0,
        'total_epochs': parameters.get('epochs', 50),
        'metrics': {
            'loss': [],
            'val_loss': [],
            'mae': [],
            'val_mae': []
        },
        'log_messages': ['Treniravimas pradėtas'],
        'parameters': parameters,
        'model_results': None
    }
    
    # Pradedame treniravimą atskiroje gijoje
    thread = threading.Thread(target=train_model, args=(parameters,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Treniravimas pradėtas'})

@training.route('/api/progress')
def api_progress():
    """API endpoint treniravimo progreso gavimui"""
    global training_progress
    return jsonify(training_progress)

@training.route('/api/save_model', methods=['POST'])
def api_save_model():
    """API endpoint modelio išsaugojimui"""
    global training_progress
    
    # Gauname modelio pavadinimą
    model_name = request.json.get('name', f'Model_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    # Tikriname ar treniravimas baigtas
    if training_progress['status'] != 'Completed':
        return jsonify({'success': False, 'message': 'Treniravimas dar nebaigtas'})
    
    # Sukuriame modelių katalogą jei jo nėra
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    
    # Sukuriame modelio duomenų failą
    model_data = {
        'name': model_name,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'metrics': training_progress['metrics'],
        'parameters': training_progress['parameters'],
        'final_metrics': {
            'loss': training_progress['metrics']['loss'][-1] if training_progress['metrics']['loss'] else None,
            'val_loss': training_progress['metrics']['val_loss'][-1] if training_progress['metrics']['val_loss'] else None,
            'mae': training_progress['metrics']['mae'][-1] if training_progress['metrics']['mae'] else None,
            'val_mae': training_progress['metrics']['val_mae'][-1] if training_progress['metrics']['val_mae'] else None
        }
    }
    
    # Sukuriame unikalų failo pavadinimą
    filename = f"{model_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Išsaugome duomenis
    with open(os.path.join(MODELS_DIR, filename), 'w') as f:
        json.dump(model_data, f, indent=4)
    
    return jsonify({'success': True, 'message': 'Modelis išsaugotas', 'filename': filename})

# Simuliuota treniravimo funkcija (realiam projekte čia būtų tikras modelio treniravimas)
def train_model(parameters):
    """Simuliuota modelio treniravimo funkcija"""
    global training_progress
    
    # Duomenų paruošimas
    training_progress['status'] = 'Preparing data'
    training_progress['progress'] = 10
    training_progress['log_messages'].append('Ruošiami duomenys...')
    time.sleep(2)
    
    # Modelio kūrimas
    training_progress['status'] = 'Creating model'
    training_progress['progress'] = 20
    training_progress['log_messages'].append('Kuriamas modelis...')
    time.sleep(1)
    
    # Treniravimas
    training_progress['status'] = 'Training'
    epochs = parameters.get('epochs', 50)
    training_progress['total_epochs'] = epochs
    
    # Apskaičiuojame progreso dalį vienai epochai
    epoch_progress = 70 / epochs
    
    # Simuliuojame treniravimą kiekvienai epochai
    for epoch in range(1, epochs + 1):
        training_progress['current_epoch'] = epoch
        
        # Simuliuojame metrikus
        loss = 1.0 / (epoch * 0.05 + 1)
        val_loss = loss * 1.2
        mae = loss * 0.8
        val_mae = val_loss * 0.8
        
        # Pridedame metrikus
        training_progress['metrics']['loss'].append(loss)
        training_progress['metrics']['val_loss'].append(val_loss)
        training_progress['metrics']['mae'].append(mae)
        training_progress['metrics']['val_mae'].append(val_mae)
        
        # Atnaujiname progresą
        training_progress['progress'] = 20 + int(epoch * epoch_progress)
        
        # Pridedame žurnalo įrašą
        training_progress['log_messages'].append(f'Epocha {epoch}/{epochs} - loss: {loss:.4f}, val_loss: {val_loss:.4f}, mae: {mae:.4f}, val_mae: {val_mae:.4f}')
        
        # Simuliuojame treniravimo laiką
        time.sleep(0.5)
    
    # Įvertinimas
    training_progress['status'] = 'Evaluating'
    training_progress['progress'] = 90
    training_progress['log_messages'].append('Modelis įvertinamas...')
    time.sleep(1)
    
    # Baigta
    training_progress['status'] = 'Completed'
    training_progress['progress'] = 100
    training_progress['log_messages'].append('Treniravimas baigtas sėkmingai!')

@training.route('/api/delete_model', methods=['POST'])
def api_delete_model():
    """API endpoint modelio ištrynimui"""
    # Gauname failą iš užklausos
    filename = request.json.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'message': 'Nenurodytas failo pavadinimas'})
    
    # Tikriname ar failas egzistuoja
    file_path = os.path.join(MODELS_DIR, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Modelis nerastas'})
    
    try:
        # Ištriname failą
        os.remove(file_path)
        
        # Taip pat ištriname modelio failus jei yra
        h5_file = os.path.splitext(file_path)[0] + '.h5'
        if os.path.exists(h5_file):
            os.remove(h5_file)
            
        return jsonify({'success': True, 'message': 'Modelis sėkmingai ištrintas'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Klaida trinant modelį: {str(e)}'})

@training.route('/api/export_model/<filename>')
def api_export_model(filename):
    """API endpoint modelio eksportavimui"""
    # Tikriname ar failas egzistuoja
    file_path = os.path.join(MODELS_DIR, filename)
    
    if not os.path.exists(file_path):
        return render_template('errors/404.html', title='Modelis nerastas'), 404
    
    # Siunčiame failą vartotojui
    return send_file(file_path, as_attachment=True, download_name=filename)

@training.route('/api/model_params/<filename>')
def api_model_params(filename):
    """API endpoint modelio parametrų gavimui"""
    # Tikriname ar failas egzistuoja
    file_path = os.path.join(MODELS_DIR, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Modelis nerastas'})
    
    # Skaitome modelio metaduomenis
    try:
        with open(file_path, 'r') as f:
            model_data = json.load(f)
            
        return jsonify({
            'success': True,
            'parameters': model_data.get('parameters', {})
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Klaida skaitant modelio duomenis: {str(e)}'})

@training.route('/history')
def view_history():
    """
    Treniravimo istorijos peržiūros puslapis
    """
    return render_template('training/history.html', title='Treniravimo istorija')

@training.route('/checkpoints')
def checkpoints():
    """
    Rodo tarpinių modelių išsaugojimus (checkpoints)
    """
    # Čia bus logika tarpinių modelių išsaugojimų atvaizdavimui
    return render_template('training/checkpoints.html', title='Tarpiniai modelių išsaugojimai')