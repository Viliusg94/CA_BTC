"""
Pavyzdinis skriptas, parodantis kaip naudoti metrikų eksportavimo ir vizualizacijos funkcijas.
"""
import os
import sys
import logging
import json
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
from services.metrics_service import MetricsService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti metrikų eksportavimo ir vizualizacijos funkcijas.
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
        metrics_service = MetricsService(db)

        # Tikriname, ar yra testinis naudotojas
        logger.info("Tikriname, ar yra testinis naudotojas...")
        test_user = user_service.get_user_by_username("test_user")
        if not test_user:
            logger.warning("Testinis naudotojas nerastas. Prašome pirmiausia paleisti metrics_calculation_example.py")
            return
        
        # Tikriname, ar yra testinis modelis
        logger.info("Tikriname, ar yra testinis modelis...")
        test_models = model_service.get_models()
        if not test_models:
            logger.warning("Testinis modelis nerastas. Prašome pirmiausia paleisti metrics_calculation_example.py")
            return
        test_model = test_models[0]
        
        # DEMO 1: Metrikų eksportavimas į CSV
        logger.info("1. DEMO: Metrikų eksportavimas į CSV")
        
        # Sukuriame eksportų direktoriją
        export_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        # Eksportuojame naudotojo metrikas į CSV
        user_csv_path = os.path.join(export_dir, f"user_metrics_{test_user.id}.csv")
        exported_user_csv = metrics_service.export_user_metrics(
            user_id=test_user.id,
            format="csv",
            output_path=user_csv_path
        )
        
        if exported_user_csv:
            logger.info(f"Naudotojo metrikos eksportuotos į CSV: {exported_user_csv}")
        
        # Eksportuojame modelio metrikas į CSV
        model_csv_path = os.path.join(export_dir, f"model_metrics_{test_model.id}.csv")
        exported_model_csv = metrics_service.export_model_metrics(
            model_id=test_model.id,
            format="csv",
            output_path=model_csv_path
        )
        
        if exported_model_csv:
            logger.info(f"Modelio metrikos eksportuotos į CSV: {exported_model_csv}")
        
        # DEMO 2: Metrikų eksportavimas į JSON
        logger.info("\n2. DEMO: Metrikų eksportavimas į JSON")
        
        # Gauname naudotojo metrikas
        user_metrics = metrics_service.get_user_metrics(
            user_id=test_user.id,
            metric_type="usage"
        )
        
        # Eksportuojame į JSON
        user_json_path = os.path.join(export_dir, f"user_metrics_{test_user.id}.json")
        exported_user_json = metrics_service.export_metrics_to_json(
            metrics=user_metrics,
            output_path=user_json_path
        )
        
        if exported_user_json:
            logger.info(f"Naudotojo metrikos eksportuotos į JSON: {exported_user_json}")
        
        # DEMO 3: Metrikų eksportavimas į Excel
        logger.info("\n3. DEMO: Metrikų eksportavimas į Excel")
        
        # Gauname modelio metrikas
        model_metrics = metrics_service.get_model_metrics(
            model_id=test_model.id
        )
        
        # Eksportuojame į Excel
        model_excel_path = os.path.join(export_dir, f"model_metrics_{test_model.id}.xlsx")
        exported_model_excel = metrics_service.export_metrics_to_excel(
            metrics=model_metrics,
            output_path=model_excel_path
        )
        
        if exported_model_excel:
            logger.info(f"Modelio metrikos eksportuotos į Excel: {exported_model_excel}")
        
        # DEMO 4: Duomenų paruošimas laiko eilutės vizualizacijai
        logger.info("\n4. DEMO: Duomenų paruošimas laiko eilutės vizualizacijai")
        
        # Nustatome laiko intervalą
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        
        # Paruošiame duomenis laiko eilutės vizualizacijai
        time_series_data = metrics_service.prepare_visualization_data(
            data_type="time_series",
            user_id=test_user.id,
            metric_name="login_count",
            start_date=start_date,
            end_date=end_date,
            period="weekly"
        )
        
        # Rodome paruoštus duomenis
        logger.info("Laiko eilutės vizualizacijos duomenys:")
        logger.info(f"Statusas: {time_series_data.get('status')}")
        logger.info(f"Antraštė: {time_series_data.get('title')}")
        logger.info(f"Etikečių skaičius: {len(time_series_data.get('labels', []))}")
        logger.info(f"Reikšmių skaičius: {len(time_series_data.get('values', []))}")
        
        # Eksportuojame vizualizacijos duomenis į JSON
        viz_json_path = os.path.join(export_dir, "time_series_visualization_data.json")
        with open(viz_json_path, 'w', encoding='utf-8') as f:
            json.dump(time_series_data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Laiko eilutės vizualizacijos duomenys išsaugoti: {viz_json_path}")
        
        # DEMO 5: Duomenų paruošimas modelių palyginimui
        logger.info("\n5. DEMO: Duomenų paruošimas modelių palyginimui")
        
        # Sukuriame dar vieną modelį palyginimui
        second_model = model_service.create_model(
            name="RNN Test Model",
            type="rnn",
            description="Testinis RNN modelis palyginimui",
            creator_id=test_user.id
        )
        
        # Pridedame metrikas antram modeliui
        predictions = [random.uniform(100, 150) for _ in range(20)]
        actual_values = [p + random.uniform(-15, 15) for p in predictions]  # Pridedame didesnį triukšmą
        
        metrics_service.calculate_and_save_model_metrics(
            second_model.id, "test_dataset", predictions, actual_values, test_user.id
        )
        
        # Paruošiame duomenis modelių palyginimo vizualizacijai
        comparison_data = metrics_service.prepare_visualization_data(
            data_type="comparison",
            model_ids=[test_model.id, second_model.id],
            metric_name="rmse",
            dataset_name="test_dataset"
        )
        
        # Rodome paruoštus duomenis
        logger.info("Modelių palyginimo vizualizacijos duomenys:")
        logger.info(f"Statusas: {comparison_data.get('status')}")
        logger.info(f"Antraštė: {comparison_data.get('title')}")
        logger.info(f"Modeliai: {comparison_data.get('labels')}")
        logger.info(f"RMSE reikšmės: {comparison_data.get('values')}")
        
        # Eksportuojame vizualizacijos duomenis į JSON
        viz_json_path = os.path.join(export_dir, "models_comparison_visualization_data.json")
        with open(viz_json_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Modelių palyginimo vizualizacijos duomenys išsaugoti: {viz_json_path}")
        
        # DEMO 6: Duomenų paruošimas pasiskirstymo vizualizacijai
        logger.info("\n6. DEMO: Duomenų paruošimas pasiskirstymo vizualizacijai")
        
        # Paruošiame duomenis pasiskirstymo vizualizacijai
        distribution_data = metrics_service.prepare_visualization_data(
            data_type="distribution",
            user_id=test_user.id,
            metric_name="login_count",
            start_date=start_date,
            end_date=end_date
        )
        
        # Rodome paruoštus duomenis
        logger.info("Pasiskirstymo vizualizacijos duomenys:")
        logger.info(f"Statusas: {distribution_data.get('status')}")
        logger.info(f"Antraštė: {distribution_data.get('title')}")
        logger.info(f"Reikšmių skaičius: {distribution_data.get('count')}")
        logger.info(f"Min reikšmė: {distribution_data.get('min')}")
        logger.info(f"Max reikšmė: {distribution_data.get('max')}")
        logger.info(f"Vidurkis: {distribution_data.get('avg')}")
        logger.info(f"Mediana: {distribution_data.get('median')}")
        
        # Eksportuojame vizualizacijos duomenis į JSON
        viz_json_path = os.path.join(export_dir, "distribution_visualization_data.json")
        with open(viz_json_path, 'w', encoding='utf-8') as f:
            json.dump(distribution_data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Pasiskirstymo vizualizacijos duomenys išsaugoti: {viz_json_path}")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("\nPavyzdžio vykdymas baigtas sėkmingai.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()