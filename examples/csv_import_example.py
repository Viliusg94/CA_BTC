"""
Pavyzdinis skriptas, parodantis kaip importuoti eksperimento rezultatus iš CSV.
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
    Pagrindinė funkcija, demonstruojanti eksperimento rezultatų importavimą iš CSV.
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
        
        # Sukuriame naują eksperimentą importavimui
        logger.info("Kuriame naują eksperimentą...")
        experiment = experiment_service.create_experiment(
            name="CSV importavimo testas",
            creator_id=test_user.id,
            description="Eksperimentas skirtas CSV importavimo testavimui"
        )
        
        logger.info(f"Sukurtas naujas eksperimentas su ID: {experiment.id}")
        
        # Nustatome kelis bazinius hiperparametrus
        hyperparameters = {
            "model_type": "RandomForest",
            "n_estimators": 100,
            "max_depth": 10
        }
        experiment_service.save_hyperparameters(experiment.id, hyperparameters)
        logger.info("Nustatyti eksperimento hiperparametrai")
        
        # CSV failo kelias
        csv_file_path = os.path.join(os.path.dirname(__file__), "data", "sample_metrics.csv")
        
        # Tikriname, ar failas egzistuoja
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV failas nerastas: {csv_file_path}")
            # Sukuriame direktoriją, jei jos nėra
            os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
            
            # Sukuriame pavyzdinį CSV failą
            logger.info("Kuriame pavyzdinį CSV failą...")
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                f.write("metric_name,metric_value,created_at,stage,notes\n")
                f.write("accuracy,0.92,2025-05-21 10:15:30,test,Galutinis modelio tikslumas\n")
                f.write("precision,0.89,2025-05-21 10:15:30,test,Galutinis modelio tikslumas\n")
                f.write("recall,0.91,2025-05-21 10:15:30,test,Galutinis modelio tikslumas\n")
                f.write("f1_score,0.9,2025-05-21 10:15:30,test,Galutinis modelio tikslumas\n")
                f.write("loss,0.15,2025-05-21 10:00:00,validation,Validacijos vertė\n")
                f.write("accuracy,0.87,2025-05-21 10:00:00,validation,Validacijos vertė\n")
                f.write("loss,0.12,2025-05-21 09:45:00,train,Treniravimo vertė\n")
                f.write("accuracy,0.91,2025-05-21 09:45:00,train,Treniravimo vertė\n")
            
            logger.info(f"Sukurtas pavyzdinis CSV failas: {csv_file_path}")
        
        # Importuojame rezultatus iš CSV
        logger.info(f"Importuojame eksperimento rezultatus iš CSV failo: {csv_file_path}")
        import_result = experiment_service.import_results_from_csv(
            experiment_id=experiment.id,
            csv_file=csv_file_path
        )
        
        # Parodome importavimo rezultatus
        if import_result["success"]:
            logger.info("Importavimas sėkmingas!")
            logger.info(f"Importuota: {import_result['imported_count']} metrikų")
            logger.info(f"Praleista: {import_result['skipped_count']} metrikų")
            logger.info(f"Klaidos: {import_result['error_count']} metrikų")
        else:
            logger.error(f"Importavimas nepavyko: {import_result.get('error', 'Nežinoma klaida')}")
        
        # Patikriname, ar rezultatai buvo importuoti
        if import_result["imported_count"] > 0:
            # Gauname eksperimento rezultatus ir parodome juos
            results = experiment_service.get_experiment_results(experiment.id)
            logger.info(f"Eksperimento rezultatai po importavimo ({len(results)} įrašai):")
            
            for i, result in enumerate(results[:5]):  # Parodome pirmus 5 rezultatus
                logger.info(f"{i+1}. {result.metric_name}: {result.metric_value} ({result.stage})")
            
            if len(results) > 5:
                logger.info(f"... ir dar {len(results) - 5} įrašai")
        
        # Eksportuojame rezultatus atgal į CSV (testavimui)
        export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        export_file = os.path.join(export_dir, f"reimported_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        logger.info(f"Eksportuojame importuotus rezultatus atgal į CSV: {export_file}")
        export_success = experiment_service.export_results_to_csv(
            experiment_id=experiment.id,
            output_file=export_file,
            include_stage=True,
            include_notes=True
        )
        
        if export_success:
            logger.info(f"Rezultatai sėkmingai eksportuoti į: {export_file}")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()