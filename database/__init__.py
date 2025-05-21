"""
Duomenų bazės inicializavimo modulis.
Šis modulis apibrėžia duomenų bazės konfigūraciją ir inicializavimo funkcijas.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Sukuriame žurnalininką
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Duomenų bazės prisijungimo URL
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./ca_btc.db"  # Numatytoji SQLite duomenų bazė, jei nenustatyta aplinkos kintamajame
)

# Inicializuojame duomenų bazės variklį
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Nustatykite True, jei norite matyti SQL užklausas konsolėje
)

# Sukuriame sesijos gamyklą
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sukuriame modulio lygmens kintamuosius
Base = declarative_base()

# Importuojame modelius, kad jie būtų prieinami
from database.models.user_models import User, UserSession
from database.models.model_models import Model
# Importuojame metrikų modelius
from database.models.metrics_models import UserMetric, ModelMetric, SessionMetric
# Importuojame eksperimentų modelius
from database.models.experiment_models import Experiment, ExperimentResult

# Importuojame metrikų lentelių inicializavimo funkciją
from database.setup_metrics_tables import setup_tables as setup_metrics_tables
# Importuojame eksperimentų lentelių inicializavimo funkciją
from database.setup_experiments_tables import setup_tables as setup_experiments_tables

def get_db():
    """
    Gražina duomenų bazės sesiją.
    Naudojama su konteksto valdikliu (with statement).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Inicializuoja duomenų bazę.
    Bandoma naudoti SQLAlchemy, o jei nepavyksta - tiesiogines SQL užklausas.
    """
    logger.info("Inicializuojama duomenų bazė...")
    
    try:
        # Pirma bandome inicializuoti per SQLAlchemy
        from database.db_utils import init_db as sqlalchemy_init
        success = sqlalchemy_init()
        
        if not success:
            raise Exception("SQLAlchemy inicializacija nepavyko")
            
        logger.info("Duomenų bazė inicializuota per SQLAlchemy sėkmingai")
        return True
        
    except Exception as e:
        logger.warning(f"SQLAlchemy inicializacija nepavyko: {e}")
        logger.info("Bandoma inicializuoti duomenų bazę per tiesiogines SQL užklausas...")
        
        # Jei SQLAlchemy nepavyko, naudojame tiesiogines SQL užklausas
        from database.fix_db import create_tables_directly
        success = create_tables_directly()
        
        if success:
            logger.info("Duomenų bazė inicializuota per SQL užklausas sėkmingai")
            return True
        else:
            logger.error("Nepavyko inicializuoti duomenų bazės")
            return False

# Inicializuojame duomenų bazę, kai importuojamas šis modulis
if os.environ.get("INITIALIZE_DB", "True").lower() in ("true", "1", "t"):
    # Tiesiogiai iškviečiame mūsų naują init_db funkciją
    init_db()
else:
    logger.info("Automatinis duomenų bazės inicializavimas išjungtas.")

# Eksportuojame duomenų bazės sesiją
db = scoped_session(SessionLocal)