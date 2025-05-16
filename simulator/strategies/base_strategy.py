"""
Bazinė prekybos strategija
-----------------------------
Šis modulis apibrėžia bazinę TradingStrategy klasę, kuri naudojama
kaip abstrakcija visoms konkrečioms prekybos strategijoms.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class TradingStrategy(ABC):
    """
    Abstrakti bazinė klasė prekybos strategijoms.
    """
    def __init__(self, name=None, signal_generator=None, risk_manager=None):
        """
        Inicializuoja prekybos strategiją.
        
        Args:
            name (str, optional): Strategijos pavadinimas
            signal_generator: Signalų generatorius
            risk_manager: Rizikos valdymo komponentas
        """
        self.name = name or self.__class__.__name__
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager
        self.state = {}  # Strategijos būsenos saugojimui
        
        logger.info(f"Inicializuota prekybos strategija: {self.name}")
    
    @abstractmethod
    def generate_decision(self, data, portfolio, timestamp):
        """
        Generuoja prekybos sprendimą pagal duomenis ir portfelio būseną.
        
        Args:
            data (pandas.Series): Duomenys su kainomis ir indikatoriais
            portfolio: Portfelio objektas
            timestamp: Dabartinis laiko žymė
        
        Returns:
            dict: Prekybos sprendimas su tokiais raktais:
                - action: 'buy', 'sell' arba 'hold'
                - amount: BTC kiekis (jei None, naudojamas visas galimas kiekis)
                - price: Kaina (jei None, naudojama dabartinė rinkos kaina)
                - stop_loss: Stop-loss kaina (pasirinktinai)
                - take_profit: Take-profit kaina (pasirinktinai)
        """
        pass
    
    def update_state(self, key, value):
        """
        Atnaujina strategijos būsenos reikšmę.
        
        Args:
            key (str): Raktas
            value: Reikšmė
        """
        self.state[key] = value
        
    def get_state(self, key, default=None):
        """
        Gauna strategijos būsenos reikšmę.
        
        Args:
            key (str): Raktas
            default: Numatytoji reikšmė, jei raktas nerastas
        
        Returns:
            Būsenos reikšmė arba numatytoji reikšmė
        """
        return self.state.get(key, default)