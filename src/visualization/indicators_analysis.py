import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
from database.models import init_db
from database.repository import BtcPriceRepository, TechnicalIndicatorRepository

def find_best_indicators(df, target='Close', shift=1, correlation_threshold=0.3, save_path="data/processed/best_indicators.png"):
    """
    Randa geriausius indikatorius prognozavimui pagal koreliaciją su būsimomis kainomis
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su indikatoriais
        target (str): Stulpelis, kurį bandome prognozuoti
        shift (int): Kiek periodų į priekį žiūrime
        correlation_threshold (float): Minimalus koreliacijos slenkstis
        save_path (str): Kelias, kur išsaugoti grafiką
        
    Returns:
        pandas.Series: Indikatorių koreliacijos su būsimomis kainomis
    """
    print(f"Ieškome geriausių indikatorių {shift} periodų prognozei...")
    
    # Sukuriame tikslinį stulpelį - kainą po N periodų
    df_shifted = df.copy()
    df_shifted[f'future_{target}_{shift}'] = df_shifted[target].shift(-shift)
    
    # Pašaliname NaN reikšmes
    df_shifted = df_shifted.dropna()
    
    # Apskaičiuojame koreliacijas
    future_target = f'future_{target}_{shift}'
    correlations = df_shifted.corr()[future_target].drop(future_target)
    
    # Rūšiuojame pagal absoliučią koreliaciją
    abs_correlations = correlations.abs().sort_values(ascending=False)
    
    # Atfiltruojame tik indikatorius (be kainų stulpelių)
    price_columns = ['Open', 'High', 'Low', 'Close', 'Volume', future_target]
    indicator_correlations = abs_correlations[~abs_correlations.index.isin(price_columns)]
    
    # Atrenkame indikatorius, kurių koreliacija didesnė už slenkstį
    strong_indicators = indicator_correlations[indicator_correlations > correlation_threshold]
    
    # Vizualizuojame rezultatus
    plt.figure(figsize=(12, 8))
    
    # Sukuriame baras su spalvomis pagal koreliacijos stiprumą
    bars = plt.barh(
        y=strong_indicators.index,
        width=strong_indicators.values,
        color=plt.cm.RdYlGn(strong_indicators.values)
    )
    
    plt.title(f'Geriausi indikatoriai {shift} periodų prognozavimui', fontsize=16)
    plt.xlabel('Absoliuti koreliacija', fontsize=12)
    plt.ylabel('Indikatoriai', fontsize=12)
    plt.grid(axis='x', alpha=0.3)
    
    # Pridedame vertės etiketes ant barų
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.01, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
                 va='center', fontsize=9)
    
    plt.tight_layout()
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300)
        print(f"Geriausių indikatorių grafikas išsaugotas: {save_path}")
    
    plt.close()
    
    return correlations

def analyze_reversal_patterns(df, window=90, save_path="data/processed/reversal_patterns.png"):
    """
    Analizuoja galimus kainos reversalo (apsisukimo) modelius pagal RSI ir MACD indikatorius
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su indikatoriais
        window (int): Laikotarpis, kurį analizuojame
        save_path (str): Kelias, kur išsaugoti grafiką
    """
    print("Analizuojame galimus kainos apsisukimo taškus...")
    
    # Naudojame paskutinius N dienų duomenis
    if len(df) > window:
        data = df.iloc[-window:].copy()
    else:
        data = df.copy()
    
    # Sukuriame reversalo sąlygas
    # Perkupimas (RSI > 70 ir krenta)
    data['rsi_overbought'] = (data['RSI_14'] > 70) & (data['RSI_14'].diff() < 0)
    
    # Perpardavimas (RSI < 30 ir kyla)
    data['rsi_oversold'] = (data['RSI_14'] < 30) & (data['RSI_14'].diff() > 0)
    
    # MACD kryžiavimas (signalo linija kerta MACD iš viršaus į apačią)
    data['macd_bearish_cross'] = (data['MACD'] < data['MACD_signal']) & (data['MACD'].shift(1) > data['MACD_signal'].shift(1))
    
    # MACD kryžiavimas (signalo linija kerta MACD iš apačios į viršų)
    data['macd_bullish_cross'] = (data['MACD'] > data['MACD_signal']) & (data['MACD'].shift(1) < data['MACD_signal'].shift(1))
    
    # Vizualizacija
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    
    # Kainos grafikas
    ax1.plot(data.index, data['Close'], label='BTC kaina', color='black')
    
    # Pažymime reversalo taškus
    # Perkupimo taškai (potencialus kritimas)
    overbought_idx = data[data['rsi_overbought']].index
    ax1.scatter(overbought_idx, data.loc[overbought_idx, 'Close'], 
                color='red', s=100, marker='v', label='Perkupimas (RSI)')
    
    # Perpardavimo taškai (potencialus kilimas)
    oversold_idx = data[data['rsi_oversold']].index
    ax1.scatter(oversold_idx, data.loc[oversold_idx, 'Close'], 
                color='green', s=100, marker='^', label='Perpardavimas (RSI)')
    
    # MACD bearish cross (potencialus kritimas)
    bearish_idx = data[data['macd_bearish_cross']].index
    ax1.scatter(bearish_idx, data.loc[bearish_idx, 'Close'], 
                color='darkred', s=80, marker='x', label='MACD bear cross')
    
    # MACD bullish cross (potencialus kilimas)
    bullish_idx = data[data['macd_bullish_cross']].index
    ax1.scatter(bullish_idx, data.loc[bullish_idx, 'Close'], 
                color='darkgreen', s=80, marker='+', label='MACD bull cross')
    
    ax1.set_title('BTC kaina ir potencialūs apsisukimo taškai', fontsize=16)
    ax1.set_ylabel('Kaina (USD)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # RSI ir MACD grafikas
    ax2.plot(data.index, data['RSI_14'], label='RSI', color='blue')
    ax2.plot(data.index, data['MACD'], label='MACD', color='purple')
    ax2.plot(data.index, data['MACD_signal'], label='MACD signal', color='orange')
    
    ax2.set_title('RSI ir MACD indikatoriai', fontsize=16)
    ax2.set_ylabel('Indikatorių reikšmės', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')
    
    plt.tight_layout()
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300)
        print(f"Reversalo modelių grafikas išsaugotas: {save_path}")
    
    plt.close()

def load_data_with_indicators():
    """
    Įkelia duomenis su techniniais indikatoriais iš duomenų bazės
    
    Returns:
        pandas.DataFrame: Duomenų rinkinys su techniniais indikatoriais
    """
    print("Įkeliami duomenys su techniniais indikatoriais...")
    
    # Inicializuojame duomenų bazės prisijungimą
    engine, session = init_db()
    
    try:
        # Gauname duomenis iš duomenų bazės
        btc_repo = BtcPriceRepository(session)
        
        # Įkeliame kainos duomenis
        price_data = btc_repo.get_all_as_dataframe()
        if price_data.empty:
            print("Nepavyko įkelti duomenų iš duomenų bazės.")
            return None
        
        # Įkeliame techninius indikatorius
        # Čia galima būtų sukurti specialią užklausą, kuri sujungtų kainos duomenis su indikatoriais
        # Bet paprastumo dėlei naudosime CSV failą, jei jis egzistuoja
        
        # Arba grąžiname tik kainos duomenis, jei nėra indikatorių
        return price_data
        
    except Exception as e:
        print(f"Klaida įkeliant duomenis: {e}")
        return None
        
    finally:
        session.close()

def analyze_sma_crossover(df, short_period=7, long_period=25):
    """
    Analizuoja SMA kryžiavimosi signalus
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
        short_period (int): Trumpojo SMA periodas
        long_period (int): Ilgojo SMA periodas
        
    Returns:
        pandas.DataFrame: Duomenų rinkinys su signalais
    """
    print(f"Analizuojami SMA kryžiavimaisi: SMA{short_period} ir SMA{long_period}...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Patikriname, ar yra reikalingi stulpeliai
    short_col = f'SMA_{short_period}'
    long_col = f'SMA_{long_period}'
    
    if short_col not in data.columns or long_col not in data.columns:
        print(f"Trūksta reikalingų SMA stulpelių: {short_col}, {long_col}")
        return None
    
    # Sukuriame signalo stulpelį
    # 1 = pirkimo signalas (trumpasis SMA kerta ilgąjį SMA iš apačios į viršų)
    # -1 = pardavimo signalas (trumpasis SMA kerta ilgąjį SMA iš viršaus į apačią)
    # 0 = nėra signalo
    
    # Inicializuojame signalo stulpelį
    data['SMA_Signal'] = 0
    
    # Skaičiuojame kryžiavimąsi
    data['SMA_Crossover'] = data[short_col] - data[long_col]
    
    # Nustatome signalus
    for i in range(1, len(data)):
        if data['SMA_Crossover'].iloc[i-1] < 0 and data['SMA_Crossover'].iloc[i] > 0:
            # Trumpasis SMA kerta ilgąjį SMA iš apačios į viršų (pirkimo signalas)
            data.loc[data.index[i], 'SMA_Signal'] = 1
        elif data['SMA_Crossover'].iloc[i-1] > 0 and data['SMA_Crossover'].iloc[i] < 0:
            # Trumpasis SMA kerta ilgąjį SMA iš viršaus į apačią (pardavimo signalas)
            data.loc[data.index[i], 'SMA_Signal'] = -1
    
    return data

def analyze_rsi_signals(df, rsi_period=14, overbought=70, oversold=30):
    """
    Analizuoja RSI signalus
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
        rsi_period (int): RSI periodas
        overbought (int): Perpirktumo lygis
        oversold (int): Perparduotumo lygis
        
    Returns:
        pandas.DataFrame: Duomenų rinkinys su signalais
    """
    print(f"Analizuojami RSI{rsi_period} signalai...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Patikriname, ar yra reikalingas stulpelis
    rsi_col = f'RSI_{rsi_period}'
    
    if rsi_col not in data.columns:
        print(f"Trūksta reikalingo RSI stulpelio: {rsi_col}")
        return None
    
    # Sukuriame signalo stulpelį
    # 1 = pirkimo signalas (RSI kerta perparduotumo lygį iš apačios į viršų)
    # -1 = pardavimo signalas (RSI kerta perpirktumo lygį iš viršaus į apačią)
    # 0 = nėra signalo
    
    # Inicializuojame signalo stulpelį
    data['RSI_Signal'] = 0
    
    # Nustatome signalus
    for i in range(1, len(data)):
        if data[rsi_col].iloc[i-1] < oversold and data[rsi_col].iloc[i] > oversold:
            # RSI kerta perparduotumo lygį iš apačios į viršų (pirkimo signalas)
            data.loc[data.index[i], 'RSI_Signal'] = 1
        elif data[rsi_col].iloc[i-1] > overbought and data[rsi_col].iloc[i] < overbought:
            # RSI kerta perpirktumo lygį iš viršaus į apačią (pardavimo signalas)
            data.loc[data.index[i], 'RSI_Signal'] = -1
    
    return data

def analyze_macd_signals(df):
    """
    Analizuoja MACD signalus
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
        
    Returns:
        pandas.DataFrame: Duomenų rinkinys su signalais
    """
    print("Analizuojami MACD signalai...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Patikriname, ar yra reikalingi stulpeliai
    if 'MACD' not in data.columns or 'MACD_signal' not in data.columns:
        print("Trūksta reikalingų MACD stulpelių: MACD, MACD_signal")
        return None
    
    # Sukuriame signalo stulpelį
    # 1 = pirkimo signalas (MACD kerta signalo liniją iš apačios į viršų)
    # -1 = pardavimo signalas (MACD kerta signalo liniją iš viršaus į apačią)
    # 0 = nėra signalo
    
    # Inicializuojame signalo stulpelį
    data['MACD_Signal'] = 0
    
    # Skaičiuojame kryžiavimąsi
    data['MACD_Crossover'] = data['MACD'] - data['MACD_signal']
    
    # Nustatome signalus
    for i in range(1, len(data)):
        if data['MACD_Crossover'].iloc[i-1] < 0 and data['MACD_Crossover'].iloc[i] > 0:
            # MACD kerta signalo liniją iš apačios į viršų (pirkimo signalas)
            data.loc[data.index[i], 'MACD_Signal'] = 1
        elif data['MACD_Crossover'].iloc[i-1] > 0 and data['MACD_Crossover'].iloc[i] < 0:
            # MACD kerta signalo liniją iš viršaus į apačią (pardavimo signalas)
            data.loc[data.index[i], 'MACD_Signal'] = -1
    
    return data

def analyze_bollinger_bands_signals(df):
    """
    Analizuoja Bollinger juostų signalus
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
        
    Returns:
        pandas.DataFrame: Duomenų rinkinys su signalais
    """
    print("Analizuojami Bollinger juostų signalai...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Patikriname, ar yra reikalingi stulpeliai
    if 'Bollinger_upper' not in data.columns or 'Bollinger_lower' not in data.columns:
        print("Trūksta reikalingų Bollinger juostų stulpelių: Bollinger_upper, Bollinger_lower")
        return None
    
    # Sukuriame signalo stulpelį
    # 1 = pirkimo signalas (kaina kirto apatinę juostą iš apačios į viršų)
    # -1 = pardavimo signalas (kaina kirto viršutinę juostą iš viršaus į apačią)
    # 0 = nėra signalo
    
    # Inicializuojame signalo stulpelį
    data['Bollinger_Signal'] = 0
    
    # Nustatome signalus
    for i in range(1, len(data)):
        if data['Close'].iloc[i-1] < data['Bollinger_lower'].iloc[i-1] and data['Close'].iloc[i] > data['Bollinger_lower'].iloc[i]:
            # Kaina kirto apatinę juostą iš apačios į viršų (pirkimo signalas)
            data.loc[data.index[i], 'Bollinger_Signal'] = 1
        elif data['Close'].iloc[i-1] > data['Bollinger_upper'].iloc[i-1] and data['Close'].iloc[i] < data['Bollinger_upper'].iloc[i]:
            # Kaina kirto viršutinę juostą iš viršaus į apačią (pardavimo signalas)
            data.loc[data.index[i], 'Bollinger_Signal'] = -1
    
    return data

def combine_signals(df):
    """
    Sujungia visus signalus į vieną bendrą signalą
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais ir signalais
        
    Returns:
        pandas.DataFrame: Duomenų rinkinys su bendru signalu
    """
    print("Sujungiami visi techninių indikatorių signalai...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Patikriname, ar yra reikalingi stulpeliai
    signal_cols = ['SMA_Signal', 'RSI_Signal', 'MACD_Signal', 'Bollinger_Signal']
    missing_cols = [col for col in signal_cols if col not in data.columns]
    
    if missing_cols:
        print(f"Trūksta reikalingų signalų stulpelių: {', '.join(missing_cols)}")
        # Sukuriame trūkstamus stulpelius su 0 reikšmėmis
        for col in missing_cols:
            data[col] = 0
    
    # Sukuriame bendro signalo stulpelį
    # Balsavimo sistema: kiekvienas indikatorius turi po vieną balsą
    # Jei daugiau teigiamų balsų - pirkimo signalas (1)
    # Jei daugiau neigiamų balsų - pardavimo signalas (-1)
    # Jei balsai lygūs - nėra signalo (0)
    
    # Sumuojame visus signalus
    data['Combined_Signal_Sum'] = data[signal_cols].sum(axis=1)
    
    # Nustatome bendrą signalą
    data['Combined_Signal'] = 0
    data.loc[data['Combined_Signal_Sum'] > 0, 'Combined_Signal'] = 1
    data.loc[data['Combined_Signal_Sum'] < 0, 'Combined_Signal'] = -1
    
    return data

def run_indicators_analysis():
    """
    Paleidžia visą techninių indikatorių analizę
    
    Returns:
        pandas.DataFrame: Duomenų rinkinys su techniniais indikatoriais ir signalais
    """
    print("Pradedama techninių indikatorių analizė...")
    
    # Įkeliame duomenis
    data = load_data_with_indicators()
    if data is None:
        print("Nepavyko įkelti duomenų. Analizė nutraukiama.")
        return None
    
    # Analizuojame SMA kryžiavimąsi
    data = analyze_sma_crossover(data)
    if data is None:
        print("Nepavyko analizuoti SMA kryžiavimosi. Analizė nutraukiama.")
        return None
    
    # Analizuojame RSI signalus
    data = analyze_rsi_signals(data)
    if data is None:
        print("Nepavyko analizuoti RSI signalų. Analizė nutraukiama.")
        return None
    
    # Analizuojame MACD signalus
    data = analyze_macd_signals(data)
    if data is None:
        print("Nepavyko analizuoti MACD signalų. Analizė nutraukiama.")
        return None
    
    # Analizuojame Bollinger juostų signalus
    data = analyze_bollinger_bands_signals(data)
    if data is None:
        print("Nepavyko analizuoti Bollinger juostų signalų. Analizė nutraukiama.")
        return None
    
    # Sujungiame visus signalus
    data = combine_signals(data)
    if data is None:
        print("Nepavyko sujungti signalų. Analizė nutraukiama.")
        return None
    
    print("Techninių indikatorių analizė baigta.")
    
    # Išsaugome analizės rezultatus
    os.makedirs('data/analysis', exist_ok=True)
    data.to_csv('data/analysis/signals.csv')
    print("Analizės rezultatai išsaugoti: data/analysis/signals.csv")
    
    return data

if __name__ == "__main__":
    # Paleidžiame analizę
    data = run_indicators_analysis()
    if data is not None:
        print(f"Analizės rezultatai: {len(data)} eilutės")