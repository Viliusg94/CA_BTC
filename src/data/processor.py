# src/data/processor.py
import pandas as pd
import numpy as np
import os
import ta  # Use ta library instead of talib
from sqlalchemy import text
from database.models import init_db, BtcPriceData, TechnicalIndicator, AdvancedFeature
from database.repository import BtcPriceRepository, TechnicalIndicatorRepository, AdvancedFeatureRepository

def process_btc_data():
    """
    Apdoroja Bitcoin duomenis:
    1. Valymas (anomalijų šalinimas)
    2. Techniniai indikatoriai
    3. Pažangių ypatybių inžinerija
    4. Duomenų transformavimas
    
    Returns:
        pandas.DataFrame: Apdoroti duomenys arba None jei įvyksta klaida
    """
    print("Apdorojami BTC duomenys...")
    
    # Inicializuojame duomenų bazės prisijungimą
    engine, session = init_db()
    btc_repo = BtcPriceRepository(session)
    
    try:
        # Gauname visus BTC kainos duomenis iš duomenų bazės
        all_price_data = btc_repo.get_all()
        
        if not all_price_data:
            print("Duomenų bazėje nėra kainų duomenų. Pirmiausia paleiskite duomenų rinkimą.")
            return None
        
        # Konvertuojame į pandas DataFrame
        df = pd.DataFrame([
            {
                'timestamp': item.timestamp,
                'Open': item.open,
                'High': item.high,
                'Low': item.low,
                'Close': item.close,
                'Volume': item.volume,
                'id': item.id  # Reikalinga ryšiams su kitomis lentelėmis
            }
            for item in all_price_data
        ])
        
        # Nustatome timestamp kaip indeksą
        df.set_index('timestamp', inplace=True)
        
        # 1. Duomenų valymas
        df = clean_data(df)
        
        # 2. Techninių indikatorių skaičiavimas
        df = calculate_technical_indicators(df)
        
        # 3. Pažangių ypatybių inžinerija
        df = create_advanced_features(df)
        
        # 4. Duomenų transformavimas
        df = transform_data_for_models(df)
        
        # Sukuriame direktoriją jei jos nėra
        os.makedirs('data/processed', exist_ok=True)
        
        # Išsaugome apdorotus duomenis CSV faile (analizei ir vizualizacijai)
        processed_data_path = "data/processed/btc_features.csv"
        df.to_csv(processed_data_path)
        print(f"Apdoroti duomenys išsaugoti: {processed_data_path}")
        
        return df
    
    except Exception as e:
        print(f"Klaida apdorojant duomenis: {e}")
        return None
    
    finally:
        session.close()

def clean_data(df):
    """
    Valo duomenis:
    - Pašalina anomalijas
    - Tvarko trūkstamas reikšmes
    """
    print("Valomi duomenys...")
    
    # Kopijuojame duomenis, kad nemodifikuotume originalo
    data = df.copy()
    
    # Pašaliname eilutes su NaN
    data.dropna(inplace=True)
    
    # Pašaliname dublikatus
    data = data[~data.index.duplicated(keep='first')]
    
    # Sortiruojame pagal datą
    data.sort_index(inplace=True)
    
    # Pašaliname anomalijas (pvz., kainos nukrypusios daugiau nei 3 std)
    z_score = (data['Close'] - data['Close'].mean()) / data['Close'].std()
    data = data[abs(z_score) <= 3]
    
    print(f"Duomenys išvalyti: prieš={len(df)}, po={len(data)} eilutės")
    
    return data

def calculate_technical_indicators(df):
    """
    Apskaičiuoja techninius indikatorius naudojant ta biblioteka
    """
    print("Skaičiuojami techniniai indikatoriai...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Slankieji vidurkiai (SMA)
    data['SMA_7'] = ta.trend.sma_indicator(data['Close'], window=7)
    data['SMA_25'] = ta.trend.sma_indicator(data['Close'], window=25)
    data['SMA_30'] = ta.trend.sma_indicator(data['Close'], window=30)
    data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
    data['SMA_200'] = ta.trend.sma_indicator(data['Close'], window=200)
    
    # Eksponentiniai slankieji vidurkiai (EMA)
    data['EMA_7'] = ta.trend.ema_indicator(data['Close'], window=7)
    data['EMA_14'] = ta.trend.ema_indicator(data['Close'], window=14)
    data['EMA_30'] = ta.trend.ema_indicator(data['Close'], window=30)
    
    # RSI (Santykinis stiprumo indeksas)
    data['RSI_7'] = ta.momentum.rsi(data['Close'], window=7)
    data['RSI_14'] = ta.momentum.rsi(data['Close'], window=14)
    
    # MACD (Judančio vidurkio konvergencijos-divergencijos indikatorius)
    macd = ta.trend.MACD(
        close=data['Close'],
        window_slow=26,
        window_fast=12,
        window_sign=9
    )
    data['MACD'] = macd.macd()
    data['MACD_signal'] = macd.macd_signal()
    data['MACD_hist'] = macd.macd_diff()
    
    # Bollinger Bands (Bolingerio juostos)
    bollinger = ta.volatility.BollingerBands(
        close=data['Close'],
        window=20,
        window_dev=2
    )
    data['Bollinger_upper'] = bollinger.bollinger_hband()
    data['Bollinger_lower'] = bollinger.bollinger_lband()
    data['Bollinger_middle'] = bollinger.bollinger_mavg()
    
    # ATR (Vidutinis tikrasis diapazonas)
    data['ATR_14'] = ta.volatility.average_true_range(
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        window=14
    )
    
    # OBV (On-Balance Volume)
    data['OBV'] = ta.volume.on_balance_volume(data['Close'], data['Volume'])
    
    # Volume SMA
    data['Volume_SMA20'] = ta.trend.sma_indicator(data['Volume'], window=20)
    
    # ADX (Vidutinis kryptinis indeksas)
    data['ADX_14'] = ta.trend.adx(
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        window=14
    )
    
    # Pašaliname eilutes su NaN, kurios atsirado skaičiuojant indikatorius
    data.dropna(inplace=True)
    
    print(f"Techniniai indikatoriai apskaičiuoti. Eilučių skaičius: {len(data)}")
    
    return data

def create_advanced_features(df):
    """
    Sukuria pažangias ypatybes
    """
    print("Kuriamos pažangios ypatybės...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # 1. Lag požymiai (praėjusių periodų kainos)
    for lag in [1, 3, 7, 14, 30]:
        data[f'Close_lag{lag}'] = data['Close'].shift(lag)
    
    # 2. Krypties indikatoriai
    # Krypties indikatorius: 1 (kyla), 0 (nekinta), -1 (krenta)
    data['trend_1d'] = np.sign(data['Close'].diff(1))
    data['trend_3d'] = np.sign(data['Close'].diff(3))
    data['trend_7d'] = np.sign(data['Close'].diff(7))
    
    # 3. Sezoniniai požymiai
    data['day_of_week'] = data.index.dayofweek
    data['month'] = data.index.month
    data['quarter'] = data.index.quarter
    data['is_weekend'] = (data.index.dayofweek >= 5).astype(int)
    
    # 4. Kintamumo (volatility) indikatoriai
    # Kintamumas (standartinis nuokrypis per pasirinktą periodą)
    data['volatility_7d'] = data['Close'].pct_change().rolling(window=7).std()
    data['volatility_14d'] = data['Close'].pct_change().rolling(window=14).std()
    data['volatility_30d'] = data['Close'].pct_change().rolling(window=30).std()
    
    # 5. Grąžos požymiai
    data['return_1d'] = data['Close'].pct_change(1)
    data['return_3d'] = data['Close'].pct_change(3)
    data['return_7d'] = data['Close'].pct_change(7)
    
    # Pašaliname eilutes su NaN, kurios atsirado kuriant naujus požymius
    data.dropna(inplace=True)
    
    print(f"Pažangios ypatybės sukurtos. Eilučių skaičius: {len(data)}")
    
    return data

def transform_data_for_models(df):
    """
    Transformuoja duomenis mašininio mokymosi modeliams
    """
    print("Transformuojami duomenys modeliams...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Sukuriame tikslo (target) kintamuosius
    # 1. Krypties prognozė (1-kils, 0-kris)
    data['target_direction_1d'] = (data['Close'].shift(-1) > data['Close']).astype(int)
    data['target_direction_3d'] = (data['Close'].shift(-3) > data['Close']).astype(int)
    data['target_direction_7d'] = (data['Close'].shift(-7) > data['Close']).astype(int)
    
    # 2. Procentinis kainos pokytis
    data['target_return_1d'] = data['Close'].pct_change(-1)  # Sekančios dienos grąža
    data['target_return_3d'] = data['Close'].pct_change(-3)  # 3 dienų grąža
    data['target_return_7d'] = data['Close'].pct_change(-7)  # 7 dienų grąža
    
    # One-hot encoding kategoriniams kintamiesiems
    # Day of week (0-6)
    for i in range(7):
        data[f'day_{i}'] = (data['day_of_week'] == i).astype(int)
    
    # Month (1-12)
    for i in range(1, 13):
        data[f'month_{i}'] = (data['month'] == i).astype(int)
    
    # Pašaliname eilutes su NaN, kurios atsirado transformuojant duomenis
    data.dropna(inplace=True)
    
    print(f"Duomenys transformuoti modeliams. Eilučių skaičius: {len(data)}")
    
    return data

if __name__ == "__main__":
    process_btc_data()