"""
Pavyzdinis skriptas, parodantis kaip naudoti ID generavimo utilą.
"""
import os
import sys
import logging

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from database.models.user_models import User, UserSession, TrainingSession, TestingSession
from utils.id_generator import (
    generate_uuid, 
    generate_simple_id, 
    generate_hash_id, 
    generate_session_id,
    ensure_unique_id
)

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti ID generavimo utilų naudojimą.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    try:
        logger.info("Pradedame ID generavimo pavyzdį")
        
        # 1. Generuojame skirtingų tipų ID
        logger.info("1. Skirtingų tipų ID generavimas:")
        
        # UUID
        uuid_id = generate_uuid()
        logger.info(f"  - UUID: {uuid_id}")
        
        # Paprastas ID su prefiksu
        simple_id_with_prefix = generate_simple_id(prefix="USR", length=8)
        logger.info(f"  - Paprastas ID su prefiksu: {simple_id_with_prefix}")
        
        # Paprastas ID be prefikso
        simple_id = generate_simple_id(length=12)
        logger.info(f"  - Paprastas ID be prefikso: {simple_id}")
        
        # Hash ID su prefiksu
        hash_id_with_prefix = generate_hash_id(prefix="DOC", salt="example_salt")
        logger.info(f"  - Hash ID su prefiksu: {hash_id_with_prefix}")
        
        # Hash ID be prefikso
        hash_id = generate_hash_id(salt="another_salt")
        logger.info(f"  - Hash ID be prefikso: {hash_id}")
        
        # 2. Generuojame sesijų ID
        logger.info("2. Sesijų ID generavimas:")
        
        # Treniravimo sesijos ID
        training_session_id = generate_session_id(session_type="training")
        logger.info(f"  - Treniravimo sesijos ID: {training_session_id}")
        
        # Testavimo sesijos ID
        testing_session_id = generate_session_id(session_type="testing")
        logger.info(f"  - Testavimo sesijos ID: {testing_session_id}")
        
        # Bendros sesijos ID
        general_session_id = generate_session_id()
        logger.info(f"  - Bendros sesijos ID: {general_session_id}")
        
        # 3. Demonstruojame unikalių ID generavimą
        logger.info("3. Unikalių ID generavimas:")
        
        # Generuojame unikalų UUID naudotojui
        unique_user_id = ensure_unique_id(session, User, generate_uuid)
        logger.info(f"  - Unikalus naudotojo ID: {unique_user_id}")
        
        # Generuojame unikalų ID naudotojo sesijai
        unique_session_id = ensure_unique_id(session, UserSession, generate_uuid)
        logger.info(f"  - Unikalus sesijos ID: {unique_session_id}")
        
        # Generuojame unikalų ID treniravimo sesijai
        unique_training_id = ensure_unique_id(
            session, 
            TrainingSession, 
            generate_session_id, 
            session_type="training"
        )
        logger.info(f"  - Unikalus treniravimo sesijos ID: {unique_training_id}")
        
        # Generuojame unikalų ID testavimo sesijai
        unique_testing_id = ensure_unique_id(
            session, 
            TestingSession, 
            generate_session_id, 
            session_type="testing"
        )
        logger.info(f"  - Unikalus testavimo sesijos ID: {unique_testing_id}")
        
        # 4. Tikrinamas unikalumo užtikrinimas
        logger.info("4. Unikalumo užtikrinimo demonstracija:")
        
        # Sugeneruokime kelis unikalius ID ir pažiūrėkime, ar jie skiriasi
        ids = []
        for i in range(5):
            new_id = ensure_unique_id(session, User, generate_uuid)
            ids.append(new_id)
            logger.info(f"  - Sugeneruotas ID #{i+1}: {new_id}")
        
        # Patikriname, ar visi ID unikalūs
        unique_ids = set(ids)
        if len(unique_ids) == len(ids):
            logger.info("  - Visi sugeneruoti ID yra unikalūs!")
        else:
            logger.error("  - Kažkurie sugeneruoti ID pasikartoja!")
        
        logger.info("ID generavimo pavyzdys baigtas")
        
    except Exception as e:
        logger.error(f"Įvyko klaida: {str(e)}")
    
    finally:
        # Uždarome duomenų bazės sesiją
        session.close()
        logger.info("Duomenų bazės sesija uždaryta")

if __name__ == "__main__":
    main()