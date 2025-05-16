# filepath: d:\CA_BTC\simulator\strategies\machine_learning_strategy.py
"""
Mašininio mokymosi strategija
-----------------------------
Ši strategija naudoja mašininio mokymosi modelio prognozes 
prekybos sprendimams priimti.
"""
import numpy as np
import pandas as pd
import logging
from simulator.strategies.base_strategy import TradingStrategy

logger = logging.getLogger(__name__)

class MachineLearningStrategy(TradingStrategy):
    def __init__(self, prediction_col='predicted_direction', confidence_col='confidence', 
                 confidence_threshold=0.65, position_sizing='dynamic', name=None):
        """
        Inicializuoja mašininio mokymosi strategiją.
        
        Args:
            prediction_col (str): Stulpelio su kryptimi (1, -1) pavadinimas
            confidence_col (str): Stulpelio su pasitikėjimu (0-1) pavadinimas
            confidence_threshold (float): Pasitikėjimo slenkstis (0-1)
            position_sizing (str): Pozicijos dydžio strategija ('fixed', 'dynamic')
            name (str, optional): Strategijos pavadinimas
        """
        super().__init__(name=name or "MachineLearningStrategy")
        
        self.prediction_col = prediction_col
        self.confidence_col = confidence_col
        self.confidence_threshold = confidence_threshold
        self.position_sizing = position_sizing
        
        logger.info(f"Inicializuota MachineLearningStrategy: confidence_threshold={confidence_threshold}, position_sizing={position_sizing}")
    
    def generate_decision(self, signals, current_data, portfolio, timestamp):
        """
        Generuoja prekybos sprendimą pagal ML prognozes.
        
        Args:
            signals (list): Signalų sąrašas
            current_data (pandas.Series): Dabartiniai duomenys
            portfolio: Portfelio objektas
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Prekybos sprendimas
        """
        # Patikriname, ar yra reikalingi stulpeliai duomenyse
        if self.prediction_col not in current_data or self.confidence_col not in current_data:
            return None
        
        # Gauname dabartinę kainą
        current_price = current_data['Close']
        
        # Gauname prognozę ir pasitikėjimą iš duomenų
        prediction = current_data[self.prediction_col]
        confidence = current_data[self.confidence_col]
        
        # Defoltinis sprendimas - laikyti
        decision = {
            "action": "hold",
            "price": current_price,
            "timestamp": timestamp,
            "strategy": self.name,
            "prediction": prediction,
            "confidence": confidence
        }
        
        # Jei pasitikėjimas per mažas, laikome
        if confidence < self.confidence_threshold:
            return decision
        
        # Jei prognozė teigiama (kainų kilimas)
        if prediction == 1 and portfolio.balance > 0:
            decision["action"] = "buy"
            
            # Nustatome pirkimo dydį
            if self.position_sizing == 'fixed':
                # Fiksuoto dydžio - 20% portfelio
                amount_to_spend = portfolio.balance * 0.2
            else:  # 'dynamic'
                # Dinaminio dydžio - pagal pasitikėjimą (nuo 10% iki 30%)
                amount_pct = 0.1 + (confidence - self.confidence_threshold) * 0.5
                amount_to_spend = portfolio.balance * min(0.3, amount_pct)
            
            decision["amount"] = amount_to_spend / current_price
            
            logger.info(f"MachineLearningStrategy: sugeneruotas pirkimo sprendimas (prediction={prediction}, confidence={confidence:.2f})")
        
        # Jei prognozė neigiama (kainų kritimas)
        elif prediction == -1 and portfolio.btc_amount > 0:
            decision["action"] = "sell"
            
            # Nustatome pardavimo dydį
            if self.position_sizing == 'fixed':
                # Fiksuoto dydžio - 50% turimų BTC
                amount_pct = 0.5
            else:  # 'dynamic'
                # Dinaminio dydžio - pagal pasitikėjimą (nuo 30% iki 70%)
                amount_pct = 0.3 + (confidence - self.confidence_threshold) * 0.8
                amount_pct = min(0.7, amount_pct)
            
            decision["amount"] = portfolio.btc_amount * amount_pct
            
            logger.info(f"MachineLearningStrategy: sugeneruotas pardavimo sprendimas (prediction={prediction}, confidence={confidence:.2f})")
        
        return decision