"""
Filtrai ir validatoriai
--------------------
Šis modulis apibrėžia filtravimo ir validavimo funkcijas.
"""

import re
from datetime import datetime

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """
    Formatuoja datetime objektą į string
    
    Args:
        value: Datetime objektas
        format: Formatavimo šablonas
        
    Returns:
        str: Suformatuota data
    """
    if value is None:
        return ""
    return value.strftime(format)

def format_currency(value, currency='€'):
    """
    Formatuoja skaičių į valiutos formatą
    
    Args:
        value: Skaičius
        currency: Valiutos simbolis
        
    Returns:
        str: Suformatuota valiuta
    """
    if value is None:
        return f"0.00{currency}"
    return f"{value:,.2f}{currency}"

def format_percent(value):
    """
    Formatuoja skaičių į procento formatą
    
    Args:
        value: Skaičius (0.05 = 5%)
        
    Returns:
        str: Suformatuotas procentas
    """
    if value is None:
        return "0%"
    return f"{value*100:.2f}%"

def validate_numeric(value, min_value=None, max_value=None):
    """
    Patikrina, ar reikšmė yra skaičius ir ar patenka į rėžius
    
    Args:
        value: Tikrinama reikšmė
        min_value: Minimali leistina reikšmė
        max_value: Maksimali leistina reikšmė
        
    Returns:
        tuple: (bool, str) - (Ar validus, Klaidos pranešimas)
    """
    try:
        num_value = float(value)
        
        if min_value is not None and num_value < min_value:
            return False, f"Reikšmė negali būti mažesnė už {min_value}"
        
        if max_value is not None and num_value > max_value:
            return False, f"Reikšmė negali būti didesnė už {max_value}"
        
        return True, ""
    except (ValueError, TypeError):
        return False, "Reikšmė turi būti skaičius"

def filter_numeric(value):
    """
    Filtruoja tik skaičius iš teksto
    
    Args:
        value: Tekstas su skaičiais
        
    Returns:
        str: Tik skaičiai
    """
    if not value:
        return ""
    return ''.join(char for char in str(value) if char.isdigit() or char == '.')