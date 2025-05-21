"""
Šis skriptas patikrina, ar trades lentelėje veikia foreign key į simulations lentelę.
"""
import sys
import os
import logging
import datetime
import uuid
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SQLALCHEMY_DATABASE_URL
from database.models.models import Model
from database.models.results_models import Simulation, Trade

# Konfigūruojame logerį
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_foreign_key():
    """
    Patikrina, ar foreign key constraint veikia trades lentelėje
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    try:
        # Tikriname lentelių struktūrą
        inspector = inspect(engine)
        
        # Gauname trades lentelės informaciją
        foreign_keys = inspector.get_foreign_keys('trades')
        logger.info(f"Trades lentelės foreign keys: {foreign_keys}")
        
        # Gauname stulpelių informaciją
        columns = inspector.get_columns('trades')
        column_info = {col['name']: col for col in columns}
        
        logger.info("Trades lentelės stulpeliai:")
        for name, info in column_info.items():
            logger.info(f"  {name}: type={info['type']}, nullable={info.get('nullable', 'unknown')}")
        
        # Sukuriame testinį modelį ir simuliaciją
        model_id = str(uuid.uuid4())
        model = Model(
            id=model_id,
            name="Test Model for FK check",
            description="Created by check_foreign_key.py",
            type="test"
        )
        
        session.add(model)
        session.flush()
        
        sim_id = str(uuid.uuid4())
        simulation = Simulation(
            id=sim_id,
            name="Test Simulation for FK check",
            model_id=model_id,
            initial_capital=10000,
            start_date=datetime.datetime.now(datetime.timezone.utc),
            end_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
            final_balance=12000,
            profit_loss=2000,
            roi=0.2
        )
        
        session.add(simulation)
        session.flush()
        
        # Sukuriame prekybos sandorį
        now = datetime.datetime.now(datetime.timezone.utc)
        trade = Trade(
            portfolio_id=1,
            trade_type="test_fk",
            btc_amount=0.1,
            timestamp=now,
            simulation_id=sim_id,
            date=now,
            type="buy",
            price=10000.0,
            amount=0.1,
            value=1000.0,
            fee=5.0,
            created_at=now
        )
        
        session.add(trade)
        session.flush()
        
        trade_id = trade.id
        logger.info(f"Sukurtas prekybos sandoris su ID: {trade_id}")
        
        # Ištriname simuliaciją ir patikriname, ar išsitrins ir sandoris
        session.delete(simulation)
        session.flush()
        
        # Bandome gauti sandorį po simuliacijos ištrynimo
        trade_after_delete = session.query(Trade).filter_by(id=trade_id).first()
        
        if trade_after_delete is None:
            logger.info("CASCADE DELETE veikia: sandoris buvo ištrintas kartu su simuliacija")
        else:
            logger.warning("CASCADE DELETE neveikia: sandoris nebuvo ištrintas")
        
        # Tikriname, ar veikia foreign key constraint, bandydami įterpti sandorį su neegzistuojančiu simulation_id
        try:
            bad_trade = Trade(
                portfolio_id=1,
                trade_type="test_bad_fk",
                btc_amount=0.1,
                timestamp=now,
                simulation_id="neegzistuojantis_id",
                date=now,
                type="buy",
                price=10000.0,
                amount=0.1,
                value=1000.0,
                fee=5.0,
                created_at=now
            )
            
            session.add(bad_trade)
            session.flush()
            logger.warning("FOREIGN KEY apribojimas neveikia: pavyko įterpti sandorį su neegzistuojančiu simulation_id")
        except Exception as e:
            logger.info(f"FOREIGN KEY apribojimas veikia: {str(e)}")
        
        # Tikrinama, ar foreign key apribojimas yra įjungtas MySQL
        with engine.connect() as conn:
            result = conn.execute(text("SHOW VARIABLES LIKE 'foreign_key_checks'"))
            for row in result:
                logger.info(f"MySQL foreign_key_checks: {row}")
            
    except Exception as e:
        logger.error(f"Klaida tikrinant foreign key: {str(e)}")
    finally:
        # Atšaukiame visus pakeitimus
        session.rollback()
        session.close()

if __name__ == "__main__":
    check_foreign_key()