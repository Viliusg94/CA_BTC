from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import os
import json
import tensorflow as tf
import numpy as np

# Sukuriame blueprint
models = Blueprint('models', __name__, url_prefix='/models')

# Modelių saugojimo kelias
MODELS_FOLDER = os.path.join('data', 'models')
os.makedirs(MODELS_FOLDER, exist_ok=True)

@models.route('/')
def model_list():
    """
    Rodo modelių sąrašą
    """
    models_list = get_all_models()
    return render_template('models/model_list.html', models=models_list)

@models.route('/visualization')
def model_visualization():
    """
    Rodo modelio vizualizacijos puslapį
    """
    models_list = get_all_models()
    return render_template('models/model_visualization.html', models=models_list)

@models.route('/comparison')
def model_comparison():
    """
    Rodo modelių palyginimo puslapį
    """
    models_list = get_all_models()
    return render_template('models/model_comparison.html', models=models_list)

@models.route('/api/models')
def api_model_list():
    """
    Grąžina modelių sąrašą JSON formatu
    """
    models_list = get_all_models()
    return jsonify(models_list)

@models.route('/api/models/<model_id>/structure')
def api_model_structure(model_id):
    """
    Grąžina modelio struktūrą JSON formatu
    """
    try:
        # Tikriname ar modelis egzistuoja
        model_path = os.path.join(MODELS_FOLDER, f"{model_id}")
        if not os.path.exists(model_path):
            return jsonify({"error": "Modelis nerastas"}), 404
        
        # Bandome užkrauti modelį
        model = tf.keras.models.load_model(model_path)
        
        # Paruošiame modelio struktūros informaciją
        model_info = {
            "id": model_id,
            "name": getattr(model, "name", f"model_{model_id}"),
            "input_shape": str(model.input_shape),
            "layers": []
        }
        
        # Einame per visus sluoksnius
        for layer in model.layers:
            layer_info = {
                "name": layer.name,
                "type": layer.__class__.__name__,
                "output_shape": str(layer.output_shape),
                "params": layer.count_params()
            }
            
            # Pridedame papildomą informaciją, jei ji yra
            config = layer.get_config()
            for key, value in config.items():
                if key not in ["name", "trainable"]:
                    layer_info[key] = str(value)
            
            model_info["layers"].append(layer_info)
        
        return jsonify(model_info)
    
    except Exception as e:
        return jsonify({"error": f"Klaida gaunant modelio struktūrą: {str(e)}"}), 500

@models.route('/api/models/<model_id>/metrics')
def api_model_metrics(model_id):
    """
    Grąžina modelio metrikas JSON formatu
    """
    try:
        # Tikriname ar modelis egzistuoja
        metrics_path = os.path.join(MODELS_FOLDER, f"{model_id}_metrics.json")
        if not os.path.exists(metrics_path):
            return jsonify({"error": "Modelio metrikos nerastos"}), 404
        
        # Skaitome metrikas iš failo
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        return jsonify(metrics)
    
    except Exception as e:
        return jsonify({"error": f"Klaida gaunant modelio metrikas: {str(e)}"}), 500

def get_all_models():
    """
    Grąžina visų modelių sąrašą
    """
    models_list = []
    
    try:
        # Einame per visus failus modelių aplanke
        for item in os.listdir(MODELS_FOLDER):
            item_path = os.path.join(MODELS_FOLDER, item)
            
            # Tikriname ar tai direktorija (modelis) ar metrikos failas
            if os.path.isdir(item_path) and not item.endswith("_metrics"):
                model_id = item
                
                # Bandome gauti modelio informaciją
                try:
                    model = tf.keras.models.load_model(item_path)
                    
                    # Gauname metrikas, jei jos yra
                    metrics = {}
                    metrics_path = os.path.join(MODELS_FOLDER, f"{model_id}_metrics.json")
                    if os.path.exists(metrics_path):
                        with open(metrics_path, 'r') as f:
                            metrics = json.load(f)
                    
                    # Sukuriame modelio informacijos objektą
                    model_info = {
                        "id": model_id,
                        "name": getattr(model, "name", f"model_{model_id}"),
                        "type": model.__class__.__name__,
                        "layers_count": len(model.layers),
                        "input_shape": str(model.input_shape),
                        "metrics": metrics
                    }
                    
                    models_list.append(model_info)
                
                except Exception as e:
                    print(f"Klaida užkraunant modelį {model_id}: {str(e)}")
    
    except Exception as e:
        print(f"Klaida gaunant modelių sąrašą: {str(e)}")
    
    return models_list