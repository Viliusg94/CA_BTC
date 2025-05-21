from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import sys
import json
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
from datetime import datetime, timedelta
import threading
import uuid

# Pridedame pagrindinį projekto katalogą į Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.model_manager import ModelManager
from app.utils.data_preprocessing import DataPreprocessor
from app.utils.visualization import create_charts

app = Flask(__name__)
app.secret_key = 'bitcoin_prediction_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Inicializuojame modelių valdytoją ir duomenų procesorių
model_manager = ModelManager()
data_processor = DataPreprocessor()

@app.route('/')
def index():
    """Pagrindinis puslapis su kainų grafikais ir modelių apžvalga"""
    # Gauname naujausią bitcoin kainą
    latest_price = data_processor.get_latest_price()
    
    # Gauname kainų istoriją grafikui
    price_history = data_processor.get_price_history(days=30)
    price_chart = create_charts.price_history_chart(price_history)
    price_chart_json = json.dumps(price_chart, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Gauname informaciją apie modelius
    models_info = model_manager.get_all_models_info()
    
    return render_template('index.html', 
                          latest_price=latest_price,
                          price_chart=price_chart_json,
                          models_info=models_info)

@app.route('/dashboard')
def dashboard():
    """Dashboardas su modelių palyginimais ir metrikomis"""
    # Gauname metrikas visiems modeliams
    metrics_df = model_manager.get_metrics_comparison()
    
    # Sukuriame metrikų palyginimo grafiką
    metrics_chart = create_charts.metrics_comparison_chart(metrics_df)
    metrics_chart_json = json.dumps(metrics_chart, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Gauname ansamblio modelio prognozes
    ensemble_data = model_manager.get_ensemble_predictions()
    ensemble_chart = create_charts.ensemble_prediction_chart(ensemble_data)
    ensemble_chart_json = json.dumps(ensemble_chart, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('dashboard.html',
                          metrics_df=metrics_df.to_html(classes='table table-striped'),
                          metrics_chart=metrics_chart_json,
                          ensemble_chart=ensemble_chart_json)

@app.route('/models')
def models_overview():
    """Modelių apžvalgos puslapis"""
    models_info = model_manager.get_all_models_info()
    
    # Sukuriame kiekvieno modelio prognozės grafiką
    model_charts = {}
    for model_name, model_info in models_info.items():
        if model_info['available']:
            model_predictions = model_manager.get_model_predictions(model_name)
            chart = create_charts.model_prediction_chart(model_name, model_predictions)
            model_charts[model_name] = json.dumps(chart, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('models.html',
                          models_info=models_info,
                          model_charts=model_charts)

@app.route('/training', methods=['GET', 'POST'])
def training():
    """Modelių apmokymo puslapis"""
    if request.method == 'POST':
        model_type = request.form.get('model_type')
        epochs = int(request.form.get('epochs', 50))
        batch_size = int(request.form.get('batch_size', 32))
        sequence_length = int(request.form.get('sequence_length', 24))
        
        # Inicijuojame modelio apmokymą
        training_id = model_manager.start_training(model_type, epochs, batch_size, sequence_length)
        
        flash(f"{model_type.upper()} modelio apmokymas pradėtas! Sekite progresą žemiau.", "success")
        return redirect(url_for('training_status', training_id=training_id))
    
    # GET užklausos atveju
    training_jobs = model_manager.get_active_training_jobs()
    return render_template('training.html', training_jobs=training_jobs)

@app.route('/training/<training_id>')
def training_status(training_id):
    """Modelio apmokymo statuso stebėjimo puslapis"""
    status = model_manager.get_training_status(training_id)
    if status is None:
        flash("Apmokymo užduotis nerasta!", "error")
        return redirect(url_for('training'))
    
    return render_template('training_status.html', status=status)

@app.route('/api/training_status/<training_id>')
def api_training_status(training_id):
    """API endpoint modelio apmokymo statusui gauti"""
    status = model_manager.get_training_status(training_id)
    if status is None:
        return jsonify({"error": "Apmokymo užduotis nerasta"}), 404
    return jsonify(status)

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    """Realaus laiko prognozių puslapis"""
    models_info = model_manager.get_all_models_info()
    available_models = {name: info for name, info in models_info.items() if info['available']}
    
    if request.method == 'POST':
        model_name = request.form.get('model_name')
        
        # Gauname paskutinius duomenis prognozei
        latest_data = data_processor.get_latest_data()
        
        # Gauname prognozę
        prediction_result = model_manager.make_prediction(model_name, latest_data)
        
        # Sukuriame prognozės grafiką
        prediction_chart = create_charts.prediction_chart(prediction_result)
        prediction_chart_json = json.dumps(prediction_chart, cls=plotly.utils.PlotlyJSONEncoder)
        
        return render_template('prediction.html',
                              models=available_models,
                              prediction=prediction_result,
                              prediction_chart=prediction_chart_json,
                              selected_model=model_name)
    
    # GET užklausos atveju
    return render_template('prediction.html', models=available_models)

@app.route('/api/models')
def api_models():
    """API endpoint modelių informacijai gauti"""
    models_info = model_manager.get_all_models_info()
    return jsonify(models_info)

@app.route('/api/ensemble')
def api_ensemble():
    """API endpoint ansamblio prognozėms gauti"""
    ensemble_data = model_manager.get_ensemble_predictions()
    return jsonify(ensemble_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)