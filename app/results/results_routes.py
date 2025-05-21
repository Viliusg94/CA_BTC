from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import logging
from datetime import datetime
from app.services.results_service import ResultsService

# Inicializuojame rezultatų maršrutus
results = Blueprint('results', __name__, url_prefix='/results')

@results.route('/')
def index():
    """
    Rezultatų pradinis puslapis
    """
    # Rodome pagrindinį rezultatų puslapį
    return render_template('results/index.html', title='Rezultatų analizė')

@results.route('/predictions')
def predictions_list():
    """
    Prognozių sąrašas
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    # Gauname modelio ID iš URL parametrų
    model_id = request.args.get('model_id')
    
    # Gauname prognozes, jei nurodytas modelis
    predictions = []
    if model_id:
        predictions = service.get_model_predictions(model_id)
    
    # Rodome prognozių sąrašą
    return render_template(
        'results/predictions.html',
        title='Prognozių rezultatai',
        predictions=predictions,
        model_id=model_id
    )

@results.route('/simulations')
def simulations_list():
    """
    Simuliacijų sąrašas
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    # TODO: Implementuoti simuliacijų gavimą iš duomenų bazės
    
    # Rodome simuliacijų sąrašą
    return render_template(
        'results/simulations.html',
        title='Simuliacijų rezultatai',
        simulations=[]
    )

@results.route('/metrics')
def metrics_list():
    """
    Metrikų sąrašas
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    # TODO: Implementuoti metrikų gavimą iš duomenų bazės
    
    # Rodome metrikų sąrašą
    return render_template(
        'results/metrics.html',
        title='Metrikų rezultatai',
        metrics=[]
    )

# API endpointai

@results.route('/api/predictions', methods=['POST'])
def api_save_prediction():
    """
    API endpointas prognozės išsaugojimui
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    try:
        # Gauname duomenis iš užklausos
        data = request.json
        
        if not data:
            return jsonify({'error': 'Trūksta duomenų'}), 400
        
        # Išsaugome prognozę
        prediction_id = service.save_prediction(data)
        
        if not prediction_id:
            return jsonify({'error': 'Nepavyko išsaugoti prognozės'}), 500
        
        # Grąžiname sėkmės pranešimą
        return jsonify({
            'success': True,
            'prediction_id': prediction_id,
            'message': 'Prognozė sėkmingai išsaugota'
        })
    
    except Exception as e:
        logging.error(f"Klaida išsaugant prognozę: {str(e)}")
        return jsonify({'error': str(e)}), 500

@results.route('/api/simulations', methods=['POST'])
def api_save_simulation():
    """
    API endpointas simuliacijos išsaugojimui
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    try:
        # Gauname duomenis iš užklausos
        data = request.json
        
        if not data:
            return jsonify({'error': 'Trūksta duomenų'}), 400
        
        # Išsaugome simuliaciją
        simulation_id = service.save_simulation(data)
        
        if not simulation_id:
            return jsonify({'error': 'Nepavyko išsaugoti simuliacijos'}), 500
        
        # Grąžiname sėkmės pranešimą
        return jsonify({
            'success': True,
            'simulation_id': simulation_id,
            'message': 'Simuliacija sėkmingai išsaugota'
        })
    
    except Exception as e:
        logging.error(f"Klaida išsaugant simuliaciją: {str(e)}")
        return jsonify({'error': str(e)}), 500

@results.route('/api/metrics', methods=['POST'])
def api_save_metric():
    """
    API endpointas metrikos išsaugojimui
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    try:
        # Gauname duomenis iš užklausos
        data = request.json
        
        if not data:
            return jsonify({'error': 'Trūksta duomenų'}), 400
        
        # Išsaugome metriką
        metric_id = service.save_metric(data)
        
        if not metric_id:
            return jsonify({'error': 'Nepavyko išsaugoti metrikos'}), 500
        
        # Grąžiname sėkmės pranešimą
        return jsonify({
            'success': True,
            'metric_id': metric_id,
            'message': 'Metrika sėkmingai išsaugota'
        })
    
    except Exception as e:
        logging.error(f"Klaida išsaugant metriką: {str(e)}")
        return jsonify({'error': str(e)}), 500

@results.route('/api/analyze/model/<model_id>', methods=['GET'])
def api_analyze_model(model_id):
    """
    API endpointas modelio analizei
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    try:
        # Analizuojame modelio rezultatus
        analysis_results = service.analyze_model(model_id)
        
        # Grąžiname analizės rezultatus
        return jsonify(analysis_results)
    
    except Exception as e:
        logging.error(f"Klaida analizuojant modelį: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
@results.route('/api/analyze/simulation/<simulation_id>', methods=['GET'])
def api_analyze_simulation(simulation_id):
    """
    API endpointas simuliacijos analizei
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    try:
        # Analizuojame simuliacijos rezultatus
        analysis_results = service.analyze_simulation(simulation_id)
        
        # Grąžiname analizės rezultatus
        return jsonify(analysis_results)
    
    except Exception as e:
        logging.error(f"Klaida analizuojant simuliaciją: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
@results.route('/api/analyze/compare_models', methods=['POST'])
def api_compare_models():
    """
    API endpointas modelių palyginimui
    """
    # Inicializuojame ResultsService
    service = ResultsService()
    
    try:
        # Gauname duomenis iš užklausos
        data = request.json
        
        if not data or 'model_ids' not in data:
            return jsonify({'error': 'Trūksta model_ids parametro'}), 400
            
        # Gauname modelių ID sąrašą
        model_ids = data['model_ids']
        
        # Palyginame modelius
        comparison_results = service.compare_models(model_ids)
        
        # Grąžiname palyginimo rezultatus
        return jsonify(comparison_results)
    
    except Exception as e:
        logging.error(f"Klaida lyginant modelius: {str(e)}")
        return jsonify({'error': str(e)}), 500