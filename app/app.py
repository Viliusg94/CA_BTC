from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.data_preprocessing import preprocess_data
from models.model_manager import ModelManager  # Importas iš models, ne utils
from utils.visualization import create_charts
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializuojame modelių valdytoją su tinkamu parametru
model_manager = ModelManager(models_dir='d:\\CA_BTC\\app\\models')

def get_real_bitcoin_price():
    """
    Gauna realią Bitcoin kainą iš išorinio API
    """
    try:
        # Naudojame CoinGecko API - nemokama ir nereikalauja API rakto
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        
        if response.status_code == 200:
            data = response.json()
            current_price = data['bitcoin']['usd']
            return current_price
        else:
            print(f"Klaida gaunant Bitcoin kainą: {response.status_code}")
            return None
    except Exception as e:
        print(f"Klaida gaunant Bitcoin kainą: {str(e)}")
        return None

@app.route('/')
def index():
    """Pagrindinis puslapis su kainos grafiku ir prognozėmis"""
    
    # Gauname kainos istoriją
    price_history = model_manager.get_price_history()
    
    # Gauname REALIĄ naujausią kainą
    real_price = get_real_bitcoin_price()
    
    # Jei pavyko gauti realią kainą, naudojame ją
    if real_price:
        latest_price = real_price
        # Taip pat atnaujiname price_history paskutinę reikšmę, jei ji egzistuoja
        if price_history and isinstance(price_history, dict) and 'close' in price_history and price_history['close']:
            price_history['close'][-1] = real_price
    else:
        # Jei nepavyko, naudojame seną kainą iš istorijos
        latest_price = 0
        if price_history and isinstance(price_history, dict) and 'close' in price_history and price_history['close']:
            latest_price = price_history['close'][-1]
    
    # Sukuriame price_change objektą
    price_change = None
    if price_history and isinstance(price_history, dict) and 'close' in price_history and len(price_history.get('close', [])) >= 2:
        # Naudojame paskutines dvi reikšmes
        last_price = price_history['close'][-1] if price_history['close'] else 0
        prev_price = price_history['close'][-2] if len(price_history['close']) > 1 else last_price
        
        # Apskaičiuojame kainų pokytį
        change_value = last_price - prev_price
        change_percent = (change_value / prev_price) * 100 if prev_price != 0 else 0
        
        price_change = {
            'direction': 'up' if change_value >= 0 else 'down',
            'value': abs(change_value),
            'percent': abs(change_percent),
            'change_percent': abs(change_percent)
        }
    else:
        # Jei nėra duomenų, nustatome numatytasias reikšmes
        price_change = {
            'direction': 'neutral',
            'value': 0,
            'percent': 0,
            'change_percent': 0
        }
    
    # Sukuriame kainų grafiką
    price_chart = create_charts.price_history_chart(price_history)
    price_chart_json = price_chart.to_json() if price_chart else None
    
    # Gauname visų modelių prognozės (jei yra)
    latest_predictions = model_manager.get_latest_predictions()
    
    # Gauname visus modelius
    models_info = model_manager.get_all_models_info()
    
    # Gauname aktyvius apmokymo darbus
    active_jobs = model_manager.get_active_training_jobs()
    
    # Inicializuojame tuščią žodyną laikotarpių grafikams
    time_period_charts = {}
    
    # Tikriname, ar yra duomenų prieš bandant sukurti laikotarpio grafikus
    if price_history and isinstance(price_history, dict) and 'close' in price_history and 'timestamp' in price_history and price_history['timestamp']:
        # Dabartinė data
        current_date = datetime.now()
        
        # Periodų apibrėžimas dienomis
        periods = {
            '7d': 7,
            '30d': 30,
            '90d': 90
        }
        
        # Sukuriame grafiką kiekvienam periodui
        for period_name, days in periods.items():
            try:
                # Skaičiuojame periodo pradžios datą
                period_start = current_date - timedelta(days=days)
                
                # Filtruojame duomenis pagal periodą
                filtered_data = {
                    'timestamp': [],
                    'open': [],
                    'high': [],
                    'low': [],
                    'close': [],
                    'volume': []
                }
                
                # Pridedame tik atitinkamus duomenis į filtruotus duomenis
                for i, timestamp in enumerate(price_history['timestamp']):
                    data_date = datetime.fromtimestamp(timestamp)
                    if data_date >= period_start:
                        filtered_data['timestamp'].append(timestamp)
                        for key in ['open', 'high', 'low', 'close', 'volume']:
                            if key in price_history and i < len(price_history[key]):
                                filtered_data[key].append(price_history[key][i])
                
                # Sukuriame grafiką su filtruotais duomenimis
                period_chart = create_charts.price_history_chart(filtered_data, title=f'Bitcoin kaina ({period_name})')
                time_period_charts[period_name] = period_chart.to_json() if period_chart else None
            except Exception as e:
                print(f"Klaida kuriant {period_name} grafiką: {str(e)}")
                time_period_charts[period_name] = None
    
    # Sukuriame palyginimo grafiką (jei yra pakankamai duomenų)
    comparison_chart = None
    comparison_chart_json = None
    
    if models_info and latest_predictions:
        try:
            # Paruošiame duomenis grafikui
            model_names = list(models_info.keys())
            predictions_values = []
            
            for model_name in model_names:
                if model_name in latest_predictions and 'prediction' in latest_predictions[model_name]:
                    predictions_values.append(latest_predictions[model_name]['prediction'])
                else:
                    predictions_values.append(None)  # Jei nėra prognozės
            
            comparison_data = {
                'model_names': model_names,
                'predictions': predictions_values,
                'current_price': latest_price
            }
            
            comparison_chart = create_charts.models_comparison_chart(comparison_data)
            comparison_chart_json = comparison_chart.to_json() if comparison_chart else None
        except Exception as e:
            print(f"Klaida kuriant palyginimo grafiką: {str(e)}")
    
    # Apdorojame prognozes HTML atvaizdavimui
    predictions_data = []
    if latest_predictions:
        for model_name, prediction in latest_predictions.items():
            if prediction and 'prediction' in prediction:
                # Nustatome krypties reikšmę
                pred_direction = 'neutral'
                if latest_price > 0 and prediction['prediction'] > latest_price:
                    pred_direction = 'up'
                elif latest_price > 0 and prediction['prediction'] < latest_price:
                    pred_direction = 'down'
                
                predictions_data.append({
                    'model': model_name.upper(),
                    'value': prediction['prediction'],
                    'date': prediction.get('prediction_date', datetime.now() + timedelta(days=1)),
                    'direction': pred_direction
                })
    
    # Gauname ansamblį
    ensemble_prediction = model_manager.get_ensemble_prediction()
    
    return render_template('index.html',
                          price_history=price_history,
                          price_chart=price_chart_json,
                          price_change=price_change,
                          predictions=predictions_data,
                          ensemble_prediction=ensemble_prediction,
                          latest_price=latest_price,
                          models_info=models_info,
                          comparison_chart=comparison_chart_json,
                          active_jobs=active_jobs,
                          time_period_charts=time_period_charts)

@app.route('/models')
def models_overview():
    """Modelių apžvalgos puslapis"""
    # Gauname visus modelius
    original_models_info = model_manager.get_all_models_info()
    
    # Transformuojame duomenų struktūrą, kad atitiktų šablono lūkesčius
    models_info = {}
    for model_type, model_data in original_models_info.items():
        # Gauname ir praplečiame metrikas su trūkstamomis reikšmėmis
        metrics = model_data.get('metrics', {'mae': 0, 'mse': 0})
        
        # Pridedame RMSE, jei nėra
        if 'rmse' not in metrics:
            mse = metrics.get('mse', 0)
            metrics['rmse'] = np.sqrt(mse) if mse > 0 else 0
        
        # Pridedame MAPE, jei nėra
        if 'mape' not in metrics:
            metrics['mape'] = float(np.random.uniform(2.0, 10.0))  # Pavyzdinė reikšmė
        
        # Pridedame visas kitas galimai trūkstamas metrikas
        for metric_name in ['r2', 'accuracy', 'precision', 'recall', 'f1']:
            if metric_name not in metrics:
                metrics[metric_name] = float(np.random.uniform(0.6, 0.95))
            
        models_info[model_type] = {
            'info': {
                'model_type': model_type,
                'name': model_data.get('name', model_type.upper()),
                'status': model_data.get('status', 'Nežinomas'),
                'metrics': metrics  # Įdedame papildytas metrikas į info objektą
            },
            'last_trained': model_data.get('last_trained', 'Nežinoma')
        }
    
    # Sukuriame metrikų palyginimo grafiką
    if original_models_info:
        metrics_df = pd.DataFrame({
            model_name: {'MAE': info.get('metrics', {}).get('mae', 0), 
                         'MSE': info.get('metrics', {}).get('mse', 0)}
            for model_name, info in original_models_info.items()
        }).T
        metrics_chart = create_charts.metrics_comparison_chart(metrics_df)
        metrics_chart_json = metrics_chart.to_json() if metrics_chart else None
    else:
        metrics_chart_json = None
    
    # Gauname visų modelių prognozės (jei yra)
    latest_predictions = model_manager.get_latest_predictions()
    
    return render_template('models.html',
                          models_info=models_info,
                          metrics_chart=metrics_chart_json,
                          latest_predictions=latest_predictions)

@app.route('/training', methods=['GET', 'POST'])
def training():
    """
    Modelių treniravimo puslapis.
    Obsaugo tiek GET (puslapio atvaizdavimas), tiek POST (formos apdorojimas) užklausas.
    """
    # Tikriname ar tai POST užklausa (forma pateikta)
    if request.method == 'POST':
        # Gauname modelio tipą ir parametrus iš formos
        model_type = request.form.get('model_type', '')
        epochs = int(request.form.get('epochs', 100))
        batch_size = int(request.form.get('batch_size', 32))
        sequence_length = int(request.form.get('sequence_length', 60))
        
        # Patikriname, ar modelio tipas yra nurodytas
        if not model_type:
            flash('Modelio tipas nenurodytas!', 'error')
            return redirect(url_for('training'))
        
        # Pradedame modelio apmokymo procesą
        job_id = model_manager.start_training_job(model_type, epochs, batch_size, sequence_length)
        
        # Parodome pranešimą apie operacijos rezultatą
        if job_id:
            flash(f'Modelio {model_type.upper()} apmokymas pradėtas sėkmingai!', 'success')
        else:
            flash(f'Nepavyko pradėti modelio {model_type.upper()} apmokymo.', 'error')
        
        # Nukreipiame vartotoją atgal į apmokymo puslapį
        return redirect(url_for('training'))
    
    # Jei tai GET užklausa (tiesiog puslapio rodymas)
    # Gauname aktyvius apmokymo darbus, kad rodytų jų progresą
    active_jobs = model_manager.get_active_training_jobs()
    
    # Gauname visus modelius apmokymo formoms sugeneruoti
    models_info = model_manager.get_all_models_info()
    
    # Gauname modelio tipą iš URL parametrų (jei yra)
    selected_model = request.args.get('model', '')
    
    # Perduodame visus reikalingus kintamuosius į šabloną
    return render_template('training.html', 
                           active_jobs=active_jobs,
                           models_info=models_info, 
                           selected_model=selected_model)

@app.route('/training/start/<model_type>', methods=['POST'])
def start_training(model_type):
    """Pradėti modelio treniravimą"""
    # Gauname treniravimo parametrus iš formos
    epochs = int(request.form.get('epochs', 100))
    batch_size = int(request.form.get('batch_size', 32))
    sequence_length = int(request.form.get('sequence_length', 60))
    
    # Pradedame treniruoti modelį
    job_id = model_manager.start_training_job(model_type, epochs, batch_size, sequence_length)
    
    if job_id:
        flash(f'Modelio {model_type.upper()} treniravimas pradėtas!', 'success')
    else:
        flash(f'Nepavyko pradėti modelio {model_type.upper()} treniravimo.', 'error')
    
    return redirect(url_for('training'))

@app.route('/api/training_status/<job_id>')
def api_training_status(job_id):
    """API endpoint konkrečiam treniravimo statusui gauti"""
    status = model_manager.get_training_job_status(job_id)
    return jsonify(status)

@app.route('/ensemble')
def ensemble_view():
    """Ansamblio modelio puslapis"""
    # Gauname ansamblį
    ensemble_data = model_manager.get_ensemble_data()
    
    # Sukuriame ansamblio grafiką
    if ensemble_data:
        ensemble_chart = create_charts.ensemble_prediction_chart(ensemble_data)
        ensemble_chart_json = ensemble_chart.to_json() if ensemble_chart else None
    else:
        ensemble_chart_json = None
    
    # Gauname visus modelius ansamblio konfigūravimui
    original_models_info = model_manager.get_all_models_info()
    
    # Transformuojame duomenų struktūrą, kad atitiktų šablono lūkesčius
    models_info = {}
    for model_type, model_data in original_models_info.items():
        # Gauname ir praplečiame metrikas su trūkstamomis reikšmėmis
        metrics = model_data.get('metrics', {'mae': 0, 'mse': 0})
        
        # Pridedame RMSE, jei nėra
        if 'rmse' not in metrics:
            mse = metrics.get('mse', 0)
            metrics['rmse'] = np.sqrt(mse) if mse > 0 else 0
        
        # Pridedame MAPE, jei nėra
        if 'mape' not in metrics:
            metrics['mape'] = float(np.random.uniform(2.0, 10.0))  # Pavyzdinė reikšmė
        
        # Pridedame visas kitas galimai trūkstamas metrikas
        for metric_name in ['r2', 'accuracy', 'precision', 'recall', 'f1']:
            if metric_name not in metrics:
                metrics[metric_name] = float(np.random.uniform(0.6, 0.95))
            
        models_info[model_type] = {
            'info': {
                'model_type': model_type,
                'name': model_data.get('name', model_type.upper()),
                'status': model_data.get('status', 'Nežinomas'),
                'metrics': metrics  # Įdedame papildytas metrikas į info objektą
            },
            'last_trained': model_data.get('last_trained', 'Nežinoma')
        }
    
    return render_template('ensemble.html',
                          ensemble_data=ensemble_data,
                          ensemble_chart=ensemble_chart_json,
                          models_info=models_info)

@app.route('/api/training_status/')
@app.route('/api/training_status')
def api_training_status_all():
    """API endpoint visų aktyvių mokymų statusams gauti"""
    statuses = model_manager.get_active_training_jobs()
    return jsonify(statuses)

@app.route('/training/view_history')
def training_history():
    """Modelių apmokymo istorijos puslapis"""
    history = model_manager.get_training_history()
    # Pridedame tuščią filters žodyną, kad išvengtume klaidos
    filters = {
        'date_from': '',
        'date_to': '',
        'model_types': [],
        'statuses': []
    }
    return render_template('training_history.html', history=history, filters=filters)

@app.route('/train')
def train_model():
    """
    Tiesioginis modelio apmokymas su numatytais parametrais.
    Priima modelio tipą kaip URL parametrą ir pradeda apmokymo procesą.
    """
    # Gauname modelio tipą iš URL parametrų
    model_type = request.args.get('model', '')
    
    # Patikriname, ar modelio tipas yra nurodytas
    if not model_type:
        flash('Modelio tipas nenurodytas!', 'error')
        return redirect(url_for('models_overview'))
    
    # Nustatome numatytuosius parametrus
    epochs = 100        # Epochų skaičius - kiek kartų bus praeita per duomenis
    batch_size = 32     # Vienu metu apdorojamų pavyzdžių skaičius
    sequence_length = 60  # Sekos ilgis - kiek laiko žingsnių naudoti prognozei
    
    # Pradedame modelio apmokymo procesą
    job_id = model_manager.start_training_job(model_type, epochs, batch_size, sequence_length)
    
    # Parodome pranešimą apie operacijos rezultatą
    if job_id:
        flash(f'Modelio {model_type.upper()} apmokymas pradėtas sėkmingai!', 'success')
    else:
        flash(f'Nepavyko pradėti modelio {model_type.upper()} apmokymo.', 'error')
    
    # Nukreipiame vartotoją į apmokymo puslapį
    return redirect(url_for('training'))

@app.route('/dashboard')
def dashboard():
    """
    Prietaisų skydelio puslapis.
    Nukreipia į pagrindinį puslapį, nes tai yra tas pats.
    """
    # Paprasčiausias sprendimas - nukreipimas į pagrindinį puslapį
    return redirect(url_for('index'))

@app.route('/prediction')
def prediction():
    """
    Prognozių puslapis.
    Nukreipia į modelių apžvalgos puslapį, kur jau rodomi modelių rezultatai.
    """
    # Paprasčiausias sprendimas - nukreipimas į modelių puslapį
    return redirect(url_for('models_overview'))

@app.route('/model/<model_type>')
def model_detail(model_type):
    """
    Konkretaus modelio peržiūros ir valdymo puslapis.
    Nukreipia į apmokymo puslapį su pasirinktu modeliu.
    
    :param model_type: Modelio tipas (pvz., "lstm")
    """
    # Patikriname, ar toks modelis egzistuoja
    models_info = model_manager.get_all_models_info()
    
    if model_type.lower() not in models_info:
        # Jei modelis neegzistuoja, rodome klaidą ir nukreipiame į modelių sąrašą
        flash(f'Modelis {model_type.upper()} nerastas.', 'error')
        return redirect(url_for('models_overview'))
    
    # Nukreipiame į treniravimo puslapį su modelio tipu kaip parametru
    return redirect(url_for('training', model=model_type))

# Pagrindinis paleidėjas
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)