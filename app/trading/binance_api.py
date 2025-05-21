import requests
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)

def get_candlestick_data(timeframe='1m', interval='1d'):
    """
    Gauna žvakių duomenis iš Binance API arba generuoja pavyzdinius duomenis
    
    :param timeframe: laiko periodas ('1d', '1w', '1m', '3m', '6m', '1y')
    :param interval: laiko intervalas ('1h', '4h', '1d', '1w')
    :return: žvakių duomenų sąrašas
    """
    try:
        # Konvertuojame parametrus į Binance API formatą
        binance_intervals = {
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w',
        }
        
        binance_interval = binance_intervals.get(interval, '1d')
        
        # SVARBU: Padidiname limitus ilgesniems periodams, kad grafikas būtų detalesnis
        if timeframe == '1d':
            limit = 24  # viena diena: 24 valandos
        elif timeframe == '1w':
            limit = 168  # viena savaitė: 7d * 24h = 168 valandos
        elif timeframe == '1m':
            limit = 30  # vienas mėnuo: 30 dienų
        elif timeframe == '3m':
            limit = 90  # trys mėnesiai: 90 dienų
        elif timeframe == '6m':
            limit = 180  # šeši mėnesiai: 180 dienų
        else:  # 1y
            limit = 365  # vieneri metai: 365 dienos
        
        # Jei intervalas valandinis, padidiname limitą atitinkamai
        if interval == '1h' and timeframe not in ['1d']:
            limit = min(1000, limit * 24)  # Binance limitas yra 1000
        
        # API užklausa
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': binance_interval,
            'limit': limit
        }
        
        logger.info(f"Siunčiama užklausa į Binance API: {url} su parametrais {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Apdorojame duomenis
        data = []
        klines = response.json()
        
        for kline in klines:
            timestamp = datetime.fromtimestamp(kline[0] / 1000)
            
            candlestick = {
                'time': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5])
            }
            
            data.append(candlestick)
        
        logger.info(f"Gauta {len(data)} žvakių iš Binance API")
        return data
        
    except Exception as e:
        logger.error(f"Klaida gaunant duomenis iš Binance API: {str(e)}")
        logger.info("Generuojami pavyzdiniai duomenys vietoj realių")
        return generate_mock_data(timeframe, interval)

def generate_mock_data(timeframe='1m', interval='1d'):
    """Generuoja pavyzdinius duomenis, jei API nepasiekiamas"""
    end_date = datetime.now()
    
    # SVARBU: Patiksliname duomenų generavimo logiką
    # Sugeneruojame tinkamą duomenų kiekį pagal timeframe ir interval
    if timeframe == '1d':
        if interval == '1h':
            start_date = end_date - timedelta(days=1)
            periods = 24
            delta = timedelta(hours=1)
        else:
            start_date = end_date - timedelta(days=1)
            periods = 24
            delta = timedelta(hours=1)
    elif timeframe == '1w':
        if interval == '1h':
            start_date = end_date - timedelta(days=7)
            periods = 7 * 24  # 168 valandos
            delta = timedelta(hours=1)
        elif interval == '4h':
            start_date = end_date - timedelta(days=7)
            periods = 7 * 6  # 42 periodai po 4 valandas
            delta = timedelta(hours=4)
        else:
            start_date = end_date - timedelta(days=7)
            periods = 7
            delta = timedelta(days=1)
    elif timeframe == '1m':
        if interval == '1h':
            start_date = end_date - timedelta(days=30)
            periods = min(1000, 30 * 24)  # 720 valandų, bet ne daugiau 1000
            delta = timedelta(hours=1)
        elif interval == '4h':
            start_date = end_date - timedelta(days=30)
            periods = 30 * 6  # 180 periodų po 4 valandas
            delta = timedelta(hours=4)
        elif interval == '1d':
            start_date = end_date - timedelta(days=30)
            periods = 30
            delta = timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=30)
            periods = 4
            delta = timedelta(weeks=1)
    elif timeframe == '3m':
        if interval == '1d':
            start_date = end_date - timedelta(days=90)
            periods = 90
            delta = timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=90)
            periods = 12  # 12 savaičių
            delta = timedelta(weeks=1)
    elif timeframe == '6m':
        if interval == '1d':
            start_date = end_date - timedelta(days=180)
            periods = 180
            delta = timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=180)
            periods = 24  # 24 savaitės
            delta = timedelta(weeks=1)
    else:  # 1y
        if interval == '1d':
            start_date = end_date - timedelta(days=365)
            periods = 365
            delta = timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=365)
            periods = 52  # 52 savaitės
            delta = timedelta(weeks=1)
    
    # Generuojame datas su konkrečiais intervalais
    dates = [end_date - delta * i for i in range(periods)]
    dates.reverse()  # Rūšiuojame nuo seniausių iki naujausių
    
    # Bazinė kaina - artima dabartinei BTC kainai
    base_price = 100000
    volatility = 3000
    
    data = []
    current_price = base_price
    
    for date in dates:
        # Atsitiktinis kainų svyravimas
        price_change = np.random.normal(0, volatility * min(1, delta.total_seconds() / 86400))
        next_price = current_price + price_change
        
        # Atsitiktinės high/low kainos
        high_price = max(current_price, next_price) + abs(np.random.normal(0, volatility * 0.5))
        low_price = min(current_price, next_price) - abs(np.random.normal(0, volatility * 0.5))
        
        data.append({
            'time': date.strftime('%Y-%m-%d %H:%M:%S'),
            'open': round(current_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(next_price, 2),
            'volume': round(np.random.random() * 1000, 2)
        })
        
        current_price = next_price
    
    logger.warning(f"Grąžinami pavyzdiniai duomenys ({len(data)} žvakių su {interval} intervalu)")
    return data