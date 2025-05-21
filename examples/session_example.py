"""
Pavyzdinis skriptas parodantis kaip naudoti SessionService klasę.
"""
import os
import sys
import logging
import time
from datetime import datetime, timedelta

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.user_service import UserService
from services.session_service import SessionService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija demonstruojanti SessionService naudojimą.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    # Sukuriame naudotojų ir sesijų servisus
    user_service = UserService(session)
    session_service = SessionService(session)
    
    try:
        logger.info("Pradedamas sesijų valdymo pavyzdys")
        
        # 1. Sukuriame naudotoją sesijų testavimui
        logger.info("1. Kuriame naudotoją sesijų testavimui")
        
        test_user_data = {
            "username": "sesiju_testas",
            "email": "sesijos@example.com",
            "password": "slaptazodis123",
            "full_name": "Sesijų Testavimas",
            "is_admin": False
        }
        
        user = user_service.create_user(test_user_data)
        
        if not user:
            logger.error("Nepavyko sukurti naudotojo sesijų testavimui")
            return
        
        logger.info(f"Sukurtas naudotojas: ID={user.id}, Vardas={user.username}")
        
        # 2. Sukuriame treniravimo sesiją
        logger.info("2. Kuriame treniravimo sesiją")
        
        training_session_data = {
            "user_id": user.id,
            "session_type": "training",
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "metadata": {
                "model_type": "lstm",
                "dataset_size": 1000,
                "learning_rate": 0.001
            }
        }
        
        training_session = session_service.create_session(training_session_data)
        
        if training_session:
            logger.info(f"Sukurta treniravimo sesija: ID={training_session.id}")
            logger.info(f"Sesijos pradžia: {training_session.start_time}")
        else:
            logger.error("Nepavyko sukurti treniravimo sesijos")
        
        # 3. Sukuriame testavimo sesiją
        logger.info("3. Kuriame testavimo sesiją")
        
        testing_session_data = {
            "user_id": user.id,
            "session_type": "testing",
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "metadata": {
                "test_dataset": "bitcoin_2021_2022",
                "metrics": ["accuracy", "precision", "recall"]
            }
        }
        
        testing_session = session_service.create_session(testing_session_data)
        
        if testing_session:
            logger.info(f"Sukurta testavimo sesija: ID={testing_session.id}")
        else:
            logger.error("Nepavyko sukurti testavimo sesijos")
        
        # 4. Gauname naudotojo sesijų sąrašą
        logger.info("4. Gauname naudotojo sesijų sąrašą")
        
        user_sessions = session_service.list_user_sessions(user.id)
        
        logger.info(f"Naudotojas turi {len(user_sessions)} sesijas:")
        for s in user_sessions:
            logger.info(f"- Sesija {s.id}: tipas={s.session_type}, aktyvi={s.is_active}")
        
        # 5. Gauname tik aktyvias sesijas
        logger.info("5. Gauname tik aktyvias sesijas")
        
        active_sessions = session_service.list_user_sessions(user.id, active_only=True)
        
        logger.info(f"Naudotojas turi {len(active_sessions)} aktyvias sesijas")
        
        # 6. Atnaujiname treniravimo sesiją
        logger.info("6. Atnaujiname treniravimo sesiją")
        
        # Imituojame, kad praėjo kažkiek laiko
        time.sleep(2)
        
        update_data = {
            "metadata": {
                "model_type": "lstm",
                "dataset_size": 1000,
                "learning_rate": 0.001,
                "epochs_completed": 10,
                "current_loss": 0.05
            }
        }
        
        updated_session = session_service.update_session(training_session.id, update_data)
        
        if updated_session:
            logger.info(f"Treniravimo sesija atnaujinta: {updated_session.id}")
            logger.info(f"Atnaujinta: {updated_session.updated_at}")
        else:
            logger.error("Nepavyko atnaujinti treniravimo sesijos")
        
        # 7. Baigiame testavimo sesiją
        logger.info("7. Baigiame testavimo sesiją")
        
        ended_session = session_service.end_session(testing_session.id)
        
        if ended_session:
            logger.info(f"Testavimo sesija baigta: {ended_session.id}")
            logger.info(f"Sesijos pabaiga: {ended_session.end_time}")
            logger.info(f"Sesijos būsena: {ended_session.status}")
        else:
            logger.error("Nepavyko baigti testavimo sesijos")
        
        # 8. Gauname sesijas pagal tipą
        logger.info("8. Gauname sesijas pagal tipą")
        
        training_sessions = session_service.list_sessions_by_type("training")
        testing_sessions = session_service.list_sessions_by_type("testing")
        
        logger.info(f"Sistemoje yra {len(training_sessions)} treniravimo sesijos")
        logger.info(f"Sistemoje yra {len(testing_sessions)} testavimo sesijos")
        
        # 9. Ištriname vieną sesiją
        logger.info("9. Ištriname vieną sesiją")
        
        if session_service.delete_session(training_session.id):
            logger.info(f"Sesija {training_session.id} ištrinta")
        else:
            logger.error(f"Nepavyko ištrinti sesijos {training_session.id}")
        
        # 10. Ištriname visas naudotojo sesijas
        logger.info("10. Ištriname visas naudotojo sesijas")
        
        deleted_count = session_service.delete_user_sessions(user.id)
        
        logger.info(f"Ištrintos {deleted_count} naudotojo sesijos")
        
        # Išvalome testavimo duomenis
        logger.info("Šaliname testavimo naudotoją")
        user_service.delete_user(user.id)
        
        logger.info("Sesijų valdymo pavyzdys baigtas")
        
    except Exception as e:
        logger.error(f"Įvyko klaida: {str(e)}")
    
    finally:
        # Uždarome sesiją
        session.close()
        logger.info("Duomenų bazės sesija uždaryta")

if __name__ == "__main__":
    main()