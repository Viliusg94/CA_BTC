"""
Grįžimo prie vidurkio strategija
-----------------------------
Šis modulis realizuoja prekybos strategiją, kuri remiasi
grįžimo prie vidurkio principu.
"""

import numpy as np
import pandas as pd
import logging
from simulator.strategies.base_strategy import TradingStrategy

logger = logging.getLogger(__name__)

class MeanReversionStrategy(TradingStrategy):
    """
    Grįžimo prie vidurkio strategija, kuri perka, kai kaina pernelyg nukrinta,
    ir parduoda, kai kaina pernelyg pakyla.
    """
    def __init__(self, z_score_threshold=2.0, lookback_period=20, name=None):
        """
        Inicializuoja grįžimo prie vidurkio strategiją.
        
        Args:
            z_score_threshold (float): Z-score slenkstis signalams generuoti
            lookback_period (int): Laikotarpio ilgis vidurkiui skaičiuoti
            name (str, optional): Strategijos pavadinimas
        """
        super().__init__(name=name or "MeanReversionStrategy")
        
        self.z_score_threshold = z_score_threshold
        self.lookback_period = lookback_period
        
        logger.info(f"Inicializuota MeanReversionStrategy strategija, z_score_threshold={z_score_threshold}, lookback_period={lookback_period}")
    
    def generate_decision(self, signals, current_data, portfolio, timestamp):
        """
        Sugeneruoja prekybos sprendimą pagal grįžimo prie vidurkio principą.
        
        Args:
            signals (list): Signalų sąrašas
            current_data (pandas.Series): Dabartiniai duomenys
            portfolio: Portfelio objektas
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Prekybos sprendimas
        """
        # Jei nėra kainų duomenų, negalime priimti sprendimo
        if 'Close' not in current_data:
            return None
        
        # Gauname dabartinę kainą
        current_price = current_data['Close']
        
        # Jei yra skaičiuotas Z-score, naudojame jį
        if 'z_score' in current_data:
            z_score = current_data['z_score']
        else:
            # Kitaip skaičiuojame patys, jei turime istorinius duomenis
            if 'historical_data' in signals and len(signals['historical_data']) >= self.lookback_period:
                prices = signals['historical_data']['Close'].tail(self.lookback_period)
                mean = prices.mean()
                std = prices.std()
                z_score = (current_price - mean) / std if std > 0 else 0
            else:
                return None
        
        # Defoltinis sprendimas - laikyti
        decision = {
            'action': 'hold',
            'price': current_price,
            'timestamp': timestamp,
            'strategy': self.name
        }
        
        # Jei kaina pernelyg aukšta (Z > threshold), parduodame
        if z_score > self.z_score_threshold and portfolio.btc_amount > 0:
            decision['action'] = 'sell'
            
            # Pardavimo dydis - visas BTC kiekis
            decision['amount'] = portfolio.btc_amount
            
            logger.info(f"MeanReversionStrategy: sugeneruotas pardavimo sprendimas (z_score={z_score:.2f})")
        
        # Jei kaina pernelyg žema (Z < -threshold), perkame
        elif z_score < -self.z_score_threshold and portfolio.balance > 0:
            decision['action'] = 'buy'
            
            # Pirkimo dydis - 20% portfelio
            amount_to_spend = portfolio.balance * 0.2
            decision['amount'] = amount_to_spend / current_price
            
            logger.info(f"MeanReversionStrategy: sugeneruotas pirkimo sprendimas (z_score={z_score:.2f})")
        
        return decision