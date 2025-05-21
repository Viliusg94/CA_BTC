import os
import sys
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Float, DateTime, ForeignKey, text
from database import SQLALCHEMY_DATABASE_URL
import datetime

def run_migration():
    """
    Vykdo migraciją - sukuria predictions lentelę
    """
    print("Pradedama migracija: kuriama predictions lentelę...")
    
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Patikriname, ar lentelė jau egzistuoja
    exists = 'predictions' in inspector.get_table_names()
    
    if exists:
        print("Lentelė 'predictions' jau egzistuoja.")
        # Patikriname stulpelių tipus
        columns = inspector.get_columns('predictions')
        id_column = next((col for col in columns if col['name'] == 'id'), None)
        
        # Jei id stulpelis nėra VARCHAR/String tipo, perkuriame lentelę
        if id_column and 'VARCHAR' not in str(id_column['type']).upper() and 'CHAR' not in str(id_column['type']).upper():
            print(f"Stulpelis 'id' yra {id_column['type']} tipo, bet turėtų būti VARCHAR. Reikalinga atnaujinti lentelę.")
            
            try:
                # Pašaliname seną lentelę ir jos apribojimus
                with engine.begin() as conn:
                    # Pirmiausia pašaliname foreign key constraints
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                    conn.execute(text("DROP TABLE IF EXISTS predictions"))
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                
                # Lentelė buvo ištrinta, dabar sukursime iš naujo su teisingais tipais
                exists = False
            except Exception as e:
                print(f"Klaida šalinant seną predictions lentelę: {str(e)}")
                return False
        else:
            print("Visi stulpeliai yra teisingų tipų.")
    
    # Jei lentelė neegzistuoja arba buvo ištrinta
    if not exists:
        try:
            metadata = MetaData()
            
            # Sukuriame predictions lentelės schema su teisingais duomenų tipais
            predictions = Table(
                'predictions', 
                metadata,
                Column('id', String(50), primary_key=True),
                Column('model_id', String(50), ForeignKey('models.id', ondelete="CASCADE"), index=True),
                Column('prediction_date', DateTime, default=datetime.datetime.now(datetime.timezone.utc)),
                Column('target_date', DateTime),
                Column('predicted_value', Float),
                Column('actual_value', Float, nullable=True),
                Column('interval', String(10)),  # 1h, 4h, 1d, 1w
                Column('confidence', Float, nullable=True),
                Column('created_at', DateTime, default=datetime.datetime.now(datetime.timezone.utc))
            )
            
            # Sukuriame lentelę
            metadata.create_all(engine)
            
            print("Lentelė 'predictions' sėkmingai sukurta su teisingais duomenų tipais.")
            return True
        except Exception as e:
            print(f"Klaida kuriant lentelę 'predictions': {str(e)}")
            return False
    else:
        print("Lentelė 'predictions' jau egzistuoja ir jos schema teisinga.")
        return True

if __name__ == "__main__":
    # Pridedame projekto katalogą į Python kelią
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    run_migration()