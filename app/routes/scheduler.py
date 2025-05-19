# Importuojame reikiamas bibliotekas
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services.scheduler_service import scheduler_service
from app import websocket_manager
import datetime

# Sukuriame blueprint
scheduler = Blueprint('scheduler', __name__)

# Tipiški maršrutai, kurie turėtų būti scheduler.py faile:
@scheduler.route('/new_task', methods=['GET'])
def new_task():
    """
    Naujos užduoties kūrimo puslapis
    """
    return render_template('scheduler/new_task.html', title='Nauja užduotis')

@scheduler.route('/calendar_view')
def calendar_view():
    """
    Kalendoriaus peržiūros puslapis
    """
    return render_template('scheduler/calendar_view.html', title='Užduočių kalendorius')

@scheduler.route('/task_queue')
def task_queue():
    """
    Užduočių eilės peržiūros puslapis
    """
    return render_template('scheduler/task_queue.html', title='Užduočių eilė')

@scheduler.route('/view_task/<task_id>')
def view_task(task_id):
    """
    Rodo užduoties detalę
    """
    task = scheduler_service.get_task_by_id(task_id)
    
    if not task:
        flash("Užduotis nerasta", "danger")
        return redirect(url_for('scheduler.task_queue'))
    
    return render_template('scheduler/view_task.html', task=task)

@scheduler.route('/run_task/<task_id>')
def run_task(task_id):
    """
    Paleidžia užduotį vykdyti dabar
    """
    success = scheduler_service.run_task(task_id)
    
    if success:
        flash("Užduotis paleista vykdyti", "success")
    else:
        flash("Nepavyko paleisti užduoties", "danger")
    
    return redirect(url_for('scheduler.task_queue'))

@scheduler.route('/delete_task/<task_id>')
def delete_task(task_id):
    """
    Užduoties ištrynimas
    """
    success = scheduler_service.delete_task(task_id)
    
    if success:
        flash("Užduotis ištrinta", "success")
    else:
        flash("Nepavyko ištrinti užduoties", "danger")
    
    return redirect(url_for('scheduler.task_queue'))

@scheduler.route('/api/task_status/<task_id>')
def task_status_api(task_id):
    """
    API endpoint užduoties būsenai gauti
    """
    task = scheduler_service.get_task_by_id(task_id)
    
    if not task:
        return jsonify({'error': 'Užduotis nerasta'}), 404
    
    # Grąžiname tik būtiną informaciją
    response = {
        'id': task_id,
        'status': task.get('status', 'unknown'),
        'progress': task.get('progress', 0)
    }
    
    return jsonify(response)

@scheduler.route('/api/calendar_events')
def calendar_events():
    """
    API endpoint, kuris grąžina užduotis kalendoriaus formatu
    """
    # Gauname parametrus iš užklausos (kalendoriaus pradžios ir pabaigos datos)
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    
    # Gauname visas užduotis
    all_tasks = scheduler_service.get_all_tasks()
    
    # Paverčiame užduotis į kalendoriaus įvykių formatą
    events = []
    
    for task in all_tasks:
        # Gauname vykdymo datą
        run_time_str = task.get('next_run_time') or task.get('start_time') or task.get('created_at')
        
        # Jei nėra datos, praleiskime
        if not run_time_str:
            continue
        
        try:
            # Konvertuojame string į datetime objektą
            run_time = datetime.datetime.strptime(run_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Dažnumo apdorojimas
            frequency = task.get('frequency', 'once')
            
            # Sukuriame pagrindinį įvykį
            event = {
                'id': task.get('id'),
                'title': task.get('name'),
                'start': run_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'allDay': False,
                'status': task.get('status', 'pending'),
                'frequency': frequency,
                'priority': task.get('priority', 5),
                'description': task.get('description', '')
            }
            
            events.append(event)
            
            # Jei užduotis periodinė ir turi kitą vykdymo laiką, pridedame papildomus įvykius
            if frequency != 'once' and task.get('status') != 'running':
                start_dt = run_time
                end_dt = datetime.datetime.now() + datetime.timedelta(days=30)  # Rodome mėnesį į priekį
                
                current_dt = start_dt
                while current_dt < end_dt:
                    # Nustatome kitą vykdymo laiką pagal dažnumą
                    if frequency == 'daily':
                        current_dt = current_dt + datetime.timedelta(days=1)
                    elif frequency == 'weekly':
                        current_dt = current_dt + datetime.timedelta(weeks=1)
                    elif frequency == 'monthly':
                        # Pridedame mėnesį (paprastas būdas, ne visiškai tikslus)
                        month = current_dt.month + 1
                        year = current_dt.year
                        if month > 12:
                            month = 1
                            year += 1
                        current_dt = current_dt.replace(year=year, month=month)
                    
                    # Pridedame papildomą įvykį
                    recurring_event = {
                        'id': task.get('id'),
                        'title': task.get('name'),
                        'start': current_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                        'allDay': False,
                        'status': 'pending',  # Būsimos užduotys visada pending
                        'frequency': frequency,
                        'priority': task.get('priority', 5),
                        'description': task.get('description', ''),
                        'color': '#aaa'  # Pilkesnis atspalvis būsimoms užduotims
                    }
                    
                    events.append(recurring_event)
        
        except Exception as e:
            print(f"Klaida apdorojant užduotį {task.get('id')}: {str(e)}")
    
    return jsonify(events)

@scheduler.route('/dashboard')
def dashboard():
    """
    Atvaizduoja užduočių statistikos ir stebėjimo sąsają
    """
    # Gauname visas užduotis
    all_tasks = scheduler_service.get_all_tasks()
    
    # Skaičiuojame statistiką
    stats = {
        'total': len(all_tasks),
        'pending': sum(1 for task in all_tasks if task.get('status') == 'pending'),
        'running': sum(1 for task in all_tasks if task.get('status') == 'running'),
        'completed': sum(1 for task in all_tasks if task.get('status') == 'completed'),
        'failed': sum(1 for task in all_tasks if task.get('status') == 'failed')
    }
    
    # Gauname vykdomas užduotis
    running_tasks = [task for task in all_tasks if task.get('status') == 'running']
    
    # Gauname neseniai pabaigtas užduotis (išrikiuotas pagal pabaigos laiką)
    recent_tasks = [task for task in all_tasks if task.get('status') in ['completed', 'failed'] and task.get('end_time')]
    recent_tasks.sort(key=lambda x: x.get('end_time', ''), reverse=True)
    recent_tasks = recent_tasks[:5]  # Tik 5 naujausios
    
    # Gauname artimiausiai vykdomas užduotis
    upcoming_tasks = [task for task in all_tasks if task.get('status') == 'pending' and task.get('next_run_time')]
    upcoming_tasks.sort(key=lambda x: x.get('next_run_time', ''))
    upcoming_tasks = upcoming_tasks[:5]  # Tik 5 artimiausios
    
    return render_template(
        'scheduler/dashboard.html',
        stats=stats,
        running_tasks=running_tasks,
        recent_tasks=recent_tasks,
        upcoming_tasks=upcoming_tasks
    )

@scheduler.route('/api/task_stats')
def task_stats():
    """
    API endpoint, kuris grąžina užduočių statistiką
    """
    # Gauname visas užduotis
    all_tasks = scheduler_service.get_all_tasks()
    
    # Skaičiuojame statistiką
    stats = {
        'total': len(all_tasks),
        'status': {
            'pending': sum(1 for task in all_tasks if task.get('status') == 'pending'),
            'running': sum(1 for task in all_tasks if task.get('status') == 'running'),
            'completed': sum(1 for task in all_tasks if task.get('status') == 'completed'),
            'failed': sum(1 for task in all_tasks if task.get('status') == 'failed')
        },
        'frequency': {
            'once': sum(1 for task in all_tasks if task.get('frequency') == 'once'),
            'daily': sum(1 for task in all_tasks if task.get('frequency') == 'daily'),
            'weekly': sum(1 for task in all_tasks if task.get('frequency') == 'weekly'),
            'monthly': sum(1 for task in all_tasks if task.get('frequency') == 'monthly')
        }
    }
    
    return jsonify(stats)

@scheduler.route('/api/running_tasks')
def api_running_tasks():
    """
    API endpoint, kuris grąžina šiuo metu vykdomas užduotis
    """
    # Gauname visas užduotis
    all_tasks = scheduler_service.get_all_tasks()
    
    # Filtruojame tik vykdomas užduotis
    running_tasks = [
        {
            'id': task.get('id'),
            'name': task.get('name'),
            'progress': task.get('progress', 0),
            'start_time': task.get('start_time')
        }
        for task in all_tasks if task.get('status') == 'running'
    ]
    
    return jsonify(running_tasks)

@scheduler.route('/api/send_notification', methods=['POST'])
def send_notification():
    """
    API endpoint tiesioginiams pranešimams siųsti
    """
    if not request.is_json:
        return jsonify({"error": "Turi būti JSON turinys"}), 400
    
    data = request.json
    
    # Būtini laukai
    title = data.get('title')
    message = data.get('message')
    status = data.get('status', 'info')  # info, success, warning, danger, primary
    
    if not title or not message:
        return jsonify({"error": "Būtini laukai: title, message"}), 400
    
    # Sukuriame pranešimą
    notification = {
        'type': 'notification',
        'title': title,
        'message': message,
        'status': status
    }
    
    # Siunčiame visiems
    try:
        websocket_manager.broadcast(notification)
        return jsonify({"success": True, "message": "Pranešimas išsiųstas"}), 200
    except Exception as e:
        return jsonify({"error": f"Klaida siunčiant pranešimą: {str(e)}"}), 500

# Pridėkite funkcijos apibrėžimą užduočių išsaugojimui
@scheduler.route('/tasks', methods=['POST'])
@scheduler.route('/tasks/<task_id>', methods=['POST'])
def save_task(task_id=None):
    """
    Užduoties išsaugojimo funkcija
    """
    # Čia bus užduoties išsaugojimo logika
    flash('Užduotis sėkmingai išsaugota!', 'success')
    return redirect(url_for('scheduler.calendar_view'))