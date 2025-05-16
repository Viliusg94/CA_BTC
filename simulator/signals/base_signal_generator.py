"""
Bazinis signalų generatorius
-----------------------------
Šis modulis apibrėžia bazinę SignalGenerator klasę,
kuri naudojama kaip pagrindas visiems signalų generatoriams.
"""

import logging

logger = logging.getLogger(__name__)

class BaseSignalGenerator:  # Pakeitėm iš SignalGenerator į BaseSignalGenerator
    """
    Bazinė signalų generatoriaus klasė, kuri apibrėžia bendrą sąsają (interface).
    """
    def __init__(self, name=None):
        """
        Inicializuoja signalų generatorių.
        
        Args:
            name (str, optional): Generatoriaus pavadinimas
        """
        self.name = name or self.__class__.__name__
        logger.info(f"Inicializuotas signalų generatorius: {self.name}")
    
    def generate_signal(self, current_data, historical_data, timestamp):
        """
        Sugeneruoja prekybos signalą.
        
        Args:
            current_data (pandas.Series): Dabartiniai duomenys
            historical_data (pandas.DataFrame): Istoriniai duomenys
            timestamp: Dabartinė laiko žyma
        
        Returns:
            dict: Sugeneruotas signalas
        """
        # Bazinė klasė tiesiog grąžina tuščią signalą - turi būti perrašyta paveldėtose klasėse
        logger.warning(f"Bazinė BaseSignalGenerator.generate_signal() metodas iškviestas. Turi būti perrašytas paveldėtose klasėse.")
        return {
            'value': 0,  # Signalo reikšmė: teigiama - pirkti, neigiama - parduoti, 0 - laikyti
            'type': 'hold',  # Signalo tipas: 'buy', 'sell', 'hold'
            'strength': 0,  # Signalo stiprumas nuo 0 iki 1
            'timestamp': timestamp,  # Laiko žyma
            'source': self.name  # Signalo šaltinis (generatoriaus pavadinimas)
        }
    
    def filter_signal(self, signal, threshold=0.3):
        """
        Filtruoja signalą pagal nurodytą slenkstį.
        
        Args:
            signal (dict): Prekybos signalas
            threshold (float): Signalo stiprumo slenkstis (0-1)
        
        Returns:
            dict: Filtruotas signalas
        """
        # Jei signalo stiprumas mažesnis už slenkstį, grąžiname 'hold' signalą
        if signal['strength'] < threshold:
            return {
                'value': 0,
                'type': 'hold',
                'strength': 0,
                'timestamp': signal['timestamp'],
                'source': signal['source']
            }
        
        return signal

# Pridedame alias, kad išlaikytume suderinamumą atgal
SignalGenerator = BaseSignalGenerator