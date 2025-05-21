"""
Paprastas ModelService naudojimo pavyzdys.
"""
import os
import sys
import uuid
import json
from datetime import datetime, timezone

# Pridedame pagrindinį projekto katalogą į Python kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService

# Sukuriame duomenų bazės prisijungimą
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame modelio servisą
model_service = ModelService(session)

try:
    # 1. Sukuriame naują modelį
    # ------------------------
    print("1. Sukuriame naują modelį:")
    
    # Generuojame unikalų ID
    model_id = str(uuid.uuid4())
    
    # Paruošiame modelio duomenis
    model_data = {
        "id": model_id,
        "name": "Paprastas LSTM modelis",
        "description": "Bitcoin kainos prognozavimo modelis naudojant LSTM tinklą",
        "type": "lstm",
        "hyperparameters": {
            "epochs": 100,
            "batch_size": 32,
            "learning_rate": 0.001,
            "hidden_layers": 2,
            "nodes_per_layer": 64
        },
        "input_features": ["price", "volume", "ma_7", "ma_30", "rsi_14"],
        "performance_metrics": {
            "accuracy": 0.85,
            "loss": 0.12,
            "mae": 350.25,
            "rmse": 420.75
        },
        "created_at": datetime.now(timezone.utc)
    }
    
    # Sukuriame modelį
    model = model_service.create_model(model_data)
    
    if model:
        print(f"Modelis sukurtas! ID: {model.id}")
        print(f"Pavadinimas: {model.name}")
        print(f"Tipas: {model.type}")
        print(f"Tikslumas: {model.performance_metrics.get('accuracy', 0) * 100:.1f}%")
    else:
        print("Nepavyko sukurti modelio.")
        sys.exit(1)
    
    # 2. Gauname modelį pagal ID
    # -------------------------
    print("\n2. Gauname modelį pagal ID:")
    
    # Gauname ką tik sukurtą modelį
    retrieved_model = model_service.get_model(model_id)
    
    if retrieved_model:
        print(f"Modelis rastas! ID: {retrieved_model.id}")
        print(f"Pavadinimas: {retrieved_model.name}")
        print(f"Aprašymas: {retrieved_model.description}")
        print(f"Įvesties požymiai: {', '.join(retrieved_model.input_features)}")
        print(f"Hiperparametrai: {json.dumps(retrieved_model.hyperparameters, indent=2)}")
    else:
        print(f"Modelis su ID {model_id} nerastas.")
    
    # 3. Sukuriame dar du modelius palyginimui
    # -------------------------------------
    print("\n3. Sukuriame dar du modelius palyginimui:")
    
    # GRU modelis
    gru_model_data = {
        "id": str(uuid.uuid4()),
        "name": "GRU modelis",
        "description": "Bitcoin kainos prognozavimo modelis naudojant GRU tinklą",
        "type": "gru",
        "hyperparameters": {
            "epochs": 80,
            "batch_size": 64,
            "learning_rate": 0.0015
        },
        "input_features": ["price", "volume", "ma_7", "ma_30"],
        "performance_metrics": {
            "accuracy": 0.82,
            "loss": 0.15,
            "mae": 380.50,
            "rmse": 450.25
        },
        "created_at": datetime.now(timezone.utc)
    }
    
    gru_model = model_service.create_model(gru_model_data)
    if gru_model:
        print(f"  - GRU modelis sukurtas! ID: {gru_model.id}")
    
    # Transformer modelis
    transformer_model_data = {
        "id": str(uuid.uuid4()),
        "name": "Transformer modelis",
        "description": "Bitcoin kainos prognozavimo modelis naudojant Transformer architektūrą",
        "type": "transformer",
        "hyperparameters": {
            "epochs": 120,
            "batch_size": 32,
            "learning_rate": 0.0005,
            "n_heads": 8,
            "n_layers": 4
        },
        "input_features": ["price", "volume", "ma_7", "ma_30", "rsi_14", "macd"],
        "performance_metrics": {
            "accuracy": 0.88,
            "loss": 0.09,
            "mae": 320.10,
            "rmse": 390.40
        },
        "created_at": datetime.now(timezone.utc)
    }
    
    transformer_model = model_service.create_model(transformer_model_data)
    if transformer_model:
        print(f"  - Transformer modelis sukurtas! ID: {transformer_model.id}")
    
    # 4. Gauname visų modelių sąrašą
    # ----------------------------
    print("\n4. Gauname visų modelių sąrašą:")
    
    # Gauname visus modelius
    all_models = model_service.list_models()
    
    print(f"Iš viso turime {len(all_models)} modelius:")
    for idx, m in enumerate(all_models, 1):
        # Formatuojame tikslumą
        accuracy = m.performance_metrics.get('accuracy', 0) * 100 if m.performance_metrics else 0
        
        # Spausdiname
        print(f"  {idx}. {m.name} ({m.type}) - Tikslumas: {accuracy:.1f}%")
    
    # 5. Filtruojame modelius pagal tipą
    # -------------------------------
    print("\n5. Filtruojame modelius pagal tipą:")
    
    # Gauname tik LSTM modelius
    lstm_models = model_service.list_models(model_type="lstm")
    
    print(f"LSTM modeliai ({len(lstm_models)}):")
    for m in lstm_models:
        print(f"  - {m.name} (ID: {m.id})")
    
    # 6. Atnaujiname modelio metrikos
    # ----------------------------
    print("\n6. Atnaujiname modelio metrikos:")
    
    # Paruošiame atnaujintas metrikos
    update_data = {
        "performance_metrics": {
            "accuracy": 0.90,     # Padidintas tikslumas
            "loss": 0.08,         # Sumažintas nuostolis
            "mae": 300.10,        # Pagerinta vidutinė absoliuti paklaida
            "rmse": 360.25,       # Pagerinta vidutinė kvadratinė paklaida
            "f1_score": 0.91      # Pridėta nauja metrika
        }
    }
    
    # Atnaujiname LSTM modelį
    updated_model = model_service.update_model(model_id, update_data)
    
    if updated_model:
        print(f"Modelis atnaujintas! Naujas tikslumas: {updated_model.performance_metrics['accuracy'] * 100:.1f}%")
        print(f"Naujos metrikos: {json.dumps(updated_model.performance_metrics, indent=2)}")
    else:
        print(f"Nepavyko atnaujinti modelio su ID {model_id}.")
    
    # 7. Ištriname vieną modelį
    # -----------------------
    print("\n7. Ištriname vieną modelį:")
    
    # Ištriname GRU modelį
    if gru_model and model_service.delete_model(gru_model.id):
        print(f"Modelis '{gru_model.name}' (ID: {gru_model.id}) ištrintas sėkmingai.")
    else:
        print("Nepavyko ištrinti modelio.")
    
    # 8. Gauname atnaujintą modelių sąrašą
    # ---------------------------------
    print("\n8. Gauname atnaujintą modelių sąrašą:")
    
    # Gauname visus likusius modelius
    remaining_models = model_service.list_models()
    
    print(f"Dabar turime {len(remaining_models)} modelius:")
    for m in remaining_models:
        print(f"  - {m.name} ({m.type})")
    
    # 9. Ištriname visus likusius modelius
    # ---------------------------------
    print("\n9. Ištriname visus likusius modelius:")
    
    # Ištriname kiekvieną likusį modelį
    deleted_count = 0
    for m in remaining_models:
        if model_service.delete_model(m.id):
            deleted_count += 1
    
    print(f"Ištrinta modelių: {deleted_count} iš {len(remaining_models)}")

except Exception as e:
    print(f"Įvyko klaida: {str(e)}")

finally:
    # Uždarome duomenų bazės sesiją
    session.close()
    print("\nDuomenų bazės sesija uždaryta.")