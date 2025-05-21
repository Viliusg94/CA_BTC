"""
Duomenų bazės įrankiai.
Šis modulis suteikia priemones duomenų bazės inicializavimui.
"""
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from database import SQLALCHEMY_DATABASE_URL

# Konfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sukuriamas bazinis ORM klasės objektas
Base = declarative_base()

# Sukuriama duomenų bazės prisijungimo sesija
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_engine():
    """
    Sukuria ir grąžina SQLAlchemy engine
    
    Returns:
        tuple: (engine, session_maker)
    """
    # Sukuriame SQLAlchemy engine su MySQL duomenų baze
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Sukuriame Session factory
    Session = sessionmaker(bind=engine)
    
    return engine, Session

def get_session():
    """
    Grąžina duomenų bazės sesiją
    
    Yields:
        Session: Duomenų bazės sesija
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """
    Inicializuojame duomenų bazę, sukurdami lenteles tinkama tvarka.
    Ši funkcija užtikrina, kad lentelės būtų sukurtos tokia tvarka, 
    kad užsienio raktai būtų tinkamai sugeneruoti.
    """
    logger.info("Inicializuojama duomenų bazė rankiniu būdu...")
    
    # 1. Sukuriame variklio ir inspektoriaus objektus
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # 2. Tikriname, ar duomenų bazė egzistuoja
    existing_tables = inspector.get_table_names()
    logger.info(f"Egzistuojančios lentelės: {existing_tables}")
    
    # 3. Importuojame visus modelius
    from database.models.user_models import User, UserSession
    from database.models.model_models import Model
    from database.models.metrics_models import UserMetric, ModelMetric, SessionMetric
    from database.models.experiment_models import Experiment, ExperimentResult
    
    # 4. Nustatome lentelių sukūrimo seką
    tables_order = [
        # Pagrindinės lentelės be užsienio raktų
        (User.__table__, "users"),
        (UserSession.__table__, "user_sessions"),
        (Model.__table__, "models"),
        
        # Lentelės su užsienio raktais į pagrindines lenteles
        (UserMetric.__table__, "user_metrics"),
        (ModelMetric.__table__, "model_metrics"),
        (SessionMetric.__table__, "session_metrics"),
        (Experiment.__table__, "experiments"),
        (ExperimentResult.__table__, "experiment_results"),
    ]
    
    # 5. Kuriame lenteles viena po kitos numatyta tvarka
    conn = engine.connect()
    try:
        # Pradedame transakciją
        trans = conn.begin()
        
        for table, name in tables_order:
            if name not in existing_tables:
                logger.info(f"Kuriama lentelė: {name}")
                try:
                    table.create(engine, checkfirst=True)
                    logger.info(f"Lentelė {name} sukurta sėkmingai")
                except Exception as e:
                    logger.error(f"Klaida kuriant lentelę {name}: {e}")
                    raise
            else:
                logger.info(f"Lentelė {name} jau egzistuoja")
        
        # Patvirtinti transakciją
        trans.commit()
        logger.info("Visos lentelės sukurtos sėkmingai")
        
    except Exception as e:
        # Atšaukti transakciją, jei kas nors nepavyko
        trans.rollback()
        logger.error(f"Klaida inicializuojant duomenų bazę: {e}")
        raise
    finally:
        # Uždaryti ryšį
        conn.close()
    
    return True

# Papildyti esamą db_utils.py failą

# Jei trades lentelė sukurta, bet neturi simulation_id stulpelio, reikia ją perkurti
def recreate_trades_table():
    """
    Perkuria trades lentelę, kad turėtų simulation_id stulpelį
    """
    from sqlalchemy import inspect
    from sqlalchemy.sql import text
    from database.models.results_models import Trade, Base
    
    engine = get_engine()
    inspector = inspect(engine)
    
    # Patikriname, ar trades lentelė egzistuoja
    exists = 'trades' in inspector.get_table_names()
    
    if exists:
        # Patikriname, ar stulpelis simulation_id egzistuoja
        columns = [col['name'] for col in inspector.get_columns('trades')]
        column_exists = 'simulation_id' in columns
        
        if not column_exists:
            # Jei lentelė egzistuoja, bet neturi stulpelio simulation_id, išvalome lentelę
            logger.info("Lentelė 'trades' neturi stulpelio 'simulation_id'. Perkuriama lentelė...")
            
            # Pašaliname lentelę
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE trades"))
            
            # Šis veiksmas sukurs lentelę iš naujo pagal ORM apibrėžimą
            Base.metadata.create_all(engine, tables=[Trade.__table__])
            
            logger.info("Lentelė 'trades' sėkmingai perkurta su stulpeliu 'simulation_id'.")