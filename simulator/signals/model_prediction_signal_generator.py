"""
Mašininio mokymosi prognozių signalų generatorius
-----------------------------
Šis modulis realizuoja signalų generatorių, kuris naudoja
mašininio mokymosi modelio prognozes prekybos signalams generuoti.
"""

import pandas as pd
import numpy as np
import logging
from simulator.signals.base_signal_generator import BaseSignalGenerator

logger = logging.getLogger(__name__)

class ModelPredictionSignalGenerator(BaseSignalGenerator):
    """
    Signalų generatorius, kuris naudoja mašininio mokymosi modelio prognozes.
    """
    def __init__(self, prediction_col='predicted_direction', confidence_col='confidence', threshold=0.6, name=None):
        """
        Inicializuoja ML prognozių signalų generatorių.
        
        Args:
            prediction_col (str): Prognozės stulpelio pavadinimas
            confidence_col (str): Pasitikėjimo stulpelio pavadinimas
            threshold (float): Pasitikėjimo slenkstis (0-1)
            name (str, optional): Generatoriaus pavadinimas
        """
        super().__init__(name=name or "ModelPredictionSignalGenerator")
        
        self.prediction_col = prediction_col
        self.confidence_col = confidence_col
        self.threshold = threshold
        
        logger.info(f"Inicializuotas ML prognozių signalų generatorius: prediction_col={prediction_col}, "
                   f"confidence_col={confidence_col}, threshold={threshold}")
    
    def generate_signal(self, current_data, historical_data, timestamp):
        """
        Sugeneruoja prekybos signalą pagal ML modelio prognozes.
        
        Args:
            current_data (pandas.Series): Dabartiniai duomenys
            historical_data (pandas.DataFrame): Istoriniai duomenys
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Sugeneruotas signalas
        """
        # Jei trūksta stulpelių, naudojame techninio indikatoriaus signalus vietoj ML
        # arba grąžiname neutralų signalą
        if self.prediction_col not in current_data or self.confidence_col not in current_data:
            # Galima logika naudoti alternatyvų signalo generavimą, pvz.:
            # 1. RSI indikatorius
            if 'RSI_14' in current_data:
                rsi = current_data['RSI_14']
                if rsi < 30:  # Perparduota - pirkimo signalas
                    signal_value = 0.7
                    signal_type = 'buy'
                elif rsi > 70:  # Perpirkta - pardavimo signalas
                    signal_value = -0.7
                    signal_type = 'sell'
                else:
                    signal_value = 0
                    signal_type = 'hold'
                
                return {
                    'value': signal_value,
                    'type': signal_type,
                    'strength': abs(signal_value),
                    'timestamp': timestamp,
                    'source': self.name,
                    'prediction': None,
                    'confidence': abs(signal_value),
                    'alternative_source': 'RSI'
                }
            # Jei nėra techninių indikatorių, grąžiname neutralų signalą
            else:
                return {
                    'value': 0,
                    'type': 'hold',
                    'strength': 0,
                    'timestamp': timestamp,
                    'source': self.name,
                    'prediction': None,
                    'confidence': 0
                }
        
        # Gauname prognozę ir pasitikėjimą
        prediction = current_data[self.prediction_col]
        confidence = current_data[self.confidence_col]
        
        # Generuojame signalą
        if confidence >= self.threshold:
            if prediction == 1:  # 1 reiškia kainos augimą
                signal_type = 'buy'
                signal_value = confidence
            else:  # 0 arba -1 reiškia kainos kritimą
                signal_type = 'sell'
                signal_value = -confidence
        else:
            signal_type = 'hold'
            signal_value = 0
        
        # Sukuriame signalo žodyną
        signal = {
            'value': signal_value,
            'type': signal_type,
            'strength': abs(signal_value),
            'timestamp': timestamp,
            'source': self.name,
            'prediction': prediction,
            'confidence': confidence
        }
        
        logger.debug(f"ML prognozių generatorius sugeneravo signalą: {signal_type}, "
                    f"stiprumas={abs(signal_value):.2f}, prognozė={prediction}, pasitikėjimas={confidence:.2f}")
        
        return signal