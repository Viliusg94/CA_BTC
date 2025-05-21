from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text
from database import SQLALCHEMY_DATABASE_URL

def run_migration():
    """
    Vykdo migraciją - prideda simulation_id stulpelį į trades lentelę
    """
    print("Pradedama migracija: pridedamas simulation_id stulpelis į trades lentelę...")
    
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Patikriname, ar lentelė egzistuoja
    exists = 'trades' in inspector.get_table_names()
    
    if not exists:
        print("Lentelė 'trades' neegzistuoja. Migracija nepavyko.")
        return False
    
    # Patikriname, ar stulpelis jau egzistuoja
    columns = [col['name'] for col in inspector.get_columns('trades')]
    column_exists = 'simulation_id' in columns
    
    if column_exists:
        print("Stulpelis 'simulation_id' jau egzistuoja. Migracija nereikalinga.")
        return True
    
    # Pridedame stulpelį - MySQL sintaksė
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE trades ADD COLUMN simulation_id VARCHAR(50)"))
            conn.execute(text("ALTER TABLE trades ADD INDEX idx_trades_simulation_id (simulation_id)"))
            # Uncomment this if you want to add a foreign key constraint
            # conn.execute(text("ALTER TABLE trades ADD FOREIGN KEY (simulation_id) REFERENCES simulations(id)"))
        print("Stulpelis 'simulation_id' sėkmingai pridėtas į lentelę 'trades'.")
        return True
    except Exception as e:
        print(f"Klaida vykdant migraciją: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration()