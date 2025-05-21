"""
Paprastas PredictionService naudojimo pavyzdys.
"""
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Pridedame pagrindinį projekto katalogą į Python kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.prediction_service import PredictionService
from services.model_service import ModelService

# Sukuriame duomenų bazės prisijungimą
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame servisus
prediction_service = PredictionService(session)
model_service = ModelService(session)

try:
    # Pirmiausia turime paruošti modelį prognozėms
    # -------------------------------------------
    print("1. Kuriame modelį prognozėms:")
    
    # Generuojame unikalų ID modeliui
    model_id = str(uuid.uuid4())
    
    # Kuriame modelį
    model_data = {
        "id": model_id,
        "name": "Modelis prognozių pavyzdžiui",
        "type": "lstm",
        "hyperparameters": {"epochs": 50},
        "input_features": ["price", "volume"],
        "created_at": datetime.now(timezone.utc)
    }
    
    # Išsaugome modelį duomenų bazėje
    model = model_service.create_model(model_data)
    
    if model:
        print(f"Modelis sukurtas! ID: {model.id}")
    else:
        print("Nepavyko sukurti modelio.")
        sys.exit(1)
    
    # 2. Sukuriame naują prognozę
    # ---------------------------
    print("\n2. Sukuriame naują prognozę:")
    
    # Paruošiame prognozės duomenis
    prediction_data = {
        "model_id": model_id,           # Susiejame su sukurtu modeliu
        "prediction_date": datetime.now(timezone.utc),  # Prognozės data
        "price": 35000.0,               # Prognozuojama kaina
        "confidence": 0.85,             # Pasitikėjimo lygis (0-1)
        "metrics": {                    # Prognozės metrikos
            "rmse": 250.5,              # Vidutinė kvadratinė paklaida
            "mae": 180.2                # Vidutinė absoliuti paklaida
        },
        "created_at": datetime.now(timezone.utc)
    }
    
    # Sukuriame prognozę
    prediction = prediction_service.create_prediction(prediction_data)
    
    if prediction:
        print(f"Prognozė sukurta! ID: {prediction.id}")
        print(f"Prognozuojama kaina: {prediction.price} USD")
        print(f"Pasitikėjimo lygis: {prediction.confidence * 100}%")
    else:
        print("Nepavyko sukurti prognozės.")
    
    # 3. Sukuriame keletą papildomų prognozių
    # --------------------------------------
    print("\n3. Sukuriame keletą papildomų prognozių skirtingoms datoms:")
    
    # Kuriame prognozes skirtingoms datoms
    for days_ahead in range(1, 6):  # Prognozės 1-5 dienoms į priekį
        # Apskaičiuojame datą
        future_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        # Apskaičiuojame prognozuojamą kainą (pavyzdžiui, kaina didėja 1% per dieną)
        future_price = 35000.0 * (1.01 ** days_ahead)
        
        # Paruošiame prognozės duomenis
        future_prediction_data = {
            "model_id": model_id,
            "prediction_date": future_date,
            "price": future_price,
            # Pasitikėjimo lygis mažėja su kiekviena diena į priekį
            "confidence": 0.85 - (days_ahead * 0.05),
            "metrics": {
                "rmse": 250.5 + (days_ahead * 20),  # Paklaida didėja
                "mae": 180.2 + (days_ahead * 15)    # Paklaida didėja
            },
            "created_at": datetime.now(timezone.utc)
        }
        
        # Sukuriame prognozę
        future_prediction = prediction_service.create_prediction(future_prediction_data)
        
        if future_prediction:
            print(f"  - Prognozė dienai +{days_ahead}: {future_prediction.price:.2f} USD, " +
                  f"pasitikėjimas: {future_prediction.confidence * 100:.1f}%")
    
    # 4. Gauname visas modelio prognozes
    # ---------------------------------
    print("\n4. Gauname visas modelio prognozes:")
    
    # Gauname visas prognozes, susijusias su šiuo modeliu
    model_predictions = prediction_service.list_predictions(model_id=model_id)
    
    if model_predictions:
        print(f"Modelis turi {len(model_predictions)} prognozes:")
        
        # Rūšiuojame prognozes pagal datą
        sorted_predictions = sorted(model_predictions, key=lambda p: p.prediction_date)
        
        for idx, pred in enumerate(sorted_predictions, 1):
            # Formatuojame datą
            date_str = pred.prediction_date.strftime("%Y-%m-%d")
            print(f"  {idx}. {date_str}: {pred.price:.2f} USD (pasitikėjimas: {pred.confidence * 100:.1f}%)")
    else:
        print("Modeliui dar nėra sukurtų prognozių.")
    
    # 5. Atnaujiname prognozę
    # ----------------------
    if model_predictions:
        print("\n5. Atnaujiname pirmą prognozę:")
        
        # Pasiimame pirmąją prognozę
        first_prediction = model_predictions[0]
        
        # Paruošiame atnaujintos prognozės duomenis
        update_data = {
            "price": first_prediction.price * 0.98,  # Sumažiname kainą 2%
            "confidence": 0.92,  # Padidiname pasitikėjimo lygį
            "metrics": {
                "rmse": 220.0,  # Pagerėjusios metrikos
                "mae": 160.5
            }
        }
        
        # Atnaujiname prognozę
        updated_prediction = prediction_service.update_prediction(first_prediction.id, update_data)
        
        if updated_prediction:
            print(f"Prognozė atnaujinta! Nauja kaina: {updated_prediction.price:.2f} USD")
            print(f"Naujas pasitikėjimo lygis: {updated_prediction.confidence * 100:.1f}%")
        else:
            print("Nepavyko atnaujinti prognozės.")
    
    # 6. Ištriname pasirinktą prognozę
    # ------------------------------
    if model_predictions and len(model_predictions) > 1:
        print("\n6. Ištriname vieną prognozę:")
        
        # Pasiimame antrąją prognozę
        prediction_to_delete = model_predictions[1]
        
        # Ištriname prognozę
        if prediction_service.delete_prediction(prediction_to_delete.id):
            print(f"Prognozė su ID {prediction_to_delete.id} ištrinta sėkmingai.")
        else:
            print(f"Nepavyko ištrinti prognozės su ID {prediction_to_delete.id}.")
    
    # 7. Ištriname modelį ir visas susijusias prognozes
    # -----------------------------------------------
    print("\n7. Ištriname modelį ir visas susijusias prognozes:")
    
    # Ištriname modelį, kartu ištrinami ir susiję įrašai
    if model_service.delete_model(model_id):
        print(f"Modelis su ID {model_id} ir visos jo prognozės ištrintos sėkmingai.")
    else:
        print(f"Nepavyko ištrinti modelio su ID {model_id}.")

except Exception as e:
    print(f"Įvyko klaida: {str(e)}")

finally:
    # Uždarome duomenų bazės sesiją
    session.close()
    print("\nDuomenų bazės sesija uždaryta.")