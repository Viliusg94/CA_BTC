"""
Maršrutai užduočių valdymui
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import traceback

from app.services.task_service import TaskService
from app.services.weights_service import WeightsService  # Importuojame modelių servisą
from app.services.task_executor import task_executor
from app.models.task import TaskStatus

# Sukuriame Blueprint objektą
task_routes = Blueprint('tasks', __name__, url_prefix='/tasks')

# Inicializuojame serviso objektus
task_service = TaskService()
weights_service = WeightsService()

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
        return render_template('error.html', error=str(e))

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
                # Grąžiname į formą su esamais duomenimis
                return render_template(
                    'training/task_form.html',
                    task=request.form,
                    models=weights_service.get_models(),
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
                models=weights_service.get_models(),
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
                    models=weights_service.get_models(),
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
                models=weights_service.get_models(),
                title="Redaguoti užduotį"
            )
    except Exception as e:
        flash(f"Klaida redaguojant užduotį: {str(e)}", "danger")
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
        model = weights_service.get_model_by_id(task.model_id)
        
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
            log_message=f"Užduotis atšaukta {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        flash(f"Užduotis '{task.name}' sėkmingai atšaukta", "success")
        return redirect(url_for('tasks.task_list'))
    except Exception as e:
        flash(f"Klaida atšaukiant užduotį: {str(e)}", "danger")
        traceback.print_exc()
        return redirect(url_for('tasks.task_list'))

@task_routes.route('/calendar')
def calendar_view():
    """Kalendoriaus vaizdas su užduotimis"""
    return render_template(
        'training/calendar_view.html',
        title="Treniravimo kalendorius"
    )

@task_routes.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """API: Grąžina visas užduotis JSON formatu"""
    try:
        tasks = task_service.get_all_tasks()
        return jsonify([task.to_dict() for task in tasks])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@task_routes.route('/api/tasks/<date>', methods=['GET'])
def api_get_tasks_for_date(date):
    """API: Grąžina užduotis konkrečiai datai JSON formatu"""
    try:
        # Konvertuojame string į date objektą
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Gauname užduotis tai datai
        tasks = task_service.get_tasks_for_date(target_date)
        
        return jsonify([task.to_dict() for task in tasks])
    except Exception as e:
        return jsonify({"error": str(e)}), 500