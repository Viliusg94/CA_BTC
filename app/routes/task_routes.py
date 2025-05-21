"""
Maršrutai užduočių valdymui
"""
# Užduočių valdymo maršrutai - atsakingi už HTTP užklausų apdorojimą
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
import traceback

from app.services.task_service import TaskService
from app.services.task_executor import task_executor
from app.models.task import TaskStatus

# Sukuriame Blueprint
task_routes = Blueprint('tasks', __name__, url_prefix='/tasks')

# Inicializuojame serviso objektą
task_service = TaskService()

# Nuoroda į modelių servisą (reikės pasirinkti modelį kuriant užduotį)
# Jei serviso nėra, sukuriame laikinąjį objektą su pavyzdiniais duomenimis
try:
    from app.services.model_service import get_models, get_model_by_id
except ImportError:
    # Pavyzdinė funkcija, jei tikros nėra
    def get_models():
        return [
            {"id": "model1", "name": "LSTM modelis"},
            {"id": "model2", "name": "GRU modelis"}
        ]
    
    def get_model_by_id(model_id):
        for model in get_models():
            if model["id"] == model_id:
                return model
        return None

@task_routes.route('/')
def task_list():
    """Rodo visų užduočių sąrašą"""
    try:
        # Gauname visas užduotis
        tasks = task_service.get_all_tasks()
        
        # Rūšiuojame pagal scheduled_time (naujiausios viršuje)
        tasks.sort(key=lambda x: x.scheduled_time if x.scheduled_time else datetime.min, reverse=True)
        
        return render_template(
            'training/task_list.html',
            tasks=tasks,
            title="Treniravimo užduotys"
        )
    except Exception as e:
        flash(f"Klaida gaunant užduočių sąrašą: {str(e)}", "danger")
        return redirect(url_for('index'))

@task_routes.route('/create', methods=['GET', 'POST'])
def create_task():
    """Užduoties sukūrimo puslapis"""
    try:
        if request.method == 'POST':
            # Gauname duomenis iš formos
            name = request.form.get('name')
            description = request.form.get('description')
            model_id = request.form.get('model_id')
            scheduled_date = request.form.get('scheduled_date')
            scheduled_time = request.form.get('scheduled_time')
            
            # Validuojame duomenis
            if not name or not model_id or not scheduled_date or not scheduled_time:
                flash("Visi privalomi laukai turi būti užpildyti", "danger")
                return render_template(
                    'training/task_form.html',
                    task=None,
                    models=get_models(),
                    title="Sukurti užduotį"
                )
            
            # Suformuojame scheduled_time datetime objektą
            scheduled_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            
            # Gauname treniravimo parametrus
            epochs = int(request.form.get('epochs', 10))
            batch_size = int(request.form.get('batch_size', 32))
            learning_rate = float(request.form.get('learning_rate', 0.001))
            save_checkpoints = 'save_checkpoints' in request.form
            early_stopping = 'early_stopping' in request.form
            
            training_params = {
                'epochs': epochs,
                'batch_size': batch_size,
                'learning_rate': learning_rate,
                'save_checkpoints': save_checkpoints,
                'early_stopping': early_stopping
            }
            
            # Sukuriame užduotį
            task = task_service.create_task(
                name=name,
                description=description,
                model_id=model_id,
                scheduled_time=scheduled_datetime,
                training_params=training_params
            )
            
            flash(f"Užduotis '{name}' sėkmingai sukurta", "success")
            return redirect(url_for('tasks.task_list'))
        else:
            # GET metodas - grąžiname tuščią formą
            return render_template(
                'training/task_form.html',
                task=None,
                models=get_models(),
                title="Sukurti užduotį"
            )
    except Exception as e:
        flash(f"Klaida kuriant užduotį: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('tasks.task_list'))

@task_routes.route('/edit/<task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    """Užduoties redagavimo puslapis"""
    try:
        # Gauname užduoties informaciją
        task = task_service.get_task_by_id(task_id)
        if not task:
            flash("Užduotis nerasta", "danger")
            return redirect(url_for('tasks.task_list'))
        
        if request.method == 'POST':
            # Tikriname, ar užduotis dar nepradėta vykdyti
            if task.status != TaskStatus.PENDING:
                flash("Galima redaguoti tik laukiančias vykdymo užduotis", "danger")
                return redirect(url_for('tasks.task_details', task_id=task_id))
            
            # Gauname duomenis iš formos
            name = request.form.get('name')
            description = request.form.get('description')
            model_id = request.form.get('model_id')
            scheduled_date = request.form.get('scheduled_date')
            scheduled_time = request.form.get('scheduled_time')
            
            # Validuojame duomenis
            if not name or not model_id or not scheduled_date or not scheduled_time:
                flash("Visi privalomi laukai turi būti užpildyti", "danger")
                return render_template(
                    'training/task_form.html',
                    task=task,
                    models=get_models(),
                    title="Redaguoti užduotį"
                )
            
            # Suformuojame scheduled_time datetime objektą
            scheduled_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            
            # Gauname treniravimo parametrus
            epochs = int(request.form.get('epochs', 10))
            batch_size = int(request.form.get('batch_size', 32))
            learning_rate = float(request.form.get('learning_rate', 0.001))
            save_checkpoints = 'save_checkpoints' in request.form
            early_stopping = 'early_stopping' in request.form
            
            training_params = {
                'epochs': epochs,
                'batch_size': batch_size,
                'learning_rate': learning_rate,
                'save_checkpoints': save_checkpoints,
                'early_stopping': early_stopping
            }
            
            # Atnaujiname užduotį
            task = task_service.update_task(
                task_id,
                name=name,
                description=description,
                model_id=model_id,
                scheduled_time=scheduled_datetime,
                training_params=training_params
            )
            
            flash(f"Užduotis '{name}' sėkmingai atnaujinta", "success")
            return redirect(url_for('tasks.task_list'))
        else:
            # GET metodas - grąžiname formą su užduoties duomenimis
            return render_template(
                'training/task_form.html',
                task=task,
                models=get_models(),
                title="Redaguoti užduotį"
            )
    except Exception as e:
        flash(f"Klaida redaguojant užduotį: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('tasks.task_list'))

@task_routes.route('/details/<task_id>')
def task_details(task_id):
    """Rodo užduoties detalią informaciją"""
    try:
        # Gauname užduoties informaciją
        task = task_service.get_task_by_id(task_id)
        if not task:
            flash("Užduotis nerasta", "danger")
            return redirect(url_for('tasks.task_list'))
        
        # Gauname modelio informaciją
        model = get_model_by_id(task.model_id)
        
        return render_template(
            'training/task_details.html',
            task=task,
            model=model,
            title=f"Užduoties '{task.name}' informacija"
        )
    except Exception as e:
        flash(f"Klaida gaunant užduoties informaciją: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('tasks.task_list'))

@task_routes.route('/delete/<task_id>', methods=['POST'])
def delete_task(task_id):
    """Ištrina užduotį"""
    try:
        # Gauname užduoties informaciją
        task = task_service.get_task_by_id(task_id)
        if not task:
            flash("Užduotis nerasta", "danger")
            return redirect(url_for('tasks.task_list'))
        
        # Tikriname, ar užduotis dar nepradėta vykdyti
        if task.status == TaskStatus.RUNNING:
            flash("Negalima ištrinti vykdomos užduoties", "danger")
            return redirect(url_for('tasks.task_list'))
        
        # Ištriname užduotį
        if task_service.delete_task(task_id):
            flash(f"Užduotis '{task.name}' sėkmingai ištrinta", "success")
        else:
            flash("Klaida trinant užduotį", "danger")
        
        return redirect(url_for('tasks.task_list'))
    except Exception as e:
        flash(f"Klaida trinant užduotį: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('tasks.task_list'))

@task_routes.route('/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """Atšaukia užduotį"""
    try:
        # Gauname užduoties informaciją
        task = task_service.get_task_by_id(task_id)
        if not task:
            flash("Užduotis nerasta", "danger")
            return redirect(url_for('tasks.task_list'))
        
        # Tikriname, ar užduotis dar nepradėta vykdyti
        if task.status != TaskStatus.PENDING:
            flash("Galima atšaukti tik laukiančias vykdymo užduotis", "danger")
            return redirect(url_for('tasks.task_details', task_id=task_id))
        
        # Atnaujiname užduoties būseną į "atšaukta"
        task_service.update_task_status(
            task_id,
            TaskStatus.CANCELED,
            log_message=f"Užduotis atšaukta vartotojo"
        )
        
        flash(f"Užduotis '{task.name}' sėkmingai atšaukta", "success")
        return redirect(url_for('tasks.task_list'))
    except Exception as e:
        flash(f"Klaida atšaukiant užduotį: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('tasks.task_list'))

@task_routes.route('/execute/<task_id>', methods=['POST'])
def execute_task(task_id):
    """Vykdo užduotį dabar"""
    try:
        # Gauname užduoties informaciją
        task = task_service.get_task_by_id(task_id)
        if not task:
            flash("Užduotis nerasta", "danger")
            return redirect(url_for('tasks.task_list'))
        
        # Tikriname, ar užduotis dar nepradėta vykdyti
        if task.status != TaskStatus.PENDING:
            flash("Galima vykdyti tik laukiančias vykdymo užduotis", "danger")
            return redirect(url_for('tasks.task_details', task_id=task_id))
        
        # Vykdome užduotį
        task_executor.execute_task_now(task_id)
        
        flash(f"Užduotis '{task.name}' pradėta vykdyti", "success")
        return redirect(url_for('tasks.task_details', task_id=task_id))
    except Exception as e:
        flash(f"Klaida vykdant užduotį: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('tasks.task_list'))

@task_routes.route('/calendar')
def calendar_view():
    """Kalendoriaus vaizdas su užduotimis"""
    return render_template(
        'training/calendar_view.html',
        title="Treniravimo kalendorius"
    )

# API maršrutai

@task_routes.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """API: Grąžina visas užduotis JSON formatu"""
    try:
        tasks = task_service.get_all_tasks()
        return jsonify([task.to_dict() for task in tasks])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@task_routes.route('/api/tasks/<date_str>', methods=['GET'])
def api_get_tasks_for_date(date_str):
    """API: Grąžina užduotis konkrečiai datai JSON formatu"""
    try:
        # Konvertuojame string į date objektą
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Gauname užduotis tai datai
        tasks = task_service.get_tasks_for_date(target_date)
        
        return jsonify([task.to_dict() for task in tasks])
    except ValueError:
        return jsonify({"error": "Neteisingas datos formatas. Naudokite YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@task_routes.route('/api/calendar_events', methods=['GET'])
def api_calendar_events():
    """API: Grąžina užduotis kalendoriaus formato duomenimis"""
    try:
        # Gauname visas užduotis
        tasks = task_service.get_all_tasks()
        
        # Konvertuojame užduotis į kalendoriaus įvykių formatą
        events = []
        for task in tasks:
            # Nustatome spalvą pagal užduoties būseną
            color = {
                TaskStatus.PENDING: "#6c757d",    # Pilka - laukianti
                TaskStatus.RUNNING: "#007bff",    # Mėlyna - vykdoma
                TaskStatus.COMPLETED: "#28a745",  # Žalia - įvykdyta
                TaskStatus.FAILED: "#dc3545",     # Raudona - nepavyko
                TaskStatus.CANCELED: "#ffc107"    # Geltona - atšaukta
            }.get(task.status, "#6c757d")
            
            # Sukuriame įvykį
            event = {
                "id": task.id,
                "title": task.name,
                "start": task.scheduled_time.isoformat() if task.scheduled_time else None,
                "description": task.description,
                "color": color,
                "status": task.status.value,
                "model_id": task.model_id
            }
            events.append(event)
        
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500