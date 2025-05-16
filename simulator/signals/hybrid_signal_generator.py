"""
Hibridinis signalų generatorius
-----------------------------
Šis modulis realizuoja signalų generatorių, kuris sujungia
kelis skirtingus signalų generatorius į vieną hibridinį generatorių.
"""

import pandas as pd
import numpy as np
import logging
from simulator.signals.base_signal_generator import BaseSignalGenerator

logger = logging.getLogger(__name__)

class HybridSignalGenerator(BaseSignalGenerator):
    """
    Hibridinis signalų generatorius, kuris apjungia kelis skirtingus generatorius.
    """
    def __init__(self, generators, weights=None, threshold=0.3, name=None):
        """
        Inicializuoja hibridinį signalų generatorių.
        
        Args:
            generators (list): SignalGenerator objektų sąrašas
            weights (dict): Generatorių svoriai (generatoriaus pavadinimas -> svoris)
            threshold (float): Bendras signalo generavimo slenkstis (0-1)
            name (str, optional): Generatoriaus pavadinimas
        """
        super().__init__(name=name or "HybridSignalGenerator")
        
        self.generators = generators
        self.weights = weights or {g.name: 1.0 for g in generators}
        self.threshold = threshold
        
        logger.info(f"Inicializuotas hibridinis signalų generatorius su {len(generators)} generatoriais: {[g.name for g in generators]}")
    
    def generate_signal(self, current_data, historical_data, timestamp):
        """
        Sugeneruoja prekybos signalą sujungdamas visų generatorių signalus.
        
        Args:
            current_data (pandas.Series): Dabartiniai duomenys
            historical_data (pandas.DataFrame): Istoriniai duomenys
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Sugeneruotas hibridinis signalas
        """
        all_signals = []
        signals_by_generator = {}
        
        # Gauname signalus iš visų generatorių
        for generator in self.generators:
            signal = generator.generate_signal(current_data, historical_data, timestamp)
            all_signals.append(signal)
            signals_by_generator[generator.name] = signal
            
            logger.debug(f"Gautas signalas iš {generator.name}: {signal['type']}, stiprumas={signal['strength']:.2f}")
        
        # Jei nėra signalų, grąžiname tuščią signalą
        if not all_signals:
            logger.warning("Negauta jokių signalų iš generatorių.")
            return {
                'value': 0,
                'type': 'hold',
                'strength': 0,
                'timestamp': timestamp,
                'source': self.name
            }
        
        # Apskaičiuojame svertinį vidurkį
        weighted_sum = 0
        total_weight = 0
        
        for signal in all_signals:
            generator_name = signal['source']
            weight = self.weights.get(generator_name, 1.0)
            
            weighted_sum += signal['value'] * weight
            total_weight += weight
        
        # Apskaičiuojame bendrą signalą
        if total_weight > 0:
            combined_value = weighted_sum / total_weight
        else:
            combined_value = 0
        
        # Nustatome signalo tipą pagal reikšmę
        if combined_value > self.threshold:
            signal_type = 'buy'
        elif combined_value < -self.threshold:
            signal_type = 'sell'
        else:
            signal_type = 'hold'
        
        # Suformuojame hibridinį signalą
        hybrid_signal = {
            'value': combined_value,
            'type': signal_type,
            'strength': abs(combined_value),
            'timestamp': timestamp,
            'source': self.name,
            'components': signals_by_generator
        }
        
        logger.debug(f"Hibridinis generatorius sugeneravo signalą: {signal_type}, stiprumas={abs(combined_value):.2f}")
        
        return hybrid_signal