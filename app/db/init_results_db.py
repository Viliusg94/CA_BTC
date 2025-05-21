import os
import logging
from database.db_utils import init_db, get_engine

# Kelias iki SQL schemos failo
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'results_schema.sql')

def init_results_tables():
    """
    Inicializuoja rezultatų lenteles esamoje duomenų bazėje
    """
    try:
        # Gauname duomenų bazės prisijungimą naudojant esamą mechanizmą
        engine, _ = init_db()
        
        # Nuskaitome schemos failą
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Vykdome SQL užklausas su esamu engine
        with engine.connect() as conn:
            conn.execute(schema_sql)
            
        logging.info("Rezultatų lentelės sėkmingai sukurtos/atnaujintos")
        
    except Exception as e:
        logging.error(f"Klaida inicializuojant rezultatų lenteles: {e}")
        raise