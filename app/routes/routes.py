"""
Šis modulis saugo visus Flask maršrutus, kad išvengtume dubliavimo
"""

import logging
from flask import render_template, request, jsonify, flash, redirect

# Importuojame reikiamas funkcijas iš kitų modulių
from app.utils import get_real_bitcoin_price, calculate_price_change, generate_dummy_price_history, generate_price_predictions

# Logger
logger = logging.getLogger(__name__)

def init_routes(app, model_manager=None):
    """
    Inicijuoja visus maršrutus Flask aplikacijai
    
    Args:
        app: Flask aplikacijos objektas
        model_manager: ModelManager objektas (arba None)
    """
    
    @app.route('/')
    def index():
        """Pagrindinis puslapis su kainos grafiku ir prognozėmis"""
        try:
            # Gauname dabartinę Bitcoin kainą
            current_price = get_real_bitcoin_price()
            if current_price is None:
                current_price = 45000.0  # Numatytoji reikšmė
                
            # Gauname Bitcoin kainos istoriją
            try:
                from trading.binance_api import get_btc_price_history
                price_history = get_btc_price_history()
            except (ImportError, ModuleNotFoundError):
                price_history = generate_dummy_price_history()
                
            # Gauname prognozes
            predictions = generate_price_predictions()
            
            # Apskaičiuojame kainos pokytį
            previous_price = None
            if price_history and len(price_history['close']) > 1:
                previous_price = price_history['close'][-2]
                
            price_change = calculate_price_change(current_price, previous_price)
            
            # Grąžiname HTML šabloną
            return render_template('index.html', 
                                  latest_price=current_price,
                                  price_history=price_history,
                                  predictions=predictions,
                                  price_change=price_change)
        except Exception as e:
            logger.error(f"Klaida index endpoint'e: {str(e)}")
            flash(f"Klaida užkraunant puslapį: {str(e)}", 'error')
            return render_template('error.html', error=str(e))
    
    @app.route('/predict')
    def predict():
        """
        LSTM modelio prognozavimo puslapis
        """
        try:
            logger.info("Užkrauna predict puslapį")
            
            # Gauname dabartinę Bitcoin kainą
            current_price = get_real_bitcoin_price()
            if current_price is None:
                current_price = 45000.0  # Numatytoji reikšmė
                
            # Gauname Bitcoin kainos istoriją
            try:
                from trading.binance_api import get_btc_price_history
                price_history = get_btc_price_history()
            except (ImportError, ModuleNotFoundError):
                price_history = generate_dummy_price_history()
                
            # Gauname prognozes
            predictions = generate_price_predictions()
            
            # Apskaičiuojame kainos pokytį
            previous_price = None
            if price_history and len(price_history['close']) > 1:
                previous_price = price_history['close'][-2]
                
            price_change = calculate_price_change(current_price, previous_price)
            
            # Grąžiname HTML šabloną
            return render_template('predict.html', 
                                  latest_price=current_price,
                                  price_history=price_history,
                                  predictions=predictions,
                                  price_change=price_change)
        except Exception as e:
            logger.error(f"Klaida predict endpoint'e: {str(e)}")
            flash(f"Klaida užkraunant puslapį: {str(e)}", 'error')
            return redirect('/')
    
    @app.route('/api/btc_price/current')
    def current_btc_price():
        """API endpoint dabartinei BTC kainai gauti"""
        try:
            # Bandome naudoti modulio funkciją
            try:
                from trading.binance_api import get_current_btc_price
                price = get_current_btc_price()
            except (ImportError, ModuleNotFoundError):
                # Jei nepavyksta, naudojame atsarginę funkciją
                price = get_real_bitcoin_price()
            
            if price is None:
                return jsonify({'error': 'Nepavyko gauti kainos'}), 500
                
            return jsonify({'price': price})
        except Exception as e:
            logger.error(f"Klaida API endpoint'e: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/train_model', methods=['POST'])
    def train_model():
        """
        Apmoko pasirinktą modelį pagal pateiktą užklausą
        """
        try:
            # Gauname modelio tipą iš užklausos parametrų (arba nustatome numatytąjį)
            model_type = request.form.get('model_type', 'lstm')
            
            logger.info(f"Pradedamas modelio {model_type.upper()} apmokymas")
            
            # Jei turite model_manager, naudokite jį
            if model_manager:
                # Pradėkite apmokymo procesą
                model_manager.train_model(model_type)
                
                # Rodome sėkmės pranešimą vartotojui
                flash(f'Modelio {model_type.upper()} apmokymas pradėtas sėkmingai!', 'success')
            else:
                # Jei model_manager nerastas, praneškite apie klaidą
                logger.error("ModelManager nerastas")
                flash(f'Klaida: ModelManager nerastas', 'error')
            
            # Nukreipiame atgal į predict puslapį
            return redirect('/predict')
        except Exception as e:
            logger.error(f"Klaida apmokant modelį: {str(e)}")
            
            # Rodome klaidos pranešimą vartotojui
            flash(f'Klaida apmokant modelį: {str(e)}', 'error')
            
            # Nukreipiame atgal į predict puslapį
            return redirect('/predict')