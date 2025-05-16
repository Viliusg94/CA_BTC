"""
Techninių indikatorių signalų generatorius
-----------------------------
Šis modulis realizuoja signalų generatorių, kuris naudoja
techninius indikatorius prekybos signalams generuoti.
"""

import pandas as pd
import numpy as np
import logging
from simulator.signals.base_signal_generator import BaseSignalGenerator

logger = logging.getLogger(__name__)

class TechnicalIndicatorSignalGenerator(BaseSignalGenerator):
    """
    Signalų generatorius, kuris naudoja techninius indikatorius.
    """
    def __init__(self, indicators=None, name=None):
        """
        Inicializuoja techninių indikatorių signalų generatorių.
        
        Args:
            indicators (list): Indikatorių sąrašas
            name (str, optional): Generatoriaus pavadinimas
        """
        super().__init__(name=name or "TechnicalIndicatorSignalGenerator")
        
        self.indicators = indicators or ["SMA_Signal", "RSI_Signal", "MACD_Signal", "Bollinger_Signal"]
        
        logger.info(f"Inicializuotas TechnicalIndicatorSignalGenerator su indikatoriais: {self.indicators}")
    
    def generate_signal(self, current_data, historical_data, timestamp):
        """
        Sugeneruoja prekybos signalą pagal techninius indikatorius.
        
        Args:
            current_data (pandas.Series): Dabartiniai duomenys
            historical_data (pandas.DataFrame): Istoriniai duomenys
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Sugeneruotas signalas
        """
        # Inicializuojame signalo reikšmes
        signal_value = 0
        signal_components = {}
        
        # Tikriname kiekvieną indikatorių
        for indicator in self.indicators:
            if indicator not in current_data:
                continue
            
            # Gauname indikatoriaus reikšmę
            indicator_value = current_data[indicator]
            
            # Pridedame indikatoriaus reikšmę prie bendro signalo
            signal_value += indicator_value
            
            # Išsaugome indikatoriaus reikšmę
            signal_components[indicator] = indicator_value
        
        # Normalizuojame bendrą signalą, padalindami iš indikatorių skaičiaus
        if self.indicators:
            signal_value /= len(self.indicators)
        
        # Nustatome signalo tipą pagal reikšmę
        if signal_value > 0.3:
            signal_type = 'buy'
        elif signal_value < -0.3:
            signal_type = 'sell'
        else:
            signal_type = 'hold'
        
        # Sukuriame signalo žodyną
        signal = {
            'value': signal_value,
            'type': signal_type,
            'strength': abs(signal_value),
            'timestamp': timestamp,
            'source': self.name,
            'components': signal_components
        }
        
        logger.debug(f"TI generatorius sugeneravo signalą: {signal_type}, stiprumas={abs(signal_value):.2f}")
        
        return signal

class MacdSignalGenerator(TechnicalIndicatorSignalGenerator):
    """
    Signalų generatorius, kuris specializuojasi MACD indikatoriumi.
    """
    def __init__(self, name=None):
        """
        Inicializuoja MACD signalų generatorių.
        """
        super().__init__(
            indicators=["MACD", "MACD_signal", "MACD_hist"],
            name=name or "MacdSignalGenerator"
        )
    
    def generate_signal(self, current_data, historical_data, timestamp):
        """
        Generuoja prekybos signalą pagal MACD indikatorių.
        
        Args:
            current_data (pandas.Series): Dabartiniai duomenys
            historical_data (pandas.DataFrame): Istoriniai duomenys
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Sugeneruotas signalas
        """
        # Tikriname, ar turime visus reikalingus duomenis
        required_columns = ["MACD", "MACD_signal", "MACD_hist"]
        if not all(col in current_data for col in required_columns):
            logger.warning(f"Trūksta MACD duomenų")
            return {"value": 0, "type": "hold", "strength": 0, "timestamp": timestamp, "source": self.name, "components": {}}
        
        macd = current_data["MACD"]
        macd_signal = current_data["MACD_signal"]
        macd_hist = current_data["MACD_hist"]
        
        # Nustatome signalą
        signal_value = macd_hist
        signal_type = "hold"
        signal_strength = abs(macd_hist)
        signal_components = {"MACD_hist": macd_hist}
        
        # MACD histogramos ženklo pakeitimas
        if macd_hist > 0:
            signal_type = "buy"
        elif macd_hist < 0:
            signal_type = "sell"
        
        # MACD ir signalo linijos susikirtimas
        if macd > macd_signal and abs(macd - macd_signal) < 50:
            signal_type = "buy"
            signal_components["MACD_cross"] = "up"
        elif macd < macd_signal and abs(macd - macd_signal) < 50:
            signal_type = "sell"
            signal_components["MACD_cross"] = "down"
        
        signal = {
            "value": signal_value,
            "type": signal_type,
            "strength": signal_strength,
            "timestamp": timestamp,
            "source": self.name,
            "components": signal_components
        }
        
        logger.info(f"MACD signalas: {signal_type} (stiprumas: {signal_strength:.2f})")
        
        return signal

class RsiSignalGenerator(TechnicalIndicatorSignalGenerator):
    """
    Signalų generatorius, kuris specializuojasi RSI indikatoriumi.
    """
    def __init__(self, oversold=30, overbought=70, name=None):
        """
        Inicializuoja RSI signalų generatorių.
        
        Args:
            oversold (float): RSI riba, žemiau kurios laikoma, kad turtas perparduotas
            overbought (float): RSI riba, aukščiau kurios laikoma, kad turtas perpirktas
            name (str, optional): Generatoriaus pavadinimas
        """
        super().__init__(
            indicators=["RSI_14"],
            name=name or "RsiSignalGenerator"
        )
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, current_data, historical_data, timestamp):
        """
        Generuoja prekybos signalą pagal RSI indikatorių.
        
        Args:
            current_data (pandas.Series): Dabartiniai duomenys
            historical_data (pandas.DataFrame): Istoriniai duomenys
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Sugeneruotas signalas
        """
        if "RSI_14" not in current_data:
            logger.warning("Trūksta RSI_14 duomenų")
            return {"value": 0, "type": "hold", "strength": 0, "timestamp": timestamp, "source": self.name, "components": {}}
        
        rsi = current_data["RSI_14"]
        
        signal_value = 0
        signal_type = "hold"
        signal_strength = 0
        signal_components = {"RSI_14": rsi}
        
        if rsi < self.oversold:
            signal_value = 1 - (rsi / self.oversold)
            signal_type = "buy"
        elif rsi > self.overbought:
            signal_value = (rsi - self.overbought) / (100 - self.overbought)
            signal_type = "sell"
        
        signal_strength = abs(signal_value)
        
        signal = {
            "value": signal_value,
            "type": signal_type,
            "strength": signal_strength,
            "timestamp": timestamp,
            "source": self.name,
            "components": signal_components
        }
        
        logger.info(f"RSI signalas: {signal_type} (stiprumas: {signal_strength:.2f})")
        
        return signal