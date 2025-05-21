"""
Paprastas TradeService naudojimo pavyzdys.
"""
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Pridedame pagrindinį projekto katalogą į Python kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.simulation_service import SimulationService
from services.trade_service import TradeService
from services.model_service import ModelService

# Sukuriame duomenų bazės prisijungimą
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame servisus
model_service = ModelService(session)
simulation_service = SimulationService(session)
trade_service = TradeService(session)

# Pirmiausia turime paruošti simuliaciją sandoriams
# -----------------------------------------------
print("Kuriame modelį ir simuliaciją sandoriams:")

# Generuojame unikalius ID
model_id = str(uuid.uuid4())
simulation_id = str(uuid.uuid4())

# Kuriame modelį
model_data = {
    "id": model_id,
    "name": "Modelis sandorių pavyzdžiui",
    "type": "lstm",
    "hyperparameters": {"epochs": 50},
    "input_features": ["price"],
    "created_at": datetime.now(timezone.utc)
}
model = model_service.create_model(model_data)

# Kuriame simuliaciją
simulation_data = {
    "id": simulation_id,
    "name": "Simuliacija sandorių pavyzdžiui",
    "model_id": model_id,
    "initial_capital": 10000.0,
    "fees": 0.1,
    "start_date": datetime.now(timezone.utc) - timedelta(days=30),
    "end_date": datetime.now(timezone.utc),
    "strategy_type": "simple",
    "created_at": datetime.now(timezone.utc)
}
simulation = simulation_service.create_simulation(simulation_data)
print(f"Simuliacija sukurta! ID: {simulation.id}")

# 1. Sukuriame naują pirkimo sandorį
# --------------------------------
print("\n1. Sukuriame naują pirkimo sandorį:")

# Paruošiame pirkimo sandorio duomenis
buy_trade_data = {
    "portfolio_id": 1,
    "trade_type": "market",
    "btc_amount": 0.5,  # 0.5 BTC
    "price": 30000.0,   # 30,000 USD už BTC
    "value": 15000.0,   # 0.5 BTC * 30000 USD = 15000 USD
    "timestamp": datetime.now(timezone.utc) - timedelta(days=25),
    "simulation_id": simulation_id,  # Susiejame su simuliacija
    "date": datetime.now(timezone.utc) - timedelta(days=25),
    "type": "buy",
    "amount": 0.5,
    "fee": 15.0,  # 0.1% nuo 15000 USD = 15 USD
    "created_at": datetime.now(timezone.utc)
}

# Sukuriame pirkimo sandorį
buy_trade = trade_service.create_trade(buy_trade_data)

if buy_trade:
    print(f"Pirkimo sandoris sukurtas! ID: {buy_trade.id}")
    print(f"Pirkta: {buy_trade.btc_amount} BTC po {buy_trade.price} USD")
    print(f"Vertė: {buy_trade.value} USD, Mokestis: {buy_trade.fee} USD")
else:
    print("Nepavyko sukurti pirkimo sandorio.")

# 2. Sukuriame naują pardavimo sandorį
# ----------------------------------
print("\n2. Sukuriame naują pardavimo sandorį:")

# Paruošiame pardavimo sandorio duomenis
sell_trade_data = {
    "portfolio_id": 1,
    "trade_type": "market",
    "btc_amount": 0.5,  # 0.5 BTC
    "price": 32000.0,   # 32,000 USD už BTC
    "value": 16000.0,   # 0.5 BTC * 32000 USD = 16000 USD
    "timestamp": datetime.now(timezone.utc) - timedelta(days=15),
    "simulation_id": simulation_id,  # Susiejame su simuliacija
    "date": datetime.now(timezone.utc) - timedelta(days=15),
    "type": "sell",
    "amount": 0.5,
    "fee": 16.0,  # 0.1% nuo 16000 USD = 16 USD
    "profit_loss": 969.0,  # (16000 - 15000) - (15 + 16) = 969 USD pelnas
    "created_at": datetime.now(timezone.utc)
}

# Sukuriame pardavimo sandorį
sell_trade = trade_service.create_trade(sell_trade_data)

if sell_trade:
    print(f"Pardavimo sandoris sukurtas! ID: {sell_trade.id}")
    print(f"Parduota: {sell_trade.btc_amount} BTC po {sell_trade.price} USD")
    print(f"Vertė: {sell_trade.value} USD, Mokestis: {sell_trade.fee} USD")
    print(f"Pelnas: {sell_trade.profit_loss} USD")
else:
    print("Nepavyko sukurti pardavimo sandorio.")

# 3. Gauname sandorį pagal ID
# -------------------------
print("\n3. Gauname sandorį pagal ID:")

# Gauname ką tik sukurtą pardavimo sandorį
retrieved_trade = trade_service.get_trade(sell_trade.id)

if retrieved_trade:
    print(f"Sandoris rastas! ID: {retrieved_trade.id}")
    print(f"Tipas: {retrieved_trade.type}, Kiekis: {retrieved_trade.btc_amount} BTC")
    print(f"Kaina: {retrieved_trade.price} USD, Data: {retrieved_trade.date}")
else:
    print(f"Sandoris su ID {sell_trade.id} nerastas.")

# 4. Gauname simuliacijos sandorius
# -------------------------------
print("\n4. Gauname simuliacijos sandorius:")

# Gauname sandorius, susijusius su mūsų simuliacija
simulation_trades = trade_service.list_trades(simulation_id=simulation_id)

print(f"Simuliacija turi {len(simulation_trades)} sandorius:")
for t in simulation_trades:
    profit_text = f", Pelnas: {t.profit_loss} USD" if t.profit_loss else ""
    print(f"- {t.date.strftime('%Y-%m-%d')}: {t.type.upper()} {t.btc_amount} BTC @ {t.price} USD{profit_text}")

# 5. Skaičiuojame simuliacijos rezultatus
# ------------------------------------
print("\n5. Skaičiuojame simuliacijos rezultatus:")

# Apskaičiuojame bendrą pelną/nuostolį
total_profit = 0
for trade in simulation_trades:
    if trade.profit_loss:
        total_profit += trade.profit_loss

# Atnaujiname simuliacijos duomenis
update_data = {
    "final_balance": simulation.initial_capital + total_profit,
    "profit_loss": total_profit,
    "roi": total_profit / simulation.initial_capital,
    "total_trades": len(simulation_trades),
    "winning_trades": len([t for t in simulation_trades if t.profit_loss and t.profit_loss > 0]),
    "losing_trades": len([t for t in simulation_trades if t.profit_loss and t.profit_loss < 0]),
    "is_completed": True
}

updated_simulation = simulation_service.update_simulation(simulation_id, update_data)

if updated_simulation:
    print(f"Simuliacijos rezultatai atnaujinti!")
    print(f"Galutinis balansas: {updated_simulation.final_balance} USD")
    print(f"Pelnas/nuostolis: {updated_simulation.profit_loss} USD")
    print(f"ROI: {updated_simulation.roi * 100}%")
    print(f"Sandorių skaičius: {updated_simulation.total_trades}")
else:
    print(f"Nepavyko atnaujinti simuliacijos rezultatų.")

# 6. Ištriname sukurtus duomenis
# ----------------------------
print("\n6. Ištriname sukurtus duomenis:")

# Ištriname simuliaciją (kartu ištrinami ir susiję sandoriai)
if simulation_service.delete_simulation(simulation_id):
    print(f"Simuliacija su ID {simulation_id} ir visi jos sandoriai ištrinti sėkmingai.")
else:
    print(f"Nepavyko ištrinti simuliacijos su ID {simulation_id}.")

# Ištriname modelį
if model_service.delete_model(model_id):
    print(f"Modelis su ID {model_id} ištrintas sėkmingai.")
else:
    print(f"Nepavyko ištrinti modelio su ID {model_id}.")

# Uždarome duomenų bazės sesiją
session.close()
print("\nDuomenų bazės sesija uždaryta.")