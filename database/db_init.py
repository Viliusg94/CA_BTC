# SUKURTI FAILĄ: d:\CA_BTC\database\db_init.py
import os
import pandas as pd
from datetime import datetime
from database.models import BtcPriceData, init_db, Base
from sqlalchemy import text, create_engine, inspect
from sqlalchemy_utils import database_exists, create_database
from database.config import DATABASE_URL, DB_NAME

def create_database():
    """
    Sukuria duomenų bazę, jei ji neegzistuoja.
    Sukuria lenteles pagal ORM modelius.
    """
    # Pirmiausia sukuriame engine objektą tik duomenų bazės sukūrimui
    # Naudojame URL be konkretaus DB pavadinimo, kad galėtume sukurti duomenų bazę
    db_url_without_name = DATABASE_URL.rsplit('/', 1)[0]
    engine = create_engine(db_url_without_name)
    
    try:
        # Patikriname, ar duomenų bazė egzistuoja
        if not database_exists(DATABASE_URL):
            # Sukuriame duomenų bazę
            create_database(DATABASE_URL)
            print(f"Duomenų bazė '{DB_NAME}' sukurta sėkmingai.")
        else:
            print(f"Duomenų bazė '{DB_NAME}' jau egzistuoja.")
        
        # Prisijungiame prie sukurtos duomenų bazės
        engine = create_engine(DATABASE_URL)
        
        # Sukuriame lentelių schemas pagal ORM modelius
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Jei lentelės neegzistuoja, sukuriame jas
        if not all(table in existing_tables for table in ['btc_price_data', 'technical_indicators', 'advanced_features', 'model_predictions']):
            Base.metadata.create_all(engine)
            print("Duomenų bazės lentelės sukurtos sėkmingai.")
        else:
            print("Visos duomenų bazės lentelės jau egzistuoja.")
            
        return True
    
    except Exception as e:
        print(f"Klaida kuriant duomenų bazę: {e}")
        return False

def import_data_from_csv(csv_path, session):
    """
    Importuoja duomenis iš CSV failo į MySQL duomenų bazę
    
    Args:
        csv_path (str): Kelias iki CSV failo
        session: SQLAlchemy sesija
    """
    if not os.path.exists(csv_path):
        print(f"Klaida: Nerastas CSV failas {csv_path}")
        return
        
    print(f"Importuojami duomenys iš {csv_path}...")
    
    # Nuskaitome CSV
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    
    # Patikriname, ar jau yra įrašų duomenų bazėje
    existing_count = session.query(BtcPriceData).count()
    print(f"Duomenų bazėje jau yra {existing_count} įrašai")
    
    # Importuojame kiekvieną eilutę
    rows_inserted = 0
    batch_size = 1000
    batch = []
    
    try:
        for idx, row in df.iterrows():
            # Patikriname, ar jau egzistuoja įrašas su tokiu laiku
            existing = session.query(BtcPriceData).filter_by(timestamp=idx).first()
            
            if existing:
                continue
                
            # Kuriame naują įrašą
            price_data = BtcPriceData(
                timestamp=idx,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume']
            )
            
            batch.append(price_data)
            rows_inserted += 1
            
            # Įtraukiame partijomis, kad būtų efektyviau
            if len(batch) >= batch_size:
                session.add_all(batch)
                session.commit()
                print(f"Importuota {rows_inserted} įrašų...")
                batch = []
        
        # Įtraukiame likusius įrašus
        if batch:
            session.add_all(batch)
            session.commit()
        
        print(f"Importavimas baigtas. Iš viso importuota {rows_inserted} naujų įrašų.")
    
    except Exception as e:
        session.rollback()
        print(f"Klaida importuojant duomenis: {e}")

def main():
    """Pagrindinis duomenų importavimo skriptas"""
    # Sukuriame duomenų bazę, jei jos dar nėra
    create_database()
    
    # Inicializuojame duomenų bazės prisijungimą
    engine, session = init_db()
    
    try:
        # Jei turime esamus CSV, importuojame jų duomenis
        raw_data_path = "data/raw/btc_data.csv"
        if os.path.exists(raw_data_path):
            import_data_from_csv(raw_data_path, session)
        else:
            print("Nerastas CSV failas. Pirmiausia paleiskite duomenų rinkimą.")
    
    finally:
        session.close()

if __name__ == "__main__":
    main()