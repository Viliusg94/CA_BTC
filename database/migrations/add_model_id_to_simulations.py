from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text
from database import SQLALCHEMY_DATABASE_URL

def run_migration():
    """
    Vykdo migraciją - prideda model_id stulpelį į simulations lentelę
    """
    print("Pradedama migracija: pridedamas model_id stulpelis į simulations lentelę...")
    
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Patikriname, ar lentelė egzistuoja
    exists = 'simulations' in inspector.get_table_names()
    
    if not exists:
        print("Lentelė 'simulations' neegzistuoja. Migracija nepavyko.")
        return False
    
    # Patikriname, ar stulpelis jau egzistuoja
    columns = [col['name'] for col in inspector.get_columns('simulations')]
    column_exists = 'model_id' in columns
    
    if column_exists:
        print("Stulpelis 'model_id' jau egzistuoja. Migracija nereikalinga.")
        return True
    
    # Pridedame stulpelį - MySQL sintaksė
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE simulations ADD COLUMN model_id VARCHAR(50)"))
            conn.execute(text("ALTER TABLE simulations ADD INDEX idx_simulations_model_id (model_id)"))
        print("Stulpelis 'model_id' sėkmingai pridėtas į lentelę 'simulations'.")
        return True
    except Exception as e:
        print(f"Klaida vykdant migraciją: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration()