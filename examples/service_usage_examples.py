"""
Praktiniai servisų naudojimo pavyzdžiai.
Šis failas parodo, kaip naudoti įvairius projekto servisus su paprastais pavyzdžiais.
"""
import uuid
import os
import sys
import logging
from datetime import datetime, timezone, timedelta
import json

# Pridedame pagrindinį projekto katalogą į Python kelią, kad galėtume importuoti modulius
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL ir servisus
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService
from services.simulation_service import SimulationService
from services.trade_service import TradeService
from services.prediction_service import PredictionService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database_session():
    """
    Sukuria ir grąžina duomenų bazės sesiją.
    """
    # Sukuriame SQLAlchemy variklį su mūsų duomenų bazės URL
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Sukuriame sesiją, kuri leidžia atlikti operacijas su duomenų baze
    session = Session(engine)
    return session

#############################
# MODEL SERVICE PAVYZDŽIAI #
#############################

def model_service_examples(session):
    """
    Parodo, kaip naudoti ModelService.
    """
    logger.info("====== MODEL SERVICE PAVYZDŽIAI ======")
    
    # Inicializuojame modelio servisą su duomenų bazės sesija
    model_service = ModelService(session)
    
    # 1. Modelio sukūrimo pavyzdys
    logger.info("1. Modelio sukūrimo pavyzdys:")
    
    # Sugeneruojame unikalų ID modeliui
    model_id = str(uuid.uuid4())
    
    # Sukuriame modelio duomenis su visais reikalingais laukais
    model_data = {
        "id": model_id,
        "name": "Pavyzdinis LSTM modelis",
        "description": "LSTM modelis Bitcoin kainos prognozavimui",
        "type": "lstm",
        "hyperparameters": {
            "epochs": 50,
            "batch_size": 32,
            "learning_rate": 0.001
        },
        "input_features": ["price", "volume", "ma_7", "ma_30"],
        "performance_metrics": {
            "accuracy": 0.85,
            "loss": 0.12
        },
        "created_at": datetime.now(timezone.utc)
    }
    
    # Sukuriame modelį duomenų bazėje
    model = model_service.create_model(model_data)
    
    if model:
        logger.info(f"Sėkmingai sukurtas modelis: ID = {model.id}, Pavadinimas = {model.name}")
    else:
        logger.error("Nepavyko sukurti modelio!")
    
    # 2. Modelio gavimo pavyzdys
    logger.info("\n2. Modelio gavimo pavyzdys:")
    
    # Gauname modelį pagal jo ID
    retrieved_model = model_service.get_model(model_id)
    
    if retrieved_model:
        logger.info(f"Gautas modelis: ID = {retrieved_model.id}, Pavadinimas = {retrieved_model.name}")
        logger.info(f"Modelio aprašymas: {retrieved_model.description}")
        logger.info(f"Modelio tipas: {retrieved_model.type}")
        logger.info(f"Hiperparametrai: {json.dumps(retrieved_model.hyperparameters, indent=2)}")
    else:
        logger.error(f"Nepavyko gauti modelio su ID {model_id}!")
    
    # 3. Modelio atnaujinimo pavyzdys
    logger.info("\n3. Modelio atnaujinimo pavyzdys:")
    
    # Paruošiame duomenis atnaujinimui - keičiame tik tuos laukus, kuriuos norime atnaujinti
    update_data = {
        "performance_metrics": {
            "accuracy": 0.88,  # Pagerintas tikslumas
            "loss": 0.10,      # Sumažintas nuostolis
            "f1_score": 0.86   # Naujas matas
        }
    }
    
    # Atnaujiname modelį
    updated_model = model_service.update_model(model_id, update_data)
    
    if updated_model:
        logger.info(f"Modelis atnaujintas sėkmingai.")
        logger.info(f"Nauji veikimo metrikai: {json.dumps(updated_model.performance_metrics, indent=2)}")
    else:
        logger.error(f"Nepavyko atnaujinti modelio su ID {model_id}!")
    
    # 4. Modelių sąrašo gavimo pavyzdys
    logger.info("\n4. Modelių sąrašo gavimo pavyzdys:")
    
    # Gauname visus modelius
    all_models = model_service.list_models()
    
    logger.info(f"Duomenų bazėje yra {len(all_models)} modeliai:")
    for m in all_models:
        logger.info(f"- {m.name} (ID: {m.id}, tipas: {m.type})")
    
    return model_id

###################################
# SIMULATION SERVICE PAVYZDŽIAI #
###################################

def simulation_service_examples(session, model_id):
    """
    Parodo, kaip naudoti SimulationService.
    """
    logger.info("\n====== SIMULATION SERVICE PAVYZDŽIAI ======")
    
    # Inicializuojame simuliacijos servisą su duomenų bazės sesija
    simulation_service = SimulationService(session)
    
    # 1. Simuliacijos sukūrimo pavyzdys
    logger.info("1. Simuliacijos sukūrimo pavyzdys:")
    
    # Sugeneruojame unikalų ID simuliacijai
    simulation_id = str(uuid.uuid4())
    
    # Nustatome simuliacijos laiko rėžius (30 dienų nuo dabar)
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    # Sukuriame simuliacijos duomenis su visais reikalingais laukais
    simulation_data = {
        "id": simulation_id,
        "name": "Pavyzdinė 30 dienų simuliacija",
        "model_id": model_id,  # Naudojame anksčiau sukurto modelio ID
        "initial_capital": 10000.0,  # Pradinis kapitalas: 10,000 USD
        "fees": 0.1,  # 0.1% prekybos mokestis
        "start_date": start_date,
        "end_date": end_date,
        "strategy_type": "moving_average_crossover",  # Kryžminių slankiųjų vidurkių strategija
        "strategy_params": json.dumps({"short_ma": 7, "long_ma": 21}),  # Strategijos parametrai
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
    
    # Sukuriame simuliaciją duomenų bazėje
    simulation = simulation_service.create_simulation(simulation_data)
    
    if simulation:
        logger.info(f"Sėkmingai sukurta simuliacija: ID = {simulation.id}, Pavadinimas = {simulation.name}")
    else:
        logger.error("Nepavyko sukurti simuliacijos!")
    
    # 2. Simuliacijos gavimo pavyzdys
    logger.info("\n2. Simuliacijos gavimo pavyzdys:")
    
    # Gauname simuliaciją pagal jos ID
    retrieved_simulation = simulation_service.get_simulation(simulation_id)
    
    if retrieved_simulation:
        logger.info(f"Gauta simuliacija: ID = {retrieved_simulation.id}, Pavadinimas = {retrieved_simulation.name}")
        logger.info(f"Modelio ID: {retrieved_simulation.model_id}")
        logger.info(f"Pradinis kapitalas: {retrieved_simulation.initial_capital} USD")
        logger.info(f"Pelnas/nuostolis: {retrieved_simulation.profit_loss} USD ({retrieved_simulation.roi * 100}% ROI)")
        logger.info(f"Laikotarpis: nuo {retrieved_simulation.start_date} iki {retrieved_simulation.end_date}")
    else:
        logger.error(f"Nepavyko gauti simuliacijos su ID {simulation_id}!")
    
    # 3. Simuliacijos atnaujinimo pavyzdys
    logger.info("\n3. Simuliacijos atnaujinimo pavyzdys:")
    
    # Paruošiame duomenis atnaujinimui - keičiame tik tuos laukus, kuriuos norime atnaujinti
    update_data = {
        "final_balance": 11800.0,  # Patikslintas galutinis balansas
        "profit_loss": 1800.0,     # Patikslintas pelnas
        "roi": 0.18                # Patikslinta ROI
    }
    
    # Atnaujiname simuliaciją
    updated_simulation = simulation_service.update_simulation(simulation_id, update_data)
    
    if updated_simulation:
        logger.info(f"Simuliacija atnaujinta sėkmingai.")
        logger.info(f"Naujas pelnas/nuostolis: {updated_simulation.profit_loss} USD ({updated_simulation.roi * 100}% ROI)")
    else:
        logger.error(f"Nepavyko atnaujinti simuliacijos su ID {simulation_id}!")
    
    # 4. Simuliacijų sąrašo gavimo pavyzdys
    logger.info("\n4. Simuliacijų sąrašo gavimo pavyzdys:")
    
    # Gauname visas simuliacijas
    all_simulations = simulation_service.list_simulations()
    
    logger.info(f"Duomenų bazėje yra {len(all_simulations)} simuliacijos:")
    for s in all_simulations:
        logger.info(f"- {s.name} (ID: {s.id}, Pelnas/nuostolis: {s.profit_loss} USD)")
    
    return simulation_id

###########################
# TRADE SERVICE PAVYZDŽIAI #
###########################

def trade_service_examples(session, simulation_id):
    """
    Parodo, kaip naudoti TradeService.
    """
    logger.info("\n====== TRADE SERVICE PAVYZDŽIAI ======")
    
    # Inicializuojame prekybos sandorių servisą su duomenų bazės sesija
    trade_service = TradeService(session)
    
    # 1. Prekybos sandorio sukūrimo pavyzdys
    logger.info("1. Prekybos sandorio sukūrimo pavyzdys:")
    
    # Sukuriame pirmą prekybos sandorį (pirkimas)
    buy_trade_data = {
        "portfolio_id": 1,
        "trade_type": "market",
        "btc_amount": 0.2,  # 0.2 BTC
        "price": 30000.0,   # po 30,000 USD už BTC
        "value": 6000.0,    # 0.2 BTC * 30000 USD = 6000 USD
        "timestamp": datetime.now(timezone.utc) - timedelta(days=20),  # 20 dienų atgal
        "simulation_id": simulation_id,  # Susiejame su anksčiau sukurta simuliacija
        "date": datetime.now(timezone.utc) - timedelta(days=20),
        "type": "buy",
        "amount": 0.2,
        "fee": 6.0,  # 0.1% nuo 6000 USD = 6 USD
        "created_at": datetime.now(timezone.utc)
    }
    
    # Sukuriame pirkimo sandorį duomenų bazėje
    buy_trade = trade_service.create_trade(buy_trade_data)
    
    if buy_trade:
        logger.info(f"Sėkmingai sukurtas pirkimo sandoris: ID = {buy_trade.id}")
        logger.info(f"Pirkta: {buy_trade.btc_amount} BTC po {buy_trade.price} USD")
        logger.info(f"Bendra vertė: {buy_trade.value} USD, Mokestis: {buy_trade.fee} USD")
    else:
        logger.error("Nepavyko sukurti pirkimo sandorio!")
    
    # Sukuriame antrą prekybos sandorį (pardavimas)
    sell_trade_data = {
        "portfolio_id": 1,
        "trade_type": "market",
        "btc_amount": 0.2,  # 0.2 BTC
        "price": 32000.0,   # po 32,000 USD už BTC
        "value": 6400.0,    # 0.2 BTC * 32000 USD = 6400 USD
        "timestamp": datetime.now(timezone.utc) - timedelta(days=10),  # 10 dienų atgal
        "simulation_id": simulation_id,  # Susiejame su anksčiau sukurta simuliacija
        "date": datetime.now(timezone.utc) - timedelta(days=10),
        "type": "sell",
        "amount": 0.2,
        "fee": 6.4,  # 0.1% nuo 6400 USD = 6.4 USD
        "profit_loss": 387.6,  # (6400 - 6000) - (6 + 6.4) = 387.6 USD pelnas
        "created_at": datetime.now(timezone.utc)
    }
    
    # Sukuriame pardavimo sandorį duomenų bazėje
    sell_trade = trade_service.create_trade(sell_trade_data)
    
    if sell_trade:
        logger.info(f"Sėkmingai sukurtas pardavimo sandoris: ID = {sell_trade.id}")
        logger.info(f"Parduota: {sell_trade.btc_amount} BTC po {sell_trade.price} USD")
        logger.info(f"Bendra vertė: {sell_trade.value} USD, Mokestis: {sell_trade.fee} USD")
        logger.info(f"Pelnas/nuostolis: {sell_trade.profit_loss} USD")
    else:
        logger.error("Nepavyko sukurti pardavimo sandorio!")
    
    # 2. Prekybos sandorio gavimo pavyzdys
    logger.info("\n2. Prekybos sandorio gavimo pavyzdys:")
    
    # Gauname pirką sandorį pagal jo ID
    retrieved_buy_trade = trade_service.get_trade(buy_trade.id)
    
    if retrieved_buy_trade:
        logger.info(f"Gautas pirkimo sandoris: ID = {retrieved_buy_trade.id}")
        logger.info(f"Tipas: {retrieved_buy_trade.type}, Kiekis: {retrieved_buy_trade.btc_amount} BTC")
        logger.info(f"Kaina: {retrieved_buy_trade.price} USD, Data: {retrieved_buy_trade.date}")
    else:
        logger.error(f"Nepavyko gauti sandorio su ID {buy_trade.id}!")
    
    # 3. Visų sandorių gavimo pavyzdys
    logger.info("\n3. Visų sandorių gavimo pavyzdys:")
    
    # Gauname visus sandorius iš duomenų bazės
    all_trades = trade_service.list_trades()
    
    logger.info(f"Duomenų bazėje yra {len(all_trades)} sandoriai:")
    for t in all_trades:
        logger.info(f"- ID: {t.id}, Tipas: {t.type}, Kiekis: {t.btc_amount} BTC, Kaina: {t.price} USD")
    
    # 4. Simuliacijos sandorių gavimo pavyzdys
    logger.info("\n4. Simuliacijos sandorių gavimo pavyzdys:")
    
    # Gauname sandorius, susijusius su konkrečia simuliacija
    simulation_trades = trade_service.list_trades(simulation_id=simulation_id)
    
    logger.info(f"Simuliacija su ID {simulation_id} turi {len(simulation_trades)} sandorius:")
    for t in simulation_trades:
        profit_text = f", Pelnas/nuostolis: {t.profit_loss} USD" if t.profit_loss else ""
        logger.info(f"- ID: {t.id}, {t.date.strftime('%Y-%m-%d')}: {t.type.upper()} {t.btc_amount} BTC @ {t.price} USD{profit_text}")
    
    return buy_trade.id, sell_trade.id

###################################
# PREDICTION SERVICE PAVYZDŽIAI #
###################################

def prediction_service_examples(session, model_id):
    """
    Parodo, kaip naudoti PredictionService.
    """
    logger.info("\n====== PREDICTION SERVICE PAVYZDŽIAI ======")
    
    # Inicializuojame prognozių servisą su duomenų bazės sesija
    prediction_service = PredictionService(session)
    
    # 1. Prognozės sukūrimo pavyzdys
    logger.info("1. Prognozės sukūrimo pavyzdys:")
    
    # Sukuriame naują prognozę
    prediction_data = {
        "model_id": model_id,  # Susiejame su anksčiau sukurtu modeliu
        "prediction_date": datetime.now(timezone.utc),
        "target_date": datetime.now(timezone.utc) + timedelta(days=1),  # Prognozuojame rytojaus kainą
        "predicted_price": 32500.0,  # Prognozuojama kaina
        "confidence": 0.85,  # Prognozės pasitikėjimo lygis
        "features_used": ["price", "volume", "ma_7"],  # Požymiai, naudoti prognozei
        "actual_price": None,  # Faktinė kaina dar nežinoma
        "error": None,  # Klaida dar nežinoma
        "created_at": datetime.now(timezone.utc)
    }
    
    # Sukuriame prognozę duomenų bazėje
    prediction = prediction_service.create_prediction(prediction_data)
    
    if prediction:
        logger.info(f"Sėkmingai sukurta prognozė: ID = {prediction.id}")
        logger.info(f"Modelio ID: {prediction.model_id}")
        logger.info(f"Prognozuojama kaina: {prediction.predicted_price} USD")
        logger.info(f"Prognozės data: {prediction.prediction_date}")
        logger.info(f"Tikslinė data: {prediction.target_date}")
    else:
        logger.error("Nepavyko sukurti prognozės!")
    
    # 2. Prognozės atnaujinimo pavyzdys (kai žinoma faktinė kaina)
    logger.info("\n2. Prognozės atnaujinimo pavyzdys:")
    
    # Tarkime, kad sužinojome faktinę kainą ir dabar norime atnaujinti prognozę
    update_data = {
        "actual_price": 32800.0,  # Faktinė kaina
        "error": 300.0  # Apskaičiuojame klaidą: 32800 - 32500 = 300
    }
    
    # Atnaujiname prognozę
    updated_prediction = prediction_service.update_prediction(prediction.id, update_data)
    
    if updated_prediction:
        logger.info(f"Prognozė atnaujinta sėkmingai.")
        logger.info(f"Prognozuota kaina: {updated_prediction.predicted_price} USD")
        logger.info(f"Faktinė kaina: {updated_prediction.actual_price} USD")
        logger.info(f"Klaida: {updated_prediction.error} USD")
    else:
        logger.error(f"Nepavyko atnaujinti prognozės su ID {prediction.id}!")
    
    # 3. Modelio prognozių gavimo pavyzdys
    logger.info("\n3. Modelio prognozių gavimo pavyzdys:")
    
    # Gauname visas prognozes, susijusias su konkrečiu modeliu
    model_predictions = prediction_service.list_predictions(model_id=model_id)
    
    logger.info(f"Modelis su ID {model_id} turi {len(model_predictions)} prognozes:")
    for p in model_predictions:
        error_text = f", Klaida: {p.error} USD" if p.error else ""
        logger.info(f"- ID: {p.id}, Prognozuota: {p.predicted_price} USD, Faktinė: {p.actual_price} USD{error_text}")
    
    return prediction.id

#############################
# SERVISŲ INTEGRAVIMO PAVYZDYS #
#############################

def integrated_example(session):
    """
    Parodo, kaip integruoti skirtingus servisus į vieną darbo eigą.
    """
    logger.info("\n====== SERVISŲ INTEGRAVIMO PAVYZDYS ======")
    
    # Inicializuojame visus reikalingus servisus
    model_service = ModelService(session)
    simulation_service = SimulationService(session)
    trade_service = TradeService(session)
    prediction_service = PredictionService(session)
    
    # 1. Sukuriame naują modelį
    logger.info("1. Sukuriame naują modelį:")
    
    model_id = str(uuid.uuid4())
    model_data = {
        "id": model_id,
        "name": "Integruotas LSTM modelis",
        "description": "Modelis, naudojamas integruotame pavyzdyje",
        "type": "lstm",
        "hyperparameters": {"epochs": 50, "batch_size": 32, "learning_rate": 0.001},
        "input_features": ["price", "volume", "ma_7", "ma_30"],
        "performance_metrics": {"accuracy": 0.85, "loss": 0.12},
        "created_at": datetime.now(timezone.utc)
    }
    
    model = model_service.create_model(model_data)
    logger.info(f"Sukurtas modelis: ID = {model.id}, Pavadinimas = {model.name}")
    
    # 2. Sukuriame keletą prognozių, naudodami šį modelį
    logger.info("\n2. Sukuriame prognozes:")
    
    # Prognozės kelių dienų laikotarpiui
    for days_ahead in range(1, 6):
        target_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        # Prognozuojama kaina didėja kiekvieną dieną
        predicted_price = 32000.0 + (days_ahead * 500)
        
        prediction_data = {
            "model_id": model_id,
            "prediction_date": datetime.now(timezone.utc),
            "target_date": target_date,
            "predicted_price": predicted_price,
            "confidence": 0.85 - (days_ahead * 0.05),  # Pasitikėjimas mažėja su laiku
            "features_used": ["price", "volume", "ma_7"],
            "created_at": datetime.now(timezone.utc)
        }
        
        prediction = prediction_service.create_prediction(prediction_data)
        logger.info(f"Sukurta prognozė datai {target_date.date()}: {prediction.predicted_price} USD (pasitikėjimas: {prediction.confidence:.2f})")
    
    # 3. Sukuriame simuliaciją, naudodami šį modelį
    logger.info("\n3. Sukuriame simuliaciją:")
    
    simulation_id = str(uuid.uuid4())
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc) + timedelta(days=5)  # Įtraukiame ir prognozuojamą laikotarpį
    
    simulation_data = {
        "id": simulation_id,
        "name": "Integruota simuliacija",
        "model_id": model_id,
        "initial_capital": 10000.0,
        "fees": 0.1,
        "start_date": start_date,
        "end_date": end_date,
        "strategy_type": "prediction_based",  # Strategija, pagrįsta prognozėmis
        "strategy_params": json.dumps({"confidence_threshold": 0.8, "min_price_change": 500}),
        "is_completed": False,  # Simuliacija dar vykdoma
        "created_at": datetime.now(timezone.utc)
    }
    
    simulation = simulation_service.create_simulation(simulation_data)
    logger.info(f"Sukurta simuliacija: ID = {simulation.id}, Pavadinimas = {simulation.name}")
    
    # 4. Sukuriame keletą prekybos sandorių simuliacijai
    logger.info("\n4. Sukuriame prekybos sandorius pagal prognozes:")
    
    # Gauname visas modelio prognozes
    model_predictions = prediction_service.list_predictions(model_id=model_id)
    model_predictions.sort(key=lambda p: p.target_date)  # Rūšiuojame pagal tikslinę datą
    
    # Simuliuojame prekybą pagal prognozes
    current_btc = 0.0  # Pradžioje neturime BTC
    current_usd = simulation.initial_capital  # Pradžioje turime tik USD
    
    for i, prediction in enumerate(model_predictions):
        # Sprendžiame, ar pirkti, ar parduoti, pagal kainų pokyčius
        if i > 0:
            price_change = prediction.predicted_price - model_predictions[i-1].predicted_price
            price_change_percent = price_change / model_predictions[i-1].predicted_price * 100
            
            # Jei kaina kyla ir pasitikėjimas aukštas, perkame
            if price_change > 0 and prediction.confidence >= 0.8 and current_usd > 0:
                # Apskaičiuojame, kiek BTC galime nusipirkti
                btc_to_buy = (current_usd * 0.5) / prediction.predicted_price  # Perkame už pusę turimų USD
                cost = btc_to_buy * prediction.predicted_price
                fee = cost * simulation.fees / 100
                
                trade_data = {
                    "portfolio_id": 1,
                    "trade_type": "market",
                    "btc_amount": btc_to_buy,
                    "price": prediction.predicted_price,
                    "value": cost,
                    "timestamp": prediction.target_date,
                    "simulation_id": simulation_id,
                    "date": prediction.target_date,
                    "type": "buy",
                    "amount": btc_to_buy,
                    "fee": fee,
                    "created_at": datetime.now(timezone.utc)
                }
                
                trade = trade_service.create_trade(trade_data)
                logger.info(f"Pirkta: {trade.btc_amount:.4f} BTC po {trade.price} USD (kainų pokytis: {price_change_percent:.2f}%)")
                
                # Atnaujiname turimą BTC ir USD
                current_btc += btc_to_buy
                current_usd -= (cost + fee)
                
            # Jei kaina krenta ir pasitikėjimas aukštas, parduodame
            elif price_change < 0 and prediction.confidence >= 0.8 and current_btc > 0:
                # Parduodame pusę turimų BTC
                btc_to_sell = current_btc * 0.5
                revenue = btc_to_sell * prediction.predicted_price
                fee = revenue * simulation.fees / 100
                
                trade_data = {
                    "portfolio_id": 1,
                    "trade_type": "market",
                    "btc_amount": btc_to_sell,
                    "price": prediction.predicted_price,
                    "value": revenue,
                    "timestamp": prediction.target_date,
                    "simulation_id": simulation_id,
                    "date": prediction.target_date,
                    "type": "sell",
                    "amount": btc_to_sell,
                    "fee": fee,
                    "created_at": datetime.now(timezone.utc)
                }
                
                trade = trade_service.create_trade(trade_data)
                logger.info(f"Parduota: {trade.btc_amount:.4f} BTC po {trade.price} USD (kainų pokytis: {price_change_percent:.2f}%)")
                
                # Atnaujiname turimą BTC ir USD
                current_btc -= btc_to_sell
                current_usd += (revenue - fee)
    
    # 5. Baigiame simuliaciją ir atnaujiname jos rezultatus
    logger.info("\n5. Baigiame simuliaciją ir atnaujiname rezultatus:")
    
    # Gauname visus simuliacijos sandorius
    simulation_trades = trade_service.list_trades(simulation_id=simulation_id)
    
    # Apskaičiuojame simuliacijos rezultatus
    total_trades = len(simulation_trades)
    buy_trades = [t for t in simulation_trades if t.type == 'buy']
    sell_trades = [t for t in simulation_trades if t.type == 'sell']
    
    # Apskaičiuojame galutinį balansą
    final_balance = current_usd + (current_btc * model_predictions[-1].predicted_price if model_predictions else 0)
    profit_loss = final_balance - simulation.initial_capital
    roi = profit_loss / simulation.initial_capital
    
    # Atnaujiname simuliacijos duomenis
    update_data = {
        "final_balance": final_balance,
        "profit_loss": profit_loss,
        "roi": roi,
        "total_trades": total_trades,
        "winning_trades": len([t for t in simulation_trades if t.profit_loss and t.profit_loss > 0]),
        "losing_trades": len([t for t in simulation_trades if t.profit_loss and t.profit_loss < 0]),
        "is_completed": True  # Pažymime, kad simuliacija baigta
    }
    
    updated_simulation = simulation_service.update_simulation(simulation_id, update_data)
    
    logger.info(f"Simuliacija baigta:")
    logger.info(f"Galutinis balansas: {updated_simulation.final_balance:.2f} USD")
    logger.info(f"Pelnas/nuostolis: {updated_simulation.profit_loss:.2f} USD ({updated_simulation.roi * 100:.2f}% ROI)")
    logger.info(f"Sandorių skaičius: {updated_simulation.total_trades}")
    
    # 6. Ištriname sukurtus duomenis (jei tai tik pavyzdys ir nenorime išsaugoti duomenų)
    logger.info("\n6. Tvarkome po pavyzdžio - ištriname sukurtus duomenis:")
    
    # Ištriname simuliaciją (ir susijusius sandorius kaskadiškai)
    if simulation_service.delete_simulation(simulation_id):
        logger.info(f"Simuliacija su ID {simulation_id} ištrinta sėkmingai")
    
    # Ištriname modelį (ir susijusias prognozes kaskadiškai)
    if model_service.delete_model(model_id):
        logger.info(f"Modelis su ID {model_id} ištrintas sėkmingai")
    
    logger.info("Integruotas pavyzdys sėkmingai baigtas!")

if __name__ == "__main__":
    # Sukuriame duomenų bazės sesiją
    session = setup_database_session()
    
    try:
        # Paleidžiame atskirus servisų pavyzdžius
        model_id = model_service_examples(session)
        simulation_id = simulation_service_examples(session, model_id)
        buy_trade_id, sell_trade_id = trade_service_examples(session, simulation_id)
        prediction_id = prediction_service_examples(session, model_id)
        
        # Paleidžiame integruotą pavyzdį
        integrated_example(session)
        
        # Ištriname sukurtus duomenis
        logger.info("\n====== IŠTRINAME SUKURTUS DUOMENIS ======")
        
        # Pradedame nuo prekybos sandorių
        trade_service = TradeService(session)
        if trade_service.delete_trade(buy_trade_id):
            logger.info(f"Pirkimo sandoris su ID {buy_trade_id} ištrintas sėkmingai")
        if trade_service.delete_trade(sell_trade_id):
            logger.info(f"Pardavimo sandoris su ID {sell_trade_id} ištrintas sėkmingai")
        
        # Tada ištriname simuliaciją
        simulation_service = SimulationService(session)
        if simulation_service.delete_simulation(simulation_id):
            logger.info(f"Simuliacija su ID {simulation_id} ištrinta sėkmingai")
        
        # Ištriname prognozę
        prediction_service = PredictionService(session)
        if prediction_service.delete_prediction(prediction_id):
            logger.info(f"Prognozė su ID {prediction_id} ištrinta sėkmingai")
        
        # Galiausiai ištriname modelį
        model_service = ModelService(session)
        if model_service.delete_model(model_id):
            logger.info(f"Modelis su ID {model_id} ištrintas sėkmingai")
        
    except Exception as e:
        logger.error(f"Įvyko klaida vykdant pavyzdžius: {str(e)}")
    finally:
        # Uždarome duomenų bazės sesiją
        session.close()
        logger.info("Duomenų bazės sesija uždaryta.")