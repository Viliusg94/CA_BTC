"""
Duomenų bazės migracijos skriptas.
Naudojamas duomenų bazės schemos sukūrimui arba atnaujinimui.
"""
import os
import sys
import logging
from datetime import datetime

# Pridedame pagrindinį projekto katalogą į Python kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame duomenų bazės prisijungimo informaciją
from database import SQLALCHEMY_DATABASE_URL
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

# Importuojame modelių klases, kad galėtume sukurti lenteles
from database.models.models import Base as ModelsBase
from database.models.results_models import Base as ResultsBase
from database.models.user_models import Base as UserBase  # Naujas importas

# Konfigūruojame žurnalą
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "migration.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_backup(engine):
    """
    Sukuria esamą duomenų bazės atsarginę kopiją.
    
    Args:
        engine: SQLAlchemy variklis
    
    Returns:
        bool: Ar pavyko sukurti atsarginę kopiją
    """
    try:
        # Gauname duomenų bazės failo kelią iš URL
        db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
        
        # Jei duomenų bazė yra atmintyje, negalime sukurti atsarginės kopijos
        if db_path == '':
            logger.warning("Duomenų bazė yra atmintyje, atsarginė kopija nesukuriama")
            return True
        
        # Tikriname, ar duomenų bazės failas egzistuoja
        if not os.path.exists(db_path):
            logger.warning(f"Duomenų bazės failas neegzistuoja: {db_path}")
            return True
        
        # Sukuriame atsarginės kopijos failo pavadinimą su data
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Kopijuojame failą
        import shutil
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Sukurta atsarginė duomenų bazės kopija: {backup_path}")
        return True
    
    except Exception as e:
        logger.error(f"Klaida kuriant atsarginę kopiją: {str(e)}")
        return False

def check_tables(engine):
    """
    Patikrina, kurios lentelės jau egzistuoja duomenų bazėje.
    
    Args:
        engine: SQLAlchemy variklis
    
    Returns:
        set: Esamų lentelių sąrašas
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    logger.info(f"Rastos egzistuojančios lentelės: {', '.join(existing_tables) if existing_tables else 'nėra'}")
    return existing_tables

def create_tables(engine, existing_tables):
    """
    Sukuria trūkstamas lenteles duomenų bazėje.
    
    Args:
        engine: SQLAlchemy variklis
        existing_tables: Jau egzistuojančių lentelių sąrašas
    
    Returns:
        bool: Ar pavyko sukurti lenteles
    """
    try:
        # Sukuriame visas lenteles, kurių dar nėra
        ModelsBase.metadata.create_all(engine, checkfirst=True)
        ResultsBase.metadata.create_all(engine, checkfirst=True)
        UserBase.metadata.create_all(engine, checkfirst=True)  # Pridėta nauja bazė
        
        # Patikriname, kokios lentelės buvo sukurtos
        new_tables = check_tables(engine) - existing_tables
        
        if new_tables:
            logger.info(f"Sukurtos naujos lentelės: {', '.join(new_tables)}")
        else:
            logger.info("Naujų lentelių sukurti nereikėjo")
        
        return True
    
    except Exception as e:
        logger.error(f"Klaida kuriant lenteles: {str(e)}")
        return False

def add_initial_data(engine):
    """
    Prideda pradinius duomenis į duomenų bazę, jei reikia.
    
    Args:
        engine: SQLAlchemy variklis
    
    Returns:
        bool: Ar pavyko pridėti pradinius duomenis
    """
    try:
        # Sukuriame sesiją
        session = Session(engine)
        
        try:
            # Čia galite pridėti bet kokius pradinius duomenis, jei reikia
            # Pavyzdžiui, pradinius nustatymus ar vartotojus
            
            # Patikriname, ar reikia pridėti pradinius duomenis
            # Šiame pavyzdyje tikriname, ar lentelėje jau yra duomenų
            model_count = session.execute(text("SELECT COUNT(*) FROM models")).scalar()
            
            if model_count == 0:
                logger.info("Pridedami pradiniai duomenys...")
                # Pridėkite pradinius duomenis čia
                # Pavyzdžiui:
                # from database.models.models import Model
                # initial_model = Model(id="default", name="Default Model", ...)
                # session.add(initial_model)
                
                # Išsaugome pakeitimus
                session.commit()
                logger.info("Pradiniai duomenys pridėti sėkmingai")
            else:
                logger.info("Pradinių duomenų pridėti nereikia, duomenų bazėje jau yra duomenų")
            
            return True
        
        except Exception as e:
            # Atšaukiame pakeitimus, jei įvyko klaida
            session.rollback()
            logger.error(f"Klaida pridedant pradinius duomenis: {str(e)}")
            return False
        
        finally:
            # Uždarome sesiją
            session.close()
    
    except Exception as e:
        logger.error(f"Klaida pridedant pradinius duomenis: {str(e)}")
        return False

def run_migration():
    """
    Vykdo duomenų bazės migraciją.
    
    Returns:
        bool: Ar migracija pavyko
    """
    logger.info("Pradedama duomenų bazės migracija")
    
    try:
        # Sukuriame SQLAlchemy variklį
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        logger.info(f"Prisijungta prie duomenų bazės: {SQLALCHEMY_DATABASE_URL}")
        
        # Sukuriame atsarginę kopiją
        if not create_backup(engine):
            logger.error("Nepavyko sukurti atsarginės kopijos, migracija nutraukiama")
            return False
        
        # Tikriname esamas lenteles
        existing_tables = check_tables(engine)
        
        # Sukuriame trūkstamas lenteles
        if not create_tables(engine, existing_tables):
            logger.error("Nepavyko sukurti lentelių, migracija nutraukiama")
            return False
        
        # Pridedame pradinius duomenis
        if not add_initial_data(engine):
            logger.error("Nepavyko pridėti pradinių duomenų, migracija nutraukiama")
            return False
        
        logger.info("Duomenų bazės migracija baigta sėkmingai")
        return True
    
    except Exception as e:
        logger.error(f"Klaida vykdant migraciją: {str(e)}")
        return False

if __name__ == "__main__":
    # Vykdome migraciją, kai skriptas paleidžiamas tiesiogiai
    success = run_migration()
    sys.exit(0 if success else 1)