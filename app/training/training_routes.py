from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, make_response, send_file
from datetime import datetime, timedelta
import uuid
import json
import os
import threading
import time
from app.services.model_service import ModelService
from app.services.template_service import TemplateService
from app.services.pdf_service import PdfGenerator
from app.services.websocket_service import websocket_manager

# Inicializuojame modelio treniravimo maršrutus
model_training = Blueprint('model_training', __name__, url_prefix='/training')

@model_training.route('/')
def index():
    """
    Modelio treniravimo pradinis puslapis
    """
    # Grąžiname bazinį puslapį
    return render_template('training/index.html', title='Modelio treniravimas')

@model_training.route('/models/create', methods=['GET', 'POST'])
def create_model():
    """
    Naujo modelio sukūrimas su parametrais
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    if request.method == 'POST':
        try:
            # 1. Gauname formos duomenis
            model_name = request.form.get('model_name', '').strip()
            model_type = request.form.get('model_type', '').strip()
            model_description = request.form.get('model_description', '').strip()
            
            # 2. Vykdome bazinių laukų validaciją
            errors = []
            
            # Pavadinimo validacija
            if not model_name:
                errors.append("Modelio pavadinimas yra privalomas.")
            elif len(model_name) < 3:
                errors.append("Modelio pavadinimas turi būti bent 3 simbolių ilgio.")
            
            # Modelio tipo validacija
            valid_types = ['lstm', 'gru', 'cnn', 'transformer']
            if not model_type:
                errors.append("Modelio tipas yra privalomas.")
            elif model_type not in valid_types:
                errors.append(f"Neteisingas modelio tipas. Galimi variantai: {', '.join(valid_types)}")
            
            # 3. Apdorojame skaitinius parametrus
            try:
                # Gauname hiperparametrus ir konvertuojame į tinkamus tipus
                epochs = int(request.form.get('epochs', 50))
                batch_size = int(request.form.get('batch_size', 64))
                learning_rate = float(request.form.get('learning_rate', 0.001))
                layers = int(request.form.get('layers', 2))
                neurons = int(request.form.get('neurons', 64))
                dropout = float(request.form.get('dropout', 0.2))
                
                # Validuojame hiperparametrų reikšmes
                if epochs < 1 or epochs > 1000:
                    errors.append("Epochų skaičius turi būti tarp 1 ir 1000.")
                
                if batch_size < 8 or batch_size > 256:
                    errors.append("Batch dydis turi būti tarp 8 ir 256.")
                
                if learning_rate < 0.0001 or learning_rate > 0.01:
                    errors.append("Mokymosi greitis turi būti tarp 0.0001 ir 0.01.")
                
                if layers < 1 or layers > 5:
                    errors.append("Sluoksnių skaičius turi būti tarp 1 ir 5.")
                
                if neurons < 16 or neurons > 256:
                    errors.append("Neuronų skaičius turi būti tarp 16 ir 256.")
                
                if dropout < 0 or dropout > 0.5:
                    errors.append("Dropout koeficientas turi būti tarp 0 ir 0.5.")
                
            except ValueError as e:
                # Jei įvyko klaida konvertuojant reikšmes
                errors.append(f"Neteisingas hiperparametrų formatas: {str(e)}")
                # Nustatome numatytasias reikšmes
                epochs = 50
                batch_size = 64
                learning_rate = 0.001
                layers = 2
                neurons = 64
                dropout = 0.2
            
            # 4. Gauname modelio tipo specifinius parametrus
            specific_params = {}
            
            if model_type == 'lstm':
                # LSTM specifiniai parametrai
                bidirectional = request.form.get('bidirectional') == 'true'
                specific_params['bidirectional'] = bidirectional
                
            elif model_type == 'cnn':
                # CNN specifiniai parametrai
                try:
                    kernel_size = int(request.form.get('kernel_size', 5))
                    if kernel_size < 3 or kernel_size > 7 or kernel_size % 2 == 0:
                        errors.append("Branduolio dydis turi būti 3, 5 arba 7.")
                        kernel_size = 5
                    specific_params['kernel_size'] = kernel_size
                except ValueError:
                    errors.append("Neteisingas branduolio dydžio formatas.")
                    specific_params['kernel_size'] = 5
            
            # 5. Jei yra klaidų, grąžiname jas
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('training/create.html', title='Naujas modelis')
            
            # 6. Sukuriame modelio konfigūracijos objektą
            model_config = {
                'name': model_name,
                'type': model_type,
                'description': model_description,
                'parameters': {
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate,
                    'layers': layers,
                    'neurons': neurons,
                    'dropout': dropout,
                    'specific': specific_params,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
            # 7. Sukuriame unikalų ID treniravimo sesijai
            training_id = str(uuid.uuid4())
            
            # 8. Išsaugome konfigūraciją
            success = service.save_model_config(training_id, model_config)
            
            if success:
                flash('Modelio konfigūracija sukurta sėkmingai!', 'success')
                # Nukreipiame į treniravimo puslapį
                return redirect(url_for('model_training.train_model', training_id=training_id))
            else:
                flash('Klaida išsaugant modelio konfigūraciją. Bandykite dar kartą.', 'danger')
                
        except Exception as e:
            # Apdorojame nenumatytas klaidas
            flash(f'Įvyko nenumatyta klaida: {str(e)}', 'danger')
    
    # GET užklausos atveju arba nesėkmingo POST atveju rodome formą
    if request.method == 'GET':
        # Tikriname, ar yra šablono ID
        template_id = request.args.get('template')
        template = None
        
        if template_id:
            # Gauname šabloną
            template_service = TemplateService()
            template = template_service.get_template(template_id)
        
        # Perduodame šabloną į formą
        return render_template('training/create_model.html', template=template)
    
    return render_template('training/create.html', title='Naujas modelis')

@model_training.route('/train/<training_id>', methods=['GET'])
def train_model(training_id):
    """
    Rodo modelio treniravimo valdymo puslapį
    
    Args:
        training_id (str): Treniravimo sesijos ID
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname modelio konfigūraciją
    model_config = service.get_model_config(training_id)
    
    # Jei konfigūracija nerasta, grąžiname klaidą
    if not model_config:
        flash('Nerasta modelio konfigūracija', 'danger')
        return redirect(url_for('model_training.index'))
    
    # Gauname dabartinę datą ir laiką formatuotą
    current_time = datetime.now().strftime('%H:%M:%S')
    
    # Perduodame konfigūraciją ir treniravimo ID į šabloną
    return render_template(
        'training/train.html',
        title="Modelio treniravimas",
        model_config=model_config,
        training_id=training_id,
        current_time=current_time
    )

@model_training.route('/start_training/<training_id>', methods=['POST'])
def start_training(training_id):
    """
    API endpointas treniravimo pradžiai
    """
    # Gauname modelio konfigūraciją
    service = ModelService()
    model_config = service.get_model_config(training_id)
    
    if not model_config:
        return jsonify({'success': False, 'error': 'Modelio konfigūracija nerasta'})
    
    # Simuliuojame treniravimą (realiam projekte čia būtų TensorFlow modelio treniravimas)
    def train_model_task():
        """Simuliacinis treniravimo procesas"""
        epochs = model_config['parameters']['epochs']
        metrics = {'loss': [], 'accuracy': [], 'val_loss': [], 'val_accuracy': []}
        
        # Simuliuojame kiekvieną epochą
        for epoch in range(epochs):
            # Apskaičiuojame progresą
            progress = (epoch + 1) / epochs * 100
            
            # Simuliuojame metrikus
            train_loss = 1.0 - (epoch / epochs) * 0.7
            train_acc = 0.5 + (epoch / epochs) * 0.4
            val_loss = 1.1 - (epoch / epochs) * 0.6
            val_acc = 0.45 + (epoch / epochs) * 0.35
            
            # Išsaugome metrikus
            metrics['loss'].append(train_loss)
            metrics['accuracy'].append(train_acc)
            metrics['val_loss'].append(val_loss)
            metrics['val_accuracy'].append(val_acc)
            
            # Siunčiame progresą per WebSocket
            websocket_manager.broadcast_message({
                'type': 'training_progress',
                'training_id': training_id,
                'progress': progress,
                'current_epoch': epoch + 1,
                'total_epochs': epochs,
                'metrics': {
                    'loss': train_loss,
                    'accuracy': train_acc,
                    'val_loss': val_loss,
                    'val_accuracy': val_acc
                }
            })
            
            # Laukiame 0.5 sekundės (simuliuojame treniravimą)
            time.sleep(0.5)
        
        # Treniravimas baigtas - išsaugome rezultatus
        service.save_model_results(training_id, metrics)
        
        # Pranešame apie baigimą
        websocket_manager.broadcast_message({
            'type': 'training_complete',
            'training_id': training_id,
            'success': True,
            'metrics': metrics
        })
    
    # Paleidžiame treniravimą atskirame thread'e
    t = threading.Thread(target=train_model_task)
    t.daemon = True
    t.start()
    
    return jsonify({'success': True})

@model_training.route('/results/<training_id>')
def view_results(training_id):
    """
    Modelio treniravimo rezultatų peržiūra
    """
    service = ModelService()
    model_config = service.get_model_config(training_id)
    model_metrics = service.get_model_metrics(training_id)
    
    if not model_config:
        flash('Modelio konfigūracija nerasta', 'danger')
        return redirect(url_for('model_training.index'))
    
    return render_template('training/results.html', 
                          title='Treniravimo rezultatai', 
                          training_id=training_id,
                          model_config=model_config,
                          metrics=model_metrics)

@model_training.route('/view_history')
def view_history():
    """
    Treniruotų modelių istorijos peržiūra
    """
    service = ModelService()
    models = service.get_all_training_history()
    
    return render_template('training/history.html', 
                          title='Treniravimo istorija', 
                          models=models)

@model_training.route('/api/training/metrics/<training_id>', methods=['GET'])
def api_get_training_metrics(training_id):
    """
    API endpointas treniravimo metrikų gavimui (su autentifikacija)
    
    Args:
        training_id (str): Treniravimo sesijos ID
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Ištraukiame parametrus iš užklausos
    epoch = request.args.get('epoch')
    
    if epoch:
        # Jei nurodyta konkreti epocha, grąžiname jos metrikas
        try:
            epoch = int(epoch)
            metrics = service.get_epoch_metrics(training_id, epoch)
            
            if not metrics:
                return jsonify({'error': f'Metrikos epochai {epoch} nerastos'}), 404
                
            return jsonify(metrics)
            
        except ValueError:
            return jsonify({'error': 'Neteisingas epochos formatas'}), 400
    else:
        # Grąžiname visas metrikas
        metrics = service.get_model_metrics(training_id)
        
        if not metrics:
            return jsonify({'error': 'Metrikos nerastos'}), 404
            
        return jsonify(metrics)

@model_training.route('/metrics/<training_id>', methods=['GET'])
def view_metrics(training_id):
    """
    Rodo modelio treniravimo metrikų puslapį
    
    Args:
        training_id (str): Treniravimo sesijos ID
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname modelio konfigūraciją
    model_config = service.get_model_config(training_id)
    
    # Jei konfigūracija nerasta, grąžiname klaidą
    if not model_config:
        flash('Nerasta modelio konfigūracija', 'danger')
        return redirect(url_for('model_training.index'))
    
    # Gauname treniravimo metrikas
    all_metrics = service.get_model_metrics(training_id)
    
    # Jei metrikos nerastos, informuojame vartotoją
    if not all_metrics:
        flash('Nerastos modelio treniravimo metrikos', 'warning')
        metrics = []
        metrics_json = "[]"
        final_metrics = {
            'train_loss': 0,
            'val_loss': 0,
            'train_accuracy': 0,
            'val_accuracy': 0,
            'training_time': 0,
            'epochs_completed': 0
        }
        best_loss = 0
        best_loss_epoch = 0
        best_val_loss = 0
        best_val_loss_epoch = 0
        best_val_acc = 0
        best_val_acc_epoch = 0
        best_epoch = None
    else:
        # Sutvarkome metrikas
        metrics = []
        for epoch, epoch_metrics in all_metrics.items():
            if isinstance(epoch_metrics, dict):
                metrics.append(epoch_metrics)
        
        # Rūšiuojame metrikas pagal epochą
        metrics.sort(key=lambda x: int(x.get('epoch', 0)))
        
        # Konvertuojame į JSON stringą perduoti į JavaScript
        import json
        metrics_json = json.dumps(metrics)
        
        # Randame geriausias metrikas
        best_loss = min(metrics, key=lambda x: x.get('loss', float('inf'))).get('loss', 0)
        best_loss_epoch = min(metrics, key=lambda x: x.get('loss', float('inf'))).get('epoch', 0)
        
        best_val_loss = min(metrics, key=lambda x: x.get('val_loss', float('inf'))).get('val_loss', 0)
        best_val_loss_epoch = min(metrics, key=lambda x: x.get('val_loss', float('inf'))).get('epoch', 0)
        
        best_val_acc = max(metrics, key=lambda x: x.get('val_accuracy', 0)).get('val_accuracy', 0)
        best_val_acc_epoch = max(metrics, key=lambda x: x.get('val_accuracy', 0)).get('epoch', 0)
        
        # Nustatome, kuri epocha laikoma geriausia (pagal val_loss)
        best_epoch = 'val_loss'
        
        # Paimame paskutines metrikas kaip galutines
        if metrics:
            final_metrics = metrics[-1]
        else:
            final_metrics = {
                'train_loss': 0,
                'val_loss': 0,
                'train_accuracy': 0,
                'val_accuracy': 0,
                'training_time': 0,
                'epochs_completed': 0
            }
    
    # Perduodame duomenis į šabloną
    return render_template(
        'training/metrics.html',
        title="Modelio metrikos",
        model_config=model_config,
        training_id=training_id,
        metrics=metrics,
        metrics_json=metrics_json,
        final_metrics=final_metrics,
        best_loss=best_loss,
        best_loss_epoch=best_loss_epoch,
        best_val_loss=best_val_loss,
        best_val_loss_epoch=best_val_loss_epoch,
        best_val_acc=best_val_acc,
        best_val_acc_epoch=best_val_acc_epoch,
        best_epoch=best_epoch
    )

@model_training.route('/metrics/analysis/<training_id>', methods=['GET'])
def analyze_metrics(training_id):
    """
    Rodo modelio treniravimas metrikų analizės puslapį
    
    Args:
        training_id (str): Treniravimo sesijos ID
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname modelio konfigūraciją
    model_config = service.get_model_config(training_id)
    
    # Jei konfigūracija nerasta, grąžiname klaidą
    if not model_config:
        flash('Nerasta modelio konfigūracija', 'danger')
        return redirect(url_for('model_training.index'))
    
    # Gauname treniravimo metrikas
    all_metrics = service.get_model_metrics(training_id)
    
    # Jei metrikos nerastos, informuojame vartotoją
    if not all_metrics:
        flash('Nerastos modelio treniravimo metrikos', 'warning')
        return redirect(url_for('model_training.view_metrics', training_id=training_id))
    
    # Sutvarkome metrikas
    metrics = []
    for epoch, epoch_metrics in all_metrics.items():
        if isinstance(epoch_metrics, dict):
            metrics.append(epoch_metrics)
    
    # Rūšiuojame metrikas pagal epochą
    metrics.sort(key=lambda x: int(x.get('epoch', 0)))
    
    # Konvertuojame į JSON stringą perduoti į JavaScript
    import json
    metrics_json = json.dumps(metrics)
    
    # Perduodame duomenis į šabloną
    return render_template(
        'training/metrics_analysis.html',
        title="Metrikų analizė",
        model_config=model_config,
        training_id=training_id,
        metrics=metrics,
        metrics_json=metrics_json
    )

@model_training.route('/api/metrics/export/<training_id>', methods=['GET'])
def export_metrics(training_id):
    """
    API endpointas metrikų eksportavimui į CSV
    
    Args:
        training_id (str): Treniravimo sesijos ID
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Tikriname, ar modelis egzistuoja
    model_config = service.get_model_config(training_id)
    if not model_config:
        return jsonify({'error': 'Modelis nerastas'}), 404
    
    # Nustatome, ar įtraukti pokyčius
    include_changes = request.args.get('include_changes', 'true').lower() == 'true'
    
    # Gauname CSV turinį
    csv_content = service.export_metrics_to_csv(training_id, include_changes)
    
    if not csv_content:
        return jsonify({'error': 'Nepavyko eksportuoti metrikų'}), 500
    
    # Nustatome atsakymo antraštes
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = f"attachment; filename=metrics_{training_id}.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response

@model_training.route('/models/<string:training_id>/version', methods=['GET', 'POST'])
def create_model_version(training_id):
    """
    Sukuria naują modelio versiją
    """
    model_service = ModelService()
    
    # Patikriname, ar modelis egzistuoja
    model_config = model_service.load_model_config(training_id)
    if not model_config:
        flash(f'Modelis su ID {training_id} nerastas.', 'danger')
        return redirect(url_for('model_training.model_history'))
    
    if request.method == 'POST':
        # Gauname duomenis iš formos
        version_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'parameters': {}
        }
        
        # Gauname parametrus
        for key in request.form:
            if key.startswith('param_'):
                param_name = key[6:]  # Pašaliname "param_" prefiksą
                value = request.form.get(key)
                
                # Konvertuojame reikšmes į tinkamą tipą
                if param_name in ['epochs', 'batch_size', 'layers', 'neurons']:
                    value = int(value)
                elif param_name in ['learning_rate', 'dropout']:
                    value = float(value)
                
                version_data['parameters'][param_name] = value
        
        # Sukuriame naują versiją
        new_training_id = model_service.create_model_version(training_id, version_data)
        
        if new_training_id:
            flash(f'Nauja modelio versija "{version_data["name"]}" sėkmingai sukurta.', 'success')
            return redirect(url_for('model_training.view_model', training_id=new_training_id))
        else:
            flash('Nepavyko sukurti naujos modelio versijos.', 'danger')
    
    # Grąžiname formą
    return render_template('training/create_version.html', model=model_config)

@model_training.route('/models/<string:training_id>/versions')
def model_versions(training_id):
    """
    Rodo modelio versijų istoriją
    """
    model_service = ModelService()
    
    # Patikriname, ar modelis egzistuoja
    model_config = model_service.load_model_config(training_id)
    if not model_config:
        flash(f'Modelis su ID {training_id} nerastas.', 'danger')
        return redirect(url_for('model_training.model_history'))
    
    # Gauname visų versijų informaciją
    versions = model_service.get_model_versions(training_id)
    
    return render_template('training/model_versions.html', model=model_config, versions=versions)

@model_training.route('/models/<string:training_id>/metrics')
def model_metrics(training_id):
    """
    Rodo modelio metrikų puslapį
    """
    model_service = ModelService()
    
    # Patikriname, ar modelis egzistuoja
    model_config = model_service.load_model_config(training_id)
    if not model_config:
        flash(f'Modelis su ID {training_id} nerastas.', 'danger')
        return redirect(url_for('model_training.model_history'))
    
    # Gauname metrikas
    metrics = model_service.get_model_metrics(training_id)
    
    return render_template('training/model_metrics.html', model=model_config, metrics=metrics)

@model_training.route('/models/<string:training_id>/download')
def download_model(training_id):
    """
    Leidžia atsisiųsti modelio failą
    """
    model_service = ModelService()
    
    # Patikriname, ar modelis egzistuoja
    model_config = model_service.load_model_config(training_id)
    if not model_config:
        flash(f'Modelis su ID {training_id} nerastas.', 'danger')
        return redirect(url_for('model_training.model_history'))
    
    # Gauname modelio failo kelią
    file_path = model_service.get_model_file_path(training_id)
    
    if not file_path or not os.path.exists(file_path):
        flash('Modelio failas nerastas.', 'danger')
        return redirect(url_for('model_training.model_history'))
    
    # Leidžiame atsisiųsti failą
    return send_file(file_path, as_attachment=True)

@model_training.route('/models/<string:training_id>/delete', methods=['POST'])
def delete_model(training_id):
    """
    Ištrina modelį ir visas jo versijas
    """
    model_service = ModelService()
    
    # Patikriname, ar modelis egzistuoja
    model_config = model_service.load_model_config(training_id)
    if not model_config:
        return jsonify({'success': False, 'message': 'Modelis nerastas'}), 404
    
    # Ištriname modelį
    success = model_service.delete_model(training_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Modelis sėkmingai ištrintas'}), 200
    else:
        return jsonify({'success': False, 'message': 'Klaida trinant modelį'}), 500

@model_training.route('/api/training/start', methods=['POST'])
def api_start_training():
    """
    API endpointas treniravimo pradžiai (su autentifikacija)
    """
    # Gauti duomenis iš užklausos
    data = request.json
    
    if not data or 'training_id' not in data:
        return jsonify({'success': False, 'message': 'Trūksta treniravimo ID'}), 400
    
    training_id = data['training_id']
    
    # Patikrinti, ar vartotojas turi teisę pradėti treniravimą
    # (čia turėtų būti jūsų autentifikacijos ir autorizacijos logika)
    user_id = 1  # Pvz., gauti iš sesijos ar ženklo
    
    # Pradėti treniravimą
    service = ModelService()
    success = service.start_training(training_id, user_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Treniravimas pradėtas'}), 200
    else:
        return jsonify({'success': False, 'message': 'Klaida pradedant treniravimą'}), 500

@model_training.route('/api/training/stop', methods=['POST'])
def api_stop_training():
    """
    API endpointas treniravimo sustabdymui (su autentifikacija)
    """
    # Gauti duomenis iš užklausos
    data = request.json
    
    if not data or 'training_id' not in data:
        return jsonify({'success': False, 'message': 'Trūksta treniravimo ID'}), 400
    
    training_id = data['training_id']
    
    # Patikrinti, ar vartotojas turi teisę sustabdyti treniravimą
    # (čia turėtų būti jūsų autentifikacijos ir autorizacijos logika)
    user_id = 1  # Pvz., gauti iš sesijos ar ženklo
    
    # Sustabdyti treniravimą
    service = ModelService()
    success = service.stop_training(training_id, user_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Treniravimas sustabdytas'}), 200
    else:
        return jsonify({'success': False, 'message': 'Klaida sustabdant treniravimą'}), 500

@model_training.route('/api/training/status/<training_id>', methods=['GET'])
def api_get_training_status(training_id):
    """
    API endpointas treniravimo būsenos gavimui (su autentifikacija)
    
    Args:
        training_id (str): Treniravimo sesijos ID
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname treniravimo būseną
    status = service.get_training_status(training_id)
    
    # Jei būsena nerasta, grąžiname klaidos kodą
    if not status:
        return jsonify({'error': 'Treniravimo sesija nerasta'}), 404
    
    # Grąžiname būseną JSON formatu
    return jsonify(status)


@model_training.route('/api/training/save-template', methods=['POST'])
def api_save_template():
    """
    API endpointas modelio parametrų šablono išsaugojimui (su autentifikacija)
    """
    try:
        # Gauname duomenis iš POST užklausos
        data = request.json
        
        if not data or 'name' not in data or 'params' not in data:
            return jsonify({'success': False, 'message': 'Trūksta reikiamų duomenų (name, params)'}), 400
        
        # Gauname šablono pavadinimą ir parametrus
        template_name = data['name']
        params = data['params']
        
        # Pridedame išsaugojimo datą
        params['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Išsaugome šabloną (panaudojant ModelService)
        service = ModelService()
        success = service.save_model_template(template_name, params)
        
        if success:
            return jsonify({'success': True, 'message': f'Šablonas "{template_name}" sėkmingai išsaugotas'})
        else:
            return jsonify({'success': False, 'message': 'Klaida išsaugant šabloną'}), 500
            
    except Exception as e:
        # Apdorojame nenumatytas klaidas
        return jsonify({'success': False, 'message': f'Įvyko klaida: {str(e)}'}), 500

@model_training.route('/api/training/get-templates', methods=['GET'])
def api_get_templates():
    """
    API endpointas visų išsaugotų modelio parametrų šablonų gavimui (su autentifikacija)
    """
    try:
        # Gauname visus šablonus (panaudojant ModelService)
        service = ModelService()
        templates = service.get_model_templates()
        
        return jsonify({'success': True, 'templates': templates})
        
    except Exception as e:
        # Apdorojame nenumatytas klaidas
        return jsonify({'success': False, 'message': f'Įvyko klaida: {str(e)}'}), 500

@model_training.route('/api/training/delete-template/<template_name>', methods=['DELETE'])
def api_delete_template(template_name):
    """
    API endpointas modelio parametrų šablono ištrinimui (su autentifikacija)
    """
    try:
        # Triname šabloną (panaudojant ModelService)
        service = ModelService()
        success = service.delete_model_template(template_name)
        
        if success:
            return jsonify({'success': True, 'message': f'Šablonas "{template_name}" sėkmingai ištrintas'})
        else:
            return jsonify({'success': False, 'message': 'Klaida trinant šabloną arba šablonas nerastas'}), 404
            
    except Exception as e:
        # Apdorojame nenumatytas klaidas
        return jsonify({'success': False, 'message': f'Įvyko klaida: {str(e)}'}), 500

@model_training.route('/models/<string:training_id>/export/pdf', methods=['GET'])
def export_model_to_pdf(training_id):
    """
    Eksportuoja modelio parametrus ir rezultatus į PDF ataskaitą
    """
    # Inicializuojame servisus
    model_service = ModelService()
    pdf_service = PdfGenerator()
    
    # Patikriname, ar modelis egzistuoja
    model_config = model_service.load_model_config(training_id)
    if not model_config:
        flash(f'Modelis su ID {training_id} nerastas.', 'danger')
        return redirect(url_for('model_training.model_history'))
    
    # Gauname metrikas
    metrics = model_service.get_model_metrics(training_id)
    
    # Generuojame PDF
    pdf_path = pdf_service.generate_model_report(training_id, model_config, metrics)
    
    if not pdf_path:
        flash('Klaida generuojant PDF ataskaitą.', 'danger')
        return redirect(url_for('model_training.view_model', training_id=training_id))
    
    # Nustatome failo pavadinimą
    model_name = model_config.get('name', f'modelis_{training_id}')
    safe_name = "".join([c if c.isalnum() else "_" for c in model_name])
    filename = f"{safe_name}_{training_id}_ataskaita.pdf"
    
    # Grąžiname PDF failą
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@model_training.route('/models')
def models():
    """
    Rodo modelių sąrašą.
    """
    return render_template('model_training/models.html')