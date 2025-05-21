import logging
import os
import sys

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Reikalingi importai
from database.migrations.create_models_table import run_migration as create_models
from database.migrations.create_simulations_table import run_migration as create_simulations
from database.migrations.create_trades_table import run_migration as create_trades
from database.migrations.create_predictions_table import run_migration as create_predictions
from database.migrations.add_simulation_id_to_trades import run_migration as add_simulation_id
from database.migrations.add_date_to_trades import run_migration as add_date
from database.migrations.add_model_id_to_simulations import run_migration as add_model_id
from database.migrations.add_type_to_trades import run_migration as add_type
from database.migrations.add_amount_to_trades import run_migration as add_amount
from database.migrations.add_price_to_trades import run_migration as add_price
from database.migrations.add_value_to_trades import run_migration as add_value
from database.migrations.add_fee_to_trades import run_migration as add_fee
from database.migrations.add_profit_loss_to_trades import run_migration as add_profit_loss
from database.migrations.create_metrics_table import run_migration as create_metrics
from database.db_utils import init_db

# Konfigūruojame logerį
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migrations():
    """Vykdo duomenų bazės migracijas"""
    logger.info("Pradedamos migracijos...")
    
    # Inicializuojame duomenų bazę
    init_db()
    
    # Vykdome migracijas tinkama tvarka
    success_models = create_models()
    success_simulations = create_simulations()
    success_trades = create_trades()
    success_predictions = create_predictions()
    
    # Kitos migracijos
    success_simulation_id = add_simulation_id()
    success_date = add_date()
    success_model_id = add_model_id()
    success_type = add_type()
    success_amount = add_amount()
    success_price = add_price()
    success_value = add_value()
    success_fee = add_fee()
    success_profit_loss = add_profit_loss()
    success_metrics = create_metrics()
    
    # Tikriname visų migracijų sėkmingumą
    all_success = (
        success_models and
        success_simulations and
        success_trades and
        success_predictions and
        success_simulation_id and 
        success_date and 
        success_model_id and 
        success_type and
        success_amount and
        success_price and
        success_value and
        success_fee and
        success_profit_loss and
        success_metrics
    )
    
    if all_success:
        logger.info("Visos migracijos sėkmingai įvykdytos!")
    else:
        logger.error("Kai kurios migracijos nepavyko! Patikrinkite klaidas aukščiau.")

if __name__ == "__main__":
    # Tikriname, ar galime prisijungti prie duomenų bazės
    from sqlalchemy import create_engine, text
    from database import SQLALCHEMY_DATABASE_URL
    
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Prisijungimas prie duomenų bazės sėkmingas!")
        # Jei prisijungimas sėkmingas, vykdome migracijas
        run_migrations()
    except Exception as e:
        print(f"Klaida jungiantis prie duomenų bazės: {str(e)}")
        print("Paleiskite konfigūracijos vedlį, kad nustatytumėte teisingus duomenų bazės parametrus.")
        
        # Klausiam vartotojo, ar nori konfigūruoti DB
        configure = input("Ar norite dabar konfigūruoti duomenų bazės prisijungimą? (y/n): ")
        if configure.lower() == 'y':
            from database.db_config import configure_database
            configure_database()
            # Bandome dar kartą paleisti migracijas
            print("Bandome dar kartą vykdyti migracijas...")
            run_migrations()
        else:
            print("Migracijos nevykdomos. Paleiskite programą vėliau su teisingais duomenų bazės parametrais.")
            sys.exit(1)