# filepath: d:\CA_BTC\simulator\strategies\breakout_strategy.py
"""
Išsiveržimo (Breakout) strategija
-----------------------------
Ši strategija ieško kainų lygio išsiveržimų ir prekiauja pagal 
naujai susiformavusią tendenciją.
"""
import numpy as np
import pandas as pd
import logging
from simulator.strategies.base_strategy import TradingStrategy

logger = logging.getLogger(__name__)

class BreakoutStrategy(TradingStrategy):
    def __init__(self, lookback_period=20, breakout_threshold=2.0, cooldown_periods=5, name=None):
        """
        Inicializuoja išsiveržimo strategiją.
        
        Args:
            lookback_period (int): Periodų skaičius kainų diapazonui nustatyti
            breakout_threshold (float): Išsiveržimo slenkstis (ATR daugiklis)
            cooldown_periods (int): Periodų skaičius po prekybos prieš naują sandorį
            name (str, optional): Strategijos pavadinimas
        """
        super().__init__(name=name or "BreakoutStrategy")
        
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.cooldown_periods = cooldown_periods
        self.last_trade_time = None
        self.trade_cooldown_counter = 0
        
        logger.info(f"Inicializuota BreakoutStrategy: lookback_period={lookback_period}, breakout_threshold={breakout_threshold}")
    
    def generate_decision(self, signals, current_data, portfolio, timestamp):
        """
        Generuoja prekybos sprendimą pagal išsiveržimo strategiją.
        
        Args:
            signals (list): Signalų sąrašas
            current_data (pandas.Series): Dabartiniai duomenys
            portfolio: Portfelio objektas
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Prekybos sprendimas
        """
        # Jei esame atvėsimo periodoje, nesiūlome jokio sprendimo
        if self.trade_cooldown_counter > 0:
            self.trade_cooldown_counter -= 1
            return None
        
        # Reikalingi duomenys
        if 'Close' not in current_data or 'High' not in current_data or 'Low' not in current_data:
            return None
        
        current_price = current_data['Close']
        
        # Ieškome ATR stulpelio duomenyse
        if 'ATR_14' in current_data:
            atr = current_data['ATR_14']
        else:
            # Jei ATR nėra, galime naudoti paprastą volatilumą
            if 'historical_data' in signals and len(signals['historical_data']) >= self.lookback_period:
                historical_prices = signals['historical_data']['Close'].tail(self.lookback_period)
                high_prices = signals['historical_data']['High'].tail(self.lookback_period)
                low_prices = signals['historical_data']['Low'].tail(self.lookback_period)
                
                # Apskaičiuojame aukščiausią aukštą ir žemiausią žemą
                highest_high = high_prices.max()
                lowest_low = low_prices.min()
                
                # Apskaičiuojame vidutinį true range kaip alternatyvą ATR
                true_ranges = []
                for i in range(1, len(historical_prices)):
                    true_range = max(
                        high_prices.iloc[i] - low_prices.iloc[i],
                        abs(high_prices.iloc[i] - historical_prices.iloc[i-1]),
                        abs(low_prices.iloc[i] - historical_prices.iloc[i-1])
                    )
                    true_ranges.append(true_range)
                
                atr = sum(true_ranges) / len(true_ranges) if true_ranges else 0
            else:
                return None
        
        # Apskaičiuojame išsiveržimo ribas
        if 'historical_data' in signals and len(signals['historical_data']) >= self.lookback_period:
            historical_highs = signals['historical_data']['High'].tail(self.lookback_period)
            historical_lows = signals['historical_data']['Low'].tail(self.lookback_period)
            
            resistance = historical_highs.max()
            support = historical_lows.min()
            
            # Pridedame ATR daugiklį prie ribų
            upper_breakout = resistance + (atr * self.breakout_threshold)
            lower_breakout = support - (atr * self.breakout_threshold)
            
            # Defoltinis sprendimas - laikyti
            decision = {
                "action": "hold",
                "price": current_price,
                "timestamp": timestamp,
                "strategy": self.name
            }
            
            # Patikriname išsiveržimą į viršų
            if current_price > upper_breakout and portfolio.balance > 0:
                decision["action"] = "buy"
                
                # Pirkimo dydis - 25% portfelio
                amount_to_spend = portfolio.balance * 0.25
                decision["amount"] = amount_to_spend / current_price
                
                # Nustatome atvėsimo periodą
                self.trade_cooldown_counter = self.cooldown_periods
                
                logger.info(f"BreakoutStrategy: sugeneruotas pirkimo sprendimas (išsiveržimas aukštyn: {current_price:.2f} > {upper_breakout:.2f})")
            
            # Patikriname išsiveržimą į apačią
            elif current_price < lower_breakout and portfolio.btc_amount > 0:
                decision["action"] = "sell"
                
                # Pardavimo dydis - 50% turimų BTC
                decision["amount"] = portfolio.btc_amount * 0.5
                
                # Nustatome atvėsimo periodą
                self.trade_cooldown_counter = self.cooldown_periods
                
                logger.info(f"BreakoutStrategy: sugeneruotas pardavimo sprendimas (išsiveržimas žemyn: {current_price:.2f} < {lower_breakout:.2f})")
            
            return decision
        
        return None