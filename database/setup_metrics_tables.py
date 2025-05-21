"""
Metrikų lentelių sukūrimo skriptas.
Šis modulis naudojamas inicializuoti metrikų lenteles duomenų bazėje.
"""
import logging
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.exc import SQLAlchemyError

# Importuojame duomenų bazės konfigūraciją
from database import SQLALCHEMY_DATABASE_URL
from database.models.metrics_models import UserMetric, ModelMetric, SessionMetric
from database.models.base import Base

# Sukuriame žurnalininką
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_tables():
    """
    Inicializuoja metrikų lenteles duomenų bazėje.
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
        
        # Metrikų lentelių sąrašas, kurias norime sukurti
        metrics_tables = [
            {"name": "user_metrics", "class": UserMetric},
            {"name": "model_metrics", "class": ModelMetric},
            {"name": "session_metrics", "class": SessionMetric}
        ]
        
        # Patikriname kiekvieną lentelę ir sukuriame, jei jos dar nėra
        tables_created = 0
        for table_info in metrics_tables:
            table_name = table_info["name"]
            if table_name not in existing_tables:
                logger.info(f"Kuriama lentelė: {table_name}")
                # Sukuriame lentelę naudodami SQLAlchemy modelį
                table_info["class"].__table__.create(engine)
                tables_created += 1
                logger.info(f"Lentelė {table_name} sėkmingai sukurta")
            else:
                logger.info(f"Lentelė {table_name} jau egzistuoja, praleidžiama")
        
        # Informuojame apie sukurtų lentelių skaičių
        if tables_created > 0:
            logger.info(f"Sukurtos {tables_created} naujos metrikų lentelės")
        else:
            logger.info("Visos metrikų lentelės jau egzistuoja")
        
        # Sukuriame indeksus, jei jų dar nėra
        # Pastaba: SQLAlchemy modeliuose apibrėžti indeksai sukuriami automatiškai kartu su lentelėmis
        logger.info("Metrikų lentelių inicializavimas baigtas sėkmingai")
        
        return True
        
    except SQLAlchemyError as e:
        # Gaudome ir registruojame duomenų bazės klaidas
        logger.error(f"Duomenų bazės klaida kuriant metrikų lenteles: {str(e)}")
        return False
    except Exception as e:
        # Gaudome visas kitas klaidas
        logger.error(f"Nenumatyta klaida kuriant metrikų lenteles: {str(e)}")
        return False

def setup_metrics_tables_for_existing_database():
    """
    Papildoma funkcija, kuri sukuria metrikų lenteles egzistuojančioje duomenų bazėje.
    Naudinga, kai duomenų bazė jau turi kitas lenteles, bet mes norime pridėti metrikų lenteles.
    """
    return setup_tables()

# Jei šis skriptas paleidžiamas tiesiogiai
if __name__ == "__main__":
    logger.info("Paleidžiamas metrikų lentelių inicializavimo skriptas")
    if setup_tables():
        logger.info("Metrikų lentelės sėkmingai inicializuotos")
    else:
        logger.error("Nepavyko inicializuoti metrikų lentelių")