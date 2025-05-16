"""
Trend Following strategija
-----------------------------
Šis modulis realizuoja prekybos strategiją, kuri remiasi
tendencijų sekimo principu.
"""

import numpy as np
import pandas as pd
import logging
from simulator.strategies.base_strategy import TradingStrategy

logger = logging.getLogger(__name__)

class TrendFollowingStrategy(TradingStrategy):
    """
    Tendencijų sekimo strategija, kuri perka, kai formauojasi kylanti
    tendencija, ir parduoda, kai formauojasi krentanti tendencija.
    """
    def __init__(self, cooldown_periods=5, name=None):
        """
        Inicializuoja tendencijų sekimo strategiją.
        
        Args:
            cooldown_periods (int): Laikotarpių skaičius po sandorio prieš naują sandorį
            name (str, optional): Strategijos pavadinimas
        """
        super().__init__(name=name or "TrendFollowingStrategy")
        
        self.cooldown_periods = cooldown_periods
        self.last_trade_time = None
        self.trade_cooldown_counter = 0
        
        logger.info(f"Inicializuota TrendFollowingStrategy strategija, cooldown_periods={cooldown_periods}")
    
    def generate_decision(self, signals, current_data, portfolio, timestamp):
        """
        Sugeneruoja prekybos sprendimą pagal tendencijų sekimo logiką.
        
        Args:
            signals (list): Signalų sąrašas
            current_data (pandas.Series): Dabartiniai duomenys
            portfolio: Portfelio objektas
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Prekybos sprendimas
        """
        # Jei esame atvėsimo periodu, nesiūlome jokio sprendimo
        if self.trade_cooldown_counter > 0:
            self.trade_cooldown_counter -= 1
            return None
        
        # Jei nėra signalų, negalime priimti sprendimo
        if not signals:
            return None
        
        # Gauname dabartinę kainą
        current_price = current_data["Close"]
        
        # Apskaičiuojame bendrą signalo reikšmę (svertinį vidurkį visų signalų)
        total_signal_value = 0
        total_signal_strength = 0
        
        for signal in signals:
            # Tikriname, ar signalas turi reikšmę ir stiprumą
            if "value" in signal and "strength" in signal:
                total_signal_value += signal["value"] * signal["strength"]
                total_signal_strength += signal["strength"]
        
        # Jei nėra signalų su reikšme ir stiprumu, negalime priimti sprendimo
        if total_signal_strength == 0:
            return None
        
        # Apskaičiuojame bendrą signalo reikšmę
        avg_signal_value = total_signal_value / total_signal_strength
        
        # Defoltinis sprendimas - laikyti
        decision = {
            "action": "hold",
            "price": current_price,
            "timestamp": timestamp,
            "strategy": self.name,
            "signal_value": avg_signal_value
        }
        
        # Jei bendras signalas stipriai teigiamas ir turime pinigų, perkame
        if avg_signal_value > 0.5 and portfolio.balance > 0:
            decision["action"] = "buy"
            
            # Pirkimo dydis - 30% portfelio
            amount_to_spend = portfolio.balance * 0.3
            decision["amount"] = amount_to_spend / current_price
            
            # Nustatome atvėsimo periodą
            self.trade_cooldown_counter = self.cooldown_periods
            
            logger.info(f"TrendFollowingStrategy: sugeneruotas pirkimo sprendimas (signal_value={avg_signal_value:.2f})")
        
        # Jei bendras signalas stipriai neigiamas ir turime BTC, parduodame
        elif avg_signal_value < -0.5 and portfolio.btc_amount > 0:
            decision["action"] = "sell"
            
            # Pardavimo dydis - 50% turimų BTC
            decision["amount"] = portfolio.btc_amount * 0.5
            
            # Nustatome atvėsimo periodą
            self.trade_cooldown_counter = self.cooldown_periods
            
            logger.info(f"TrendFollowingStrategy: sugeneruotas pardavimo sprendimas (signal_value={avg_signal_value:.2f})")
        
        return decision