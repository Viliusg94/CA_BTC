"""
Pavyzdinis skriptas, parodantis kaip naudoti hiperparametrų valdymo funkcijas.
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
    Pagrindinė funkcija, demonstruojanti hiperparametrų valdymo funkcijas.
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

        # Tikriname, ar yra testinis naudotojas
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
        logger.info("\n1. DEMO: Naujo eksperimento sukūrimas")
        
        experiment = experiment_service.create_experiment(
            name="LSTM modelis su hiperparametrais",
            creator_id=test_user.id,
            description="LSTM modelio testavimas su įvairiais hiperparametrais"
        )
        
        logger.info(f"Sukurtas naujas eksperimentas su ID: {experiment.id}")
        
        # DEMO 2: Išsaugojame hiperparametrus
        logger.info("\n2. DEMO: Hiperparametrų išsaugojimas")
        
        # Apibrėžiame hiperparametrus
        hyperparameters = {
            "learning_rate": 0.001,
            "batch_size": 64,
            "epochs": 100,
            "optimizer": "adam",
            "hidden_layers": 2,
            "hidden_units": 128,
            "dropout_rate": 0.2
        }
        
        # Išsaugome hiperparametrus
        experiment = experiment_service.save_hyperparameters(
            experiment_id=experiment.id,
            hyperparameters=hyperparameters
        )
        
        logger.info("Išsaugoti hiperparametrai:")
        for param_name, param_value in hyperparameters.items():
            logger.info(f"- {param_name}: {param_value}")
        
        # DEMO 3: Gauname hiperparametrus
        logger.info("\n3. DEMO: Hiperparametrų gavimas")
        
        retrieved_hyperparameters = experiment_service.get_hyperparameters(experiment.id)
        
        logger.info("Gauti hiperparametrai:")
        for param_name, param_value in retrieved_hyperparameters.items():
            logger.info(f"- {param_name}: {param_value}")
        
        # DEMO 4: Atnaujiname hiperparametrus
        logger.info("\n4. DEMO: Hiperparametrų atnaujinimas")
        
        # Apibrėžiame naujus hiperparametrus
        updated_hyperparameters = {
            "learning_rate": 0.0005,  # Pakeičiame mokymosi greitį
            "batch_size": 128,        # Pakeičiame batch dydį
            "early_stopping": True    # Pridedame naują parametrą
        }
        
        # Atnaujiname hiperparametrus
        experiment = experiment_service.update_hyperparameters(
            experiment_id=experiment.id,
            hyperparameters=updated_hyperparameters
        )
        
        # Gauname atnaujintus hiperparametrus
        updated_params = experiment_service.get_hyperparameters(experiment.id)
        
        logger.info("Atnaujinti hiperparametrai:")
        for param_name, param_value in updated_params.items():
            logger.info(f"- {param_name}: {param_value}")
        
        # DEMO 5: Pašaliname hiperparametrą
        logger.info("\n5. DEMO: Hiperparametro pašalinimas")
        
        # Pašaliname dropout_rate hiperparametrą
        experiment = experiment_service.delete_hyperparameter(
            experiment_id=experiment.id,
            param_name="dropout_rate"
        )
        
        # Gauname hiperparametrus po pašalinimo
        final_params = experiment_service.get_hyperparameters(experiment.id)
        
        logger.info("Hiperparametrai po pašalinimo:")
        for param_name, param_value in final_params.items():
            logger.info(f"- {param_name}: {param_value}")
        
        # Tikriname, ar dropout_rate buvo pašalintas
        if "dropout_rate" not in final_params:
            logger.info("Sėkmingai pašalintas 'dropout_rate' hiperparametras")
        else:
            logger.warning("'dropout_rate' hiperparametras nebuvo pašalintas")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()