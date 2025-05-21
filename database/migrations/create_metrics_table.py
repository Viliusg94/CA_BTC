import os
import sys
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Float, DateTime, ForeignKey, Text, JSON, text
from database import SQLALCHEMY_DATABASE_URL
import datetime

def run_migration():
    """
    Vykdo migraciją - sukuria metrics lentelę
    """
    print("Pradedama migracija: kuriama metrics lentelę...")
    
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Patikriname, ar lentelė jau egzistuoja
    exists = 'metrics' in inspector.get_table_names()
    
    if exists:
        print("Lentelė 'metrics' jau egzistuoja.")
        # Patikriname stulpelių tipus
        columns = inspector.get_columns('metrics')
        id_column = next((col for col in columns if col['name'] == 'id'), None)
        
        # Jei id stulpelis nėra VARCHAR/String tipo, perkuriame lentelę
        if id_column and 'VARCHAR' not in str(id_column['type']).upper() and 'CHAR' not in str(id_column['type']).upper():
            print(f"Stulpelis 'id' yra {id_column['type']} tipo, bet turėtų būti VARCHAR. Reikalinga atnaujinti lentelę.")
            
            try:
                # Pašaliname seną lentelę ir jos apribojimus
                with engine.begin() as conn:
                    # Pirmiausia pašaliname foreign key constraints
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                    conn.execute(text("DROP TABLE IF EXISTS metrics"))
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                
                # Lentelė buvo ištrinta, dabar sukursime iš naujo su teisingais tipais
                exists = False
            except Exception as e:
                print(f"Klaida šalinant seną metrics lentelę: {str(e)}")
                return False
        else:
            print("Visi stulpeliai yra teisingų tipų.")
            
            # Tikriname ar yra additional_data stulpelis
            column_names = [col['name'] for col in columns]
            
            # Jei yra metadata, bet nėra additional_data, pervadiname stulpelį
            if 'metadata' in column_names and 'additional_data' not in column_names:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("ALTER TABLE metrics CHANGE COLUMN metadata additional_data JSON"))
                    print("Stulpelis 'metadata' pervadintas į 'additional_data'")
                except Exception as e:
                    print(f"Klaida pervadinant stulpelį: {str(e)}")
            
            # Jei nėra additional_data, pridedame
            if 'additional_data' not in column_names:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("ALTER TABLE metrics ADD COLUMN additional_data JSON"))
                    print("Stulpelis 'additional_data' pridėtas į lentelę 'metrics'")
                except Exception as e:
                    print(f"Klaida pridedant stulpelį: {str(e)}")
    
    # Jei lentelė neegzistuoja arba buvo ištrinta
    if not exists:
        try:
            metadata = MetaData()
            
            # Sukuriame metrics lentelės schema su teisingais duomenų tipais
            metrics = Table(
                'metrics', 
                metadata,
                Column('id', String(50), primary_key=True),
                Column('model_id', String(50), ForeignKey('models.id', ondelete="CASCADE"), nullable=True, index=True),
                Column('simulation_id', String(50), ForeignKey('simulations.id', ondelete="CASCADE"), nullable=True, index=True),
                Column('metric_type', String(50), nullable=False),
                Column('metric_value', Float, nullable=False),
                Column('description', Text, nullable=True),
                Column('additional_data', JSON, nullable=True),  # Pakeista iš metadata į additional_data
                Column('created_at', DateTime, default=datetime.datetime.now(datetime.timezone.utc))
            )
            
            # Sukuriame lentelę
            metadata.create_all(engine)
            
            print("Lentelė 'metrics' sėkmingai sukurta su teisingais duomenų tipais.")
            return True
        except Exception as e:
            print(f"Klaida kuriant lentelę 'metrics': {str(e)}")
            return False
    else:
        print("Lentelė 'metrics' jau egzistuoja ir jos schema teisinga.")
        return True

if __name__ == "__main__":
    # Pridedame projekto katalogą į Python kelią
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    run_migration()