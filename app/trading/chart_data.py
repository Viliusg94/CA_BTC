"""
Grafikų duomenų modulis
----------------------
Šis modulis paruošia duomenis grafikams ir indikatorių vizualizacijoms.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random  # Tik pavyzdinių duomenų generavimui

def get_price_data(symbol="BTCUSDT", interval="1h", limit=100):
    """
    Gauna kainos duomenis grafikui
    
    Args:
        symbol: Prekybos simbolis
        interval: Laiko intervalas (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Įrašų skaičius
        
    Returns:
        dict: Duomenys JSON formatu, tinkamu Chart.js
    """
    try:
        # Čia būtų tikras API užklausimas
        # Šiuo atveju generuojame pavyzdinius duomenis
        
        # Pavyzdinė pradinė kaina
        base_price = 50000
        
        # Datos generavimas
        end_date = datetime.now()
        
        # Intervalo konvertavimas į minutes
        if interval.endswith('m'):
            minutes = int(interval[:-1])
        elif interval.endswith('h'):
            minutes = int(interval[:-1]) * 60
        elif interval.endswith('d'):
            minutes = int(interval[:-1]) * 24 * 60
        else:
            minutes = 60  # Numatytasis 1h
        
        # Duomenų generavimas
        dates = []
        prices = []
        volumes = []
        
        for i in range(limit):
            current_date = end_date - timedelta(minutes=minutes * (limit - i - 1))
            dates.append(current_date.strftime('%Y-%m-%d %H:%M'))
            
            # Simuliuojame kainų pokyčius (random walk)
            if i > 0:
                price_change = random.uniform(-500, 500)  # Kainos pokytis
                new_price = prices[-1] + price_change
                prices.append(max(10000, new_price))  # Kaina nebus žemesnė nei 10000
            else:
                prices.append(base_price)
            
            # Simuliuojame prekybos kiekius
            volumes.append(random.uniform(10, 100))
        
        # Skaičiuojame 20 periodu slenkantį vidurkį
        sma_20 = calculate_sma(prices, 20)
        
        # Skaičiuojame 50 periodų slenkantį vidurkį
        sma_50 = calculate_sma(prices, 50)
        
        # Skaičiuojame MACD
        macd, signal = calculate_macd(prices)
        
        # Skaičiuojame Bollinger juostas
        middle_band, upper_band, lower_band = calculate_bollinger_bands(prices)
        
        # Skaičiuojame RSI
        rsi = calculate_rsi(prices)
        
        # Simuliuojame prekybos signalus
        buy_signals, sell_signals = generate_signals(dates, prices)
        
        # Paruošiame rezultatą
        result = {
            'labels': dates,
            'prices': prices,
            'volumes': volumes,
            'sma20': sma_20,
            'sma50': sma_50,
            'macd': macd,
            'signal': signal,
            'bollingerMiddle': middle_band,
            'bollingerUpper': upper_band,
            'bollingerLower': lower_band,
            'rsi': rsi,
            'buySignals': buy_signals,
            'sellSignals': sell_signals
        }
        
        return result
    
    except Exception as e:
        print(f"Klaida gaunant kainos duomenis: {e}")
        return {'error': str(e)}

def calculate_sma(prices, window):
    """
    Skaičiuoja paprastą slenkantį vidurkį (SMA)
    
    Args:
        prices: Kainų sąrašas
        window: Lango dydis
        
    Returns:
        list: SMA reikšmių sąrašas
    """
    sma = []
    
    # Pridedame None reikšmes pradžioje
    for i in range(window - 1):
        sma.append(None)
    
    # Skaičiuojame SMA
    for i in range(window - 1, len(prices)):
        window_avg = sum(prices[i-(window-1):i+1]) / window
        sma.append(window_avg)
    
    return sma

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Skaičiuoja MACD (Moving Average Convergence Divergence)
    
    Args:
        prices: Kainų sąrašas
        fast: Greito EMA periodų skaičius
        slow: Lėto EMA periodų skaičius
        signal: Signalo linijos periodų skaičius
        
    Returns:
        tuple: (MACD linija, Signalo linija)
    """
    # Dėl paprastumo, naudojame SMA vietoj EMA
    macd_line = []
    signal_line = []
    
    # Pridedame None reikšmes pradžioje
    for i in range(slow - 1):
        macd_line.append(None)
    
    # Skaičiuojame MACD
    for i in range(slow - 1, len(prices)):
        fast_avg = sum(prices[i-(fast-1):i+1]) / fast
        slow_avg = sum(prices[i-(slow-1):i+1]) / slow
        macd_line.append(fast_avg - slow_avg)
    
    # Pridedame None reikšmes signalo linijai
    for i in range(slow - 1 + signal - 1):
        signal_line.append(None)
    
    # Skaičiuojame signalo liniją
    for i in range(slow - 1 + signal - 1, len(prices)):
        macd_window = macd_line[i-(signal-1):i+1]
        # Pašaliname None reikšmes
        macd_window = [x for x in macd_window if x is not None]
        if macd_window:
            signal_avg = sum(macd_window) / len(macd_window)
            signal_line.append(signal_avg)
        else:
            signal_line.append(None)
    
    return macd_line, signal_line

def calculate_bollinger_bands(prices, window=20, num_std=2):
    """
    Skaičiuoja Bollinger juostas
    
    Args:
        prices: Kainų sąrašas
        window: Periodų skaičius
        num_std: Standartinių nuokrypių skaičius
        
    Returns:
        tuple: (Vidurinė juosta, Viršutinė juosta, Apatinė juosta)
    """
    try:
        # Vektorius numpy formatu
        prices_array = np.array(prices)
        
        # Inicializuojame rezultatų masyvus
        middle_band = [None] * len(prices)
        upper_band = [None] * len(prices)
        lower_band = [None] * len(prices)
        
        # Skaičiuojame juostas
        for i in range(window - 1, len(prices)):
            window_slice = prices_array[i-(window-1):i+1]
            
            # Vidurinė juosta (SMA)
            middle = np.mean(window_slice)
            middle_band[i] = middle
            
            # Standartinis nuokrypis
            std = np.std(window_slice)
            
            # Viršutinė ir apatinė juostos
            upper_band[i] = middle + (std * num_std)
            lower_band[i] = middle - (std * num_std)
        
        return (middle_band, upper_band, lower_band)
    
    except Exception as e:
        print(f"Klaida skaičiuojant Bollinger juostas: {e}")
        return ([None] * len(prices), [None] * len(prices), [None] * len(prices))

def calculate_rsi(prices, window=14):
    """
    Skaičiuoja RSI (Relative Strength Index)
    
    Args:
        prices: Kainų sąrašas
        window: Periodų skaičius
        
    Returns:
        list: RSI reikšmių sąrašas
    """
    try:
        # Inicializuojame rezultatų masyvą
        rsi_values = [None] * len(prices)
        
        # Reikia bent window+1 kainų
        if len(prices) <= window:
            return rsi_values
        
        # Skaičiuojame pokyčius
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])
        
        # Inicializuojame gains ir losses
        gains = []
        losses = []
        
        for delta in deltas:
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(delta))
        
        # Pridedame None reikšmes pradžioje
        for i in range(window):
            rsi_values[i] = None
        
        # Skaičiuojame pirmąjį avg_gain ir avg_loss
        avg_gain = sum(gains[:window]) / window
        avg_loss = sum(losses[:window]) / window
        
        # Skaičiuojame RSI
        for i in range(window, len(prices)):
            # Atnaujiname avg_gain ir avg_loss
            avg_gain = (avg_gain * (window - 1) + gains[i-1]) / window
            avg_loss = (avg_loss * (window - 1) + losses[i-1]) / window
            
            # Skaičiuojame RS ir RSI
            if avg_loss == 0:
                rsi_values[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100 - (100 / (1 + rs))
        
        return rsi_values
    
    except Exception as e:
        print(f"Klaida skaičiuojant RSI: {e}")
        return [None] * len(prices)

def generate_signals(dates, prices):
    """
    Generuoja pavyzdinius prekybos signalus
    
    Args:
        dates: Datų sąrašas
        prices: Kainų sąrašas
        
    Returns:
        tuple: (Pirkimo signalai, Pardavimo signalai)
    """
    buy_signals = {}
    sell_signals = {}
    
    # Generuojame kelis atsitiktinius signalus
    for i in range(5):  # 5 pirkimo signalai
        idx = random.randint(10, len(dates) - 10)
        buy_signals[dates[idx]] = prices[idx]
    
    for i in range(5):  # 5 pardavimo signalai
        idx = random.randint(10, len(dates) - 10)
        sell_signals[dates[idx]] = prices[idx]
    
    return buy_signals, sell_signals

def get_portfolio_history(days=30):
    """
    Gauna portfelio vertės istoriją
    
    Args:
        days: Dienų skaičius
        
    Returns:
        dict: Duomenys JSON formatu, tinkamu Chart.js
    """
    # Pavyzdiniai duomenys
    end_date = datetime.now()
    
    dates = []
    portfolio_values = []
    btc_amounts = []
    cash_values = []
    
    initial_value = 10000
    portfolio_value = initial_value
    cash_value = initial_value * 0.7
    
    for i in range(days):
        current_date = end_date - timedelta(days=days-i-1)
        dates.append(current_date.strftime('%Y-%m-%d'))
        
        # Simuliuojame portfelio pokyčius
        daily_change = random.uniform(-0.05, 0.07)  # -5% iki 7% pokytis
        portfolio_value = portfolio_value * (1 + daily_change)
        portfolio_values.append(round(portfolio_value, 2))
        
        # Simuliuojame BTC kiekio pokyčius
        btc_amount = portfolio_value / 50000 * random.uniform(0.8, 1.2)
        btc_amounts.append(round(btc_amount, 6))
        
        # Simuliuojame grynųjų pinigų pokyčius
        cash_change = random.uniform(-0.03, 0.03)  # -3% iki 3% pokytis
        cash_value = cash_value * (1 + cash_change)
        cash_values.append(round(cash_value, 2))
    
    result = {
        'labels': dates,
        'portfolio': portfolio_values,
        'btc': btc_amounts,
        'cash': cash_values
    }
    
    return result

def get_candlestick_data(symbol="BTCUSDT", interval="1h", limit=100):
    """
    Gauna žvakidės duomenis grafikui
    
    Args:
        symbol: Prekybos simbolis
        interval: Laiko intervalas (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Įrašų skaičius
        
    Returns:
        dict: Duomenys JSON formatu, tinkamu Chart.js
    """
    try:
        # Čia būtų tikras API užklausimas
        # Šiuo atveju generuojame pavyzdinius duomenis
        
        # Pavyzdinė pradinė kaina
        base_price = 50000
        
        # Datos generavimas
        end_date = datetime.now()
        
        # Intervalo konvertavimas į minutes
        if interval.endswith('m'):
            minutes = int(interval[:-1])
        elif interval.endswith('h'):
            minutes = int(interval[:-1]) * 60
        elif interval.endswith('d'):
            minutes = int(interval[:-1]) * 24 * 60
        else:
            minutes = 60  # Numatytasis 1h
        
        # Duomenų generavimas
        dates = []
        open_prices = []
        high_prices = []
        low_prices = []
        close_prices = []
        volumes = []
        
        for i in range(limit):
            current_date = end_date - timedelta(minutes=minutes * (limit - i - 1))
            dates.append(current_date.strftime('%Y-%m-%d %H:%M'))
            
            # Simuliuojame kainų pokyčius (random walk)
            if i > 0:
                price_change = random.uniform(-500, 500)  # Kainos pokytis
                new_price = close_prices[-1] + price_change
                close_prices.append(max(10000, new_price))  # Kaina nebus žemesnė nei 10000
            else:
                close_prices.append(base_price)
            
            # Simuliuojame prekybos kiekius
            volumes.append(random.uniform(10, 100))
            
            # Simuliuojame open, high, low
            open_prices.append(close_prices[-1] - random.uniform(-200, 200))
            high_prices.append(close_prices[-1] + random.uniform(0, 300))
            low_prices.append(close_prices[-1] - random.uniform(0, 300))
        
        # Skaičiuojame 20 periodų slenkantį vidurkį
        sma_20 = calculate_sma(close_prices, 20)
        
        # Skaičiuojame 50 periodų slenkantį vidurkį
        sma_50 = calculate_sma(close_prices, 50)
        
        # Skaičiuojame Bollinger juostas
        middle_band, upper_band, lower_band = calculate_bollinger_bands(close_prices)
        
        # Skaičiuojame RSI
        rsi = calculate_rsi(close_prices)
        
        # Paruošiame rezultatą
        result = {
            'labels': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volumes': volumes,
            'sma20': sma_20,
            'sma50': sma_50,
            'middle_band': middle_band,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'rsi': rsi
        }
        
        return result
    
    except Exception as e:
        print(f"Klaida gaunant žvakidės duomenis: {e}")
        return {'error': str(e)}