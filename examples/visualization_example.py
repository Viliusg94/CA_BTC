"""
Pavyzdinis skriptas, parodantis kaip vizualizuoti eksperimentų rezultatus.
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
    Pagrindinė funkcija, demonstruojanti eksperimentų vizualizaciją.
    """
    try:
        # Tikriname, ar yra matplotlib
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error("Vizualizacijai reikalinga matplotlib biblioteka.")
            logger.error("Įdiekite ją įvykdę komandą: pip install matplotlib")
            return
        
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
        
        # DEMO 1: Sukuriame naują eksperimentą su duomenimis vizualizacijai
        logger.info("\n1. DEMO: Naujo eksperimento sukūrimas")
        
        experiment = experiment_service.create_experiment(
            name="Vizualizacijos testas",
            creator_id=test_user.id,
            description="Šis eksperimentas sukurtas vizualizacijos funkcionalumo demonstravimui"
        )
        
        logger.info(f"Sukurtas naujas eksperimentas su ID: {experiment.id}")
        
        # Nustatome eksperimento hiperparametrus
        hyperparameters = {
            "model_type": "NeuralNetwork",
            "epochs": 100,
            "batch_size": 64,
            "learning_rate": 0.001,
            "dropout": 0.2
        }
        experiment_service.save_hyperparameters(experiment.id, hyperparameters)
        
        # Pridedame treniravimo metrikas su reikšmėmis, kurios kinta pagal epochą
        logger.info("Pridedame treniravimo metrikos rezultatus...")
        for epoch in range(1, 101):  # 100 epochų
            # Tikslumas gerėja, bet su svyravimais
            accuracy = 0.5 + 0.4 * (1 - (1 / (epoch/20 + 1))) + 0.05 * (0.5 - (epoch % 10) / 10)
            # Praradimai mažėja
            loss = 0.5 * (1 / (epoch/10 + 1)) + 0.1 * (0.5 - (epoch % 8) / 8)
            
            # Pridedame rezultatus
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name="accuracy",
                metric_value=accuracy,
                stage="train",
                notes=f"Epocha {epoch}/100"
            )
            
            experiment_service.add_experiment_result(
                experiment_id=experiment.id,
                metric_name="loss",
                metric_value=loss,
                stage="train",
                notes=f"Epocha {epoch}/100"
            )
            
            # Pridedame validacijos metrikas kas 5 epochas
            if epoch % 5 == 0:
                # Validacijos tikslumas yra šiek tiek mažesnis nei treniravimo
                val_accuracy = accuracy * 0.9
                # Validacijos praradimai šiek tiek didesni
                val_loss = loss * 1.2
                
                experiment_service.add_experiment_result(
                    experiment_id=experiment.id,
                    metric_name="accuracy",
                    metric_value=val_accuracy,
                    stage="validation",
                    notes=f"Epocha {epoch}/100"
                )
                
                experiment_service.add_experiment_result(
                    experiment_id=experiment.id,
                    metric_name="loss",
                    metric_value=val_loss,
                    stage="validation",
                    notes=f"Epocha {epoch}/100"
                )
        
        # Pridedame testavimo metrikas
        logger.info("Pridedame testavimo metrikos rezultatus...")
        experiment_service.add_experiment_result(
            experiment_id=experiment.id,
            metric_name="accuracy",
            metric_value=0.82,
            stage="test",
            notes="Galutinis tikslumas"
        )
        
        experiment_service.add_experiment_result(
            experiment_id=experiment.id,
            metric_name="loss",
            metric_value=0.35,
            stage="test",
            notes="Galutinis praradimas"
        )
        
        experiment_service.add_experiment_result(
            experiment_id=experiment.id,
            metric_name="precision",
            metric_value=0.84,
            stage="test",
            notes="Galutinis tikslumas"
        )
        
        experiment_service.add_experiment_result(
            experiment_id=experiment.id,
            metric_name="recall",
            metric_value=0.80,
            stage="test",
            notes="Galutinis atšaukimas"
        )
        
        experiment_service.add_experiment_result(
            experiment_id=experiment.id,
            metric_name="f1_score",
            metric_value=0.82,
            stage="test",
            notes="Galutinis F1 balas"
        )
        
        # Nustatome eksperimento statusą
        experiment_service.update_experiment_status(experiment.id, "baigtas")
        
        # DEMO 2: Vizualizuojame tikslumo metrikas visoms stadijoms
        logger.info("\n2. DEMO: Tikslumo metrikų vizualizacija visoms stadijoms")
        
        # Nustatome išvesties failą
        viz_dir = os.path.join(os.path.dirname(__file__), '..', 'visualizations')
        os.makedirs(viz_dir, exist_ok=True)
        accuracy_output_file = os.path.join(viz_dir, "accuracy_visualization.png")
        
        # Vizualizuojame tikslumo metrikas
        success = experiment_service.visualize_experiment_metrics(
            experiment_id=experiment.id,
            metric_names=["accuracy"],
            output_file=accuracy_output_file,
            title="Tikslumo metrikos per mokymosi etapus"
        )
        
        if success:
            logger.info(f"Tikslumo metrikos vizualizacija išsaugota į: {accuracy_output_file}")
        else:
            logger.error("Nepavyko vizualizuoti tikslumo metrikų")
        
        # DEMO 3: Vizualizuojame praradimų metrikas visoms stadijoms
        logger.info("\n3. DEMO: Praradimų metrikų vizualizacija visoms stadijoms")
        
        # Nustatome išvesties failą
        loss_output_file = os.path.join(viz_dir, "loss_visualization.png")
        
        # Vizualizuojame praradimų metrikas
        success = experiment_service.visualize_experiment_metrics(
            experiment_id=experiment.id,
            metric_names=["loss"],
            output_file=loss_output_file,
            title="Praradimų metrikos per mokymosi etapus"
        )
        
        if success:
            logger.info(f"Praradimų metrikos vizualizacija išsaugota į: {loss_output_file}")
        else:
            logger.error("Nepavyko vizualizuoti praradimų metrikų")
        
        # DEMO 4: Palyginame tikslumo ir praradimų metrikas treniravimo etape
        logger.info("\n4. DEMO: Tikslumo ir praradimų metrikų palyginimas treniravimo etape")
        
        # Nustatome išvesties failą
        comparison_output_file = os.path.join(viz_dir, "train_metrics_comparison.png")
        
        # Vizualizuojame palyginimą
        success = experiment_service.visualize_metrics_comparison(
            experiment_id=experiment.id,
            metrics=["accuracy", "loss"],
            stage="train",
            output_file=comparison_output_file,
            title="Tikslumo ir praradimų palyginimas treniravimo etape"
        )
        
        if success:
            logger.info(f"Metrikų palyginimo vizualizacija išsaugota į: {comparison_output_file}")
        else:
            logger.error("Nepavyko vizualizuoti metrikų palyginimo")
        
        # DEMO 5: Vizualizuojame visas testavimo metrikas
        logger.info("\n5. DEMO: Visų testavimo metrikų vizualizacija")
        
        # Nustatome išvesties failą
        test_metrics_output_file = os.path.join(viz_dir, "test_metrics.png")
        
        # Vizualizuojame testavimo metrikas
        success = experiment_service.visualize_experiment_metrics(
            experiment_id=experiment.id,
            stages=["test"],
            output_file=test_metrics_output_file,
            title="Visos testavimo metrikos"
        )
        
        if success:
            logger.info(f"Testavimo metrikų vizualizacija išsaugota į: {test_metrics_output_file}")
        else:
            logger.error("Nepavyko vizualizuoti testavimo metrikų")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nVizualizacijos pavyzdžio vykdymas baigtas sėkmingai.")
        logger.info(f"Visos vizualizacijos išsaugotos kataloge: {os.path.abspath(viz_dir)}")
        
    except Exception as e:
        logger.error(f"Klaida vykdant vizualizacijos pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()