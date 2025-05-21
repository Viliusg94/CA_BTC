"""
Pavyzdinis skriptas, parodantis kaip eksportuoti ir importuoti eksperimentus JSON formatu.
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
    Pagrindinė funkcija, demonstruojanti eksperimentų eksportavimą/importavimą JSON formatu.
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
        
        # DEMO 1: Sukuriame naują eksperimentą su duomenimis
        logger.info("\n1. DEMO: Naujo eksperimento sukūrimas")
        
        experiment = experiment_service.create_experiment(
            name="JSON eksporto-importo testas",
            creator_id=test_user.id,
            description="Šis eksperimentas skirtas JSON eksportavimo ir importavimo funkcijų testavimui"
        )
        
        logger.info(f"Sukurtas naujas eksperimentas su ID: {experiment.id}")
        
        # Nustatome hiperparametrus
        hyperparameters = {
            "model": "LSTM",
            "epochs": 50,
            "batch_size": 32,
            "learning_rate": 0.001,
            "activation": "relu",
            "dropout": 0.2,
            "optimizer": "adam"
        }
        experiment_service.save_hyperparameters(experiment.id, hyperparameters)
        
        # Pridedame keletą rezultatų
        metrics = {
            "accuracy": 0.87,
            "precision": 0.85,
            "recall": 0.83,
            "f1_score": 0.84,
            "loss": 0.32
        }
        
        for metric_name, metric_value in metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="validation",
                notes="Validacijos metrikos"
            )
        
        logger.info("Pridėti eksperimento hiperparametrai ir rezultatai")
        
        # DEMO 2: Eksportuojame eksperimentą į JSON
        logger.info("\n2. DEMO: Eksperimento eksportavimas į JSON")
        
        # Sukuriame direktoriją eksportui
        export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports', 'packages')
        os.makedirs(export_dir, exist_ok=True)
        
        # Sukuriame failo pavadinimą su data
        json_filename = f"experiment_{experiment.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_filepath = os.path.join(export_dir, json_filename)
        
        # Eksportuojame eksperimentą į JSON
        export_success = experiment_service.export_experiment_to_json(
            experiment_id=experiment.id,
            output_file=json_filepath
        )
        
        if export_success:
            logger.info(f"Eksperimentas sėkmingai eksportuotas į: {json_filepath}")
            
            # Parodome, kad failas buvo sukurtas
            file_size = os.path.getsize(json_filepath)
            logger.info(f"JSON failo dydis: {file_size} baitų")
        else:
            logger.error("Nepavyko eksportuoti eksperimento į JSON")
            return
        
        # DEMO 3: Importuojame eksperimentą iš JSON
        logger.info("\n3. DEMO: Eksperimento importavimas iš JSON (naujas ID)")
        
        # Importuojame eksperimentą iš JSON, sukuriant naują ID
        import_result = experiment_service.import_experiment_from_json(
            json_file=json_filepath,
            create_new_id=True,  # Kurimas naujas ID (išvengiama konfliktų)
            creator_id=test_user.id  # Nurodome kūrėją
        )
        
        if import_result["success"]:
            logger.info("Eksperimentas sėkmingai importuotas:")
            logger.info(f"- Naujas eksperimento ID: {import_result['experiment_id']}")
            logger.info(f"- Eksperimento pavadinimas: {import_result['experiment_name']}")
            logger.info(f"- Originalus ID: {import_result['original_id']}")
            logger.info(f"- Importuota rezultatų: {import_result['imported_results_count']}")
            logger.info(f"- Praleista rezultatų: {import_result['skipped_results_count']}")
            
            # Išsaugome naujo importuoto eksperimento ID
            imported_experiment_id = import_result["experiment_id"]
        else:
            logger.error(f"Nepavyko importuoti eksperimento: {import_result.get('error', 'Nežinoma klaida')}")
            return
        
        # DEMO 4: Bandome importuoti su tuo pačiu ID (turėtų nepavykti)
        logger.info("\n4. DEMO: Importavimas su tuo pačiu ID (turėtų nepavykti)")
        
        # Bandome importuoti su tuo pačiu ID
        import_conflict_result = experiment_service.import_experiment_from_json(
            json_file=json_filepath,
            create_new_id=False  # Bandome naudoti originalų ID
        )
        
        if not import_conflict_result["success"]:
            logger.info("Teisingai aptiktas ID konfliktas:")
            logger.info(f"- Klaidos pranešimas: {import_conflict_result.get('error', 'Nežinoma klaida')}")
        else:
            logger.warning("Neaptiktas ID konfliktas - tai neturėtų įvykti!")
        
        # DEMO 5: Tikriname importuoto eksperimento duomenis
        logger.info("\n5. DEMO: Importuoto eksperimento duomenų patikrinimas")
        
        # Gauname importuotą eksperimentą
        imported_experiment = experiment_service.get_experiment(imported_experiment_id)
        
        if imported_experiment:
            logger.info(f"Importuotas eksperimentas: {imported_experiment.name}")
            
            # Gauname hiperparametrus
            imported_hyperparams = experiment_service.get_hyperparameters(imported_experiment_id)
            logger.info(f"Importuoti hiperparametrai ({len(imported_hyperparams)} vnt.):")
            for param_name, param_value in imported_hyperparams.items():
                logger.info(f"- {param_name}: {param_value}")
            
            # Gauname rezultatus
            imported_results = experiment_service.get_experiment_results(imported_experiment_id)
            logger.info(f"Importuoti rezultatai ({len(imported_results)} vnt.):")
            for i, result in enumerate(imported_results):
                logger.info(f"- {i+1}. {result.metric_name}: {result.metric_value} ({result.stage})")
        else:
            logger.error(f"Nepavyko rasti importuoto eksperimento su ID: {imported_experiment_id}")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()