import os
import sys
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Float, DateTime, ForeignKey, text
from database import SQLALCHEMY_DATABASE_URL
import datetime

def run_migration():
    """
    Vykdo migraciją - sukuria trades lentelę su visais reikalingais stulpeliais
    """
    print("Pradedama migracija: kuriama trades lentelė...")
    
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Patikriname, ar lentelė jau egzistuoja
    exists = 'trades' in inspector.get_table_names()
    
    if exists:
        print("Lentelė 'trades' jau egzistuoja.")
        # Patikriname stulpelių tipus
        columns = inspector.get_columns('trades')
        id_column = next((col for col in columns if col['name'] == 'id'), None)
        
        # Jei id stulpelis nėra VARCHAR/String tipo, perkuriame lentelę
        if id_column and 'VARCHAR' not in str(id_column['type']).upper() and 'CHAR' not in str(id_column['type']).upper():
            print(f"Stulpelis 'id' yra {id_column['type']} tipo, bet turėtų būti VARCHAR. Reikalinga atnaujinti lentelę.")
            
            try:
                # Pašaliname seną lentelę ir jos apribojimus
                with engine.begin() as conn:
                    # Pirmiausia pašaliname foreign key constraints
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                    conn.execute(text("DROP TABLE IF EXISTS trades"))
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                
                # Lentelė buvo ištrinta, dabar sukursime iš naujo su teisingais tipais
                exists = False
            except Exception as e:
                print(f"Klaida šalinant seną trades lentelę: {str(e)}")
                return False
        else:
            print("Visi stulpeliai yra teisingų tipų.")
    
    # Jei lentelė neegzistuoja arba buvo ištrinta
    if not exists:
        try:
            metadata = MetaData()
            
            # Sukuriame trades lentelės schema su teisingais duomenų tipais
            trades = Table(
                'trades', 
                metadata,
                Column('id', String(50), primary_key=True),
                Column('simulation_id', String(50), ForeignKey('simulations.id', ondelete="CASCADE"), index=True),
                Column('date', DateTime),
                Column('type', String(10)),
                Column('price', Float),
                Column('amount', Float),
                Column('value', Float),
                Column('fee', Float, default=0.0),
                Column('profit_loss', Float, nullable=True),
                Column('created_at', DateTime, default=datetime.datetime.now(datetime.timezone.utc))
            )
            
            # Sukuriame lentelę
            metadata.create_all(engine)
            
            print("Lentelė 'trades' sėkmingai sukurta su teisingais duomenų tipais.")
            return True
        except Exception as e:
            print(f"Klaida kuriant lentelę 'trades': {str(e)}")
            return False
    else:
        print("Lentelė 'trades' jau egzistuoja ir jos schema teisinga.")
        return True

if __name__ == "__main__":
    # Pridedame projekto katalogą į Python kelią
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    run_migration()