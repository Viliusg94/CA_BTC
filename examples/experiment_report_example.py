"""
Pavyzdinis skriptas, parodantis kaip generuoti ir išsaugoti eksperimentų ataskaitas.
"""
import os
import sys
import logging
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
    Pagrindinė funkcija, demonstruojanti eksperimentų ataskaitų generavimą.
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
        
        # DEMO 1: Sukuriame naują eksperimentą ataskaitai
        logger.info("\n1. DEMO: Naujo eksperimento su duomenimis sukūrimas")
        
        experiment = experiment_service.create_experiment(
            name="Ataskaitos testavimo eksperimentas",
            creator_id=test_user.id,
            description="Šis eksperimentas sukurtas ataskaitų generavimo funkcionalumo demonstravimui"
        )
        
        logger.info(f"Sukurtas naujas eksperimentas su ID: {experiment.id}")
        
        # Nustatome eksperimento statusą
        experiment_service.update_experiment_status(experiment.id, "baigtas")
        
        # Nustatome hiperparametrus
        hyperparameters = {
            "model_type": "XGBoost",
            "learning_rate": 0.01,
            "max_depth": 6,
            "n_estimators": 100,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "objective": "binary:logistic",
            "eval_metric": "auc"
        }
        experiment_service.save_hyperparameters(experiment.id, hyperparameters)
        logger.info("Nustatyti eksperimento hiperparametrai")
        
        # Pridedame treniravimo metrikos rezultatus
        train_metrics = {
            "accuracy": 0.92,
            "precision": 0.94,
            "recall": 0.89,
            "f1_score": 0.915,
            "loss": 0.21
        }
        
        for metric_name, metric_value in train_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="train",
                notes="Treniravimo metrikos"
            )
        
        # Pridedame validacijos metrikos rezultatus
        validation_metrics = {
            "accuracy": 0.89,
            "precision": 0.91,
            "recall": 0.86,
            "f1_score": 0.884,
            "loss": 0.28
        }
        
        for metric_name, metric_value in validation_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="validation",
                notes="Validacijos metrikos"
            )
        
        # Pridedame testavimo metrikos rezultatus
        test_metrics = {
            "accuracy": 0.875,
            "precision": 0.89,
            "recall": 0.84,
            "f1_score": 0.864,
            "auc": 0.91
        }
        
        for metric_name, metric_value in test_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="test",
                notes="Testavimo metrikos"
            )
        
        logger.info("Pridėti eksperimento metrikų rezultatai")
        
        # DEMO 2: Generuojame eksperimento ataskaitą
        logger.info("\n2. DEMO: Eksperimento ataskaitos generavimas")
        
        # Generuojame ataskaitą
        report = experiment_service.generate_experiment_report(
            experiment_id=experiment.id,
            include_hyperparams=True,
            include_metrics=True
        )
        
        logger.info("Sugeneruota ataskaita:")
        logger.info("\n" + report)
        
        # DEMO 3: Išsaugome ataskaitą į failą
        logger.info("\n3. DEMO: Ataskaitos išsaugojimas į failą")
        
        # Apibrėžiame failo pavadinimą
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Sukuriame failo pavadinimą su data ir eksperimento pavadinimu
        file_name = f"{experiment.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        output_file = os.path.join(reports_dir, file_name)
        
        # Išsaugome ataskaitą
        success = experiment_service.save_experiment_report(
            experiment_id=experiment.id,
            output_file=output_file
        )
        
        if success:
            logger.info(f"Ataskaita sėkmingai išsaugota į: {output_file}")
            
            # Patikriname, ar failas buvo sukurtas
            if os.path.exists(output_file):
                logger.info(f"Failo dydis: {os.path.getsize(output_file)} baitų")
                logger.info(f"Pilnas failo kelias: {os.path.abspath(output_file)}")
        else:
            logger.error("Nepavyko išsaugoti ataskaitos")
        
        # DEMO 4: Generuojame ataskaitą be hiperparametrų
        logger.info("\n4. DEMO: Eksperimento ataskaitos generavimas be hiperparametrų")
        
        # Generuojame ataskaitą be hiperparametrų
        report_no_hyperparams = experiment_service.generate_experiment_report(
            experiment_id=experiment.id,
            include_hyperparams=False,
            include_metrics=True
        )
        
        logger.info("Sugeneruota ataskaita be hiperparametrų:")
        logger.info("\n" + report_no_hyperparams[:500] + "...\n(Ataskaita sutrumpinta)")
        
        # Išsaugome ataskaitą be hiperparametrų
        file_name_no_hyperparams = f"{experiment.name.replace(' ', '_')}_be_hiperparametrų_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        output_file_no_hyperparams = os.path.join(reports_dir, file_name_no_hyperparams)
        
        experiment_service.save_experiment_report(
            experiment_id=experiment.id,
            output_file=output_file_no_hyperparams,
            include_hyperparams=False
        )
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()