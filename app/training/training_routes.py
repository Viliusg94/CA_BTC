from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify

# SVARBU: kitas pavadinimas blueprint'ui!
model_training = Blueprint('model_training', __name__)

@model_training.route('/')
@model_training.route('/index')
def index():
    """
    Pagrindinis treniravimo puslapis
    """
    return render_template('training/index.html', title='Modelio treniravimas')

@model_training.route('/train')
def train():
    """
    Modelio treniravimo puslapis
    """
    return render_template('training/train.html', title='Treniruoti modelį')

@model_training.route('/monitor')
def monitor():
    """
    Treniravimo progreso stebėjimo puslapis
    """
    return render_template('training/monitor.html', title='Stebėti treniravimą')

@model_training.route('/optimize')
def optimize():
    """
    Hiperparametrų optimizavimo puslapis
    """
    return render_template('training/optimize.html', title='Hiperparametrų optimizavimas')

@model_training.route('/history')
def view_history():
    """
    Treniravimo istorijos peržiūros puslapis
    """
    return render_template('training/history.html', title='Treniravimo istorija')

@model_training.route('/checkpoints')
def checkpoints():
    """
    Tarpinių modelių išsaugojimų puslapis
    """
    return render_template('training/checkpoints.html', title='Tarpiniai išsaugojimai')

@model_training.route('/compare_models')
def compare_models():
    """
    Modelių palyginimo puslapis
    """
    return render_template('training/compare_models.html', title='Modelių palyginimas')

@model_training.route('/model_architectures')
def model_architectures():
    """
    Modelio architektūros vizualizacijos puslapis
    """
    return render_template('training/model_architectures.html', title='Modelio architektūra')

@model_training.route('/model_weights')
def model_weights():
    """
    Modelio svorių vizualizacijos puslapis
    """
    return render_template('training/model_weights.html', title='Modelio svoriai')

@model_training.route('/validation_graph')
def validation_graph():
    """
    Validavimo grafiko puslapis
    """
    return render_template('training/validation_graph.html', title='Validavimo grafikas')