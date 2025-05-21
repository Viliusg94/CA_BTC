"""
Duomenų bazės įrašų saugaus ištrynimo pavyzdys.
"""
import sys
import os
import logging

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService
from services.simulation_service import SimulationService
from services.trade_service import TradeService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinis pavyzdžio vykdymo metodas.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    try:
        # Inicializuojame servisus
        logger.info("Inicializuojami servisai")
        model_service = ModelService(session)
        simulation_service = SimulationService(session)
        trade_service = TradeService(session)
        
        # 1. SIMULIACIJOS IŠTRYNIMAS
        # =========================
        logger.info("=== SIMULIACIJOS IŠTRYNIMAS ===")
        
        # Gaukime simuliacijų sąrašą
        simulations = simulation_service.list_simulations()
        
        if not simulations:
            logger.info("Nėra simuliacijų duomenų bazėje, kurias būtų galima ištrinti!")
        else:
            # Pasirenkami simuliaciją, kurią ištrinsime
            simulation_to_delete = simulations[0]  # Imame pirmą simuliaciją iš sąrašo
            logger.info(f"Pasirinkta ištrinti simuliacija: {simulation_to_delete.name} ({simulation_to_delete.id})")
            
            # Prieš ištrinant, patikrinkime susijusius sandorius
            related_trades = simulation_service.get_simulation_trades(simulation_to_delete.id)
            logger.info(f"Simuliacija turi {len(related_trades)} susijusius sandorius, kurie taip pat bus ištrinti")
            
            # Ištrinkime simuliaciją naudodami servisą (kuris naudoja saugų trynimo metodą)
            deletion_result = simulation_service.delete_simulation(simulation_to_delete.id)
            
            if deletion_result:
                logger.info(f"Simuliacija {simulation_to_delete.id} sėkmingai ištrinta!")
                
                # Patikrinkime, ar neliko susijusių sandorių
                remaining_trades = trade_service.list_trades(simulation_id=simulation_to_delete.id)
                if not remaining_trades:
                    logger.info("Visi susiję sandoriai taip pat ištrinti (kaskadinis trynimas veikia)")
                else:
                    logger.warning(f"ĮSPĖJIMAS: Vis dar yra {len(remaining_trades)} susijusių sandorių!")
            else:
                logger.error(f"Nepavyko ištrinti simuliacijos {simulation_to_delete.id}")
        
        # 2. MODELIO IŠTRYNIMAS
        # ====================
        logger.info("=== MODELIO IŠTRYNIMAS ===")
        
        # Gaukime modelių sąrašą
        models = model_service.list_models()
        
        if not models:
            logger.info("Nėra modelių duomenų bazėje, kuriuos būtų galima ištrinti!")
        else:
            # Pasirenkame modelį, kurį ištrinsime
            model_to_delete = models[0]  # Imame pirmą modelį iš sąrašo
            logger.info(f"Pasirinktas ištrinti modelis: {model_to_delete.name} ({model_to_delete.id})")
            
            # Prieš ištrinant, patikrinkime susijusias simuliacijas
            related_simulations = simulation_service.list_simulations(model_id=model_to_delete.id)
            logger.info(f"Modelis turi {len(related_simulations)} susijusias simuliacijas, kurios taip pat bus ištrintos")
            
            # Ištrinkime modelį naudodami servisą
            deletion_result = model_service.delete_model(model_to_delete.id)
            
            if deletion_result:
                logger.info(f"Modelis {model_to_delete.id} sėkmingai ištrintas!")
                
                # Patikrinkime, ar neliko susijusių simuliacijų
                remaining_simulations = simulation_service.list_simulations(model_id=model_to_delete.id)
                if not remaining_simulations:
                    logger.info("Visos susijusios simuliacijos taip pat ištrintos (kaskadinis trynimas veikia)")
                else:
                    logger.warning(f"ĮSPĖJIMAS: Vis dar yra {len(remaining_simulations)} susijusių simuliacijų!")
            else:
                logger.error(f"Nepavyko ištrinti modelio {model_to_delete.id}")
        
        # 3. TIESIOGINIS SANDORIO IŠTRYNIMAS
        # =================================
        logger.info("=== SANDORIO IŠTRYNIMAS ===")
        
        # Gaukime sandorių sąrašą
        trades = trade_service.list_trades()
        
        if not trades:
            logger.info("Nėra sandorių duomenų bazėje, kuriuos būtų galima ištrinti!")
        else:
            # Pasirenkame sandorį, kurį ištrinsime
            trade_to_delete = trades[0]  # Imame pirmą sandorį iš sąrašo
            logger.info(f"Pasirinktas ištrinti sandoris: ID = {trade_to_delete.id}, Tipas = {trade_to_delete.type}, Kaina = {trade_to_delete.price} USD")
            
            # Ištrinkime sandorį naudodami servisą
            deletion_result = trade_service.delete_trade(trade_to_delete.id)
            
            if deletion_result:
                logger.info(f"Sandoris {trade_to_delete.id} sėkmingai ištrintas!")
                
                # Patikrinkime, ar sandoris tikrai ištrintas
                if not trade_service.get_trade(trade_to_delete.id):
                    logger.info("Patvirtinta: sandoris ištrintas iš duomenų bazės")
                else:
                    logger.warning("ĮSPĖJIMAS: Sandoris vis dar egzistuoja duomenų bazėje!")
            else:
                logger.error(f"Nepavyko ištrinti sandorio {trade_to_delete.id}")
        
    except Exception as e:
        logger.error(f"Įvyko klaida vykdant pavyzdį: {str(e)}")
    finally:
        # Uždarome sesiją kai baigėme
        logger.info("Uždaroma duomenų bazės sesija")
        session.close()

if __name__ == "__main__":
    main()