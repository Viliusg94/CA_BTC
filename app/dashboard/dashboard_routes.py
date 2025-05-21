from flask import Blueprint, redirect, url_for

# Inicializuojame dashboard maršrutus
dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard.route('/')
def index():
    """
    Dashboard pradinis puslapis - nukreipiame į modelių įvertinimą
    """
    return redirect(url_for('model_evaluation.index'))