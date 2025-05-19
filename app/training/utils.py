"""
Pagalbinių funkcijų modulis
--------------------------
Šis modulis apibrėžia pagalbines funkcijas treniravimui.
"""

import os
import json
from datetime import datetime


# Globalūs kintamieji treniravimo būsenai
current_model = None
training_thread = None


def get_training_state():
    """
    Gauna dabartinę treniravimo būseną
    
    Returns:
        dict: Treniravimo būsenos žodynas
    """
    if current_model is None:
        return {
            'status': 'Not started',
            'progress': 0,
            'current_epoch': 0,
            'total_epochs': 0,
            'metrics': {
                'loss': [],
                'val_loss': [],
                'mae': [],
                'val_mae': []
            },
            'log_messages': []
        }
    
    return current_model.get_state()


def get_saved_models():
    """
    Gauna visus išsaugotus modelius
    
    Returns:
        list: Išsaugotų modelių sąrašas
    """
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
    
    models = []
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(models_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    model_data = json.load(f)
                
                # Pridedame pagrindinę informaciją
                model_info = {
                    'name': model_data.get('name', filename.replace('.json', '')),
                    'type': model_data.get('config', {}).get('model_type', 'unknown'),
                    'epochs': model_data.get('config', {}).get('epochs', 0),
                    'loss': model_data.get('metrics', {}).get('final_loss', 0),
                    'val_loss': model_data.get('metrics', {}).get('final_val_loss', 0),
                    'mae': model_data.get('metrics', {}).get('final_mae', 0),
                    'val_mae': model_data.get('metrics', {}).get('final_val_mae', 0),
                    'created_at': model_data.get('training_time', {}).get('end', None),
                    'file_path': file_path
                }
                
                models.append(model_info)
            except Exception as e:
                print(f"Klaida skaitant modelio failą {filename}: {e}")
    
    # Rūšiuojame pagal sukūrimo datą (naujausi viršuje)
    models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return models


def get_model_details(model_name):
    """
    Gauna detalią modelio informaciją
    
    Args:
        model_name: Modelio pavadinimas
        
    Returns:
        dict: Modelio detalės
    """
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
    file_path = os.path.join(models_dir, f"{model_name}.json")
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            model_data = json.load(f)
        
        return model_data
    except Exception as e:
        print(f"Klaida skaitant modelio failą {model_name}: {e}")
        return None


def delete_model(model_name):
    """
    Ištrina modelį
    
    Args:
        model_name: Modelio pavadinimas
        
    Returns:
        bool: Ar sėkmingai ištrinta
    """
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
    file_path = os.path.join(models_dir, f"{model_name}.json")
    
    if not os.path.exists(file_path):
        return False
    
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        print(f"Klaida trinant modelio failą {model_name}: {e}")
        return False