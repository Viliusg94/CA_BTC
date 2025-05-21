import os
import sys
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Float, DateTime, ForeignKey, text
from database import SQLALCHEMY_DATABASE_URL
import datetime

def run_migration():
    """
    Vykdo migraciją - sukuria simulations lentelę
    """
    print("Pradedama migracija: kuriama simulations lentelę...")
    
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Patikriname, ar lentelė jau egzistuoja
    exists = 'simulations' in inspector.get_table_names()
    
    if exists:
        print("Lentelė 'simulations' jau egzistuoja.")
        # Patikriname stulpelių tipus
        columns = inspector.get_columns('simulations')
        id_column = next((col for col in columns if col['name'] == 'id'), None)
        
        # Jei id stulpelis nėra VARCHAR/String tipo, perkuriame lentelę
        if id_column and 'VARCHAR' not in str(id_column['type']).upper() and 'CHAR' not in str(id_column['type']).upper():
            print(f"Stulpelis 'id' yra {id_column['type']} tipo, bet turėtų būti VARCHAR. Reikalinga atnaujinti lentelę.")
            
            try:
                # Pašaliname seną lentelę ir jos apribojimus
                with engine.begin() as conn:
                    # Pirmiausia pašaliname foreign key constraints
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                    conn.execute(text("DROP TABLE IF EXISTS simulations"))
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                
                # Lentelė buvo ištrinta, dabar sukursime iš naujo su teisingais tipais
                exists = False
            except Exception as e:
                print(f"Klaida šalinant seną simulations lentelę: {str(e)}")
                return False
        else:
            print("Visi stulpeliai yra teisingų tipų.")
    
    # Jei lentelė neegzistuoja arba buvo ištrinta
    if not exists:
        try:
            metadata = MetaData()
            
            # Sukuriame simulations lentelės schema su teisingais duomenų tipais
            simulations = Table(
                'simulations', 
                metadata,
                Column('id', String(50), primary_key=True),
                Column('name', String(100), nullable=True),
                Column('model_id', String(50), ForeignKey('models.id', ondelete="CASCADE"), nullable=True, index=True),
                Column('initial_capital', Float, nullable=False),
                Column('start_date', DateTime, nullable=False),
                Column('end_date', DateTime, nullable=False),
                Column('final_balance', Float, nullable=False),
                Column('profit_loss', Float, nullable=False),
                Column('roi', Float, nullable=False),
                Column('created_at', DateTime, default=datetime.datetime.now(datetime.timezone.utc))
            )
            
            # Sukuriame lentelę
            metadata.create_all(engine)
            
            print("Lentelė 'simulations' sėkmingai sukurta su teisingais duomenų tipais.")
            return True
        except Exception as e:
            print(f"Klaida kuriant lentelę 'simulations': {str(e)}")
            return False
    else:
        print("Lentelė 'simulations' jau egzistuoja ir jos schema teisinga.")
        return True

if __name__ == "__main__":
    # Pridedame projekto katalogą į Python kelią
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    run_migration()