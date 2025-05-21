"""
Pavyzdinis skriptas, parodantis kaip naudoti eksperimentų servisą.
"""
import os
import sys
import logging
import json
from datetime import datetime

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from database.setup_experiments_tables import setup_tables
from services.user_service import UserService
from services.experiment_service import ExperimentService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti eksperimentų serviso naudojimą.
    """
    try:
        # Sukuriame duomenų bazės ryšį
        logger.info("Jungiamasi prie duomenų bazės...")
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        db = Session(engine)

        # Inicializuojame eksperimentų lenteles
        logger.info("Inicializuojame eksperimentų lenteles...")
        setup_tables()

        # Inicializuojame reikalingus servisus
        logger.info("Inicializuojame servisus...")
        user_service = UserService(db)
        experiment_service = ExperimentService(db)

        # DEMO: Sukuriame naudotoją jei nėra
        logger.info("Tikriname, ar yra testinis naudotojas...")
        test_user = user_service.get_user_by_username("test_user")
        if not test_user:
            logger.info("Kuriame testinį naudotoją...")
            test_user = user_service.create_user(
                username="test_user",
                email="test@example.com",
                password="password123",
                full_name="Testas Testauskas"
            )
            logger.info(f"Sukurtas testinis naudotojas su ID: {test_user.id}")
        
        # DEMO 1: Sukuriame naują eksperimentą
        logger.info("\n1. DEMO: Eksperimento sukūrimas")
        
        experiment = experiment_service.create_experiment(
            name="LSTM modelio testavimas",
            creator_id=test_user.id,
            description="Testavimas, kaip LSTM modelis veikia su BTC kainų duomenimis",
            metadata={
                "model_type": "LSTM",
                "dataset": "BTC_daily_prices",
                "test_date": datetime.now().strftime("%Y-%m-%d")
            }
        )
        
        logger.info(f"Sukurtas naujas eksperimentas:")
        logger.info(f"ID: {experiment.id}")
        logger.info(f"Pavadinimas: {experiment.name}")
        logger.info(f"Statusas: {experiment.status}")
        logger.info(f"Sukūrimo laikas: {experiment.created_at}")
        
        # DEMO 2: Atnaujinkime eksperimento statusą
        logger.info("\n2. DEMO: Eksperimento statuso atnaujinimas")
        
        updated_experiment = experiment_service.update_experiment_status(
            experiment_id=experiment.id,
            status="vykdomas"
        )
        
        logger.info(f"Atnaujintas eksperimento statusas:")
        logger.info(f"ID: {updated_experiment.id}")
        logger.info(f"Pavadinimas: {updated_experiment.name}")
        logger.info(f"Statusas: {updated_experiment.status}")
        logger.info(f"Atnaujinimo laikas: {updated_experiment.updated_at}")
        
        # DEMO 3: Gauname eksperimentą pagal ID
        logger.info("\n3. DEMO: Eksperimento gavimas pagal ID")
        
        retrieved_experiment = experiment_service.get_experiment(experiment.id)
        
        if retrieved_experiment:
            logger.info(f"Rastas eksperimentas:")
            logger.info(f"ID: {retrieved_experiment.id}")
            logger.info(f"Pavadinimas: {retrieved_experiment.name}")
            logger.info(f"Statusas: {retrieved_experiment.status}")
            logger.info(f"Metaduomenys: {retrieved_experiment.metadata}")
        else:
            logger.warning("Eksperimentas nerastas")
        
        # DEMO 4: Sukuriame dar kelis eksperimentus paieškai
        logger.info("\n4. DEMO: Eksperimentų paieška")
        
        # Sukuriame dar kelis eksperimentus
        experiment_service.create_experiment(
            name="CNN modelio bandymas",
            creator_id=test_user.id,
            description="CNN modelio bandymas su BTC duomenimis",
            metadata={"model_type": "CNN"}
        )
        
        experiment_service.create_experiment(
            name="RNN modelio testavimas",
            creator_id=test_user.id,
            description="RNN modelio testavimas su ETH duomenimis",
            metadata={"model_type": "RNN", "dataset": "ETH_prices"}
        )
        
        # Ieškome eksperimentų su paieškos terminu "modelio"
        search_results = experiment_service.search_experiments(
            search_term="modelio",
            limit=10
        )
        
        logger.info(f"Rasta {len(search_results)} eksperimentų su terminu 'modelio':")
        for idx, exp in enumerate(search_results, 1):
            logger.info(f"{idx}. {exp.name} (status: {exp.status})")
        
        # Ieškome eksperimentų pagal statusą
        status_results = experiment_service.search_experiments(
            status="vykdomas",
            limit=10
        )
        
        logger.info(f"\nRasta {len(status_results)} eksperimentų su statusu 'vykdomas':")
        for idx, exp in enumerate(status_results, 1):
            logger.info(f"{idx}. {exp.name}")
        
        # DEMO 5: Atnaujinkime eksperimento duomenis
        logger.info("\n5. DEMO: Eksperimento duomenų atnaujinimas")
        
        updated_experiment = experiment_service.update_experiment(
            experiment_id=experiment.id,
            name="LSTM modelio patobulintas testavimas",
            metadata={
                "accuracy": 0.92,
                "epochs": 100
            }
        )
        
        logger.info(f"Atnaujinti eksperimento duomenys:")
        logger.info(f"ID: {updated_experiment.id}")
        logger.info(f"Naujas pavadinimas: {updated_experiment.name}")
        logger.info(f"Metaduomenys: {updated_experiment.metadata}")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()