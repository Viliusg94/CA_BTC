"""
Dinaminis rizikos reguliatorius
-----------------------------
Šis modulis realizuoja dinaminio rizikos reguliavimo funkcionalumą,
kuris automatiškai koreguoja rizikos parametrus pagal prekybos rezultatus.
"""

import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DynamicRiskAdjuster:
    """
    Dinaminio rizikos reguliavimo klasė, kuri koreguoja rizikos parametrus 
    pagal naujausius prekybos rezultatus.
    """
    def __init__(self, base_risk=0.02, min_risk=0.005, max_risk=0.05, adjustment_period=10):
        """
        Inicializuoja dinaminio rizikos reguliavimo komponentą.
        
        Args:
            base_risk (float): Bazinė rizika kaip dalis portfelio (0.02 = 2%)
            min_risk (float): Minimali rizika (0.005 = 0.5%)
            max_risk (float): Maksimali rizika (0.05 = 5%)
            adjustment_period (int): Po kiek sandorių reguliuoti riziką
        """
        self.base_risk = base_risk
        self.current_risk = base_risk
        self.min_risk = min_risk
        self.max_risk = max_risk
        self.adjustment_period = adjustment_period
        
        # Statistikai
        self.trades = []
        self.win_count = 0
        self.loss_count = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.total_profit = 0
        self.total_loss = 0
        
        logger.info(f"Inicializuotas dinaminis rizikos reguliatorius: base_risk={base_risk*100}%, "
                   f"min_risk={min_risk*100}%, max_risk={max_risk*100}%")
    
    def update_risk(self, trade_result):
        """
        Atnaujina rizikos parametrus pagal naujausią prekybos rezultatą.
        
        Args:
            trade_result (dict): Prekybos rezultato informacija:
                - timestamp: Laiko žyma
                - action: 'buy' arba 'sell'
                - price: Kaina
                - amount: BTC kiekis
                - profit: Pelnas/nuostolis
        """
        # Pridedame prekybos rezultatą į istoriją
        self.trades.append(trade_result)
        
        # Jei nėra profit reikšmės arba ji yra None, nieko nedarome
        if 'profit' not in trade_result or trade_result['profit'] is None:
            return
        
        # Atnaujiname statistiką
        profit = trade_result['profit']
        
        if profit > 0:
            self.win_count += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self.total_profit += profit
        elif profit < 0:
            self.loss_count += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self.total_loss += abs(profit)
        
        # Jei turime pakankamai sandorių, reguliuojame riziką
        if len(self.trades) % self.adjustment_period == 0:
            self._adjust_risk()
    
    def _adjust_risk(self):
        """
        Koreguoja rizikos parametrus pagal naujausius prekybos rezultatus.
        """
        # Jei neturime pakankamai duomenų, nieko nedarome
        if len(self.trades) < self.adjustment_period:
            return
        
        # Skaičiuojame win rate
        total_trades = self.win_count + self.loss_count
        win_rate = self.win_count / total_trades if total_trades > 0 else 0
        
        # Skaičiuojame profit factor
        profit_factor = self.total_profit / self.total_loss if self.total_loss > 0 else float('inf')
        
        # Pradiniai rizikos parametrai
        risk_adjustment = 1.0
        
        # Koreguojame riziką pagal win rate
        if win_rate > 0.6:  # Jei win rate aukštas, galime didinti riziką
            risk_adjustment *= 1.2
        elif win_rate < 0.4:  # Jei win rate žemas, mažiname riziką
            risk_adjustment *= 0.8
        
        # Koreguojame riziką pagal profit factor
        if profit_factor > 2.0:  # Jei profit factor aukštas, galime didinti riziką
            risk_adjustment *= 1.2
        elif profit_factor < 1.0:  # Jei profit factor žemas, mažiname riziką
            risk_adjustment *= 0.8
        
        # Koreguojame riziką pagal nuoseklių nuostolių skaičių
        if self.consecutive_losses > 3:
            # Mažiname riziką po kelių nuoseklių nuostolių
            risk_adjustment *= max(0.5, 1.0 - (self.consecutive_losses * 0.1))
        
        # Koreguojame riziką pagal nuoseklių laimėjimų skaičių
        if self.consecutive_wins > 3:
            # Didžiname riziką po kelių nuoseklių laimėjimų
            risk_adjustment *= min(1.5, 1.0 + (self.consecutive_wins * 0.05))
        
        # Apskaičiuojame naują rizikos reikšmę
        new_risk = self.base_risk * risk_adjustment
        
        # Apribojame riziką
        self.current_risk = max(self.min_risk, min(self.max_risk, new_risk))
        
        logger.info(f"Rizikos parametrai dinamiškai pakoreguoti: current_risk={self.current_risk*100:.2f}%, "
                   f"win_rate={win_rate*100:.2f}%, profit_factor={profit_factor:.2f}, "
                   f"consecutive_wins={self.consecutive_wins}, consecutive_losses={self.consecutive_losses}")
    
    def get_current_risk(self):
        """
        Grąžina dabartinį rizikos parametrą.
        
        Returns:
            float: Dabartinis rizikos parametras
        """
        return self.current_risk
    
    def get_statistics(self):
        """
        Grąžina prekybos statistiką.
        
        Returns:
            dict: Prekybos statistikos duomenys
        """
        total_trades = self.win_count + self.loss_count
        win_rate = self.win_count / total_trades if total_trades > 0 else 0
        profit_factor = self.total_profit / self.total_loss if self.total_loss > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'current_risk': self.current_risk
        }