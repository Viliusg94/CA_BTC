"""
Pavyzdinis skriptas, parodantis kaip naudoti eksperimentų palyginimo funkcijas.
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
    Pagrindinė funkcija, demonstruojanti eksperimentų palyginimo funkcijas.
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
        
        # DEMO 1: Sukuriame du skirtingus eksperimentus palyginimui
        logger.info("\n1. DEMO: Dviejų eksperimentų sukūrimas palyginimui")
        
        # Sukuriame pirmą eksperimentą (LSTM)
        experiment1 = experiment_service.create_experiment(
            name="LSTM eksperimentas",
            creator_id=test_user.id,
            description="LSTM modelio bandymas su BTC duomenimis"
        )
        
        # Nustatome LSTM hiperparametrus
        lstm_hyperparams = {
            "learning_rate": 0.001,
            "batch_size": 64,
            "epochs": 100,
            "optimizer": "adam",
            "layers": 2,
            "hidden_units": 128,
            "dropout": 0.2
        }
        experiment_service.save_hyperparameters(experiment1.id, lstm_hyperparams)
        
        # Pridedame LSTM rezultatus
        lstm_metrics = {
            "train_loss": 0.056,
            "train_accuracy": 0.912,
            "val_loss": 0.089,
            "val_accuracy": 0.873,
            "test_accuracy": 0.865,
            "test_f1_score": 0.842,
            "inference_time_ms": 35.7
        }
        
        for metric_name, metric_value in lstm_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment1.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="test" if metric_name.startswith("test") else "train"
            )
        
        logger.info(f"Sukurtas LSTM eksperimentas su ID: {experiment1.id}")
        
        # Sukuriame antrą eksperimentą (GRU)
        experiment2 = experiment_service.create_experiment(
            name="GRU eksperimentas",
            creator_id=test_user.id,
            description="GRU modelio bandymas su BTC duomenimis"
        )
        
        # Nustatome GRU hiperparametrus (šiek tiek kitokie)
        gru_hyperparams = {
            "learning_rate": 0.001,  # toks pat
            "batch_size": 32,        # mažesnis
            "epochs": 120,           # daugiau
            "optimizer": "adam",     # toks pat
            "layers": 3,             # daugiau
            "hidden_units": 128,     # toks pat
            "dropout": 0.3           # didesnis
        }
        experiment_service.save_hyperparameters(experiment2.id, gru_hyperparams)
        
        # Pridedame GRU rezultatus (šiek tiek geresni)
        gru_metrics = {
            "train_loss": 0.048,        # geresnis
            "train_accuracy": 0.928,    # geresnis
            "val_loss": 0.072,          # geresnis
            "val_accuracy": 0.892,      # geresnis
            "test_accuracy": 0.884,     # geresnis
            "test_f1_score": 0.860,     # geresnis
            "inference_time_ms": 32.1   # greitesnis
        }
        
        for metric_name, metric_value in gru_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment2.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="test" if metric_name.startswith("test") else "train"
            )
        
        logger.info(f"Sukurtas GRU eksperimentas su ID: {experiment2.id}")
        
        # Sukuriame dar vieną eksperimentą panašų į LSTM (panašių eksperimentų radimui)
        experiment3 = experiment_service.create_experiment(
            name="LSTM variantas 2",
            creator_id=test_user.id,
            description="LSTM modelio variantas su šiek tiek kitokiais parametrais"
        )
        
        # Nustatome panašius LSTM hiperparametrus
        lstm_v2_hyperparams = {
            "learning_rate": 0.001,
            "batch_size": 64,
            "epochs": 90,           # šiek tiek mažiau
            "optimizer": "adam",
            "layers": 2,
            "hidden_units": 156,    # šiek tiek daugiau
            "dropout": 0.2
        }
        experiment_service.save_hyperparameters(experiment3.id, lstm_v2_hyperparams)
        
        # Pridedame panašius rezultatus
        lstm_v2_metrics = {
            "train_loss": 0.062,
            "train_accuracy": 0.908,
            "val_loss": 0.092,
            "val_accuracy": 0.870,
            "test_accuracy": 0.862,
            "test_f1_score": 0.839,
            "inference_time_ms": 36.2
        }
        
        for metric_name, metric_value in lstm_v2_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment3.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="test" if metric_name.startswith("test") else "train"
            )
        
        logger.info(f"Sukurtas LSTM variantas 2 eksperimentas su ID: {experiment3.id}")
        
        # DEMO 2: Dviejų eksperimentų palyginimas
        logger.info("\n2. DEMO: Dviejų eksperimentų palyginimas")
        
        # Lyginame LSTM ir GRU eksperimentus
        comparison = experiment_service.compare_experiments(experiment1.id, experiment2.id)
        
        if comparison.get("success", False):
            # Formatuojame palyginimą lentelėje
            table = experiment_service.format_comparison_table(comparison)
            
            logger.info("Eksperimentų palyginimo rezultatai:")
            logger.info("\n" + table)
        else:
            logger.error(f"Nepavyko palyginti eksperimentų: {comparison.get('error', 'Nežinoma klaida')}")
        
        # DEMO 3: Panašių eksperimentų radimas
        logger.info("\n3. DEMO: Panašių eksperimentų radimas")
        
        # Ieškome eksperimentų, panašių į pradinį LSTM
        similar_experiments = experiment_service.find_similar_experiments(
            experiment_id=experiment1.id,
            max_results=3
        )
        
        logger.info(f"Rasta {len(similar_experiments)} eksperimentų, panašių į {experiment1.name}:")
        
        for idx, similar in enumerate(similar_experiments, 1):
            logger.info(f"\n{idx}. {similar['experiment']['name']} (ID: {similar['experiment']['id']})")
            logger.info(f"   Bendras panašumas: {similar['similarity_score']:.2f}")
            logger.info(f"   Hiperparametrų panašumas: {similar['hyperparams_similarity']:.2f}")
            logger.info(f"   Metrikų panašumas: {similar['metrics_similarity']:.2f}")
        
        # Sukuriame ketvirtą eksperimentą su kitokiu modeliu
        experiment4 = experiment_service.create_experiment(
            name="Transformer eksperimentas",
            creator_id=test_user.id,
            description="Transformer modelio bandymas su BTC duomenimis"
        )
        
        # Nustatome visiškai kitokius hiperparametrus
        transformer_hyperparams = {
            "learning_rate": 0.0005,
            "batch_size": 16,
            "epochs": 50,
            "optimizer": "adagrad",
            "num_heads": 8,
            "d_model": 512,
            "num_layers": 4
        }
        experiment_service.save_hyperparameters(experiment4.id, transformer_hyperparams)
        
        # Pridedame kitus rezultatus
        transformer_metrics = {
            "train_loss": 0.035,
            "train_accuracy": 0.945,
            "val_loss": 0.058,
            "val_accuracy": 0.912,
            "test_accuracy": 0.905,
            "test_f1_score": 0.894,
            "inference_time_ms": 45.8
        }
        
        for metric_name, metric_value in transformer_metrics.items():
            experiment_service.add_experiment_result(
                experiment_id=experiment4.id,
                metric_name=metric_name,
                metric_value=metric_value,
                stage="test" if metric_name.startswith("test") else "train"
            )
        
        logger.info(f"Sukurtas Transformer eksperimentas su ID: {experiment4.id}")
        
        # Ieškome eksperimentų, panašių pagal konkrečias metrikas (ne pagal hiperparametrus)
        similar_by_metrics = experiment_service.find_similar_experiments(
            experiment_id=experiment1.id,
            metric_names=["test_accuracy", "test_f1_score"],
            hyperparameter_names=[],  # Ignoruojame hiperparametrus
            max_results=3
        )
        
        logger.info(f"\nRasta {len(similar_by_metrics)} eksperimentų, panašių pagal testavimo tikslumo metrikas:")
        
        for idx, similar in enumerate(similar_by_metrics, 1):
            logger.info(f"\n{idx}. {similar['experiment']['name']} (ID: {similar['experiment']['id']})")
            logger.info(f"   Bendras panašumas: {similar['similarity_score']:.2f}")
            logger.info(f"   Hiperparametrų panašumas: {similar['hyperparams_similarity']:.2f}")
            logger.info(f"   Metrikų panašumas: {similar['metrics_similarity']:.2f}")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()