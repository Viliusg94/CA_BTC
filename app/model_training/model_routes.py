from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database.models import Model, Template
from app.database import db
from app.trading.binance_api import get_candlestick_data
from datetime import datetime
import time
import logging
import json
import os
import numpy as np
import pandas as pd

# Sukuriame maršrutus
model_training = Blueprint('model_training', __name__, url_prefix='/model-training')
logger = logging.getLogger(__name__)

@model_training.route('/')
def list_models():
    """Rodo visų modelių sąrašą"""
    # Gauti filtravimo parametrus
    model_type = request.args.get('type')
    status = request.args.get('status')
    min_accuracy = request.args.get('min_accuracy')
    
    # Formuoti bazinę užklausą
    query = db.query(Model)
    
    # Taikyti filtrus
    if model_type:
        query = query.filter(Model.type == model_type)
    if status:
        query = query.filter(Model.status == status)
    if min_accuracy:
        min_acc = float(min_accuracy) / 100.0
        query = query.filter(Model.accuracy >= min_acc)
    
    # Gauti modelius
    models = query.order_by(Model.created_at.desc()).all()
    
    return render_template('training/models_list.html', models=models)

@model_training.route('/create', methods=['GET', 'POST'])
def create_model():
    """Naujo modelio kūrimo puslapis"""
    if request.method == 'POST':
        # Gauname duomenis iš formos
        name = request.form.get('name')
        model_type = request.form.get('type')
        template_id = request.form.get('template')
        description = request.form.get('description')
        parameters = request.form.get('parameters')
        
        # Validacija
        if not name or not model_type:
            flash('Prašome užpildyti visus būtinus laukus', 'danger')
            return redirect(url_for('model_training.create_model'))
        
        # Tikriname, ar modelis su tokiu pavadinimu jau egzistuoja
        existing_model = db.query(Model).filter(Model.name == name).first()
        if existing_model:
            flash(f'Modelis pavadinimu "{name}" jau egzistuoja', 'danger')
            return redirect(url_for('model_training.create_model'))
        
        # Sukuriame naują modelį
        try:
            # Jei pasirinktas šablonas, gauname jo parametrus
            template = None
            if template_id:
                template = db.query(Template).filter(Template.id == template_id).first()
                if template and template.parameters:
                    parameters = template.parameters
            
            # Sukuriame modelio įrašą duomenų bazėje
            new_model = Model(
                name=name,
                type=model_type,
                description=description,
                parameters=parameters,
                status='inactive',
                accuracy=0.0,
                created_at=datetime.now(),
                last_trained_at=datetime.now(),
                template_id=template_id if template_id else None
            )
            
            db.add(new_model)
            db.commit()
            
            flash(f'Modelis "{name}" sėkmingai sukurtas', 'success')
            return redirect(url_for('model_training.view_model', model_id=new_model.id))
            
        except Exception as e:
            db.rollback()
            logger.error(f"Klaida kuriant modelį: {str(e)}")
            flash(f'Klaida kuriant modelį: {str(e)}', 'danger')
            return redirect(url_for('model_training.create_model'))
    
    # GET užklausa
    templates = db.query(Template).all()
    return render_template('training/create_model.html', templates=templates)

@model_training.route('/view/<int:model_id>')
def view_model(model_id):
    """Rodo detalią informaciją apie modelį"""
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        flash('Modelis nerastas', 'danger')
        return redirect(url_for('model_training.list_models'))
    
    # Jei modelis turi šabloną, gauname jo informaciją
    template = None
    if model.template_id:
        template = db.query(Template).filter(Template.id == model.template_id).first()
    
    return render_template('training/view_model.html', model=model, template=template)

@model_training.route('/delete/<int:model_id>')
def delete_model(model_id):
    """Ištrina modelį"""
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        flash('Modelis nerastas', 'danger')
        return redirect(url_for('model_training.list_models'))
    
    try:
        db.delete(model)
        db.commit()
        flash(f'Modelis "{model.name}" sėkmingai ištrintas', 'success')
    except Exception as e:
        db.rollback()
        logger.error(f"Klaida trinant modelį: {str(e)}")
        flash(f'Klaida trinant modelį: {str(e)}', 'danger')
    
    return redirect(url_for('model_training.list_models'))

@model_training.route('/update/<int:model_id>', methods=['POST'])
def update_model_with_latest_data(model_id):
    """Apmoko esamą modelį su naujausiais duomenimis"""
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        return jsonify({'error': 'Modelis nerastas'}), 404
    
    try:
        # Atnaujinti modelio statusą
        model.status = 'training'
        db.commit()
        
        # Gauti naujausius duomenis iš Binance
        latest_data = get_candlestick_data(timeframe='3m', interval='1d')
        
        if not latest_data or len(latest_data) < 10:
            return jsonify({'error': 'Nepavyko gauti pakankamai duomenų iš Binance API'}), 400
        
        # Apdoroti duomenis modelio apmokymui
        df = pd.DataFrame(latest_data)
        
        # Čia būtų jūsų modelio apmokymo logika
        # Šiame pavyzdyje tiesiog simuliuosime apmokymą
        
        # Simuliuojame apmokymo procesą
        time.sleep(3)
        
        # Užregistruojame laiką
        start_time = time.time()
        
        # Simuliuojame modelio apmokymo rezultatus
        previous_accuracy = model.accuracy
        new_accuracy = min(previous_accuracy + np.random.uniform(-0.05, 0.15), 0.99)
        accuracy_change = new_accuracy - previous_accuracy
        
        # Atnaujinti modelio parametrus
        model.accuracy = new_accuracy
        model.last_trained_at = datetime.now()
        model.status = 'active'
        db.commit()
        
        # Apskaičiuojame apmokymo laiką
        training_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'model_id': model.id,
            'new_accuracy': new_accuracy,
            'previous_accuracy': previous_accuracy,
            'accuracy_change': accuracy_change,
            'training_time': f"{training_time:.2f} s"
        })
        
    except Exception as e:
        # Jei įvyko klaida, atstatome modelio statusą
        model.status = 'inactive' if model.accuracy == 0 else 'active'
        db.commit()
        
        logger.error(f"Klaida apmokant modelį: {str(e)}")
        return jsonify({'error': f'Klaida apmokant modelį: {str(e)}'}), 500