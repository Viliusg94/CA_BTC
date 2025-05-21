"""
Pagalbinės funkcijos darbui su duomenų baze
"""
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def safe_delete_simulation(session: Session, simulation_id: str) -> bool:
    """
    Saugiai ištrina simuliaciją ir visus susijusius įrašus.
    Naudoja tiesioginius SQL užklausas, kad išvengtų ORM ryšių problemų.
    
    Args:
        session: SQLAlchemy sesija
        simulation_id: Simuliacijos ID, kurią norima ištrinti
        
    Returns:
        bool: True, jei ištrynimas sėkmingas, False priešingu atveju
    """
    try:
        # Sukuriame naują veiksmą, kad galėtume anuliuoti jį nesėkmės atveju
        connection = session.connection()
        
        # Pirmiausia ištriname susijusius sandorius
        result = connection.execute(
            text(f"DELETE FROM trades WHERE simulation_id = :sim_id"),
            {"sim_id": simulation_id}
        )
        deleted_trades = result.rowcount
        logger.info(f"Ištrinta {deleted_trades} susijusių sandorių")
        
        # Tada ištriname pačią simuliaciją
        result = connection.execute(
            text(f"DELETE FROM simulations WHERE id = :sim_id"),
            {"sim_id": simulation_id}
        )
        deleted_sims = result.rowcount
        logger.info(f"Ištrinta {deleted_sims} simuliacijų")
        
        # Įsipareigojame pakeitimus
        session.commit()
        return True
    except Exception as e:
        # Anuliuojame pakeitimus klaidos atveju
        session.rollback()
        logger.error(f"Klaida trinant simuliaciją {simulation_id}: {str(e)}")
        return False