"""
Paprastas SimulationService naudojimo pavyzdys.
"""
import os
import sys
import uuid
import json
from datetime import datetime, timezone, timedelta

# Pridedame pagrindinį projekto katalogą į Python kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService
from services.simulation_service import SimulationService

# Sukuriame duomenų bazės prisijungimą
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame servisus
model_service = ModelService(session)
simulation_service = SimulationService(session)

# Pirmiausia turime sukurti modelį simuliacijai
# -------------------------------------------
print("Kuriame modelį simuliacijai:")

# Generuojame unikalų ID
model_id = str(uuid.uuid4())

# Paruošiame modelio duomenis
model_data = {
    "id": model_id,
    "name": "Modelis simuliacijai",
    "description": "Modelis, naudojamas simuliacijos pavyzdyje",
    "type": "gru",
    "hyperparameters": {
        "epochs": 50,
        "batch_size": 32
    },
    "input_features": ["price", "volume"],
    "performance_metrics": {
        "accuracy": 0.75
    },
    "created_at": datetime.now(timezone.utc)
}

# Sukuriame modelį
model = model_service.create_model(model_data)
print(f"Modelis sukurtas! ID: {model.id}")

# 1. Sukuriame naują simuliaciją
# -----------------------------
print("\n1. Sukuriame naują simuliaciją:")

# Generuojame unikalų ID
simulation_id = str(uuid.uuid4())

# Nustatome simuliacijos laikotarpį (praėjusios 30 dienų)
start_date = datetime.now(timezone.utc) - timedelta(days=30)
end_date = datetime.now(timezone.utc)

# Paruošiame simuliacijos duomenis
simulation_data = {
    "id": simulation_id,
    "name": "Paprastas kryžminis testas",
    "model_id": model_id,  # Susiejame su ką tik sukurtu modeliu
    "initial_capital": 10000.0,  # Pradinis kapitalas: 10,000 USD
    "fees": 0.1,  # 0.1% prekybos mokestis
    "start_date": start_date,
    "end_date": end_date,
    "strategy_type": "ma_crossover",  # Slankiųjų vidurkių kryžminimo strategija
    "strategy_params": json.dumps({"short_ma": 5, "long_ma": 20}),  # Strategijos parametrai
    "final_balance": 11200.0,  # Galutinis balansas
    "profit_loss": 1200.0,  # Pelnas
    "roi": 0.12,  # 12% grąža
    "max_drawdown": 0.08,  # 8% maksimalus nuosmukis
    "total_trades": 8,  # Iš viso 8 sandoriai
    "winning_trades": 5,  # 5 pelningi sandoriai
    "losing_trades": 3,  # 3 nuostolingi sandoriai
    "is_completed": True,  # Simuliacija baigta
    "created_at": datetime.now(timezone.utc)
}

# Sukuriame simuliaciją
simulation = simulation_service.create_simulation(simulation_data)

if simulation:
    print(f"Simuliacija sukurta! ID: {simulation.id}, Pavadinimas: {simulation.name}")
    print(f"Pradinis kapitalas: {simulation.initial_capital} USD")
    print(f"Pelnas: {simulation.profit_loss} USD ({simulation.roi * 100}% ROI)")
else:
    print("Nepavyko sukurti simuliacijos.")

# 2. Gauname simuliaciją pagal ID
# ------------------------------
print("\n2. Gauname simuliaciją pagal ID:")

# Gauname ką tik sukurtą simuliaciją
retrieved_simulation = simulation_service.get_simulation(simulation_id)

if retrieved_simulation:
    print(f"Simuliacija rasta! Pavadinimas: {retrieved_simulation.name}")
    print(f"Modelio ID: {retrieved_simulation.model_id}")
    print(f"Strategija: {retrieved_simulation.strategy_type}")
    print(f"Laikotarpis: {retrieved_simulation.start_date.date()} - {retrieved_simulation.end_date.date()}")
else:
    print(f"Simuliacija su ID {simulation_id} nerasta.")

# 3. Atnaujiname simuliaciją
# -------------------------
print("\n3. Atnaujiname simuliaciją:")

# Paruošiame atnaujinimo duomenis
update_data = {
    "final_balance": 11500.0,  # Patikslintas galutinis balansas
    "profit_loss": 1500.0,  # Patikslintas pelnas
    "roi": 0.15,  # Patikslinta ROI
    "total_trades": 10,  # Patikslintas sandorių skaičius
    "winning_trades": 7,  # Patikslinti pelningi sandoriai
    "losing_trades": 3  # Nuostolingi sandoriai
}

# Atnaujiname simuliaciją
updated_simulation = simulation_service.update_simulation(simulation_id, update_data)

if updated_simulation:
    print(f"Simuliacija atnaujinta! Naujas pelnas: {updated_simulation.profit_loss} USD")
    print(f"Nauja ROI: {updated_simulation.roi * 100}%")
    print(f"Sandorių skaičius: {updated_simulation.total_trades}")
else:
    print(f"Nepavyko atnaujinti simuliacijos su ID {simulation_id}.")

# 4. Gauname visų simuliacijų sąrašą
# --------------------------------
print("\n4. Gauname visų simuliacijų sąrašą:")

# Gauname visas simuliacijas
simulations = simulation_service.list_simulations()

print(f"Duomenų bazėje yra {len(simulations)} simuliacijos:")
for s in simulations:
    print(f"- {s.name} (ID: {s.id}, Pelnas: {s.profit_loss} USD)")

# 5. Ištriname simuliaciją ir modelį
# --------------------------------
print("\n5. Ištriname simuliaciją ir modelį:")

# Ištriname ką tik sukurtą simuliaciją
if simulation_service.delete_simulation(simulation_id):
    print(f"Simuliacija su ID {simulation_id} sėkmingai ištrinta.")
else:
    print(f"Nepavyko ištrinti simuliacijos su ID {simulation_id}.")

# Ištriname ką tik sukurtą modelį
if model_service.delete_model(model_id):
    print(f"Modelis su ID {model_id} sėkmingai ištrintas.")
else:
    print(f"Nepavyko ištrinti modelio su ID {model_id}.")

# Uždarome duomenų bazės sesiją
session.close()
print("\nDuomenų bazės sesija uždaryta.")