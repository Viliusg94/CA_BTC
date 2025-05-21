"""
Pavyzdinis skriptas, parodantis kaip naudoti eksperimentų rezultatų registravimo funkcijas.
"""
import os
import sys
import logging
import random
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
    Pagrindinė funkcija, demonstruojanti eksperimentų rezultatų registravimą.
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
            name="CNN modelio rezultatų testavimas",
            creator_id=test_user.id,
            description="CNN modelio treniravimo ir validacijos rezultatų registravimas"
        )
        
        logger.info(f"Sukurtas naujas eksperimentas su ID: {experiment.id}")
        
        # Nustatome hiperparametrus
        hyperparameters = {
            "learning_rate": 0.001,
            "batch_size": 64,
            "epochs": 20,
            "optimizer": "adam",
            "layers": 3
        }
        
        experiment_service.save_hyperparameters(experiment.id, hyperparameters)
        logger.info("Išsaugoti eksperimento hiperparametrai")
        
        # DEMO 2: Pridedame treniravimo rezultatus
        logger.info("\n2. DEMO: Treniravimo rezultatų pridėjimas")
        
        # Imituojame treniravimo procesą su rezultatais skirtinguose eposuose
        epochs = hyperparameters["epochs"]
        
        for epoch in range(1, epochs + 1):
            # Imituojame treniravimo metrikas
            train_loss = 0.5 - 0.4 * (epoch / epochs) + random.uniform(-0.05, 0.05)
            train_accuracy = 0.6 + 0.35 * (epoch / epochs) + random.uniform(-0.05, 0.05)
            
            # Pridedame treniravimo metrikas
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name="loss",
                metric_value=train_loss,
                stage="train",
                notes=f"Epocha {epoch}/{epochs}"
            )
            
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name="accuracy",
                metric_value=train_accuracy,
                stage="train",
                notes=f"Epocha {epoch}/{epochs}"
            )
            
            # Imituojame validacijos metrikas
            val_loss = 0.6 - 0.3 * (epoch / epochs) + random.uniform(-0.1, 0.1)
            val_accuracy = 0.55 + 0.3 * (epoch / epochs) + random.uniform(-0.1, 0.1)
            
            # Pridedame validacijos metrikas
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name="loss",
                metric_value=val_loss,
                stage="validation",
                notes=f"Epocha {epoch}/{epochs}"
            )
            
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name="accuracy",
                metric_value=val_accuracy,
                stage="validation",
                notes=f"Epocha {epoch}/{epochs}"
            )
            
            # Kas 5 epochas rašome progresą
            if epoch % 5 == 0 or epoch == epochs:
                logger.info(f"Epocha {epoch}/{epochs}: "
                          f"train_loss={train_loss:.4f}, train_acc={train_accuracy:.4f}, "
                          f"val_loss={val_loss:.4f}, val_acc={val_accuracy:.4f}")
        
        logger.info("Visi treniravimo ir validacijos rezultatai pridėti")
        
        # DEMO 3: Gauname eksperimento rezultatus
        logger.info("\n3. DEMO: Rezultatų gavimas")
        
        # Gauname visus rezultatus
        all_results = experiment_service.get_experiment_results(experiment.id)
        logger.info(f"Eksperimente yra iš viso {len(all_results)} rezultatų įrašų")
        
        # Gauname tik tiklumo (accuracy) metrikos rezultatus
        accuracy_results = experiment_service.get_experiment_results(experiment.id, "accuracy")
        logger.info(f"Eksperimente yra {len(accuracy_results)} tiklumo (accuracy) metrikos įrašų")
        
        # Gauname naujausią validacijos tikslumo rezultatą
        latest_val_accuracy = experiment_service.get_latest_experiment_result(
            experiment_id=experiment.id,
            metric_name="accuracy"
        )
        
        if latest_val_accuracy:
            logger.info(f"Naujausias tiklumo rezultatas: {latest_val_accuracy.metric_value} "
                      f"({latest_val_accuracy.stage} etape, {latest_val_accuracy.created_at})")
        
        # DEMO 4: Gauname metrikų suvestinę
        logger.info("\n4. DEMO: Metrikų suvestinė")
        
        metrics_summary = experiment_service.get_experiment_metrics_summary(experiment.id)
        
        logger.info("Eksperimento metrikų suvestinė:")
        for metric_name, metric_value in metrics_summary.items():
            logger.info(f"- {metric_name}: {metric_value:.4f}")
        
        # DEMO 5: Pridedame testavimo rezultatus
        logger.info("\n5. DEMO: Testavimo rezultatų pridėjimas")
        
        # Imituojame testavimo metrikas
        test_metrics = {
            "accuracy": 0.923,
            "precision": 0.917,
            "recall": 0.908,
            "f1_score": 0.912,
            "auc": 0.945
        }
        
        # Pridedame testavimo metrikas
        for metric_name, metric_value in test_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="test",
                notes="Galutinis modelio įvertinimas"
            )
        
        logger.info("Testavimo rezultatai pridėti:")
        for metric_name, metric_value in test_metrics.items():
            logger.info(f"- {metric_name}: {metric_value:.4f}")
        
        # DEMO 6: Atnaujinta metrikų suvestinė
        logger.info("\n6. DEMO: Atnaujinta metrikų suvestinė su testavimo rezultatais")
        
        updated_summary = experiment_service.get_experiment_metrics_summary(experiment.id)
        
        logger.info("Atnaujinta eksperimento metrikų suvestinė:")
        for metric_name, metric_value in updated_summary.items():
            logger.info(f"- {metric_name}: {metric_value:.4f}")
        
        # DEMO 7: Patikriname, kad priimami tik skaičių tipo rezultatai
        logger.info("\n7. DEMO: Bandome pridėti neteisingą reikšmę")
        
        try:
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name="invalid_metric",
                metric_value="ne skaičius",  # Tai sukels klaidą
                stage="test"
            )
            logger.warning("Neteisingas rezultatas buvo pridėtas - tai neturėtų įvykti!")
        except ValueError as e:
            logger.info(f"Teisingai sugauta klaida: {str(e)}")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()