"""
Prekybos signalų modulis
-----------------------
Šis modulis generuoja prekybos signalus pagal techninius indikatorius.
"""

import random
from datetime import datetime, timedelta

def generate_signals_from_indicators(data):
    """
    Generuoja prekybos signalus pagal techninius indikatorius
    
    Args:
        data: Kainų ir indikatorių duomenys
        
    Returns:
        tuple: (Pirkimo signalai, Pardavimo signalai) - abu yra žodynai su data kaip raktu ir kaina kaip reikšme
    """
    buy_signals = {}
    sell_signals = {}
    
    # Gauname duomenis
    dates = data.get('labels', [])
    closes = data.get('close', [])
    sma20 = data.get('sma20', [])
    sma50 = data.get('sma50', [])
    rsi = data.get('rsi', [])
    
    if not dates or not closes or len(dates) != len(closes):
        return buy_signals, sell_signals
    
    # Ieškome signalų pagal SMA kirtimą
    for i in range(1, len(dates)):
        # Tikriname ar yra pakankamai duomenų
        if i < 50 or sma20[i] is None or sma50[i] is None or sma20[i-1] is None or sma50[i-1] is None:
            continue
        
        # SMA kirtimo signalas: SMA20 kerta SMA50 iš apačios į viršų (Golden Cross) - pirkimo signalas
        if sma20[i-1] <= sma50[i-1] and sma20[i] > sma50[i]:
            buy_signals[dates[i]] = closes[i]
        
        # SMA kirtimo signalas: SMA20 kerta SMA50 iš viršaus į apačią (Death Cross) - pardavimo signalas
        elif sma20[i-1] >= sma50[i-1] and sma20[i] < sma50[i]:
            sell_signals[dates[i]] = closes[i]
    
    # Ieškome signalų pagal RSI
    for i in range(1, len(dates)):
        # Tikriname ar yra pakankamai duomenų
        if rsi[i] is None or rsi[i-1] is None:
            continue
        
        # RSI signalai: RSI kyla virš 30 iš persipardavimo zonos - pirkimo signalas
        if rsi[i-1] <= 30 and rsi[i] > 30:
            buy_signals[dates[i]] = closes[i]
        
        # RSI signalai: RSI krenta žemiau 70 iš persipirkimo zonos - pardavimo signalas
        elif rsi[i-1] >= 70 and rsi[i] < 70:
            sell_signals[dates[i]] = closes[i]
    
    return buy_signals, sell_signals

def get_formatted_signals(signals):
    """
    Suformatuoja signalus HTML rodymui
    
    Args:
        signals: Signalų žodynas (data: kaina)
        
    Returns:
        list: Suformatuotų signalų sąrašas
    """
    result = []
    for date, price in signals.items():
        # Tikriname ar data yra string
        if isinstance(date, str):
            date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M')
        else:
            date_obj = date
            
        formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
        result.append({
            'date': formatted_date,
            'price': round(price, 2)
        })
    
    # Rikiuojame pagal datą (naujausią viršuje)
    result.sort(key=lambda x: x['date'], reverse=True)
    
    return result