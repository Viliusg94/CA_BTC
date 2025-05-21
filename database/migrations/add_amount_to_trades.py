from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text
from database import SQLALCHEMY_DATABASE_URL

def run_migration():
    """
    Vykdo migraciją - prideda amount stulpelį į trades lentelę
    """
    print("Pradedama migracija: pridedamas amount stulpelis į trades lentelę...")
    
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
    column_exists = 'amount' in columns
    
    if column_exists:
        print("Stulpelis 'amount' jau egzistuoja. Migracija nereikalinga.")
        return True
    
    # Pridedame stulpelį - MySQL sintaksė
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE trades ADD COLUMN amount FLOAT"))
        print("Stulpelis 'amount' sėkmingai pridėtas į lentelę 'trades'.")
        return True
    except Exception as e:
        print(f"Klaida vykdant migraciją: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration()