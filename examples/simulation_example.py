"""
Simuliacijos sukūrimo ir valdymo pavyzdys.
"""
import uuid
import sys
import os
import logging
from datetime import datetime, timezone, timedelta

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService
from services.simulation_service import SimulationService

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
        
        # Pirma turime rasti modelį, kurį naudosime simuliacijai
        logger.info("Ieškomas modelis simuliacijai")
        models = model_service.list_models(limit=1)
        
        if not models:
            logger.error("Nėra modelių duomenų bazėje! Pirmiausia sukurkite modelį.")
            return
        
        selected_model = models[0]
        logger.info(f"Naudojamas modelis: {selected_model.name} ({selected_model.id})")
        
        # Sugeneruojame unikalų ID simuliacijai
        simulation_id = str(uuid.uuid4())
        logger.info(f"Sugeneruotas simuliacijos ID: {simulation_id}")
        
        # Nustatome simuliacijos laiko rėžius
        start_date = datetime.now(timezone.utc) - timedelta(days=30)  # Prieš 30 dienų
        end_date = datetime.now(timezone.utc)  # Dabar
        
        # Sukuriame simuliacijos duomenis
        logger.info("Ruošiami simuliacijos duomenys")
        simulation_data = {
            "id": simulation_id,
            "name": "BTC 30d simuliacija",
            "model_id": selected_model.id,
            "initial_capital": 10000.0,  # Pradinis kapitalas: 10,000 USD
            "fees": 0.1,  # 0.1% prekybos mokestis
            "start_date": start_date,
            "end_date": end_date,
            "strategy_type": "crossover",  # Kryžminės strategijos tipas
            "strategy_params": '{"short_ma": 7, "long_ma": 21}',  # Strategijos parametrai JSON formatu
            "final_balance": 11500.0,  # Galutinis balansas po simuliacijos
            "profit_loss": 1500.0,  # Bendras pelnas
            "roi": 0.15,  # 15% grąža
            "max_drawdown": 0.05,  # 5% maksimalus nuosmukis
            "total_trades": 12,  # Iš viso 12 sandorių
            "winning_trades": 8,  # 8 pelningi sandoriai
            "losing_trades": 4,  # 4 nuostolingi sandoriai
            "is_completed": True,  # Simuliacija baigta
            "created_at": datetime.now(timezone.utc)
        }
        
        # Sukuriame simuliaciją
        logger.info("Kuriama nauja simuliacija")
        simulation = simulation_service.create_simulation(simulation_data)
        
        if simulation:
            logger.info(f"Sėkmingai sukurta simuliacija: ID = {simulation.id}, Pavadinimas = {simulation.name}")
        else:
            logger.error("Nepavyko sukurti simuliacijos!")
            return
        
        # Gaukime simuliaciją pagal ID
        logger.info(f"Gaunama simuliacija pagal ID: {simulation_id}")
        retrieved_simulation = simulation_service.get_simulation(simulation_id)
        
        if retrieved_simulation:
            logger.info(f"Rasta simuliacija: {retrieved_simulation.name}")
            logger.info(f"Pradinis kapitalas: {retrieved_simulation.initial_capital} USD")
            logger.info(f"Galutinis balansas: {retrieved_simulation.final_balance} USD")
            logger.info(f"Pelnas/nuostolis: {retrieved_simulation.profit_loss} USD ({retrieved_simulation.roi * 100}%)")
        else:
            logger.error(f"Simuliacija su ID {simulation_id} nerasta!")
            return
        
        # Atnaujinkime simuliacijos duomenis (pvz., pakoreguojame metrikos)
        logger.info("Ruošiami simuliacijos atnaujinimo duomenys")
        update_data = {
            "final_balance": 11600.0,  # Patikslintas galutinis balansas
            "profit_loss": 1600.0,     # Patikslintas pelnas
            "roi": 0.16                # Patikslinta ROI
        }
        
        logger.info(f"Atnaujinama simuliacija su ID: {simulation_id}")
        updated_simulation = simulation_service.update_simulation(simulation_id, update_data)
        
        if updated_simulation:
            logger.info(f"Simuliacija atnaujinta: Pelnas/nuostolis = {updated_simulation.profit_loss} USD")
        else:
            logger.error("Nepavyko atnaujinti simuliacijos!")
            return
        
        # Gaukime visų simuliacijų sąrašą
        logger.info("Gaunamas visų simuliacijų sąrašas")
        all_simulations = simulation_service.list_simulations()
        
        logger.info(f"Iš viso turime {len(all_simulations)} simuliacijas:")
        for s in all_simulations:
            logger.info(f"- {s.name} ({s.id}): Pelnas/nuostolis: {s.profit_loss} USD")
        
    except Exception as e:
        logger.error(f"Įvyko klaida vykdant pavyzdį: {str(e)}")
    finally:
        # Uždarome sesiją kai baigėme
        logger.info("Uždaroma duomenų bazės sesija")
        session.close()

if __name__ == "__main__":
    main()