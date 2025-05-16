# src/data/collector.py
import os
import pandas as pd
import datetime
from datetime import timedelta
from dotenv import load_dotenv
from binance.client import Client
from database.models import init_db, BtcPriceData
from database.repository import BtcPriceRepository

def collect_btc_data(start_date=None, end_date=None):
    """
    Renka Bitcoin kainos duomenis iš Binance API ir išsaugo MySQL duomenų bazėje
    
    Args:
        start_date: Pradžios data (str arba datetime)
        end_date: Pabaigos data (str arba datetime)
        
    Returns:
        pandas.DataFrame: Surinktų duomenų DataFrame arba None jei įvyko klaida
    """
    print(f"Renkame BTC duomenis nuo {start_date}")
    
    # Jei nenurodyta pradžios data, naudojame datą prieš metus
    if start_date is None:
        start_date = datetime.datetime.now() - timedelta(days=365)
    elif isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    
    # Jei nenurodyta pabaigos data, naudojame šiandienos datą
    if end_date is None:
        end_date = datetime.datetime.now()
    elif isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    # Konvertuojame į timestamp formatą
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # Įkelti aplinkos kintamuosius iš .env failo
    load_dotenv()

    # Gauti API raktus iš aplinkos kintamųjų
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    # Inicializuojame Binance klientą
    if api_key and api_secret:
        client = Client(api_key, api_secret)
        print("Naudojami Binance API raktai")
    else:
        client = Client()
        print("Nenaudojami Binance API raktai - gali būti taikomi griežtesni apribojimai")
    
    # Gauname kainų duomenis (15 min intervalas)
    # BTCUSDT - Bitcoin/USDT pora
    try:
        klines = client.get_historical_klines(
            symbol="BTCUSDT",
            interval=Client.KLINE_INTERVAL_15MINUTE,
            start_str=start_timestamp,
            end_str=end_timestamp
        )
    except Exception as e:
        print(f"Klaida gaunant duomenis iš Binance: {e}")
        return None
    
    # Konvertuojame duomenis į pandas DataFrame
    columns = ['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 
               'Quote asset volume', 'Number of trades', 'Taker buy base volume', 
               'Taker buy quote volume', 'Ignore']
    
    df = pd.DataFrame(klines, columns=columns)
    
    # Konvertuojame stulpelius į tinkamus duomenų tipus
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = df[col].astype(float)
    
    # Naudojame 'Open time' kaip indeksą
    df.set_index('Open time', inplace=True)
    
    # Pasiliekame tik reikalingus stulpelius
    btc_data = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    # Sukuriame direktoriją, jei jos nėra
    os.makedirs('data/raw', exist_ok=True)
    
    # Išsaugome duomenis CSV formatu (galima palikti kaip atsarginę kopiją)
    btc_data.to_csv("data/raw/btc_data.csv")
    print(f"Duomenys išsaugoti CSV: data/raw/btc_data.csv")
    
    # Išsaugome duomenis į MySQL duomenų bazę
    save_data_to_db(btc_data)
    
    return btc_data

def save_data_to_db(dataframe):
    """
    Išsaugo pandas DataFrame duomenis į MySQL duomenų bazę
    
    Args:
        dataframe (pandas.DataFrame): Duomenų DataFrame su BTC kainomis
    """
    print("Išsaugome duomenis į MySQL duomenų bazę...")
    
    # Inicializuojame duomenų bazę
    engine, session = init_db()
    repo = BtcPriceRepository(session)
    
    try:
        # Sukuriame BtcPriceData objektus
        price_data_list = []
        rows_processed = 0
        rows_added = 0
        
        for idx, row in dataframe.iterrows():
            # Patikriname, ar jau yra įrašas su tokiu laiku
            existing = session.query(BtcPriceData).filter_by(timestamp=idx).first()
            rows_processed += 1
            
            if existing:
                continue
                
            # Kuriame naują įrašą
            price_data = BtcPriceData(
                timestamp=idx,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume']
            )
            price_data_list.append(price_data)
            rows_added += 1
            
            # Periodiškai išsaugome duomenis
            if len(price_data_list) >= 1000:
                repo.add_all(price_data_list)
                price_data_list = []
                print(f"Išsaugota {rows_added} iš {rows_processed} eilučių...")
        
        # Išsaugome likusius duomenis
        if price_data_list:
            repo.add_all(price_data_list)
        
        print(f"Duomenys išsaugoti MySQL duomenų bazėje. Iš viso: {rows_processed} eilutės, naujai pridėta: {rows_added} eilutės.")
    
    except Exception as e:
        print(f"Klaida išsaugant duomenis į MySQL duomenų bazę: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    # Pavyzdinis paleidimas
    btc_data = collect_btc_data()
    print(f"Surinkta {len(btc_data) if btc_data is not None else 0} BTC kainos įrašų.")