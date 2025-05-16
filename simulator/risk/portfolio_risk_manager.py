# filepath: d:\CA_BTC\simulator\risk\portfolio_risk_manager.py
"""
Portfelio rizikos valdymas
-----------------------------
Šis modulis realizuoja portfelio rizikos valdymą keliems 
instrumentams, įskaitant diversifikaciją ir koreliaciją.
"""
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PortfolioRiskManager:
    def __init__(self, max_portfolio_risk=0.05, max_instrument_risk=0.02, 
                 max_correlated_exposure=0.1, correlation_threshold=0.7):
        """
        Inicializuoja portfelio rizikos valdytoją.
        
        Args:
            max_portfolio_risk (float): Maksimali portfelio rizika (0-1)
            max_instrument_risk (float): Maksimali vieno instrumento rizika (0-1)
            max_correlated_exposure (float): Maksimali koreliuotų instrumentų pozicija (0-1)
            correlation_threshold (float): Koreliacija, virš kurios instrumentai laikomi susijusiais (0-1)
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_instrument_risk = max_instrument_risk
        self.max_correlated_exposure = max_correlated_exposure
        self.correlation_threshold = correlation_threshold
        
        # Saugome aktyvias pozicijas
        self.active_positions = {}  # symbol -> position_details
        
        # Saugome instrumentų koreliaciją
        self.correlation_matrix = pd.DataFrame()
        
        logger.info(f"Inicializuotas PortfolioRiskManager: max_portfolio_risk={max_portfolio_risk}, max_instrument_risk={max_instrument_risk}")
    
    def update_correlation_matrix(self, price_data):
        """
        Atnaujina instrumentų koreliacijos matricą.
        
        Args:
            price_data (pandas.DataFrame): Kainų duomenys pagal instrumentus
        """
        # Apskaičiuojame grąžas
        returns = price_data.pct_change().dropna()
        
        # Apskaičiuojame koreliaciją
        self.correlation_matrix = returns.corr()
        
        logger.debug(f"Atnaujinta koreliacijos matrica: {len(self.correlation_matrix)} instrumentai")
    
    def calculate_position_risk(self, symbol, price, amount, volatility, portfolio_value):
        """
        Apskaičiuoja pozicijos riziką.
        
        Args:
            symbol (str): Instrumento simbolis
            price (float): Instrumento kaina
            amount (float): Pozicijos dydis
            volatility (float): Instrumento volatilumas (std devation)
            portfolio_value (float): Portfelio vertė
        
        Returns:
            float: Pozicijos rizika (0-1)
        """
        position_value = price * amount
        position_risk = (position_value / portfolio_value) * (volatility / 100)
        
        return position_risk
    
    def calculate_portfolio_risk(self, positions, correlations=None):
        """
        Apskaičiuoja bendrą portfelio riziką.
        
        Args:
            positions (dict): Pozicijų informacija (symbol -> position_details)
            correlations (pandas.DataFrame, optional): Koreliacijos matrica
        
        Returns:
            float: Bendra portfelio rizika (0-1)
        """
        if not positions:
            return 0
        
        # Jei nenurodyta koreliacijos matrica, naudojame vidinę
        if correlations is None:
            correlations = self.correlation_matrix
        
        # Jei nėra koreliacijos duomenų, skaičiuojame paprastu būdu
        if correlations.empty:
            total_risk = sum(pos['risk'] for pos in positions.values())
            return total_risk
        
        # Kitu atveju naudojame koreliacijos matricą
        symbols = list(positions.keys())
        risks = np.array([positions[s]['risk'] for s in symbols])
        
        # Kuriame kovariacijos matricą
        cov_matrix = np.zeros((len(symbols), len(symbols)))
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if sym1 in correlations.index and sym2 in correlations.columns:
                    corr = correlations.loc[sym1, sym2]
                    cov_matrix[i, j] = risks[i] * risks[j] * corr
                elif i == j:
                    cov_matrix[i, j] = risks[i] * risks[i]
        
        # Apskaičiuojame portfelio riziką
        portfolio_risk = np.sqrt(np.sum(cov_matrix))
        
        return portfolio_risk
    
    def check_correlated_exposure(self, symbol, positions):
        """
        Patikrina, ar nauja pozicija neviršija koreliuotų instrumentų ekspozicijos.
        
        Args:
            symbol (str): Naujos pozicijos simbolis
            positions (dict): Esamos pozicijos (symbol -> position_details)
        
        Returns:
            float: Koreliuotų instrumentų ekspozicija (0-1)
        """
        if symbol not in self.correlation_matrix.index or not positions:
            return 0
        
        correlated_exposure = 0
        for other_symbol, position in positions.items():
            if other_symbol != symbol and other_symbol in self.correlation_matrix.columns:
                corr = self.correlation_matrix.loc[symbol, other_symbol]
                if abs(corr) >= self.correlation_threshold:
                    correlated_exposure += position['exposure']
        
        return correlated_exposure
    
    def get_max_position_size(self, symbol, price, volatility, portfolio_value, positions):
        """
        Nustato maksimalų pozicijos dydį, atsižvelgiant į rizikos ribojimus.
        
        Args:
            symbol (str): Instrumento simbolis
            price (float): Instrumento kaina
            volatility (float): Instrumento volatilumas
            portfolio_value (float): Portfelio vertė
            positions (dict): Esamos pozicijos
        
        Returns:
            float: Maksimalus pozicijos dydis
        """
        # Apskaičiuojame esamą portfelio riziką
        current_portfolio_risk = self.calculate_portfolio_risk(positions)
        
        # Rizika, kurią dar galime prisiimti
        available_risk = self.max_portfolio_risk - current_portfolio_risk
        
        # Tikriname, ar nauja pozicija neviršys instrumento rizikos ribos
        instrument_position_limit = (self.max_instrument_risk * portfolio_value) / (price * (volatility / 100))
        
        # Tikriname koreliuotų instrumentų ribojimą
        correlated_exposure = self.check_correlated_exposure(symbol, positions)
        exposure_limit = (self.max_correlated_exposure - correlated_exposure) * portfolio_value
        correlated_position_limit = exposure_limit / price
        
        # Tikriname bendrą portfelio rizikos ribojimą
        portfolio_position_limit = (available_risk * portfolio_value) / (price * (volatility / 100))
        
        # Grąžiname mažiausią iš trijų apribojimų
        max_position = min(instrument_position_limit, correlated_position_limit, portfolio_position_limit)
        
        logger.debug(f"Maksimalus pozicijos dydis {symbol}: {max_position}, limitas: instr={instrument_position_limit}, corr={correlated_position_limit}, port={portfolio_position_limit}")
        
        return max(0, max_position)