"""
Eksperimentų lentelių sukūrimo skriptas.
Šis modulis naudojamas inicializuoti eksperimentų lenteles duomenų bazėje.
"""
import os
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

# Importuojame duomenų bazės konfigūraciją
from database import SQLALCHEMY_DATABASE_URL
from database.models.experiment_models import Experiment, ExperimentResult
from database.models.base import Base

# Sukuriame žurnalininką
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_tables():
    """
    Inicializuoja eksperimentų lenteles duomenų bazėje.
    Funkcija patikrina, ar lentelės jau egzistuoja, ir sukuria tik tas, kurių nėra.
    Ši funkcija yra saugi vykdyti pakartotinai.
    """
    try:
        # Sukuriame ryšį su duomenų baze
        logger.info("Jungiamasi prie duomenų bazės...")
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        # Tikriname, ar lentelės jau egzistuoja
        logger.info("Tikriname egzistuojančias lenteles...")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Sukuriame lenteles, kurių dar nėra
        tables_to_create = []
        
        if "experiments" not in existing_tables:
            logger.info("Sukuriama eksperimentų lentelė...")
            tables_to_create.append(Experiment.__table__)
        else:
            logger.info("Eksperimentų lentelė jau egzistuoja")
            
        if "experiment_results" not in existing_tables:
            logger.info("Sukuriama eksperimentų rezultatų lentelė...")
            tables_to_create.append(ExperimentResult.__table__)
        else:
            logger.info("Eksperimentų rezultatų lentelė jau egzistuoja")
            
        # Sukuriame lenteles, jei yra ką sukurti
        if tables_to_create:
            Base.metadata.create_all(engine, tables=tables_to_create)
            logger.info("Lentelės sukurtos sėkmingai")
        
        logger.info("Eksperimentų lentelių inicializavimas baigtas sėkmingai")
        
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy klaida inicializuojant lenteles: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Nenumatyta klaida inicializuojant lenteles: {str(e)}")
        raise

if __name__ == "__main__":
    """
    Jei šis skriptas paleidžiamas tiesiogiai, inicializuojamos lentelės.
    """
    setup_tables()