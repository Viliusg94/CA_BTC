from flask import Blueprint, render_template, request, jsonify
from app.analysis.analysis_service import AnalysisService

analysis = Blueprint('analysis', __name__, url_prefix='/analysis')
analysis_service = AnalysisService()

@analysis.route('/')
def index():
    """Pagrindinis analizės puslapis"""
    return render_template('analysis/index.html')

@analysis.route('/graphs')
def graphs():
    """Grafikų vizualizacijos puslapis"""
    # Gauname Bitcoin kainos duomenis
    btc_data = analysis_service.get_bitcoin_price_data()
    
    # Gauname visus modelius, kurių metrikas norime atvaizduoti
    models = analysis_service.get_trained_models()
    
    # Perduodame duomenis į šabloną
    return render_template('analysis/graphs.html', 
                          btc_data=btc_data,
                          models=models)

@analysis.route('/api/graph-data')
def get_graph_data():
    """API endpoint grafikų duomenims gauti"""
    graph_type = request.args.get('type', 'price')
    timeframe = request.args.get('timeframe', '1y')
    model_id = request.args.get('model_id')
    
    data = analysis_service.get_graph_data(graph_type, timeframe, model_id)
    return jsonify(data)