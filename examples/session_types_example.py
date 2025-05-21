"""
Pavyzdinis skriptas, parodantis kaip naudoti skirtingų tipų sesijas (treniravimo ir testavimo).
"""
import os
import sys
import logging
import json
import time
from datetime import datetime, timezone

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.user_service import UserService
from services.session_service import SessionService
from services.training_session_service import TrainingSessionService
from services.testing_session_service import TestingSessionService
from services.model_service import ModelService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti skirtingų tipų sesijų naudojimą.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    # Sukuriame servisus
    user_service = UserService(session)
    session_service = SessionService(session)
    training_session_service = TrainingSessionService(session)
    testing_session_service = TestingSessionService(session)
    model_service = ModelService(session)
    
    user_id = None
    model_id = None
    
    try:
        logger.info("Pradedamas skirtingų tipų sesijų pavyzdys")
        
        # 1. Sukuriame naudotoją
        logger.info("1. Kuriame naudotoją")
        
        test_user_data = {
            "username": "sesiju_tipai",
            "email": "tipai@example.com",
            "password": "slaptazodis123",
            "full_name": "Sesijų Tipai",
            "is_admin": False
        }
        
        user = user_service.create_user(test_user_data)
        
        if not user:
            logger.error("Nepavyko sukurti naudotojo")
            return
        
        user_id = user.id
        logger.info(f"Sukurtas naudotojas: ID={user.id}, Vardas={user.username}")
        
        # 2. Sukuriame modelį, su kuriuo dirbsime
        logger.info("2. Kuriame modelį")
        
        model_data = {
            "name": "Sesijų tipų testavimo modelis",
            "type": "lstm",
            "hyperparameters": {
                "epochs": 50,
                "batch_size": 32,
                "learning_rate": 0.001
            },
            "input_features": ["price", "volume"]
        }
        
        model = model_service.create_model(model_data)
        
        if not model:
            logger.error("Nepavyko sukurti modelio")
            return
        
        model_id = model.id
        logger.info(f"Sukurtas modelis: ID={model.id}, Pavadinimas={model.name}")
        
        # 3. Sukuriame treniravimo sesiją (pirma kuriame naudotojo sesiją)
        logger.info("3. Kuriame treniravimo sesiją")
        
        # Sukuriame naudotojo sesiją
        user_session_data = {
            "user_id": user.id,
            "session_type": "training",  # Svarbu nurodyti tipą
            "ip_address": "127.0.0.1"
        }
        
        user_session = session_service.create_session(user_session_data)
        
        if not user_session:
            logger.error("Nepavyko sukurti naudotojo sesijos")
            return
        
        logger.info(f"Sukurta naudotojo sesija: ID={user_session.id}, Tipas={user_session.session_type}")
        
        # Sukuriame treniravimo sesiją
        training_data = {
            "model_id": model.id,
            "dataset_name": "bitcoin_2020_2021",
            "total_epochs": 50,
            "learning_rate": 0.001,
            "batch_size": 32,
            "loss_function": "mse",
            "validation_split": 0.2,
            "early_stopping": True,
            "checkpoint_enabled": True,
            "training_status": "running"
        }
        
        training_session = training_session_service.create_training_session(user_session.id, training_data)
        
        if not training_session:
            logger.error("Nepavyko sukurti treniravimo sesijos")
            return
        
        logger.info(f"Sukurta treniravimo sesija: ID={training_session.id}")
        logger.info(f"Modelis: {training_session.model_id}, Statusas: {training_session.training_status}")
        
        # 4. Imituojame modelio treniravimą (atnaujinant progresą)
        logger.info("4. Imituojame modelio treniravimą")
        
        for epoch in range(1, 11):  # Imituojame 10 epochų
            # Atnaujinome progresą
            updated_session = training_session_service.update_training_progress(
                training_session.id, epoch, "running"
            )
            
            if updated_session:
                logger.info(f"Epocha {epoch}/{updated_session.total_epochs}, Statusas: {updated_session.training_status}")
            
            # Trumpas uždelsimas (imitavimui)
            time.sleep(0.5)
        
        # 5. Baigiame treniravimo sesiją
        logger.info("5. Baigiame treniravimo sesiją")
        
        completed_training = training_session_service.complete_training(training_session.id)
        
        if completed_training:
            logger.info(f"Treniravimo sesija baigta: ID={completed_training.id}")
            logger.info(f"Galutinis statusas: {completed_training.training_status}")
            logger.info(f"Naudotojo sesijos statusas: {completed_training.session.status}")
        
        # 6. Sukuriame testavimo sesiją
        logger.info("6. Kuriame testavimo sesiją")
        
        # Sukuriame naudotojo sesiją
        user_session_data = {
            "user_id": user.id,
            "session_type": "testing",  # Svarbu nurodyti tipą
            "ip_address": "127.0.0.1"
        }
        
        user_session = session_service.create_session(user_session_data)
        
        if not user_session:
            logger.error("Nepavyko sukurti naudotojo sesijos")
            return
        
        logger.info(f"Sukurta naudotojo sesija: ID={user_session.id}, Tipas={user_session.session_type}")
        
        # Sukuriame testavimo sesiją
        testing_data = {
            "model_id": model.id,
            "dataset_name": "bitcoin_2022_test",
            "test_type": "accuracy",
            "test_params": {
                "metrics": ["mae", "rmse", "mape"],
                "test_size": 100,
                "threshold": 0.8
            },
            "testing_status": "running"
        }
        
        testing_session = testing_session_service.create_testing_session(user_session.id, testing_data)
        
        if not testing_session:
            logger.error("Nepavyko sukurti testavimo sesijos")
            return
        
        logger.info(f"Sukurta testavimo sesija: ID={testing_session.id}")
        logger.info(f"Modelis: {testing_session.model_id}, Statusas: {testing_session.testing_status}")
        
        # 7. Imituojame modelio testavimą ir rezultatų išsaugojimą
        logger.info("7. Imituojame modelio testavimą ir išsaugome rezultatus")
        
        # Trumpas uždelsimas (imitavimui)
        time.sleep(1)
        
        # Imituojame testavimo rezultatus
        test_results = {
            "accuracy": 0.87,
            "mae": 320.45,
            "rmse": 450.12,
            "mape": 0.15,
            "confusion_matrix": [[45, 5], [8, 42]],
            "test_duration_seconds": 12.5
        }
        
        # Išsaugome rezultatus
        success = True  # Testas pavyko
        updated_testing = testing_session_service.save_test_results(testing_session.id, test_results, success)
        
        if updated_testing:
            logger.info(f"Testavimo sesija baigta: ID={updated_testing.id}")
            logger.info(f"Galutinis statusas: {updated_testing.testing_status}, Sėkmė: {updated_testing.success}")
            logger.info(f"Naudotojo sesijos statusas: {updated_testing.session.status}")
            
            # Išparsink ir parodyk rezultatus
            results_dict = json.loads(updated_testing.results)
            logger.info(f"Testavimo rezultatai: Tikslumas={results_dict['accuracy']*100:.1f}%, MAE={results_dict['mae']}")
        
        # 8. Gauname sesijas pagal modelį
        logger.info("8. Gauname visas modelio sesijas")
        
        # Gauname modelio treniravimo sesijas
        training_sessions = training_session_service.list_training_sessions(model_id=model.id)
        logger.info(f"Modelis turi {len(training_sessions)} treniravimo sesijas")
        
        # Gauname modelio testavimo sesijas
        testing_sessions = testing_session_service.list_testing_sessions(model_id=model.id)
        logger.info(f"Modelis turi {len(testing_sessions)} testavimo sesijas")
        
        # 9. Valome testavimo duomenis
        logger.info("9. Valome testavimo duomenis")
        
        # Ištriname modelį
        if model_service.delete_model(model.id):
            logger.info(f"Modelis {model.id} ištrintas")
        
        # Ištriname naudotoją
        if user_service.delete_user(user.id):
            logger.info(f"Naudotojas {user.id} ištrintas")
        
        logger.info("Sesijų tipų pavyzdys baigtas")
        
    except Exception as e:
        logger.error(f"Įvyko klaida: {str(e)}")
        
        # Bandome išvalyti duomenis, net jei įvyko klaida
        try:
            if model_id and model_service:
                model_service.delete_model(model_id)
            
            if user_id and user_service:
                user_service.delete_user(user_id)
        except:
            pass
    
    finally:
        # Uždarome duomenų bazės sesiją
        session.close()
        logger.info("Duomenų bazės sesija uždaryta")

if __name__ == "__main__":
    main()