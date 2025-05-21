from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, abort
import os
import json
import logging
from app.services.model_service import ModelService
from app.services.data_service import DataService

# Inicializuojame modelio vertinimo maršrutus
model_evaluation = Blueprint('model_evaluation', __name__, url_prefix='/evaluation')

@model_evaluation.route('/')
def index():
    """
    Modelio vertinimo pradinis puslapis
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname visų modelių sąrašą
    models = service.get_all_models()
    
    # Grąžiname šabloną su modelių sąrašu
    return render_template('evaluation/index.html', title='Modelių vertinimas', models=models)