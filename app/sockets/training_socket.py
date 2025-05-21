from flask_socketio import emit, join_room
from flask import request
from app import socketio
from app.services.model_service import ModelService
import threading
import time
import logging
import json
from datetime import datetime

# Nustatome žurnalo objektą
logger = logging.getLogger(__name__)

# Aktyvių treniravimo gijų žodynas
active_training_threads = {}

# Sustabdymo žymių žodynas
stop_flags = {}

@socketio.on('connect')
def handle_connect():
    """
    Apdoroja kliento prisijungimą
    """
    logger.info(f"Klientas prisijungė: {request.sid}")
    emit('training_log', {'message': 'Prisijungta prie serverio', 'type': 'info'})

@socketio.on('disconnect')
def handle_disconnect():
    """
    Apdoroja kliento atsijungimą
    """
    logger.info(f"Klientas atsijungė: {request.sid}")

@socketio.on('join_training')
def handle_join_training(data):
    """
    Apdoroja kliento prisijungimą prie konkretaus treniravimo kanalo
    """
    training_id = data.get('training_id')
    
    if not training_id:
        emit('training_log', {'message': 'Nenurodyta treniravimo sesijos ID', 'type': 'error'})
        return
    
    # Prisijungiame prie "kambario" su treniravimo ID
    join_room(training_id)
    logger.info(f"Klientas {request.sid} prisijungė prie treniravimo {training_id}")
    
    # Gauname dabartinę treniravimo būseną
    service = ModelService()
    status = service.get_training_status(training_id)
    
    if status:
        # Siunčiame dabartinę būseną
        emit('training_status', {'status': status.get('status', 'not_started')}, room=training_id)
        
        # Jei treniravimas jau vyksta, siunčiame progresą
        if status.get('status') == 'in_progress':
            emit('training_progress', {
                'progress': status.get('progress', 0),
                'current_epoch': int(status.get('current_epoch', 0)),
                'total_epochs': int(status.get('total_epochs', 0))
            }, room=training_id)
            
            # Informuojame, kad treniravimas jau vyksta
            emit('training_log', {
                'message': f'Treniravimas jau vyksta (progresas: {status.get("progress", 0)}%)',
                'type': 'info'
            }, room=training_id)
        elif status.get('status') == 'completed':
            # Informuojame, kad treniravimas jau baigtas
            emit('training_log', {
                'message': 'Treniravimas jau baigtas',
                'type': 'success'
            }, room=training_id)
        elif status.get('status') == 'failed':
            # Informuojame, kad treniravimas nepavyko
            emit('training_log', {
                'message': 'Treniravimas nepavyko',
                'type': 'error'
            }, room=training_id)
        elif status.get('status') == 'stopped':
            # Informuojame, kad treniravimas buvo sustabdytas
            emit('training_log', {
                'message': 'Treniravimas buvo sustabdytas',
                'type': 'warning'
            }, room=training_id)
        else:
            # Informuojame apie dabartinę būseną
            emit('training_log', {
                'message': f'Treniravimo būsena: {status.get("status", "nežinoma")}',
                'type': 'info'
            }, room=training_id)
    else:
        # Jei būsena nerasta, siunčiame pradžios būseną
        emit('training_status', {'status': 'not_started'}, room=training_id)
        emit('training_log', {
            'message': 'Treniravimo sesija paruošta',
            'type': 'info'
        }, room=training_id)

@socketio.on('start_training')
def handle_start_training(data):
    """
    Pradeda modelio treniravimą
    """
    training_id = data.get('training_id')
    
    if not training_id:
        emit('training_log', {'message': 'Nenurodyta treniravimo sesijos ID', 'type': 'error'})
        return
    
    # Tikriname, ar treniravimas jau vyksta
    if training_id in active_training_threads and active_training_threads[training_id].is_alive():
        emit('training_log', {'message': 'Treniravimas jau vyksta', 'type': 'warning'}, room=training_id)
        return
    
    # Gauname modelio konfigūraciją
    service = ModelService()
    model_config = service.get_model_config(training_id)
    
    if not model_config:
        emit('training_log', {'message': 'Nerasta modelio konfigūracija', 'type': 'error'}, room=training_id)
        return
    
    # Atnaujiname būseną į "pasiruošimo"
    service.update_training_status(training_id, 'preparing', 0)
    emit('training_status', {'status': 'preparing'}, room=training_id)
    emit('training_log', {'message': 'Ruošiamasi pradėti treniravimą...', 'type': 'info'}, room=training_id)
    
    # Nustatome, kad treniravimas nėra sustabdytas
    stop_flags[training_id] = False
    
    # Paleidžiame treniravimą atskiroje gijoje
    thread = threading.Thread(
        target=train_model_thread,
        args=(training_id, model_config)
    )
    thread.daemon = True  # Gija bus sustabdyta kai pagrindinė programa baigsis
    thread.start()
    
    # Įrašome giją į aktyvių gijų žodyną
    active_training_threads[training_id] = thread
    
    emit('training_log', {'message': 'Treniravimo procesas pradėtas', 'type': 'success'}, room=training_id)

@socketio.on('stop_training')
def handle_stop_training(data):
    """
    Sustabdo modelio treniravimą
    """
    training_id = data.get('training_id')
    
    if not training_id:
        emit('training_log', {'message': 'Nenurodyta treniravimo sesijos ID', 'type': 'error'})
        return
    
    # Tikriname, ar treniravimas vyksta
    if training_id not in active_training_threads or not active_training_threads[training_id].is_alive():
        emit('training_log', {'message': 'Treniravimas nevyksta arba jau baigtas', 'type': 'warning'}, room=training_id)
        return
    
    # Nustatome sustabdymo žymę
    stop_flags[training_id] = True
    
    # Atnaujiname būseną
    service = ModelService()
    service.update_training_status(training_id, 'stopped', 0)
    
    emit('training_status', {'status': 'stopped'}, room=training_id)
    emit('training_log', {'message': 'Treniravimas nutrauktas vartotojo nurodymu', 'type': 'warning'}, room=training_id)

@socketio.on('resume_training')
def handle_resume_training(data):
    """
    Atnaujina sustabdytą modelio treniravimą
    """
    training_id = data.get('training_id')
    
    if not training_id:
        emit('training_log', {'message': 'Nenurodyta treniravimo sesijos ID', 'type': 'error'})
        return
    
    # Tikriname, ar treniravimas buvo sustabdytas
    service = ModelService()
    status = service.get_training_status(training_id)
    
    if not status or status.get('status') != 'stopped':
        emit('training_log', {'message': 'Treniravimas nebuvo sustabdytas arba nerasta sesija', 'type': 'warning'}, room=training_id)
        return
    
    # Gauname modelio konfigūraciją
    model_config = service.get_model_config(training_id)
    
    if not model_config:
        emit('training_log', {'message': 'Nerasta modelio konfigūracija', 'type': 'error'}, room=training_id)
        return
    
    # Atnaujiname būseną į "pasiruošimo"
    service.update_training_status(training_id, 'preparing', 0)
    emit('training_status', {'status': 'preparing'}, room=training_id)
    emit('training_log', {'message': 'Ruošiamasi atnaujinti treniravimą...', 'type': 'info'}, room=training_id)
    
    # Nustatome, kad treniravimas nėra sustabdytas
    stop_flags[training_id] = False
    
    # Paleidžiame treniravimą atskiroje gijoje
    thread = threading.Thread(
        target=train_model_thread,
        args=(training_id, model_config, status.get('current_epoch', 0))
    )
    thread.daemon = True
    thread.start()
    
    # Įrašome giją į aktyvių gijų žodyną
    active_training_threads[training_id] = thread
    
    emit('training_log', {'message': 'Treniravimo procesas atnaujintas', 'type': 'success'}, room=training_id)

def train_model_thread(training_id, model_config, start_epoch=0):
    """
    Vykdo modelio treniravimą atskiroje gijoje ir siunčia atnaujinimus per WebSocket
    
    Args:
        training_id (str): Treniravimo sesijos ID
        model_config (dict): Modelio konfigūracija
        start_epoch (int, optional): Epocha, nuo kurios pradėti treniravimą (tęsiant sustabdytą)
    """
    # Importuojame socketio čia, kad išvengtumėme ciklinių importų
    from app import socketio
    import random
    import math
    import time
    from datetime import datetime
    
    service = ModelService()
    
    try:
        # Atnaujiname būseną į "vykdoma"
        service.update_training_status(training_id, 'in_progress', 0)
        socketio.emit('training_status', {'status': 'in_progress'}, room=training_id)
        socketio.emit('training_log', {'message': 'Treniravimas pradėtas', 'type': 'info'}, room=training_id)
        
        # Gauname treniravimo parametrus
        epochs = model_config['parameters'].get('epochs', 50)
        learning_rate = float(model_config['parameters'].get('learning_rate', 0.001))
        
        # Metrikų sąrašų inicializavimas
        training_metrics = {
            'loss': [],
            'accuracy': [],
            'val_loss': [],
            'val_accuracy': []
        }
        
        # Jei treniravimas tęsiamas, gauname anksčiau išsaugotas metrikas
        if start_epoch > 0:
            saved_metrics = service.get_model_metrics(training_id)
            if saved_metrics:
                # Užpildome metrikų sąrašus iš išsaugotų metrikų
                for i in range(1, start_epoch + 1):
                    if str(i) in saved_metrics:
                        epoch_metrics = saved_metrics[str(i)]
                        training_metrics['loss'].append(epoch_metrics.get('loss', 0))
                        training_metrics['accuracy'].append(epoch_metrics.get('accuracy', 0))
                        training_metrics['val_loss'].append(epoch_metrics.get('val_loss', 0))
                        training_metrics['val_accuracy'].append(epoch_metrics.get('val_accuracy', 0))
                
                socketio.emit('training_log', {
                    'message': f'Užkrautos anksčiau išsaugotos metrikos ({len(training_metrics["loss"])} epochos)',
                    'type': 'info'
                }, room=training_id)
        
        # Simuliuojame treniravimą per visas epochas
        start_time = time.time()
        
        for epoch in range(start_epoch + 1, epochs + 1):
            # Tikriname, ar treniravimas nebuvo sustabdytas
            if training_id in stop_flags and stop_flags[training_id]:
                socketio.emit('training_log', {
                    'message': 'Treniravimas sustabdytas',
                    'type': 'warning'
                }, room=training_id)
                break
            
            # Skaičiuojame progresą
            progress = int((epoch / epochs) * 100)
            
            # Simuliuojame treniravimo žingsnį
            # Čia būtų realus modelio treniravimas (viena epocha)
            
            # Simuliuojame metrikas
            # Klaidos funkcija (loss) paprastai mažėja eksponentiškai
            base_loss = 1.0 * math.exp(-0.05 * epoch)
            
            # Pridedame atsitiktinį triukšmą, kad būtų realistiškiau
            train_loss = base_loss + random.uniform(-0.05, 0.05)
            train_loss = max(0.01, train_loss)  # Minimumo apribojimas
            
            # Validacijos loss paprastai šiek tiek didesnis
            val_loss = train_loss * random.uniform(1.0, 1.3)
            
            # Tikslumas (accuracy) paprastai didėja su epochomis
            train_accuracy = min(0.99, 0.5 + 0.5 * (1 - math.exp(-0.05 * epoch)))
            train_accuracy += random.uniform(-0.03, 0.03)
            train_accuracy = max(0, min(1, train_accuracy))  # Ribos [0, 1]
            
            # Validacijos tikslumas paprastai šiek tiek mažesnis
            val_accuracy = train_accuracy * random.uniform(0.85, 0.98)
            val_accuracy = max(0, min(1, val_accuracy))  # Ribos [0, 1]
            
            # Išsaugome metrikas į sąrašus
            training_metrics['loss'].append(train_loss)
            training_metrics['accuracy'].append(train_accuracy)
            training_metrics['val_loss'].append(val_loss)
            training_metrics['val_accuracy'].append(val_accuracy)
            
            # Išsaugome metrikas dabartinei epochai
            epoch_metrics = {
                'epoch': epoch,
                'loss': train_loss,
                'accuracy': train_accuracy,
                'val_loss': val_loss,
                'val_accuracy': val_accuracy,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Išsaugome metrikas į duomenų bazę/failą
            service.save_epoch_metrics(training_id, epoch, epoch_metrics)
            
            # Siunčiame metrikas klientui
            socketio.emit('training_metrics', epoch_metrics, room=training_id)
            
            # Atnaujiname būseną kas epochą
            service.update_training_status(
                training_id, 
                'in_progress', 
                progress, 
                current_epoch=epoch, 
                total_epochs=epochs
            )
            
            # Siunčiame progreso atnaujinimą
            socketio.emit('training_progress', {
                'progress': progress,
                'current_epoch': epoch,
                'total_epochs': epochs
            }, room=training_id)
            
            # Skaičiuojame likusį laiką
            elapsed_time = time.time() - start_time
            time_per_epoch = elapsed_time / (epoch - start_epoch)
            remaining_epochs = epochs - epoch
            remaining_time = remaining_epochs * time_per_epoch
            
            # Formatuojame likusį laiką
            remaining_hours = int(remaining_time // 3600)
            remaining_minutes = int((remaining_time % 3600) // 60)
            remaining_seconds = int(remaining_time % 60)
            time_str = f"{remaining_hours:02d}:{remaining_minutes:02d}:{remaining_seconds:02d}"
            
            # Siunčiame žurnalo įrašą kas 5 epochas arba pirmą ir paskutinę
            if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
                socketio.emit('training_log', {
                    'message': f'Epocha {epoch}/{epochs} - loss: {train_loss:.4f}, val_loss: {val_loss:.4f}, '
                               f'acc: {train_accuracy:.4f}, val_acc: {val_accuracy:.4f}, likęs laikas: {time_str}',
                    'type': 'info'
                }, room=training_id)
            
            # Simuliuojame treniravimo laiką (1 sekundė per epochą)
            time.sleep(1)
        
        # Tikriname, ar treniravimas buvo baigtas, o ne sustabdytas
        if not (training_id in stop_flags and stop_flags[training_id]):
            # Treniravimas baigtas sėkmingai
            service.update_training_status(training_id, 'completed', 100, current_epoch=epochs, total_epochs=epochs)
            socketio.emit('training_status', {'status': 'completed'}, room=training_id)
            socketio.emit('training_log', {
                'message': 'Treniravimas sėkmingai baigtas!',
                'type': 'success'
            }, room=training_id)
            
            # Išsaugome galutinius treniravimo rezultatus
            final_metrics = {
                'train_loss': training_metrics['loss'][-1] if training_metrics['loss'] else 0,
                'val_loss': training_metrics['val_loss'][-1] if training_metrics['val_loss'] else 0,
                'train_accuracy': training_metrics['accuracy'][-1] if training_metrics['accuracy'] else 0,
                'val_accuracy': training_metrics['val_accuracy'][-1] if training_metrics['val_accuracy'] else 0,
                'training_time': time.time() - start_time,
                'epochs_completed': epoch,
                'learning_rate': learning_rate,
                'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Išsaugome visas metrikas
            final_metrics['metrics_history'] = {
                'epochs': list(range(1, epoch + 1)),
                'loss': training_metrics['loss'],
                'accuracy': training_metrics['accuracy'],
                'val_loss': training_metrics['val_loss'],
                'val_accuracy': training_metrics['val_accuracy']
            }
            
            service.save_model_results(training_id, final_metrics)
            
            socketio.emit('training_log', {
                'message': 'Treniravimo rezultatai išsaugoti',
                'type': 'info'
            }, room=training_id)
            
            # Pranešame apie treniravimo pabaigą
            elapsed_time = time.time() - start_time
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            socketio.emit('training_log', {
                'message': f'Treniravimo trukmė: {time_str}',
                'type': 'info'
            }, room=training_id)
        
    except Exception as e:
        # Įrašome klaidą į žurnalą
        logger.error(f"Klaida treniruojant modelį: {str(e)}")
        
        # Atnaujiname būseną į "nepavyko"
        service.update_training_status(training_id, 'failed', 0)
        socketio.emit('training_status', {'status': 'failed', 'message': str(e)}, room=training_id)
        socketio.emit('training_log', {
            'message': f'Klaida treniruojant modelį: {str(e)}',
            'type': 'error'
        }, room=training_id)