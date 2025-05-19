"""
Prekybos maršrutai
---------------
Šis modulis apibrėžia prekybos maršrutus (endpoints).
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.trading.chart_data import get_price_data, get_portfolio_history
from app.services.scheduler_service import scheduler_service
from datetime import datetime, timedelta
import json
from app.routes.scheduler import scheduler

# Sukuriame Blueprint objektą
trading = Blueprint('trading', __name__, url_prefix='/trading')

@trading.route('/')
def index():
    """Prekybos skydelis"""
    # Čia galima pridėti logiką duomenų gavimui
    btc_price = 50000  # Pavyzdinis BTC kursas
    
    # Grąžiname šabloną su duomenimis
    return render_template(
        'trading/index.html', 
        title='Prekyba',
        btc_price=btc_price
    )

@trading.route('/simulate', methods=['GET', 'POST'])
def simulate():
    """Prekybos simuliacija"""
    if request.method == 'POST':
        # Gauname formos duomenis
        capital = request.form.get('capital', type=float)
        days = request.form.get('days', type=int)
        
        # Tikriname ar duomenys validūs
        if not capital or capital <= 0:
            flash('Pradinis kapitalas turi būti teigiamas skaičius', 'danger')
            return redirect(url_for('trading.simulate'))
        
        if not days or days <= 0:
            flash('Dienų skaičius turi būti teigiamas skaičius', 'danger')
            return redirect(url_for('trading.simulate'))
        
        # Čia būtų simuliacijos paleidimo logika
        flash(f'Simuliacija paleista su {capital}€ kapitalu per {days} dienas', 'success')
        return redirect(url_for('trading.index'))
    
    # GET užklausos atveju tiesiog rodome formą
    return render_template('trading/simulate.html', title='Simuliacija')

# NAUJI API ENDPOINTS GRAFIKAMS

@trading.route('/api/price-data')
def price_data_api():
    """
    API endpoint kainos duomenims gauti
    """
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1h')
    limit = request.args.get('limit', 100, type=int)
    
    data = get_price_data(symbol, interval, limit)
    return jsonify(data)

@trading.route('/api/portfolio-history')
def portfolio_history_api():
    """
    API endpoint portfelio istorijos duomenims gauti
    """
    days = request.args.get('days', 30, type=int)
    
    data = get_portfolio_history(days)
    return jsonify(data)

@trading.route('/api/candlestick-data')
def candlestick_data_api():
    """
    API endpoint žvakių grafiko duomenims gauti
    """
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1h')
    limit = request.args.get('limit', 100, type=int)
    
    from app.trading.candlestick import get_candlestick_data
    data = get_candlestick_data(symbol, interval, limit)
    
    return jsonify(data)

@trading.route('/api/signals')
def signals_api():
    """
    API endpoint prekybos signalams gauti
    """
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1h')
    
    from app.trading.chart_data import get_candlestick_data
    from app.trading.signals import generate_signals_from_indicators, get_formatted_signals
    
    # Gauname kainos duomenis
    data = get_candlestick_data(symbol, interval, limit=100)
    
    # Generuojame signalus
    buy_signals, sell_signals = generate_signals_from_indicators(data)
    
    # Formatuojame duomenis HTML rodymui
    formatted_buy = get_formatted_signals(buy_signals)
    formatted_sell = get_formatted_signals(sell_signals)
    
    result = {
        'buySignals': buy_signals,
        'sellSignals': sell_signals,
        'formattedBuy': formatted_buy,
        'formattedSell': formatted_sell
    }
    
    return jsonify(result)

@trading.route('/charts')
def charts():
    """Grafikų puslapis"""
    return render_template('trading/charts.html', title='Grafikų analizė')

@trading.route('/candlestick')
def candlestick():
    """Žvakių grafiko puslapis"""
    return render_template('trading/candlestick.html', title='Žvakių grafikas')

# Papildyti failą šiais maršrutais

# Sukurkite naują blueprint
trading_scheduler = Blueprint('trading_scheduler', __name__, url_prefix='/trading/scheduler')

@trading_scheduler.route('/calendar_view')
def trading_calendar_view():
    """
    Prekybos kalendoriaus peržiūros puslapis
    """
    return render_template('scheduler/calendar_view.html', title='Prekybos kalendorius')