"""
Žvakių grafikų modulis
--------------------
Šis modulis paruošia duomenis žvakių tipo grafikams ir techniniams indikatoriams.
"""

import random
from datetime import datetime, timedelta

def get_candlestick_data(symbol="BTCUSDT", interval="1h", limit=100):
    """
    Gauna žvakių diagramos duomenis
    
    Args:
        symbol: Prekybos simbolis
        interval: Laiko intervalas (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Įrašų skaičius
        
    Returns:
        dict: Duomenys JSON formatu, tinkamu žvakių grafikui
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
            
            # Simuliuojame kainų pokyčius
            if i > 0:
                # Atidarymą nustatome kaip ankstesnio uždarymo kainą
                open_price = close_prices[i-1]
                
                # Nustatome simuliuotus High/Low pokyčius
                price_volatility = open_price * random.uniform(0.01, 0.05)  # 1-5% svyravimas
                
                # Atsitiktinai nustatome, ar kaina kilo ar krito
                if random.random() > 0.5:  # 50% tikimybė
                    close_price = open_price + random.uniform(0, price_volatility)
                    high_price = close_price + random.uniform(0, price_volatility * 0.5)
                    low_price = open_price - random.uniform(0, price_volatility * 0.3)
                else:
                    close_price = open_price - random.uniform(0, price_volatility)
                    high_price = open_price + random.uniform(0, price_volatility * 0.3)
                    low_price = close_price - random.uniform(0, price_volatility * 0.5)
            else:
                # Pirmam elementui naudojame bazinę kainą
                open_price = base_price
                close_price = base_price + random.uniform(-500, 500)
                high_price = max(open_price, close_price) + random.uniform(10, 200)
                low_price = min(open_price, close_price) - random.uniform(10, 200)
            
            # Užtikriname, kad Low ≤ Open ≤ Close ≤ High (arba Low ≤ Close ≤ Open ≤ High)
            low_price = min(low_price, open_price, close_price)
            high_price = max(high_price, open_price, close_price)
            
            # Pridedame į sąrašus
            open_prices.append(open_price)
            high_prices.append(high_price)
            low_prices.append(low_price)
            close_prices.append(close_price)
            
            # Simuliuojame prekybos kiekius
            volumes.append(random.uniform(10, 100))
        
        # Skaičiuojame techninius indikatorius
        sma20 = calculate_sma(close_prices, 20)
        sma50 = calculate_sma(close_prices, 50)
        rsi = calculate_rsi(close_prices, 14)
        bollinger = calculate_bollinger_bands(close_prices, 20)
        
        # Paruošiame rezultatą
        result = {
            'labels': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volumes': volumes,
            'sma20': sma20,
            'sma50': sma50,
            'rsi': rsi,
            'bollinger': bollinger
        }
        
        return result
    
    except Exception as e:
        print(f"Klaida gaunant žvakių duomenis: {e}")
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

def calculate_rsi(prices, window=14):
    """
    Skaičiuoja santykinio stiprumo indeksą (RSI)
    
    Args:
        prices: Kainų sąrašas
        window: RSI lango dydis
        
    Returns:
        list: RSI reikšmių sąrašas
    """
    rsi = []
    
    # Pridedame None reikšmes pradžioje
    for i in range(window):
        rsi.append(None)
    
    # Skaičiuojame RSI
    for i in range(window, len(prices)):
        # Skaičiuojame pokyčius
        changes = [prices[j] - prices[j-1] for j in range(i-(window-1), i+1)]
        
        # Atskiriame teigiamus ir neigiamus pokyčius
        gains = [change for change in changes if change > 0]
        losses = [-change for change in changes if change < 0]
        
        # Jei nėra pokyčių, RSI yra 50
        if not gains and not losses:
            rsi.append(50)
            continue
        
        # Skaičiuojame vidutinį kilimą ir kritimą
        avg_gain = sum(gains) / window if gains else 0
        avg_loss = sum(losses) / window if losses else 0
        
        # Apsaugome nuo dalybos iš nulio
        if avg_loss == 0:
            rsi.append(100)
            continue
            
        # Skaičiuojame RS ir RSI
        rs = avg_gain / avg_loss
        rsi_value = 100 - (100 / (1 + rs))
        
        rsi.append(rsi_value)
    
    return rsi

def calculate_bollinger_bands(prices, window=20, num_std=2):
    """
    Skaičiuoja Bollinger juostas
    
    Args:
        prices: Kainų sąrašas
        window: Lango dydis
        num_std: Standartinių nuokrypių skaičius
        
    Returns:
        dict: Viršutinės ir apatinės juostos
    """
    # Skaičiuojame SMA (vidurinė juosta)
    sma = calculate_sma(prices, window)
    
    upper_band = []
    lower_band = []
    
    # Pridedame None reikšmes pradžioje
    for i in range(window - 1):
        upper_band.append(None)
        lower_band.append(None)
    
    # Skaičiuojame viršutinę ir apatinę juostas
    for i in range(window - 1, len(prices)):
        # Skaičiuojame standartinį nuokrypį
        price_window = prices[i-(window-1):i+1]
        mean = sum(price_window) / window
        variance = sum([(p - mean) ** 2 for p in price_window]) / window
        std_dev = variance ** 0.5
        
        # Skaičiuojame juostas
        upper_band.append(sma[i] + (num_std * std_dev))
        lower_band.append(sma[i] - (num_std * std_dev))
    
    return {'upper': upper_band, 'lower': lower_band}