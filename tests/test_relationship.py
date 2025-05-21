"""
Duomenų bazės ryšių testavimas.
"""
import os
import sys
import unittest
import uuid
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importuojame tik tas klases, kurios egzistuoja
from database.models.models import Model
from database.models.results_models import Simulation, Trade

# Konfigūruojame logerį
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDatabaseRelationships(unittest.TestCase):
    """
    Testai duomenų bazės ryšių patikrinimui
    """
    
    def setUp(self):
        """
        Paruošia testų aplinką - sukuria duomenų bazės sesiją ir pradinius objektus
        """
        # Sukuriame duomenų bazės sesiją
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        self.session = Session(self.engine)
        
        # Tikriname lentelių schemą
        inspector = inspect(self.engine)
        
        # Patikriname, ar egzistuoja reikalingos lentelės
        tables = inspector.get_table_names()
        required_tables = ["models", "simulations", "trades"]
        
        for table in required_tables:
            self.assertIn(table, tables, f"Lentelė '{table}' nerasta duomenų bazėje")
            
        # Sukuriame testinį modelį
        self.model_id = str(uuid.uuid4())
        self.test_model = Model(
            id=self.model_id,
            name="Testinis modelis",
            description="Modelis sukurtas testavimo tikslais",
            type="test",
            hyperparameters={"test_param": 1},
            input_features=["price", "volume"],
            performance_metrics={"accuracy": 0.9},
            created_at=datetime.now(timezone.utc)
        )
        
        # Sukuriame testinę simuliaciją
        self.simulation_id = str(uuid.uuid4())
        self.test_simulation = Simulation(
            id=self.simulation_id,
            name="Testinė simuliacija",
            model_id=self.model_id,
            initial_capital=10000.0,
            fees=0.1,
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc),
            strategy_type="test",
            strategy_params="{}",
            final_balance=11000.0,
            profit_loss=1000.0,
            roi=0.1,
            max_drawdown=0.05,
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            is_completed=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Sukuriame testinį sandorį
        self.test_trade = Trade(
            portfolio_id=1,
            trade_type="market",
            btc_amount=0.1,
            price=30000.0,
            value=3000.0,
            timestamp=datetime.now(timezone.utc),
            simulation_id=self.simulation_id,
            date=datetime.now(timezone.utc),
            type="buy",
            amount=0.1,
            fee=3.0,
            created_at=datetime.now(timezone.utc)
        )
        
        # Išsaugome objektus duomenų bazėje
        self.session.add(self.test_model)
        self.session.commit()
        
        self.session.add(self.test_simulation)
        self.session.commit()
        
        self.session.add(self.test_trade)
        self.session.commit()
        
        logger.info("Testiniai duomenys sukurti sėkmingai")
    
    def tearDown(self):
        """
        Išvalo testų aplinką - ištrina testinius duomenis ir uždaro sesiją
        """
        # Ištriname testinius duomenis atvirkštine tvarka
        try:
            # Ištriname sandorį
            self.session.query(Trade).filter(Trade.simulation_id == self.simulation_id).delete()
            
            # Ištriname simuliaciją
            self.session.query(Simulation).filter(Simulation.id == self.simulation_id).delete()
            
            # Ištriname modelį
            self.session.query(Model).filter(Model.id == self.model_id).delete()
            
            # Įrašome pakeitimus
            self.session.commit()
            logger.info("Testiniai duomenys ištrinti sėkmingai")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Klaida trinant testinius duomenis: {str(e)}")
        finally:
            # Uždarome sesiją
            self.session.close()
    
    def test_model_to_simulation_relationship(self):
        """
        Testuoja ryšį tarp Model ir Simulation lentelių
        """
        # Gaukime modelį iš duomenų bazės
        model = self.session.query(Model).filter(Model.id == self.model_id).first()
        self.assertIsNotNone(model, "Modelis nerastas duomenų bazėje")
        
        # Patikrinkime, ar galime gauti susijusias simuliacijas
        if hasattr(model, 'simulations'):
            simulations = model.simulations
            self.assertGreaterEqual(len(simulations), 1, "Nerastos su modeliu susijusios simuliacijos")
            self.assertEqual(simulations[0].id, self.simulation_id, "Simuliacijos ID nesutampa")
            logger.info(f"Modelis '{model.name}' turi {len(simulations)} simuliaciją (-as)")
        else:
            self.fail("Modelis neturi 'simulations' atributo")
    
    def test_simulation_to_model_relationship(self):
        """
        Testuoja ryšį tarp Simulation ir Model lentelių
        """
        # Gaukime simuliaciją iš duomenų bazės
        simulation = self.session.query(Simulation).filter(Simulation.id == self.simulation_id).first()
        self.assertIsNotNone(simulation, "Simuliacija nerasta duomenų bazėje")
        
        # Patikrinkime, ar galime gauti susijusį modelį
        if hasattr(simulation, 'model'):
            model = simulation.model
            self.assertIsNotNone(model, "Nerastas su simuliacija susijęs modelis")
            self.assertEqual(model.id, self.model_id, "Modelio ID nesutampa")
            logger.info(f"Simuliacija '{simulation.name}' susieta su modeliu '{model.name}'")
        else:
            self.fail("Simuliacija neturi 'model' atributo")
    
    def test_simulation_to_trade_relationship(self):
        """
        Testuoja ryšį tarp Simulation ir Trade lentelių
        """
        # Gaukime simuliaciją iš duomenų bazės
        simulation = self.session.query(Simulation).filter(Simulation.id == self.simulation_id).first()
        self.assertIsNotNone(simulation, "Simuliacija nerasta duomenų bazėje")
        
        # Patikrinkime, ar galime gauti susijusius sandorius
        if hasattr(simulation, 'trades'):
            trades = simulation.trades
            self.assertGreaterEqual(len(trades), 1, "Nerasti su simuliacija susiję sandoriai")
            self.assertEqual(trades[0].simulation_id, self.simulation_id, "Sandorio simulation_id nesutampa")
            logger.info(f"Simuliacija '{simulation.name}' turi {len(trades)} sandorį (-ius)")
        else:
            self.fail("Simuliacija neturi 'trades' atributo")
    
    def test_trade_to_simulation_relationship(self):
        """
        Testuoja ryšį tarp Trade ir Simulation lentelių
        """
        # Gaukime sandorį iš duomenų bazės
        trade = self.session.query(Trade).filter(Trade.simulation_id == self.simulation_id).first()
        self.assertIsNotNone(trade, "Sandoris nerastas duomenų bazėje")
        
        # Patikrinkime, ar galime gauti susijusią simuliaciją
        if hasattr(trade, 'simulation'):
            simulation = trade.simulation
            self.assertIsNotNone(simulation, "Nerasta su sandoriu susijusi simuliacija")
            self.assertEqual(simulation.id, self.simulation_id, "Simuliacijos ID nesutampa")
            logger.info(f"Sandoris ID={trade.id} susietas su simuliacija '{simulation.name}'")
        else:
            self.fail("Sandoris neturi 'simulation' atributo")
    
    def test_cascade_delete_simulation(self):
        """
        Testuoja kaskadinio trynimo veikimą tarp Simulation ir Trade lentelių
        """
        # Patikriname, ar yra sandorių prieš ištrinant simuliaciją
        trades_before = self.session.query(Trade).filter(Trade.simulation_id == self.simulation_id).count()
        self.assertGreater(trades_before, 0, "Nerasta su simuliacija susijusių sandorių")
        
        try:
            # Ištriname simuliaciją
            simulation = self.session.query(Simulation).filter(Simulation.id == self.simulation_id).first()
            self.session.delete(simulation)
            self.session.commit()
            
            # Tikriname, ar sandoriai buvo ištrinti
            trades_after = self.session.query(Trade).filter(Trade.simulation_id == self.simulation_id).count()
            self.assertEqual(trades_after, 0, "Sandoriai nebuvo automatiškai ištrinti")
            
            logger.info("Kaskadinis trynimas veikia: ištrynus simuliaciją, sandoriai taip pat buvo ištrinti")
        except Exception as e:
            self.session.rollback()
            self.fail(f"Testas nepavyko dėl klaidos: {str(e)}")
    
    def test_cascade_delete_model(self):
        """
        Testuoja kaskadinio trynimo veikimą tarp Model ir Simulation lentelių
        """
        # Patikriname, ar yra simuliacijų prieš ištrinant modelį
        simulations_before = self.session.query(Simulation).filter(Simulation.model_id == self.model_id).count()
        self.assertGreater(simulations_before, 0, "Nerasta su modeliu susijusių simuliacijų")
        
        try:
            # Ištriname modelį
            model = self.session.query(Model).filter(Model.id == self.model_id).first()
            self.session.delete(model)
            self.session.commit()
            
            # Tikriname, ar simuliacijos buvo ištrintos
            simulations_after = self.session.query(Simulation).filter(Simulation.model_id == self.model_id).count()
            self.assertEqual(simulations_after, 0, "Simuliacijos nebuvo automatiškai ištrintos")
            
            # Tikriname, ar sandoriai buvo ištrinti (per simuliacijos trynimą)
            trades_after = self.session.query(Trade).filter(Trade.simulation_id == self.simulation_id).count()
            self.assertEqual(trades_after, 0, "Sandoriai nebuvo automatiškai ištrinti")
            
            logger.info("Kaskadinis trynimas veikia: ištrynus modelį, simuliacijos ir sandoriai taip pat buvo ištrinti")
        except Exception as e:
            self.session.rollback()
            self.fail(f"Testas nepavyko dėl klaidos: {str(e)}")

if __name__ == "__main__":
    unittest.main()