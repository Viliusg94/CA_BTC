"""
Rizikos valdymo modulis
-----------------------------
Šis modulis realizuoja rizikos valdymo funkcionalumą,
kuris apskaičiuoja pozicijos dydį, stop-loss ir take-profit reikšmes.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Rizikos valdymo klasė, kuri apskaičiuoja pozicijos dydį ir nuostolių ribojimo taškus.
    """
    def __init__(self, risk_per_trade=0.02, max_risk_multiplier=3.0, stop_loss_atr_multiplier=2.0, take_profit_risk_ratio=2.0):
        """
        Inicializuoja rizikos valdymo komponentą.
        
        Args:
            risk_per_trade (float): Maksimali rizika vienam sandoriui kaip dalis portfelio (0.02 = 2%)
            max_risk_multiplier (float): Maksimalus rizikos daugiklis pagal signalo stiprumą
            stop_loss_atr_multiplier (float): ATR daugiklis stop-loss ribai nustatyti
            take_profit_risk_ratio (float): Take-profit ir rizikos santykis (2.0 = take-profit yra 2x stop-loss)
        """
        self.risk_per_trade = risk_per_trade
        self.max_risk_multiplier = max_risk_multiplier
        self.stop_loss_atr_multiplier = stop_loss_atr_multiplier
        self.take_profit_risk_ratio = take_profit_risk_ratio
        
        logger.info(f"Inicializuotas rizikos valdytojas: risk_per_trade={risk_per_trade*100}%, "
                   f"max_risk_multiplier={max_risk_multiplier}, stop_loss_atr_multiplier={stop_loss_atr_multiplier}, "
                   f"take_profit_risk_ratio={take_profit_risk_ratio}")
    
    def calculate_position_size(self, portfolio_value, entry_price, stop_loss_price, signal_strength=0.5):
        """
        Apskaičiuoja pozicijos dydį pagal rizikos valdymo taisykles.
        
        Args:
            portfolio_value (float): Dabartinė portfelio vertė
            entry_price (float): Įėjimo kaina
            stop_loss_price (float): Stop-loss kaina
            signal_strength (float): Signalo stiprumas (0-1)
        
        Returns:
            float: Pozicijos dydis (BTC kiekis)
        """
        # Apskaičiuojame rizikos daugiklį pagal signalo stiprumą
        risk_multiplier = 1.0 + (self.max_risk_multiplier - 1.0) * signal_strength
        
        # Apskaičiuojame rizikuojamą sumą
        risk_amount = portfolio_value * self.risk_per_trade * risk_multiplier
        
        # Apskaičiuojame potencialų nuostolį vienam BTC
        price_difference = abs(entry_price - stop_loss_price)
        
        if price_difference == 0:
            logger.warning("Įėjimo kaina ir stop-loss kaina yra vienodos. Naudojama standartinė 2% rizika.")
            price_difference = entry_price * 0.02
        
        # Apskaičiuojame pozicijos dydį BTC
        position_size = risk_amount / price_difference
        
        # Konvertuojame į BTC kiekį
        btc_amount = position_size / entry_price
        
        logger.info(f"Apskaičiuotas pozicijos dydis: {btc_amount:.6f} BTC (rizikos suma: ${risk_amount:.2f})")
        
        return btc_amount
    
    def calculate_stop_loss_take_profit(self, entry_price, position_type, atr=None, custom_sl_percentage=None, custom_tp_percentage=None):
        """
        Apskaičiuoja stop-loss ir take-profit kainas.
        
        Args:
            entry_price (float): Įėjimo kaina
            position_type (str): Pozicijos tipas ("long" arba "short")
            atr (float, optional): Average True Range reikšmė
            custom_sl_percentage (float, optional): Pasirinktinis stop-loss procentas
            custom_tp_percentage (float, optional): Pasirinktinis take-profit procentas
        
        Returns:
            tuple: (stop_loss_price, take_profit_price)
        """
        # Nustatome stop-loss procentą
        if custom_sl_percentage is not None:
            sl_percentage = custom_sl_percentage
        elif atr is not None and atr > 0:
            # Naudojame ATR, jei jis yra nurodytas ir teigiamas
            sl_percentage = (atr * self.stop_loss_atr_multiplier) / entry_price
        else:
            # Numatytasis stop-loss procentas
            sl_percentage = 0.05  # 5%
        
        # Nustatome take-profit procentą
        if custom_tp_percentage is not None:
            tp_percentage = custom_tp_percentage
        else:
            # Take-profit yra proporcingas stop-loss
            tp_percentage = sl_percentage * self.take_profit_risk_ratio
        
        # Apskaičiuojame stop-loss ir take-profit kainas priklausomai nuo pozicijos tipo
        if position_type == "long":
            stop_loss_price = entry_price * (1 - sl_percentage)
            take_profit_price = entry_price * (1 + tp_percentage)
        else:  # short
            stop_loss_price = entry_price * (1 + sl_percentage)
            take_profit_price = entry_price * (1 - tp_percentage)
        
        logger.info(f"{position_type.capitalize()} pozicijos SL/TP: įėjimo kaina=${entry_price:.2f}, "
                   f"stop-loss=${stop_loss_price:.2f} ({sl_percentage*100:.2f}%), "
                   f"take-profit=${take_profit_price:.2f} ({tp_percentage*100:.2f}%)")
        
        return stop_loss_price, take_profit_price
    
    def update_risk_parameters(self, performance_metrics):
        """
        Atnaujina rizikos valdymo parametrus pagal veiklos rezultatus.
        
        Args:
            performance_metrics (dict): Veiklos rezultatų metrikos
        """
        # Jei sėkmės rodiklis (win rate) mažas, sumažiname riziką
        if "win_rate" in performance_metrics and performance_metrics["win_rate"] < 0.4:
            self.risk_per_trade = max(0.01, self.risk_per_trade * 0.9)
            logger.info(f"Sumažinta rizika dėl žemo sėkmės rodiklio: {self.risk_per_trade*100:.2f}%")
        
        # Jei sėkmės rodiklis aukštas, šiek tiek padidiname riziką
        elif "win_rate" in performance_metrics and performance_metrics["win_rate"] > 0.6:
            self.risk_per_trade = min(0.05, self.risk_per_trade * 1.1)
            logger.info(f"Padidinta rizika dėl aukšto sėkmės rodiklio: {self.risk_per_trade*100:.2f}%")
    
    def calculate_trailing_stop(self, entry_price, current_price, highest_price, trailing_percentage=0.02):
        """
        Apskaičiuoja trailing stop kainą.
        
        Args:
            entry_price (float): Įėjimo kaina
            current_price (float): Dabartinė kaina
            highest_price (float): Aukščiausia kaina nuo pozicijos atidarymo
            trailing_percentage (float): Trailing stop procentas
        
        Returns:
            float: Trailing stop kaina
        """
        if current_price <= entry_price:
            # Jei kaina nukrito žemiau įėjimo kainos, naudojame fiksuotą stop-loss
            return entry_price * (1 - trailing_percentage)
        
        # Apskaičiuojame trailing stop
        trailing_stop = highest_price * (1 - trailing_percentage)
        
        # Trailing stop negali būti žemiau įėjimo kainos
        trailing_stop = max(trailing_stop, entry_price)
        
        return trailing_stop