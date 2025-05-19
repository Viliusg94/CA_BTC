from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.services.model_service import get_model_by_id

# Inicializuojame modelių įvertinimo maršrutus
model_evaluation = Blueprint('model_evaluation', __name__, url_prefix='/evaluation')

@model_evaluation.route('/')
def index():
    """
    Modelių įvertinimo pradinis puslapis
    """
    return render_template('evaluation/index.html', title='Modelių įvertinimas')

@model_evaluation.route('/model/<model_id>')
def model_details(model_id):
    """
    Modelio detalių puslapis
    
    Args:
        model_id (str): Modelio ID
    """
    # Gauname modelį pagal ID
    model = get_model_by_id(model_id)
    
    if not model:
        flash('Modelis nerastas', 'danger')
        return redirect(url_for('model_evaluation.index'))
    
    return render_template('evaluation/model_details.html', title=f'Modelio {model.name} detalės', model=model)

@model_evaluation.route('/model/<model_id>/validation')
def model_validation(model_id):
    """
    Modelio validavimo grafikų puslapis
    
    Args:
        model_id (str): Modelio ID
    """
    # Gauname modelį pagal ID
    model = get_model_by_id(model_id)
    
    if not model:
        flash('Modelis nerastas', 'danger')
        return redirect(url_for('model_evaluation.index'))
    
    return render_template('evaluation/model_validation.html', title=f'Modelio {model.name} validavimas', model=model)