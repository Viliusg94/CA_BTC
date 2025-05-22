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