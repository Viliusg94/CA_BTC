"""
Pagalbinės funkcijos Bitcoin kainų analizės programai
"""

import requests
from datetime import datetime
import numpy as np
import logging
import random

# Logger
logger = logging.getLogger(__name__)

def get_real_bitcoin_price():
    """
    Gauna realią Bitcoin kainą iš Binance API
    
    Returns:
        float: Bitcoin kaina arba None jei įvyksta klaida
    """
    try:
        # Naudojame Binance API ticker endpoint
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', 
                              headers={'User-Agent': 'Mozilla/5.0'}, 
                              timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current_price = float(data['price'])
            logger.info(f"Gauta Bitcoin kaina: {current_price}")
            return current_price
        else:
            logger.error(f"Klaida gaunant Bitcoin kainą: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Klaida gaunant Bitcoin kainą: {str(e)}")
        return None

def calculate_price_change(current_price, previous_price=None):
    """
    Apskaičiuoja kainos pokytį
    
    Args:
        current_price (float): Dabartinė kaina
        previous_price (float, optional): Ankstesnė kaina
        
    Returns:
        dict: Kainos pokyčio informacija
    """
    try:
        # Jei neturime ankstesnės kainos, naudojame 1% mažesnę nei dabartinė
        if previous_price is None:
            previous_price = current_price * 0.99
        
        # Apskaičiuojame pokytį
        change_amount = current_price - previous_price
        change_percent = (change_amount / previous_price) * 100
        
        # Nustatome krypties rodyklę
        if change_amount > 0:
            direction = 'up'
        elif change_amount < 0:
            direction = 'down'
        else:
            direction = 'neutral'
        
        return {
            'amount': change_amount,
            'percent': change_percent,
            'direction': direction
        }
    except Exception as e:
        logger.error(f"Klaida apskaičiuojant kainos pokytį: {str(e)}")
        # Jei įvyksta klaida, grąžiname numatytąją reikšmę
        return {
            'amount': 0,
            'percent': 0,
            'direction': 'neutral'
        }

def generate_dummy_price_history():
    """
    Sugeneruoja Bitcoin kainos istorijos duomenis, kai negalima gauti tikrų duomenų
    
    Returns:
        dict: Sugeneruota kainos istorija
    """
    # Generuojame 30 dienų istoriją
    dates = []
    close_prices = []
    
    base_price = 45000
    
    for i in range(30):
        # Datos (30 dienų atgal iki dabar)
        day = datetime.now().day - 30 + i + 1
        month = datetime.now().month
        year = datetime.now().year
        
        # Jei diena neegzistuoja tame mėnesyje, koreguojame
        if day <= 0:
            month -= 1
            if month <= 0:
                month = 12
                year -= 1
            # Nustatome paskutinę praėjusio mėnesio dieną
            if month in [4, 6, 9, 11]:
                day = 30 + day
            elif month == 2:
                day = 28 + day
            else:
                day = 31 + day
        
        date_str = f"{year}-{month:02d}-{day:02d}"
        dates.append(date_str)
        
        # Generuojame atsitiktinę kainą su nedideliais svyravimais
        variation = np.random.randint(-1000, 1000)
        price = base_price + variation
        close_prices.append(price)
    
    return {
        "dates": dates,
        "close": close_prices
    }

def generate_price_predictions():
    """Generuoja paprastas ateities prognozes"""
    # Generuojame 7 dienų prognozes
    dates = []
    values = []
    
    # Bazinė kaina
    base_price = get_real_bitcoin_price() or 45000
    
    for i in range(7):
        # Datos (nuo rytojaus iki 7 dienų į priekį)
        day = datetime.now().day + i + 1
        month = datetime.now().month
        year = datetime.now().year
        
        # Koreguojame, jei diena neegzistuoja tame mėnesyje
        if month in [4, 6, 9, 11] and day > 30:
            day = day - 30
            month += 1
        elif month == 2 and day > 28:
            day = day - 28
            month += 1
        elif day > 31:
            day = day - 31
            month += 1
        
        # Jei mėnuo virš 12, pereiname į kitus metus
        if month > 12:
            month = 1
            year += 1
        
        date_str = f"{year}-{month:02d}-{day:02d}"
        dates.append(date_str)
        
        # Generuojame prognozuojamą kainą su tendencija kilti
        variation = random.randint(-500, 1500)
        price = base_price + variation + (i * 100)
        values.append(price)
    
    # PATAISYMAS: Grąžiname žodyną su "dates" ir "values" raktais, ne reikšme kaip atributą
    return {
        "dates": dates,
        "values": values
    }