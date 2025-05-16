"""
Duomenų diagnostikos įrankiai
-----------------------------
Šis modulis pateikia įrankius duomenų analizei ir diagnostikai,
padedančius identifikuoti problemas prieš vykdant simuliaciją.
"""

import pandas as pd
import logging
import numpy as np

logger = logging.getLogger(__name__)

def check_required_columns(data, required_columns):
    """
    Patikrina, ar duomenyse yra visi reikalingi stulpeliai.
    
    Args:
        data (pandas.DataFrame): Duomenų rinkinys
        required_columns (list): Reikalingų stulpelių sąrašas
    
    Returns:
        bool: True, jei yra visi reikalingi stulpeliai, False - priešingu atveju
    """
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        logger.warning(f"Trūksta šių stulpelių: {missing_columns}")
        return False
    
    return True

def diagnose_data(data):
    """
    Atlieka detalią duomenų diagnostiką ir grąžina rezultatus.
    
    Args:
        data (pandas.DataFrame): Duomenų rinkinys
    
    Returns:
        dict: Diagnostikos rezultatai
    """
    results = {
        'rows': len(data),
        'columns': len(data.columns),
        'missing_values': {},
        'date_range': (data.index[0], data.index[-1]),
        'time_interval': None,
        'price_range': None,
        'available_indicators': []
    }
    
    # Tikriname, ar yra trūkstamų reikšmių
    for column in data.columns:
        missing = data[column].isna().sum()
        if missing > 0:
            results['missing_values'][column] = missing
    
    # Nustatome laiko intervalą tarp įrašų
    time_diffs = np.diff(data.index)
    if len(time_diffs) > 0:
        most_common_interval = pd.Series(time_diffs).mode()[0]
        results['time_interval'] = str(most_common_interval)
    
    # Tikriname kainų diapazoną
    if 'Close' in data.columns:
        results['price_range'] = (data['Close'].min(), data['Close'].max())
    
    # Nustatome, kokie indikatoriai yra duomenyse
    for column in data.columns:
        # Tipiški indikatorių pavadinimai
        if any(ind in column for ind in ['SMA', 'EMA', 'RSI', 'MACD', 'ATR', 'BB', 'Signal']):
            results['available_indicators'].append(column)
    
    # Patikriname, ar yra prognozių stulpeliai
    if 'predicted_direction' in data.columns:
        results['has_predictions'] = True
        # Tikriname prognozių pasiskirstymą
        if data['predicted_direction'].dtype in [np.int64, np.float64]:
            results['prediction_distribution'] = data['predicted_direction'].value_counts().to_dict()
    else:
        results['has_predictions'] = False
    
    # Spausdiname diagnostikos rezultatus
    logger.info(f"Duomenų diagnostikos rezultatai:")
    logger.info(f"- Eilučių skaičius: {results['rows']}")
    logger.info(f"- Laiko intervalas: nuo {results['date_range'][0]} iki {results['date_range'][1]}")
    logger.info(f"- Tipinis žingsnis: {results['time_interval']}")
    
    if results['missing_values']:
        logger.warning(f"- Yra trūkstamų reikšmių: {results['missing_values']}")
    
    logger.info(f"- Rasti indikatoriai: {', '.join(results['available_indicators'])}")
    
    if not results['has_predictions']:
        logger.warning("- Nėra prognozių stulpelio 'predicted_direction'")
    
    return results

def add_test_signals(data):
    """
    Prideda testavimo signalų stulpelius į duomenis, jei jų trūksta.
    
    Args:
        data (pandas.DataFrame): Duomenų rinkinys
    
    Returns:
        pandas.DataFrame: Duomenys su pridėtais signalų stulpeliais
    """
    # Padarome duomenų kopiją, kad nepakeistume originalių duomenų
    df = data.copy()
    
    # Pridedame paprastą SMA signalą, jei jo nėra
    if 'SMA_Signal' not in df.columns:
        if 'Close' in df.columns:
            # Skaičiuojame 20 periodų SMA
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            # Skaičiuojame 50 periodų SMA
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            # Generuojame signalą: 1 kai trumpas SMA virš ilgo, -1 kai po juo
            df['SMA_Signal'] = np.where(df['SMA_20'] > df['SMA_50'], 0.5, -0.5)
            logger.info("Pridėtas SMA_Signal stulpelis")
    
    # Pridedame RSI signalą, jei jo nėra
    if 'RSI_Signal' not in df.columns:
        if 'Close' in df.columns:
            # Labai supaprastintas RSI skaičiavimas (tik demonstracijai)
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI_14'] = 100 - (100 / (1 + rs))
            # Generuojame signalą: 1 kai RSI < 30 (perparduota), -1 kai RSI > 70 (perpirkta)
            df['RSI_Signal'] = np.where(df['RSI_14'] < 30, 0.7, np.where(df['RSI_14'] > 70, -0.7, 0))
            logger.info("Pridėti RSI_14 ir RSI_Signal stulpeliai")
    
    # Pridedame dirbtines prognozės ir pasitikėjimo stulpelius
    if 'predicted_direction' not in df.columns:
        # Generuojame paprastą prognozę pagal kainą:
        # Jei kaina pakilo per paskutines 3 dienas, prognozuojame kilimą (1)
        # Jei kaina nukrito, prognozuojame kritimą (-1)
        if 'Close' in df.columns:
            price_change = df['Close'].pct_change(3)
            df['predicted_direction'] = np.where(price_change > 0, 1, -1)
            # Pasitikėjimas - kuo didesnis pokytis, tuo didesnis pasitikėjimas (iki 1.0)
            df['confidence'] = np.minimum(np.abs(price_change) * 10, 1.0)
            logger.info("Pridėti predicted_direction ir confidence stulpeliai")
    
    return df