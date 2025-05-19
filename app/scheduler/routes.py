from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from app.services.scheduler_service import scheduler_service

# Sukuriame Blueprint
scheduler = Blueprint('scheduler', __name__)

@scheduler.route('/task_queue')
def task_queue():
    """
    Atvaizduoja užduočių sąrašą su filtravimo galimybėmis
    """
    # Gaukime filtravimo parametrus
    status = request.args.get('status', '')
    frequency = request.args.get('frequency', '')
    priority = request.args.get('priority', '')
    
    # Puslapiavimui
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Užduočių skaičius puslapyje
    
    # Konvertuojame tekstinį prioritetą į skaitinį
    priority_val = None
    if priority:
        if priority == 'high':
            priority_val = 1
        elif priority == 'medium':
            priority_val = 5
        elif priority == 'low':
            priority_val = 10
        else:
            try:
                priority_val = int(priority)
            except ValueError:
                pass
    
    # Gauname užduotis iš serviso
    tasks, total_count = scheduler_service.get_tasks(
        page=page,
        per_page=per_page,
        status=status if status else None,
        frequency=frequency if frequency else None,
        priority=priority_val
    )
    
    # Apskaičiuojame puslapių skaičių
    pages = (total_count + per_page - 1) // per_page
    
    return render_template(
        'scheduler/task_queue.html',
        tasks=tasks,
        page=page,
        pages=pages,
        total_count=total_count
    )

@scheduler.route('/view_task/<task_id>')
def view_task(task_id):
    """
    Atvaizduoja užduoties detalią informaciją
    """
    task = scheduler_service.get_task_by_id(task_id)
    
    if not task:
        flash('Užduotis nerasta.', 'danger')
        return redirect(url_for('scheduler.task_queue'))
        
    return render_template('scheduler/view_task.html', task=task)

@scheduler.route('/run_task/<task_id>')
def run_task(task_id):
    """
    Paleidžia užduotį vykdyti tuojau pat
    """
    success = scheduler_service.run_task(task_id)
    
    if success:
        flash('Užduotis paleista vykdyti.', 'success')
    else:
        flash('Nepavyko paleisti užduoties.', 'danger')
        
    return redirect(url_for('scheduler.task_queue'))

@scheduler.route('/delete_task/<task_id>')
def delete_task(task_id):
    """
    Ištrina užduotį
    """
    success = scheduler_service.delete_task(task_id)
    
    if success:
        flash('Užduotis ištrinta.', 'success')
    else:
        flash('Nepavyko ištrinti užduoties.', 'danger')
        
    return redirect(url_for('scheduler.task_queue'))

@scheduler.route('/edit_task/<task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    """
    Užduoties redagavimas
    """
    # Šią funkciją galima įgyvendinti vėliau, kai bus sukurta forma
    task = scheduler_service.get_task_by_id(task_id)
    
    if not task:
        flash('Užduotis nerasta.', 'danger')
        return redirect(url_for('scheduler.task_queue'))
    
    # Kol kas tik grąžiname į sąrašą
    flash('Redagavimo funkcija dar neįgyvendinta.', 'warning')
    return redirect(url_for('scheduler.task_queue'))

@scheduler.route('/new_task', methods=['GET', 'POST'])
def new_task():
    """
    Naujos užduoties sukūrimas
    """
    # Šią funkciją galima įgyvendinti vėliau, kai bus sukurta forma
    flash('Naujos užduoties kūrimo funkcija dar neįgyvendinta.', 'warning')
    return redirect(url_for('scheduler.task_queue'))

@scheduler.route('/calendar_view')
def calendar_view():
    """
    Atvaizduoja užduočių kalendorių
    """
    # Šią funkciją galima įgyvendinti vėliau
    flash('Kalendoriaus funkcija dar neįgyvendinta.', 'warning')
    return redirect(url_for('scheduler.task_queue'))