import os
import sys
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Float, DateTime, JSON, Text, text
from database import SQLALCHEMY_DATABASE_URL
import datetime

def run_migration():
    """
    Vykdo migraciją - sukuria models lentelę
    """
    print("Pradedama migracija: kuriama models lentelė...")
    
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Patikriname, ar lentelė jau egzistuoja
    exists = 'models' in inspector.get_table_names()
    
    if exists:
        print("Lentelė 'models' jau egzistuoja.")
        # Patikriname stulpelių tipus
        columns = inspector.get_columns('models')
        id_column = next((col for col in columns if col['name'] == 'id'), None)
        
        # Jei id stulpelis nėra VARCHAR/String tipo, perkuriame lentelę
        if id_column and 'VARCHAR' not in str(id_column['type']).upper() and 'CHAR' not in str(id_column['type']).upper():
            print(f"Stulpelis 'id' yra {id_column['type']} tipo, bet turėtų būti VARCHAR. Reikalinga atnaujinti lentelę.")
            
            try:
                # Pašaliname seną lentelę ir jos apribojimus
                with engine.begin() as conn:
                    # Pirmiausia pašaliname foreign key constraints
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                    conn.execute(text("DROP TABLE IF EXISTS models"))
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                
                # Lentelė buvo ištrinta, dabar sukursime iš naujo su teisingais tipais
                exists = False
            except Exception as e:
                print(f"Klaida šalinant seną models lentelę: {str(e)}")
                return False
        else:
            print("Visi stulpeliai yra teisingų tipų.")
            
            # Patikrinam, ar performance_metrics stulpelis egzistuoja
            column_names = [col['name'] for col in columns]
            
            # Jei yra metrics, bet nėra performance_metrics, pervadiname stulpelį
            if 'metrics' in column_names and 'performance_metrics' not in column_names:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("ALTER TABLE models CHANGE COLUMN metrics performance_metrics JSON"))
                    print("Stulpelis 'metrics' pervadintas į 'performance_metrics'")
                except Exception as e:
                    print(f"Klaida pervadinant stulpelį: {str(e)}")
            
            # Jei nėra performance_metrics, pridedame
            if 'performance_metrics' not in column_names:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("ALTER TABLE models ADD COLUMN performance_metrics JSON"))
                    print("Stulpelis 'performance_metrics' pridėtas į lentelę 'models'")
                except Exception as e:
                    print(f"Klaida pridedant stulpelį: {str(e)}")
    
    # Jei lentelė neegzistuoja arba buvo ištrinta
    if not exists:
        try:
            metadata = MetaData()
            
            # Sukuriame models lentelės schema su teisingais duomenų tipais
            models = Table(
                'models', 
                metadata,
                Column('id', String(50), primary_key=True),
                Column('name', String(100), nullable=False),
                Column('description', Text, nullable=True),
                Column('type', String(50), nullable=True),
                Column('hyperparameters', JSON, nullable=True),
                Column('input_features', JSON, nullable=True),
                Column('performance_metrics', JSON, nullable=True),  # Pakeista iš metrics į performance_metrics
                Column('created_at', DateTime, default=datetime.datetime.now(datetime.timezone.utc))
            )
            
            # Sukuriame lentelę
            metadata.create_all(engine)
            
            print("Lentelė 'models' sėkmingai sukurta su teisingais duomenų tipais.")
            return True
        except Exception as e:
            print(f"Klaida kuriant lentelę 'models': {str(e)}")
            return False
    else:
        print("Lentelė 'models' jau egzistuoja ir jos schema teisinga.")
        return True

if __name__ == "__main__":
    # Pridedame projekto katalogą į Python kelią
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    run_migration()