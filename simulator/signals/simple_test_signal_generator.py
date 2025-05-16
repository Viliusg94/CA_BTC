"""
Paprastas testavimo signalų generatorius
-----------------------------
Šis modulis sukuria paprastą signalų generatorių testavimui, 
kuris reguliariai generuoja pirkimo ir pardavimo signalus.
"""

import logging
import random
from simulator.signals.base_signal_generator import BaseSignalGenerator

logger = logging.getLogger(__name__)

class SimpleTestSignalGenerator(BaseSignalGenerator):
    """
    Paprastas signalų generatorius testavimui, kuris generuoja
    pirkimo ir pardavimo signalus pagal paprastą logiką.
    """
    def __init__(self, interval=15, name=None):
        """
        Inicializuoja paprastą testavimo signalų generatorių.
        
        Args:
            interval (int): Kas kiek žingsnių generuoti signalą
            name (str, optional): Generatoriaus pavadinimas
        """
        super().__init__(name=name or "SimpleTestSignalGenerator")
        
        # Kas kiek žingsnių generuoti naują signalą
        self.interval = interval
        
        # Skaičiuosime žingsnius
        self.step_counter = 0
        
        # Paskutinio sugeneruoto signalo tipas
        self.last_signal_type = None
        
        logger.info(f"Inicializuotas SimpleTestSignalGenerator su intervalu: {interval}")
    
    def generate_signal(self, current_data, historical_data, timestamp):
        """
        Sugeneruoja prekybos signalą pagal paprastą logiką.
        
        Args:
            current_data (pandas.Series): Dabartiniai duomenys
            historical_data (pandas.DataFrame): Istoriniai duomenys
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Sugeneruotas signalas
        """
        # Padidiname žingsnių skaitliuką
        self.step_counter += 1
        
        # Nustatome signalo tipą - generuojame tik kas interval žingsnių
        # ir keičiame signalo tipą kiekvieną kartą (pirkti, parduoti, laikyti)
        if self.step_counter % self.interval == 0:
            # Jei paskutinis signalas buvo "buy", dabar generuojame "sell"
            if self.last_signal_type == "buy":
                signal_type = "sell"
                signal_value = -0.8  # Stiprus pardavimo signalas
            # Jei paskutinis signalas buvo "sell" arba None, generuojame "buy"
            else:
                signal_type = "buy"
                signal_value = 0.8  # Stiprus pirkimo signalas
            
            # Įsimename paskutinio signalo tipą
            self.last_signal_type = signal_type
            
            # Pridedame šiek tiek atsitiktinumo signalo stiprumui
            strength = abs(signal_value) * (0.8 + 0.4 * random.random())
            
            logger.info(f"SimpleTestSignalGenerator sugeneravo signalą: {signal_type}, stiprumas={strength:.2f}")
        else:
            # Kitais atvejais generuojame neutralų "hold" signalą
            signal_type = "hold"
            signal_value = 0
            strength = 0
        
        # Sukuriame signalo žodyną
        signal = {
            'value': signal_value,
            'type': signal_type,
            'strength': strength,
            'timestamp': timestamp,
            'source': self.name,
            'components': {'test_signal': signal_value}
        }
        
        return signal