# Naudojimo pavyzdžiai

Šiame dokumente pateikti praktiniai sistemos naudojimo pavyzdžiai. Jie skirti pradedantiesiems programuotojams suprasti, kaip naudotis sukurtais servisais.

## 1. Modelio sukūrimas ir naudojimas

Šis pavyzdys parodo, kaip sukurti naują modelį ir jį panaudoti.

```python
# Importuojame reikalingas bibliotekas
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService

# Prisijungiame prie duomenų bazės
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame modelio servisą
model_service = ModelService(session)

# Sugeneruojame unikalų ID modeliui
model_id = str(uuid.uuid4())

# Sukuriame modelio duomenis
model_data = {
    "id": model_id,
    "name": "LSTM modelis",
    "description": "Ilgosios trumpalaikės atminties modelis Bitcoin kainos prognozavimui",
    "type": "lstm",
    "hyperparameters": {
        "epochs": 100,
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

# Sukuriame modelį
model = model_service.create_model(model_data)

if model:
    print(f"Sėkmingai sukurtas modelis: ID = {model.id}, Pavadinimas = {model.name}")
else:
    print("Nepavyko sukurti modelio!")

# Gaukime modelį pagal ID
retrieved_model = model_service.get_model(model_id)
if retrieved_model:
    print(f"Rastas modelis: {retrieved_model.name}, tipas: {retrieved_model.type}")
    print(f"Hiperparametrai: {retrieved_model.hyperparameters}")
else:
    print(f"Modelis su ID {model_id} nerastas!")

# Atnaujinkime modelio veikimo metrikas
update_data = {
    "performance_metrics": {
        "accuracy": 0.88,  # Pagerintas tikslumas
        "loss": 0.10,      # Sumažintas nuostolis
        "f1_score": 0.86   # Pridėtas naujas matas
    }
}

updated_model = model_service.update_model(model_id, update_data)
if updated_model:
    print(f"Modelis atnaujintas: {updated_model.performance_metrics}")
else:
    print("Nepavyko atnaujinti modelio!")

# Gaukime visų modelių sąrašą
all_models = model_service.list_models()
print(f"Iš viso turime {len(all_models)} modelius:")
for m in all_models:
    print(f"- {m.name} ({m.id})")

# Uždarome sesiją kai baigėme
session.close()
```

## 2. Simuliacijos sukūrimas ir naudojimas

Šis pavyzdys parodo, kaip sukurti simuliaciją naudojant esamą modelį ir kaip atnaujinti simuliacijos duomenis.

```python
# Importuojame reikalingas bibliotekas
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService
from services.simulation_service import SimulationService

# Prisijungiame prie duomenų bazės
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame servisus
model_service = ModelService(session)
simulation_service = SimulationService(session)

# Pirma turime rasti modelį, kurį naudosime simuliacijai
# Imame pirmą modelį iš sąrašo (paprastai būtų konkrečiai pasirinktas)
models = model_service.list_models(limit=1)
if not models:
    print("Nėra modelių duomenų bazėje! Pirmiausia sukurkite modelį.")
    session.close()
    exit()

selected_model = models[0]
print(f"Naudojamas modelis: {selected_model.name} ({selected_model.id})")

# Sugeneruojame unikalų ID simuliacijai
simulation_id = str(uuid.uuid4())

# Nustatome simuliacijos laiko rėžius
start_date = datetime.now(timezone.utc) - timedelta(days=30)  # Prieš 30 dienų
end_date = datetime.now(timezone.utc)  # Dabar

# Sukuriame simuliacijos duomenis
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
simulation = simulation_service.create_simulation(simulation_data)

if simulation:
    print(f"Sėkmingai sukurta simuliacija: ID = {simulation.id}, Pavadinimas = {simulation.name}")
else:
    print("Nepavyko sukurti simuliacijos!")
    session.close()
    exit()

# Gaukime simuliaciją pagal ID
retrieved_simulation = simulation_service.get_simulation(simulation_id)
if retrieved_simulation:
    print(f"Rasta simuliacija: {retrieved_simulation.name}")
    print(f"Pradinis kapitalas: {retrieved_simulation.initial_capital} USD")
    print(f"Galutinis balansas: {retrieved_simulation.final_balance} USD")
    print(f"Pelnas/nuostolis: {retrieved_simulation.profit_loss} USD ({retrieved_simulation.roi * 100}%)")
else:
    print(f"Simuliacija su ID {simulation_id} nerasta!")

# Atnaujinkime simuliacijos duomenis (pvz., pakoreguojame metrikos)
update_data = {
    "final_balance": 11600.0,  # Patikslintas galutinis balansas
    "profit_loss": 1600.0,     # Patikslintas pelnas
    "roi": 0.16                # Patikslinta ROI
}

updated_simulation = simulation_service.update_simulation(simulation_id, update_data)
if updated_simulation:
    print(f"Simuliacija atnaujinta: Pelnas/nuostolis = {updated_simulation.profit_loss} USD")
else:
    print("Nepavyko atnaujinti simuliacijos!")

# Gaukime visų simuliacijų sąrašą
all_simulations = simulation_service.list_simulations()
print(f"Iš viso turime {len(all_simulations)} simuliacijas:")
for s in all_simulations:
    print(f"- {s.name} ({s.id}): Pelnas/nuostolis: {s.profit_loss} USD")

# Uždarome sesiją kai baigėme
session.close()
```

## 3. Simuliacijos rezultatų analizė

Šis pavyzdys parodo, kaip analizuoti simuliacijos rezultatus ir susijusius prekybos sandorius.

```python
# Importuojame reikalingas bibliotekas
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.simulation_service import SimulationService
from services.trade_service import TradeService

# Prisijungiame prie duomenų bazės
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame servisus
simulation_service = SimulationService(session)
trade_service = TradeService(session)

# Gaukime visų simuliacijų sąrašą
simulations = simulation_service.list_simulations()
if not simulations:
    print("Nėra simuliacijų duomenų bazėje! Pirmiausia sukurkite simuliaciją.")
    session.close()
    exit()

# Pasirinkime pirmą simuliaciją analizei
selected_simulation = simulations[0]
print(f"Analizuojama simuliacija: {selected_simulation.name} ({selected_simulation.id})")

# Pagrindinė simuliacijos informacija
print("\n=== SIMULIACIJOS REZULTATAI ===")
print(f"Pradinis kapitalas: {selected_simulation.initial_capital} USD")
print(f"Galutinis balansas: {selected_simulation.final_balance} USD")
print(f"Bendras pelnas/nuostolis: {selected_simulation.profit_loss} USD")
print(f"Grąža (ROI): {selected_simulation.roi * 100:.2f}%")
print(f"Maksimalus nuosmukis: {selected_simulation.max_drawdown * 100:.2f}%")
print(f"Sandorių skaičius: {selected_simulation.total_trades}")
print(f"Pelningų sandorių: {selected_simulation.winning_trades} ({selected_simulation.winning_trades / selected_simulation.total_trades * 100:.2f}%)")
print(f"Nuostolingų sandorių: {selected_simulation.losing_trades} ({selected_simulation.losing_trades / selected_simulation.total_trades * 100:.2f}%)")

# Dabar sukurkime keletą prekybos sandorių šiai simuliacijai analizei
# Simuliacijos pradžios ir pabaigos datos
start_date = selected_simulation.start_date
end_date = selected_simulation.end_date

# Laiko intervalai simuliacijos metu
days_between = (end_date - start_date).days
if days_between <= 0:
    days_between = 30  # Naudokime numatytąją reikšmę, jei neteisinga

# Sukurkime kelis pavyzdinius sandorius
# Pirmasis sandoris - pirkimas
buy_trade_data = {
    "portfolio_id": 1,
    "trade_type": "market",
    "btc_amount": 0.2,
    "price": 30000.0,
    "value": 6000.0,  # 0.2 BTC * 30000 USD = 6000 USD
    "timestamp": start_date + timedelta(days=1),
    "simulation_id": selected_simulation.id,
    "date": start_date + timedelta(days=1),
    "type": "buy",
    "amount": 0.2,
    "fee": 6.0,  # 0.1% nuo 6000 USD = 6 USD
    "created_at": datetime.now(timezone.utc)
}

buy_trade = trade_service.create_trade(buy_trade_data)
if buy_trade:
    print(f"\nSukurtas pirkimo sandoris: ID = {buy_trade.id}, Kiekis = {buy_trade.btc_amount} BTC, Kaina = {buy_trade.price} USD")
else:
    print("Nepavyko sukurti pirkimo sandorio!")

# Antrasis sandoris - pardavimas
sell_trade_data = {
    "portfolio_id": 1,
    "trade_type": "market",
    "btc_amount": 0.2,
    "price": 32000.0,
    "value": 6400.0,  # 0.2 BTC * 32000 USD = 6400 USD
    "timestamp": start_date + timedelta(days=10),
    "simulation_id": selected_simulation.id,
    "date": start_date + timedelta(days=10),
    "type": "sell",
    "amount": 0.2,
    "fee": 6.4,  # 0.1% nuo 6400 USD = 6.4 USD
    "profit_loss": 387.6,  # (6400 - 6000) - (6 + 6.4) = 387.6 USD
    "created_at": datetime.now(timezone.utc)
}

sell_trade = trade_service.create_trade(sell_trade_data)
if sell_trade:
    print(f"Sukurtas pardavimo sandoris: ID = {sell_trade.id}, Kiekis = {sell_trade.btc_amount} BTC, Kaina = {sell_trade.price} USD")
else:
    print("Nepavyko sukurti pardavimo sandorio!")

# Gaukime visus simuliacijos prekybos sandorius
simulation_trades = simulation_service.get_simulation_trades(selected_simulation.id)
print(f"\n=== PREKYBOS SANDORIAI (viso: {len(simulation_trades)}) ===")

# Atspausdinkime sandorius
total_profit = 0.0
for i, trade in enumerate(simulation_trades, 1):
    profit_text = f", Pelnas/nuostolis: {trade.profit_loss} USD" if trade.profit_loss else ""
    print(f"{i}. {trade.date.strftime('%Y-%m-%d')}: {trade.type.upper()} {trade.btc_amount} BTC @ {trade.price} USD{profit_text}")

    # Skaičiuojame bendrą pelną
    if trade.profit_loss:
        total_profit += trade.profit_loss

print(f"\nBendras apskaičiuotas sandorių pelnas/nuostolis: {total_profit} USD")

# Analizuokime pirkimo ir pardavimo kainas
buy_trades = [t for t in simulation_trades if t.type == 'buy']
sell_trades = [t for t in simulation_trades if t.type == 'sell']

avg_buy_price = sum(t.price for t in buy_trades) / len(buy_trades) if buy_trades else 0
avg_sell_price = sum(t.price for t in sell_trades) / len(sell_trades) if sell_trades else 0

print(f"\n=== KAINŲ ANALIZĖ ===")
print(f"Vidutinė pirkimo kaina: {avg_buy_price:.2f} USD")
print(f"Vidutinė pardavimo kaina: {avg_sell_price:.2f} USD")
print(f"Kainų skirtumas: {avg_sell_price - avg_buy_price:.2f} USD ({(avg_sell_price - avg_buy_price) / avg_buy_price * 100 if avg_buy_price else 0:.2f}%)")

# Uždarome sesiją kai baigėme
session.close()
```

## 4. Simuliacijų, modelių ir sandorių trynimas

Šis pavyzdys parodo, kaip saugiai ištrinti simuliacijas, modelius ir sandorius, naudojant kaskadinį trynimą.

```python
# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import logging

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService
from services.simulation_service import SimulationService
from services.trade_service import TradeService
from database.helper_functions import safe_delete_simulation

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prisijungiame prie duomenų bazės
engine = create_engine(SQLALCHEMY_DATABASE_URL)
session = Session(engine)

# Inicializuojame servisus
model_service = ModelService(session)
simulation_service = SimulationService(session)
trade_service = TradeService(session)

# 1. SIMULIACIJOS IŠTRYNIMAS
# =========================
print("\n=== SIMULIACIJOS IŠTRYNIMAS ===")

# Gaukime simuliacijų sąrašą
simulations = simulation_service.list_simulations()
if not simulations:
    print("Nėra simuliacijų duomenų bazėje, kurias būtų galima ištrinti!")
else:
    # Pasirenkami simuliaciją, kurią ištrinsime
    simulation_to_delete = simulations[0]  # Imame pirmą simuliaciją iš sąrašo
    print(f"Pasirinkta ištrinti simuliacija: {simulation_to_delete.name} ({simulation_to_delete.id})")

    # Prieš ištrinant, patikrinkime susijusius sandorius
    related_trades = simulation_service.get_simulation_trades(simulation_to_delete.id)
    print(f"Simuliacija turi {len(related_trades)} susijusius sandorius, kurie taip pat bus ištrinti")

    # Ištrinkime simuliaciją naudodami servisą (kuris naudoja saugų trynimo metodą)
    deletion_result = simulation_service.delete_simulation(simulation_to_delete.id)

    if deletion_result:
        print(f"Simuliacija {simulation_to_delete.id} sėkmingai ištrinta!")

        # Patikrinkime, ar neliko susijusių sandorių
        remaining_trades = trade_service.list_trades(simulation_id=simulation_to_delete.id)
        if not remaining_trades:
            print("Visi susiję sandoriai taip pat ištrinti (kaskadinis trynimas veikia)")
        else:
            print(f"ĮSPĖJIMAS: Vis dar yra {len(remaining_trades)} susijusių sandorių!")
    else:
        print(f"Nepavyko ištrinti simuliacijos {simulation_to_delete.id}")

# 2. MODELIO IŠTRYNIMAS
# ====================
print("\n=== MODELIO IŠTRYNIMAS ===")

# Gaukime modelių sąrašą
models = model_service.list_models()
if not models:
    print("Nėra modelių duomenų bazėje, kuriuos būtų galima ištrinti!")
else:
    # Pasirenkame modelį, kurį ištrinsime
    model_to_delete = models[0]  # Imame pirmą modelį iš sąrašo
    print(f"Pasirinktas ištrinti modelis: {model_to_delete.name} ({model_to_delete.id})")

    # Prieš ištrinant, patikrinkime susijusias simuliacijas
    related_simulations = simulation_service.list_simulations(model_id=model_to_delete.id)
    print(f"Modelis turi {len(related_simulations)} susijusias simuliacijas, kurios taip pat bus ištrintos")

    # Ištrinkime modelį naudodami servisą
    deletion_result = model_service.delete_model(model_to_delete.id)

    if deletion_result:
        print(f"Modelis {model_to_delete.id} sėkmingai ištrintas!")

        # Patikrinkime, ar neliko susijusių simuliacijų
        remaining_simulations = simulation_service.list_simulations(model_id=model_to_delete.id)
        if not remaining_simulations:
            print("Visos susijusios simuliacijos taip pat ištrintos (kaskadinis trynimas veikia)")
        else:
            print(f"ĮSPĖJIMAS: Vis dar yra {len(remaining_simulations)} susijusių simuliacijų!")
    else:
        print(f"Nepavyko ištrinti modelio {model_to_delete.id}")

# 3. TIESIOGINIS SANDORIO IŠTRYNIMAS
# =================================
print("\n=== SANDORIO IŠTRYNIMAS ===")

# Gaukime sandorių sąrašą
trades = trade_service.list_trades()
if not trades:
    print("Nėra sandorių duomenų bazėje, kuriuos būtų galima ištrinti!")
else:
    # Pasirenkame sandorį, kurį ištrinsime
    trade_to_delete = trades[0]  # Imame pirmą sandorį iš sąrašo
    print(f"Pasirinktas ištrinti sandoris: ID = {trade_to_delete.id}, Tipas = {trade_to_delete.type}, Kaina = {trade_to_delete.price} USD")

    # Ištrinkime sandorį naudodami servisą
    deletion_result = trade_service.delete_trade(trade_to_delete.id)

    if deletion_result:
        print(f"Sandoris {trade_to_delete.id} sėkmingai ištrintas!")

        # Patikrinkime, ar sandoris tikrai ištrintas
        if not trade_service.get_trade(trade_to_delete.id):
            print("Patvirtinta: sandoris ištrintas iš duomenų bazės")
        else:
            print("ĮSPĖJIMAS: Sandoris vis dar egzistuoja duomenų bazėje!")
    else:
        print(f"Nepavyko ištrinti sandorio {trade_to_delete.id}")

# Uždarome sesiją kai baigėme
session.close()
```

## 3.2-3.5 Sukurti Python pavyzdžio failus

Sukursiu keletą Python failų su naudojimo pavyzdžiais:

### [D:\CA_BTC\examples\model_example.py](D:\CA_BTC\examples\model_example.py)

```python
"""
Modelio sukūrimo ir naudojimo pavyzdys.
"""
import uuid
import sys
import os
import logging
from datetime import datetime, timezone

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.model_service import ModelService

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
        # Inicializuojame modelio servisą
        logger.info("Inicializuojamas ModelService")
        model_service = ModelService(session)

        # Sugeneruojame unikalų ID modeliui
        model_id = str(uuid.uuid4())
        logger.info(f"Sugeneruotas modelio ID: {model_id}")

        # Sukuriame modelio duomenis
        logger.info("Ruošiami modelio duomenys")
        model_data = {
            "id": model_id,
            "name": "LSTM modelis",
            "description": "Ilgosios trumpalaikės atminties modelis Bitcoin kainos prognozavimui",
            "type": "lstm",
            "hyperparameters": {
                "epochs": 100,
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

        # Sukuriame modelį
        logger.info("Kuriamas naujas modelis")
        model = model_service.create_model(model_data)

        if model:
            logger.info(f"Sėkmingai sukurtas modelis: ID = {model.id}, Pavadinimas = {model.name}")
        else:
            logger.error("Nepavyko sukurti modelio!")
            return

        # Gaukime modelį pagal ID
        logger.info(f"Gaunamas modelis pagal ID: {model_id}")
        retrieved_model = model_service.get_model(model_id)

        if retrieved_model:
            logger.info(f"Rastas modelis: {retrieved_model.name}, tipas: {retrieved_model.type}")
            logger.info(f"Hiperparametrai: {retrieved_model.hyperparameters}")
        else:
            logger.error(f"Modelis su ID {model_id} nerastas!")
            return

        # Atnaujinkime modelio veikimo metrikas
        logger.info("Ruošiami modelio atnaujinimo duomenys")
        update_data = {
            "performance_metrics": {
                "accuracy": 0.88,  # Pagerintas tikslumas
                "loss": 0.10,      # Sumažintas nuostolis
                "f1_score": 0.86   # Pridėtas naujas matas
            }
        }

        logger.info(f"Atnaujinamas modelis su ID: {model_id}")
        updated_model = model_service.update_model(model_id, update_data)

        if updated_model:
            logger.info(f"Modelis atnaujintas: {updated_model.performance_metrics}")
        else:
            logger.error("Nepavyko atnaujinti modelio!")
            return

        # Gaukime visų modelių sąrašą
        logger.info("Gaunamas visų modelių sąrašas")
        all_models = model_service.list_models()

        logger.info(f"Iš viso turime {len(all_models)} modelius:")
        for m in all_models:
            logger.info(f"- {m.name} ({m.id})")

    except Exception as e:
        logger.error(f"Įvyko klaida vykdant pavyzdį: {str(e)}")
    finally:
        # Uždarome sesiją kai baigėme
        logger.info("Uždaroma duomenų bazės sesija")
        session.close()

if __name__ == "__main__":
    main()
```
