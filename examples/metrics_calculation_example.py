"""
Pavyzdinis skriptas, parodantis kaip naudoti metrikų skaičiavimo ir analizės funkcijas.
"""
import os
import sys
import logging
import json
import time
import random
from datetime import datetime, timedelta, timezone

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from database.setup_metrics_tables import setup_tables
from services.user_service import UserService
from services.model_service import ModelService
from services.session_manager_service import SessionManagerService
from services.metrics_service import MetricsService
from services.metrics_calculator import MetricsCalculator

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti metrikų skaičiavimo ir analizės funkcijas.
    """
    try:
        # Sukuriame duomenų bazės ryšį
        logger.info("Jungiamasi prie duomenų bazės...")
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        db = Session(engine)

        # Inicializuojame metrikų lenteles
        logger.info("Inicializuojame metrikų lenteles...")
        setup_tables()

        # Inicializuojame reikalingus servisus
        logger.info("Inicializuojame servisus...")
        user_service = UserService(db)
        model_service = ModelService(db)
        session_manager = SessionManagerService(db)
        metrics_service = MetricsService(db)
        metrics_calculator = MetricsCalculator(db)

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
        
        # DEMO: Sukuriame modelį jei nėra
        logger.info("Tikriname, ar yra testinis modelis...")
        test_models = model_service.get_models()
        if not test_models:
            logger.info("Kuriame testinį modelį...")
            test_model = model_service.create_model(
                name="LSTM Test Model",
                type="lstm",
                description="Testinis LSTM modelis metrikų demonstracijai",
                creator_id=test_user.id
            )
            logger.info(f"Sukurtas testinis modelis su ID: {test_model.id}")
        else:
            test_model = test_models[0]
        
        # DEMO 1: Sesijų metrikų skaičiavimas
        logger.info("1. DEMO: Sesijų metrikų skaičiavimas")
        
        # Sukuriame testavimo sesiją
        test_session = session_manager.create_session(
            user_id=test_user.id,
            session_type="testing",
            ip_address="127.0.0.1"
        )
        logger.info(f"Sukurta testavimo sesija su ID: {test_session.id}")
        
        # Imituojame sesijos veikimą
        time.sleep(2)  # Laukiame 2 sekundes
        
        # Baigiame sesiją
        session_manager.end_session(test_session.id, "completed")
        logger.info(f"Testavimo sesija baigta")
        
        # Apskaičiuojame ir išsaugome sesijos metrikas
        session_metrics = metrics_service.calculate_and_save_session_metrics(test_session.id)
        logger.info(f"Apskaičiuotos ir išsaugotos {len(session_metrics)} sesijos metrikos")
        
        # Gauname išsaugotas sesijos metrikas
        saved_metrics = metrics_service.get_session_metrics(test_session.id)
        logger.info("Išsaugotos sesijos metrikos:")
        for metric in saved_metrics:
            if metric.numeric_value:
                logger.info(f"- {metric.metric_name}: {metric.numeric_value}")
            else:
                logger.info(f"- {metric.metric_name}: {metric.string_value}")
        
        # DEMO 2: Naudotojo metrikų skaičiavimas ir agregavimas
        logger.info("\n2. DEMO: Naudotojo metrikų skaičiavimas ir agregavimas")
        
        # Sukuriame keletą naudotojo metrikų
        for i in range(30):
            # Sukuriame metrikos datą (paskutinės 30 dienų)
            metric_date = datetime.now(timezone.utc) - timedelta(days=i)
            
            # Pridedame login_count metriką
            metrics_service.create_user_metric(
                user_id=test_user.id,
                metric_type="usage",
                metric_name="login_count",
                numeric_value=random.randint(1, 5),  # Atsitiktinis prisijungimų skaičius
                time_period="daily",
                metadata={"date": metric_date.strftime("%Y-%m-%d")}
            )
        
        logger.info("Sukurtos 30 login_count metrikų testiniam naudotojui")
        
        # Agreguojame metrikas pagal savaitę
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        aggregated_metrics = metrics_service.get_aggregated_metrics(
            test_user.id, "login_count", start_date, end_date, "weekly"
        )
        
        logger.info("Agreguotos savaitinės login_count metrikos:")
        for metric in aggregated_metrics:
            logger.info(f"- Savaitė pradedant {metric['period']}: vidutiniškai {metric['average_value']:.2f} prisijungimų ({metric['count']} įrašai)")
        
        # DEMO 3: Metrikų tendencijų analizė
        logger.info("\n3. DEMO: Metrikų tendencijų analizė")
        
        # Analizuojame login_count tendencijas
        trends = metrics_service.get_metric_trends(test_user.id, "login_count", 30)
        
        logger.info("Login_count metrikos tendencijos:")
        logger.info(f"- Dabartinio laikotarpio vidurkis: {trends['current_period_avg']:.2f}")
        logger.info(f"- Ankstesnio laikotarpio vidurkis: {trends['past_period_avg']:.2f}")
        logger.info(f"- Pokytis: {trends['absolute_change']:.2f} ({trends['percent_change']:.2f}%)")
        logger.info(f"- Tendencija: {trends['trend']}")
        
        # DEMO 4: Modelio metrikų skaičiavimas
        logger.info("\n4. DEMO: Modelio metrikų skaičiavimas")
        
        # Generuojame atsitiktines prognozes ir faktinius rezultatus
        predictions = [random.uniform(100, 150) for _ in range(20)]
        actual_values = [p + random.uniform(-10, 10) for p in predictions]  # Pridedame atsitiktinį triukšmą
        
        # Apskaičiuojame ir išsaugome modelio metrikas
        model_metrics = metrics_service.calculate_and_save_model_metrics(
            test_model.id, "test_dataset", predictions, actual_values, test_user.id
        )
        
        logger.info(f"Apskaičiuotos ir išsaugotos {len(model_metrics)} modelio metrikos")
        
        # Gauname išsaugotas modelio metrikas
        saved_model_metrics = metrics_service.get_model_metrics(test_model.id)
        logger.info("Išsaugotos modelio metrikos:")
        for metric in saved_model_metrics:
            logger.info(f"- {metric.metric_name}: {metric.value}")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("Pavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()