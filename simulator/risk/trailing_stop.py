# filepath: d:\CA_BTC\simulator\risk\trailing_stop.py
"""
Trailing stop funkcionalumas
-----------------------------
Šis modulis realizuoja trailing stop logiką, kuri leidžia stop-loss
slenkti pelno kryptimi.
"""
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class TrailingStop:
    def __init__(self, initial_stop_pct=0.05, activation_pct=0.02, step_pct=0.01):
        """
        Inicializuoja trailing stop.
        
        Args:
            initial_stop_pct (float): Pradinis stop-loss procentas
            activation_pct (float): Pelno procentas, kuriam esant aktyvuojamas trailing stop
            step_pct (float): Žingsnis, kuriuo juda trailing stop
        """
        self.initial_stop_pct = initial_stop_pct
        self.activation_pct = activation_pct
        self.step_pct = step_pct
        self.active_positions = {}  # position_id -> position_details
        
        logger.info(f"Inicializuotas TrailingStop: initial_stop_pct={initial_stop_pct}, activation_pct={activation_pct}, step_pct={step_pct}")
    
    def add_position(self, position_id, entry_price, position_type, stop_price=None):
        """
        Prideda naują poziciją.
        
        Args:
            position_id (str): Pozicijos identifikatorius
            entry_price (float): Įėjimo kaina
            position_type (str): Pozicijos tipas ('long' arba 'short')
            stop_price (float, optional): Pradinis stop-loss lygis
        """
        # Jei stop_price nepateiktas, naudojame pradinį procentą
        if stop_price is None:
            if position_type == 'long':
                stop_price = entry_price * (1 - self.initial_stop_pct)
            else:  # 'short'
                stop_price = entry_price * (1 + self.initial_stop_pct)
        
        # Apskaičiuojame, kada aktyvuosis trailing stop
        if position_type == 'long':
            activation_price = entry_price * (1 + self.activation_pct)
        else:  # 'short'
            activation_price = entry_price * (1 - self.activation_pct)
        
        self.active_positions[position_id] = {
            'entry_price': entry_price,
            'current_stop': stop_price,
            'position_type': position_type,
            'activation_price': activation_price,
            'highest_price': entry_price if position_type == 'long' else float('inf'),
            'lowest_price': entry_price if position_type == 'short' else 0,
            'is_trailing_active': False
        }
        
        logger.info(f"Pridėta pozicija į trailing stop: {position_id}, entry_price={entry_price}, stop_price={stop_price}, activation_price={activation_price}")
        
        return stop_price
    
    def update_position(self, position_id, current_price):
        """
        Atnaujina poziciją pagal dabartinę kainą.
        
        Args:
            position_id (str): Pozicijos identifikatorius
            current_price (float): Dabartinė kaina
        
        Returns:
            float: Dabartinis stop-loss lygis
        """
        if position_id not in self.active_positions:
            logger.warning(f"Pozicija {position_id} nerasta trailing stop sistemoje")
            return None
        
        position = self.active_positions[position_id]
        
        # Atnaujiname aukščiausią/žemiausią kainą
        if position['position_type'] == 'long':
            position['highest_price'] = max(position['highest_price'], current_price)
        else:  # 'short'
            position['lowest_price'] = min(position['lowest_price'], current_price)
        
        # Tikriname, ar aktyvintas trailing stop
        if not position['is_trailing_active']:
            if (position['position_type'] == 'long' and current_price >= position['activation_price']) or \
               (position['position_type'] == 'short' and current_price <= position['activation_price']):
                position['is_trailing_active'] = True
                logger.info(f"Trailing stop aktyvuotas pozicijai {position_id}: current_price={current_price}, activation_price={position['activation_price']}")
        
        # Jei trailing stop aktyvus, atnaujiname stop-loss
        if position['is_trailing_active']:
            if position['position_type'] == 'long':
                new_stop = position['highest_price'] * (1 - self.step_pct)
                if new_stop > position['current_stop']:
                    position['current_stop'] = new_stop
                    logger.debug(f"Trailing stop pakeltas pozicijai {position_id}: new_stop={new_stop}")
            else:  # 'short'
                new_stop = position['lowest_price'] * (1 + self.step_pct)
                if new_stop < position['current_stop']:
                    position['current_stop'] = new_stop
                    logger.debug(f"Trailing stop nuleistas pozicijai {position_id}: new_stop={new_stop}")
        
        return position['current_stop']
    
    def check_stop_triggered(self, position_id, current_price):
        """
        Patikrina, ar suveikė stop-loss.
        
        Args:
            position_id (str): Pozicijos identifikatorius
            current_price (float): Dabartinė kaina
        
        Returns:
            bool: True, jei stop-loss suveikė
        """
        if position_id not in self.active_positions:
            return False
        
        position = self.active_positions[position_id]
        
        if position['position_type'] == 'long':
            if current_price <= position['current_stop']:
                logger.info(f"Trailing stop suveikė pozicijai {position_id}: current_price={current_price}, stop_price={position['current_stop']}")
                return True
        else:  # 'short'
            if current_price >= position['current_stop']:
                logger.info(f"Trailing stop suveikė pozicijai {position_id}: current_price={current_price}, stop_price={position['current_stop']}")
                return True
        
        return False
    
    def remove_position(self, position_id):
        """
        Pašalina poziciją iš trailing stop sistemos.
        
        Args:
            position_id (str): Pozicijos identifikatorius
        
        Returns:
            dict: Pašalintos pozicijos informacija
        """
        if position_id in self.active_positions:
            position = self.active_positions.pop(position_id)
            logger.info(f"Pozicija {position_id} pašalinta iš trailing stop sistemos")
            return position
        return None