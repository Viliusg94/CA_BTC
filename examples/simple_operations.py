"""
Labai paprastas pavyzdys, parodantis pagrindines projekto operacijas.
"""
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
import logging

# Pridedame pagrindinį projekto katalogą į Python kelią, kad galėtume importuoti modulius
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Nustatome žurnalą, kad matytume, kas vyksta
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importuojame reikalingas bibliotekas darbui su duomenų baze
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL

# Importuojame servisus darbui su duomenimis
from services.model_service import ModelService
from services.simulation_service import SimulationService
from services.trade_service import TradeService
from services.prediction_service import PredictionService

def main():
    """
    Pagrindinis programos metodas, demonstruojantis pagrindines operacijas.
    """
    # Sukuriame duomenų bazės prisijungimą
    logger.info("Jungiamės prie duomenų bazės")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    try:
        # Inicializuojame servisus, naudodami tą pačią sesijos objektą
        logger.info("Inicializuojame servisus")
        model_service = ModelService(session)
        simulation_service = SimulationService(session)
        trade_service = TradeService(session)
        prediction_service = PredictionService(session)
        
        # -------------------------------
        # 1. Sukuriame naują modelį
        # -------------------------------
        logger.info("1. MODELIO SUKŪRIMAS")
        
        # Generuojame unikalų ID
        model_id = str(uuid.uuid4())
        
        # Paruošiame modelio duomenis
        model_data = {
            "id": model_id,                             # Unikalus ID
            "name": "Pirmasis modelis",                 # Modelio pavadinimas
            "description": "Paprastas LSTM modelis",    # Aprašymas
            "type": "lstm",                             # Modelio tipas
            "hyperparameters": {                        # Hiperparametrai
                "epochs": 50,                           # Epochų skaičius
                "batch_size": 32                        # Partijos dydis
            },
            "input_features": ["price", "volume"],      # Įvesties požymiai
            "created_at": datetime.now(timezone.utc)    # Sukūrimo data
        }
        
        # Sukuriame modelį duomenų bazėje
        model = model_service.create_model(model_data)
        logger.info(f"Sukurtas modelis: ID={model.id}, Pavadinimas={model.name}")
        
        # -------------------------------
        # 2. Sukuriame simuliaciją
        # -------------------------------
        logger.info("2. SIMULIACIJOS SUKŪRIMAS")
        
        # Generuojame unikalų ID
        simulation_id = str(uuid.uuid4())
        
        # Nustatome simuliacijos pradžios ir pabaigos datas
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        # Paruošiame simuliacijos duomenis
        simulation_data = {
            "id": simulation_id,                        # Unikalus ID
            "name": "Pirmoji simuliacija",              # Pavadinimas
            "model_id": model_id,                       # Susiejame su modeliu
            "initial_capital": 10000.0,                 # Pradinis kapitalas (USD)
            "fees": 0.1,                                # Mokesčiai (%)
            "start_date": start_date,                   # Pradžios data
            "end_date": end_date,                       # Pabaigos data
            "strategy_type": "simple",                  # Strategijos tipas
            "created_at": datetime.now(timezone.utc)    # Sukūrimo data
        }
        
        # Sukuriame simuliaciją duomenų bazėje
        simulation = simulation_service.create_simulation(simulation_data)
        logger.info(f"Sukurta simuliacija: ID={simulation.id}, Pavadinimas={simulation.name}")
        
        # -------------------------------
        # 3. Sukuriame prekybos sandorį
        # -------------------------------
        logger.info("3. PREKYBOS SANDORIO SUKŪRIMAS")
        
        # Paruošiame pirkimo sandorio duomenis
        trade_data = {
            "portfolio_id": 1,                          # Portfelio ID
            "trade_type": "market",                     # Sandorio tipas (rinkos)
            "btc_amount": 0.1,                          # BTC kiekis
            "price": 30000.0,                           # Kaina (USD už BTC)
            "value": 3000.0,                            # Vertė (USD)
            "timestamp": start_date + timedelta(days=1),# Sandorio laikas
            "simulation_id": simulation_id,             # Susiejame su simuliacija
            "date": start_date + timedelta(days=1),     # Sandorio data
            "type": "buy",                              # Sandorio tipas (pirkimas)
            "amount": 0.1,                              # Kiekis
            "fee": 3.0,                                 # Mokestis (USD)
            "created_at": datetime.now(timezone.utc)    # Sukūrimo data
        }
        
        # Sukuriame sandorį duomenų bazėje
        trade = trade_service.create_trade(trade_data)
        logger.info(f"Sukurtas sandoris: ID={trade.id}, Tipas={trade.type}, Kiekis={trade.btc_amount} BTC, Kaina={trade.price} USD")
        
        # -------------------------------
        # 4. Sukuriame prognozę
        # -------------------------------
        logger.info("4. PROGNOZĖS SUKŪRIMAS")
        
        # Paruošiame prognozės duomenis
        prediction_data = {
            "model_id": model_id,                       # Susiejame su modeliu
            "prediction_date": end_date + timedelta(days=1), # Prognozės data
            "price": 32000.0,                           # Prognozuojama kaina
            "confidence": 0.85,                         # Pasitikėjimo lygis
            "metrics": {                                # Metrikos
                "rmse": 250.0,                          # Vidutinė kvadratinė paklaida
                "mae": 180.0                            # Vidutinė absoliuti paklaida
            },
            "created_at": datetime.now(timezone.utc)    # Sukūrimo data
        }
        
        # Sukuriame prognozę duomenų bazėje
        prediction = prediction_service.create_prediction(prediction_data)
        logger.info(f"Sukurta prognozė: ID={prediction.id}, Kaina={prediction.price} USD, Pasitikėjimas={prediction.confidence*100}%")
        
        # -------------------------------
        # 5. Gauname duomenis
        # -------------------------------
        logger.info("5. DUOMENŲ GAVIMAS")
        
        # Gauname modelį pagal ID
        retrieved_model = model_service.get_model(model_id)
        logger.info(f"Gautas modelis: ID={retrieved_model.id}, Pavadinimas={retrieved_model.name}")
        
        # Gauname simuliaciją pagal ID
        retrieved_simulation = simulation_service.get_simulation(simulation_id)
        logger.info(f"Gauta simuliacija: ID={retrieved_simulation.id}, Pavadinimas={retrieved_simulation.name}")
        
        # Gauname visus simuliacijos sandorius
        simulation_trades = simulation_service.get_simulation_trades(simulation_id)
        logger.info(f"Simuliacija turi {len(simulation_trades)} sandorius")
        
        # Gauname visas modelio prognozes
        model_predictions = prediction_service.list_predictions(model_id=model_id)
        logger.info(f"Modelis turi {len(model_predictions)} prognozes")
        
        # -------------------------------
        # 6. Atnaujiname duomenis
        # -------------------------------
        logger.info("6. DUOMENŲ ATNAUJINIMAS")
        
        # Atnaujiname modelio duomenis
        model_update = {
            "performance_metrics": {                    # Veikimo metrikos
                "accuracy": 0.87,                       # Tikslumas
                "loss": 0.12                            # Nuostolis
            }
        }
        updated_model = model_service.update_model(model_id, model_update)
        logger.info(f"Atnaujintas modelis: Tikslumas={updated_model.performance_metrics.get('accuracy', 0)*100}%")
        
        # Atnaujiname simuliacijos duomenis
        simulation_update = {
            "final_balance": 11000.0,                  # Galutinis balansas
            "profit_loss": 1000.0,                     # Pelnas/nuostolis
            "roi": 0.1,                                # Grąža (10%)
            "max_drawdown": 0.05,                      # Maksimalus nuosmukis (5%)
            "total_trades": 1,                         # Sandorių skaičius
            "winning_trades": 1,                       # Pelningų sandorių
            "losing_trades": 0,                        # Nuostolingų sandorių
            "is_completed": True                       # Simuliacija baigta
        }
        updated_simulation = simulation_service.update_simulation(simulation_id, simulation_update)
        logger.info(f"Atnaujinta simuliacija: Balansas={updated_simulation.final_balance} USD, Pelnas={updated_simulation.profit_loss} USD")
        
        # -------------------------------
        # 7. Ištriname duomenis
        # -------------------------------
        logger.info("7. DUOMENŲ IŠTRYNIMAS")
        
        # Ištriname prognozę
        if prediction_service.delete_prediction(prediction.id):
            logger.info(f"Prognozė su ID {prediction.id} ištrinta")
        else:
            logger.warning(f"Nepavyko ištrinti prognozės su ID {prediction.id}")
        
        # Ištriname simuliaciją (kartu ištrinami ir susieti sandoriai)
        if simulation_service.delete_simulation(simulation_id):
            logger.info(f"Simuliacija su ID {simulation_id} ištrinta")
        else:
            logger.warning(f"Nepavyko ištrinti simuliacijos su ID {simulation_id}")
        
        # Ištriname modelį
        if model_service.delete_model(model_id):
            logger.info(f"Modelis su ID {model_id} ištrintas")
        else:
            logger.warning(f"Nepavyko ištrinti modelio su ID {model_id}")
            
        logger.info("Visos operacijos atliktos sėkmingai!")
        
    except Exception as e:
        # Apdorojame galimas klaidas
        logger.error(f"Įvyko klaida: {str(e)}")
        
    finally:
        # Uždarome duomenų bazės sesiją
        session.close()
        logger.info("Duomenų bazės sesija uždaryta")

# Vykdome pavyzdį, jei failas paleidžiamas tiesiogiai
if __name__ == "__main__":
    main()