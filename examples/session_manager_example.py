"""
Pavyzdinis skriptas, parodantis kaip naudoti SessionManagerService klasę.
"""
import os
import sys
import logging
import json
import time
from datetime import datetime

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.user_service import UserService
from services.model_service import ModelService
from services.session_manager_service import SessionManagerService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti SessionManagerService naudojimą.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    db_session = Session(engine)
    
    # Sukuriame reikalingus servisus
    user_service = UserService(db_session)
    model_service = ModelService(db_session)
    session_manager = SessionManagerService(db_session)
    
    # Saugosime sukurtų objektų ID, kad galėtume juos ištrinti pabaigoje
    user_id = None
    model_id = None
    training_session_id = None
    testing_session_id = None
    
    try:
        logger.info("Pradedamas sesijos valdymo serviso pavyzdys")
        
        # 1. Sukuriame naudotoją testavimui
        logger.info("1. Kuriame naudotoją")
        
        user_data = {
            "username": "session_manager_test",
            "email": "session_manager@example.com",
            "password": "slaptazodis123",
            "full_name": "Sesijos Valdymas"
        }
        
        user = user_service.create_user(user_data)
        
        if not user:
            logger.error("Nepavyko sukurti naudotojo")
            return
        
        user_id = user.id
        logger.info(f"Sukurtas naudotojas: ID={user.id}, Vardas={user.username}")
        
        # 2. Sukuriame modelį, su kuriuo dirbsime
        logger.info("2. Kuriame modelį")
        
        model_data = {
            "name": "Sesijos valdymo testavimo modelis",
            "type": "rnn",
            "hyperparameters": {
                "layers": 2,
                "units": 64,
                "dropout": 0.2
            }
        }
        
        model = model_service.create_model(model_data)
        
        if not model:
            logger.error("Nepavyko sukurti modelio")
            return
        
        model_id = model.id
        logger.info(f"Sukurtas modelis: ID={model.id}, Pavadinimas={model.name}")
        
        # 3. Pradedame treniravimo sesiją
        logger.info("3. Pradedame treniravimo sesiją")
        
        training_metadata = {
            "model_id": model.id,
            "dataset_name": "btc_training_data",
            "total_epochs": 50,
            "learning_rate": 0.001,
            "batch_size": 32
        }
        
        training_result = session_manager.start_session(user.id, "training", training_metadata)
        
        if not training_result:
            logger.error("Nepavyko pradėti treniravimo sesijos")
            return
        
        training_session_id = training_result["user_session"]["id"]
        logger.info(f"Pradėta treniravimo sesija: ID={training_session_id}")
        logger.info(f"Treniravimo sesijos detalės: {json.dumps(training_result, default=str, indent=2)}")
        
        # 4. Atnaujiname treniravimo sesiją (simuliuojame progresą)
        logger.info("4. Atnaujiname treniravimo sesiją")
        
        # Imituojame modelio treniravimą
        for epoch in range(1, 6):  # 5 epochos demonstracijai
            update_data = {
                "current_epoch": epoch,
                "training_status": "running"
            }
            
            update_result = session_manager.update_session(training_session_id, update_data)
            
            if update_result:
                logger.info(f"Atnaujinta treniravimo sesija: Epocha {epoch}/50")
            else:
                logger.error(f"Nepavyko atnaujinti treniravimo sesijos")
            
            time.sleep(0.5)  # Trumpas uždelsimas simuliacijai
        
        # 5. Gauname sesijos informaciją
        logger.info("5. Gauname treniravimo sesijos informaciją")
        
        session_info = session_manager.get_session_info(training_session_id)
        
        if session_info:
            logger.info(f"Sesijos informacija: {json.dumps(session_info, default=str, indent=2)}")
        else:
            logger.error("Nepavyko gauti sesijos informacijos")
        
        # 6. Baigiame treniravimo sesiją
        logger.info("6. Baigiame treniravimo sesiją")
        
        end_result = session_manager.end_session(training_session_id, success=True)
        
        if end_result:
            logger.info(f"Treniravimo sesija baigta: {json.dumps(end_result, default=str, indent=2)}")
        else:
            logger.error("Nepavyko baigti treniravimo sesijos")
        
        # 7. Pradedame testavimo sesiją
        logger.info("7. Pradedame testavimo sesiją")
        
        testing_metadata = {
            "model_id": model.id,
            "dataset_name": "btc_test_data",
            "test_type": "accuracy",
            "test_params": {
                "batch_size": 32,
                "metrics": ["mae", "rmse"]
            }
        }
        
        testing_result = session_manager.start_session(user.id, "testing", testing_metadata)
        
        if not testing_result:
            logger.error("Nepavyko pradėti testavimo sesijos")
            return
        
        testing_session_id = testing_result["user_session"]["id"]
        logger.info(f"Pradėta testavimo sesija: ID={testing_session_id}")
        logger.info(f"Testavimo sesijos detalės: {json.dumps(testing_result, default=str, indent=2)}")
        
        # 8. Atnaujiname testavimo sesiją
        logger.info("8. Atnaujiname testavimo sesiją")
        
        update_data = {
            "testing_status": "running"
        }
        
        update_result = session_manager.update_session(testing_session_id, update_data)
        
        if update_result:
            logger.info(f"Atnaujinta testavimo sesija: {update_result['testing_session']['status']}")
        else:
            logger.error("Nepavyko atnaujinti testavimo sesijos")
        
        # 9. Baigiame testavimo sesiją su rezultatais
        logger.info("9. Baigiame testavimo sesiją su rezultatais")
        
        test_results = {
            "accuracy": 0.92,
            "mae": 245.6,
            "rmse": 312.3,
            "prediction_time_ms": 120.5
        }
        
        end_result = session_manager.end_session(testing_session_id, success=True, results=test_results)
        
        if end_result:
            logger.info(f"Testavimo sesija baigta: {json.dumps(end_result, default=str, indent=2)}")
        else:
            logger.error("Nepavyko baigti testavimo sesijos")
        
        # 10. Gauname naudotojo sesijų sąrašą
        logger.info("10. Gauname naudotojo sesijų sąrašą")
        
        sessions_list = session_manager.list_user_sessions(user.id)
        
        if sessions_list:
            logger.info(f"Naudotojo sesijų skaičius: {sessions_list['total']}")
            logger.info(f"Sesijų sąrašas: {json.dumps(sessions_list, default=str, indent=2)}")
        else:
            logger.error("Nepavyko gauti naudotojo sesijų sąrašo")
        
        # 11. Valome testavimo duomenis
        logger.info("11. Valome testavimo duomenis")
        
        # Ištriname modelį
        if model_service.delete_model(model.id):
            logger.info(f"Modelis {model.id} ištrintas")
        
        # Ištriname naudotoją (kartu ištrins ir visas susijusias sesijas)
        if user_service.delete_user(user.id):
            logger.info(f"Naudotojas {user.id} ištrintas")
        
        logger.info("Sesijos valdymo serviso pavyzdys baigtas")
        
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
        db_session.close()
        logger.info("Duomenų bazės sesija uždaryta")

if __name__ == "__main__":
    main()