import random
import uuid
import json
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TestDataGenerator:
    """
    Klasė testiniams duomenims generuoti
    Sukuria atsitiktinius duomenis testavimui
    """
    
    def __init__(self, seed=42):
        """
        Inicializuoja generatorių
        
        Args:
            seed (int): Atsitiktinių skaičių generatoriaus sėkla
        """
        # Nustatome atsitiktinių skaičių generatorių, kad rezultatai būtų atkuriami
        random.seed(seed)
        np.random.seed(seed)
        
        # Pradinis laiko momentas duomenims (2023-01-01)
        self.base_date = datetime(2023, 1, 1)
        
        # Kainų intervalas (Bitcoin kainos tarp 10,000 ir 50,000)
        self.price_min = 10000.0
        self.price_max = 50000.0
        
        # Galimi laiko intervalai
        self.intervals = ['1h', '4h', '1d', '1w']
        
        # Prekybos strategijų tipai
        self.strategy_types = ['ma_cross', 'rsi', 'macd', 'bollinger', 'ml_based']
        
        # Modelių ID sąrašas (atsitiktinai sugeneruoti UUID)
        self.model_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        # Metrikų pavadinimai
        self.metric_names = ['accuracy', 'precision', 'recall', 'f1_score', 'mae', 'mse', 'rmse']
    
    def generate_random_uuid(self):
        """
        Generuoja atsitiktinį UUID
        
        Returns:
            str: UUID eilutė
        """
        return str(uuid.uuid4())
    
    def generate_random_date(self, start_days=0, end_days=365):
        """
        Generuoja atsitiktinę datą
        
        Args:
            start_days (int): Dienų skaičius nuo bazinės datos pradžios
            end_days (int): Dienų skaičius nuo bazinės datos pabaigos
            
        Returns:
            datetime: Atsitiktinė data
        """
        days = random.randint(start_days, end_days)
        return self.base_date + timedelta(days=days)
    
    def generate_random_price(self):
        """
        Generuoja atsitiktinę kainą
        
        Returns:
            float: Atsitiktinė kaina
        """
        return random.uniform(self.price_min, self.price_max)
    
    def generate_prediction(self, model_id=None, with_actual=True):
        """
        Generuoja atsitiktinę prognozę
        
        Args:
            model_id (str, optional): Modelio ID
            with_actual (bool): Ar pridėti faktinę vertę
            
        Returns:
            dict: Prognozės duomenys
        """
        # Jei nenurodytas modelio ID, pasirenkame atsitiktinį
        if model_id is None:
            model_id = random.choice(self.model_ids)
            
        # Generuojame prognozes datos
        prediction_date = self.generate_random_date(0, 300)
        
        # Prognozuojama data yra 1-30 dienų vėliau
        target_days = random.randint(1, 30)
        target_date = prediction_date + timedelta(days=target_days)
        
        # Generuojame prognozuojamą vertę
        predicted_value = self.generate_random_price()
        
        # Faktinė vertė su nedidele paklaida (jei reikia)
        actual_value = None
        if with_actual and target_date < datetime.now():
            error_percent = random.uniform(-0.1, 0.1)  # ±10% paklaida
            actual_value = predicted_value * (1 + error_percent)
            
        # Pasirenkame atsitiktinį intervalą
        interval = random.choice(self.intervals)
        
        # Generuojame pasitikėjimo lygį (0.5-1.0)
        confidence = random.uniform(0.5, 1.0)
        
        # Formuojame prognozės duomenis
        return {
            'id': self.generate_random_uuid(),
            'model_id': model_id,
            'prediction_date': prediction_date,
            'target_date': target_date,
            'predicted_value': predicted_value,
            'actual_value': actual_value,
            'interval': interval,
            'confidence': confidence,
            'created_at': prediction_date
        }
    
    def generate_simulation(self):
        """
        Generuoja atsitiktinę simuliaciją
        
        Returns:
            dict: Simuliacijos duomenys
        """
        # Generuojame pradžios datą
        start_date = self.generate_random_date(0, 300)
        
        # Simuliacijos trukmė (10-90 dienų)
        duration_days = random.randint(10, 90)
        end_date = start_date + timedelta(days=duration_days)
        
        # Pasirenkame atsitiktinę strategiją
        strategy_type = random.choice(self.strategy_types)
        
        # Generuojame strategijos parametrus
        strategy_params = {
            'param1': random.uniform(5, 50),
            'param2': random.uniform(10, 100),
            'threshold': random.uniform(0.01, 0.1)
        }
        
        # Pradinis kapitalas
        initial_capital = random.uniform(1000.0, 10000.0)
        
        # Komisiniai mokesčiai
        fees = random.uniform(0.001, 0.005)
        
        # Generuojame rezultatų metrikas
        # ROI tarp -30% ir +100%
        roi = random.uniform(-0.3, 1.0)
        final_balance = initial_capital * (1 + roi)
        profit_loss = final_balance - initial_capital
        
        # Maksimalus nuosmukis (1-25%)
        max_drawdown = random.uniform(0.01, 0.25)
        
        # Sandorių skaičiai
        total_trades = random.randint(10, 200)
        win_rate = random.uniform(0.3, 0.7)
        winning_trades = int(total_trades * win_rate)
        losing_trades = total_trades - winning_trades
        
        # Formuojame simuliacijos duomenis
        return {
            'id': self.generate_random_uuid(),
            'name': f"Sim_{strategy_type}_{start_date.strftime('%Y%m%d')}",
            'initial_capital': initial_capital,
            'fees': fees,
            'start_date': start_date,
            'end_date': end_date,
            'strategy_type': strategy_type,
            'strategy_params': json.dumps(strategy_params),
            'final_balance': final_balance,
            'profit_loss': profit_loss,
            'roi': roi * 100,  # ROI procentais
            'max_drawdown': max_drawdown * 100,  # Nuosmukis procentais
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'is_completed': True,
            'created_at': start_date,
            'updated_at': end_date
        }
    
    def generate_trade(self, simulation_id):
        """
        Generuoja atsitiktinį sandorį
        
        Args:
            simulation_id (str): Simuliacijos ID
            
        Returns:
            dict: Sandorio duomenys
        """
        # Prekybos data
        trade_date = self.generate_random_date(0, 365)
        
        # Prekybos tipas (pirkimas arba pardavimas)
        trade_type = random.choice(['buy', 'sell'])
        
        # Prekybos kaina
        price = self.generate_random_price()
        
        # Prekybos kiekis
        amount = random.uniform(0.01, 1.0)
        
        # Prekybos vertė
        value = price * amount
        
        # Komisinis mokestis (0.1-0.5% nuo vertės)
        fee = value * random.uniform(0.001, 0.005)
        
        # Pelnas/nuostolis (tik pardavimo sandoriams)
        profit_loss = None
        if trade_type == 'sell':
            # Atsitiktinis pelnas arba nuostolis (-20% iki +20% nuo vertės)
            profit_loss = value * random.uniform(-0.2, 0.2)
        
        # Formuojame sandorio duomenis
        return {
            'id': self.generate_random_uuid(),
            'simulation_id': simulation_id,
            'date': trade_date,
            'type': trade_type,
            'price': price,
            'amount': amount,
            'value': value,
            'fee': fee,
            'profit_loss': profit_loss,
            'created_at': trade_date
        }
    
    def generate_metric(self, model_id=None, simulation_id=None):
        """
        Generuoja atsitiktinę metriką
        
        Args:
            model_id (str, optional): Modelio ID
            simulation_id (str, optional): Simuliacijos ID
            
        Returns:
            dict: Metrikos duomenys
        """
        # Turi būti nurodytas bent vienas: model_id arba simulation_id
        if model_id is None and simulation_id is None:
            model_id = random.choice(self.model_ids)
            
        # Pasirenkame atsitiktinį metrikos pavadinimą
        name = random.choice(self.metric_names)
        
        # Generuojame metrikos vertę (priklausomai nuo metrikos tipo)
        if name in ['accuracy', 'precision', 'recall', 'f1_score']:
            # Šios metrikos yra tarp 0 ir 1
            value = random.uniform(0.5, 1.0)
        else:
            # Klaidos metrikos (mažesnė vertė geriau)
            value = random.uniform(100.0, 5000.0)
            
        # Metrikos data
        metric_date = self.generate_random_date(0, 365)
        
        # Laikotarpis (dienų, savaičių, mėnesių)
        period = random.choice(['day', 'week', 'month'])
        
        # Formuojame metrikos duomenis
        return {
            'id': self.generate_random_uuid(),
            'name': name,
            'value': value,
            'model_id': model_id,
            'simulation_id': simulation_id,
            'period': period,
            'date': metric_date,
            'description': f"Test metric {name}",
            'created_at': metric_date
        }
    
    def generate_bulk_predictions(self, count, model_id=None):
        """
        Generuoja daug prognozių
        
        Args:
            count (int): Prognozių skaičius
            model_id (str, optional): Modelio ID
            
        Returns:
            list: Prognozių sąrašas
        """
        return [self.generate_prediction(model_id) for _ in range(count)]
    
    def generate_bulk_simulations(self, count):
        """
        Generuoja daug simuliacijų
        
        Args:
            count (int): Simuliacijų skaičius
            
        Returns:
            list: Simuliacijų sąrašas
        """
        return [self.generate_simulation() for _ in range(count)]
    
    def generate_simulation_with_trades(self, trades_count=50):
        """
        Generuoja simuliaciją su sandoriais
        
        Args:
            trades_count (int): Sandorių skaičius
            
        Returns:
            tuple: (simuliacija, sandoriai)
        """
        # Generuojame simuliaciją
        simulation = self.generate_simulation()
        
        # Generuojame sandorius
        trades = [self.generate_trade(simulation['id']) for _ in range(trades_count)]
        
        return (simulation, trades)
    
    def generate_model_with_predictions(self, model_id=None, predictions_count=100):
        """
        Generuoja modelio prognozes
        
        Args:
            model_id (str, optional): Modelio ID
            predictions_count (int): Prognozių skaičius
            
        Returns:
            tuple: (modelio ID, prognozės)
        """
        # Jei nenurodytas modelio ID, sugeneruojame naują
        if model_id is None:
            model_id = self.generate_random_uuid()
            
        # Generuojame prognozes
        predictions = self.generate_bulk_predictions(predictions_count, model_id)
        
        return (model_id, predictions)