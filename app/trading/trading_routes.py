from flask import Blueprint, render_template, request, jsonify
from app.trading.binance_api import get_candlestick_data
import logging

# Inicializuojame logger
logger = logging.getLogger(__name__)

# Inicializuojame trading maršrutus
trading = Blueprint('trading', __name__, url_prefix='/trading')

@trading.route('/')
def index():
    """
    Prekybos pradinis puslapis
    """
    return render_template('trading/index.html')

@trading.route('/candlestick')
def candlestick():
    """
    Žvakių grafiko puslapis
    """
    return render_template('trading/candlestick.html')

@trading.route('/charts')
def charts():
    """
    Grafikų analizės puslapis
    """
    return render_template('trading/charts.html')

@trading.route('/simulate')
def simulate():
    """
    Prekybos simuliacijos puslapis
    """
    return render_template('trading/simulate.html')

# API endpoint žvakių grafiko duomenims
@trading.route('/api/candlestick_data')
def candlestick_data_api():
    """API endpoint žvakių grafiko duomenims"""
    timeframe = request.args.get('timeframe', '1m')
    interval = request.args.get('interval', '1d')
    
    try:
        data = get_candlestick_data(timeframe, interval)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Klaida gaunant žvakių duomenis: {str(e)}")
        return jsonify({'error': str(e)}), 500