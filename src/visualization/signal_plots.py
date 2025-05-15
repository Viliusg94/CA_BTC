# SUKURTI FAILĄ: d:\CA_BTC\src\visualization\signal_plots.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_signals(df, window=120, save_path="data/analysis/signals_plot.png"):
    """
    Nubraižo kainų grafiką su signalais
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais ir signalais
        window (int): Kiek paskutinių periodų rodyti
        save_path (str): Kelias, kur išsaugoti grafiką
    """
    # Paimame tik paskutinius X periodų
    if len(df) > window:
        data = df.iloc[-window:].copy()
    else:
        data = df.copy()
    
    # Sukuriame grafiką
    plt.figure(figsize=(14, 8))
    
    # Nubraižome kainų grafiką
    plt.plot(data.index, data['Close'], color='black', label='Kaina')
    
    # Pridedame slankiuosius vidurkius
    if 'SMA_7' in data.columns:
        plt.plot(data.index, data['SMA_7'], color='blue', alpha=0.7, label='SMA 7')
    if 'SMA_25' in data.columns:
        plt.plot(data.index, data['SMA_25'], color='orange', alpha=0.7, label='SMA 25')
    
    # Pridedame Bollinger juostas
    if all(col in data.columns for col in ['Bollinger_upper', 'Bollinger_lower']):
        plt.plot(data.index, data['Bollinger_upper'], 'r--', alpha=0.3)
        plt.plot(data.index, data['Bollinger_lower'], 'r--', alpha=0.3)
        plt.fill_between(data.index, data['Bollinger_upper'], data['Bollinger_lower'], 
                         alpha=0.1, color='red')
    
    # Pridedame signalus
    if 'Combined_Signal' in data.columns:
        # Pirkimo signalai (teigiami)
        buy_signals = data[data['Combined_Signal'] == 1]
        if not buy_signals.empty:
            plt.scatter(buy_signals.index, buy_signals['Close'], 
                        color='green', marker='^', s=100, label='Pirkimo signalas')
        
        # Pardavimo signalai (neigiami)
        sell_signals = data[data['Combined_Signal'] == -1]
        if not sell_signals.empty:
            plt.scatter(sell_signals.index, sell_signals['Close'], 
                        color='red', marker='v', s=100, label='Pardavimo signalas')
    
    plt.title('BTC kaina ir signalai')
    plt.xlabel('Data')
    plt.ylabel('Kaina (USD)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"Signalų grafikas išsaugotas: {save_path}")
    
    plt.close()

def plot_signal_comparison(df, save_path="data/analysis/signal_comparison.png"):
    """
    Nubraižo skirtingų signalų palyginimą
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais ir signalais
        save_path (str): Kelias, kur išsaugoti grafiką
    """
    # Patikriname, ar yra reikalingi stulpeliai
    signal_cols = ['SMA_Signal', 'RSI_Signal', 'MACD_Signal', 'Bollinger_Signal', 'Combined_Signal']
    missing_cols = [col for col in signal_cols if col not in df.columns]
    
    if missing_cols:
        print(f"Trūksta reikalingų signalų stulpelių: {', '.join(missing_cols)}")
        return
    
    # Sukuriame grafiką
    plt.figure(figsize=(14, 10))
    
    # Sukuriame 5 subplots
    gs = plt.GridSpec(5, 1, hspace=0.4)
    
    # Kainų grafikas
    ax1 = plt.subplot(gs[0])
    ax1.plot(df.index, df['Close'], color='black')
    ax1.set_title('BTC kaina')
    ax1.set_ylabel('Kaina (USD)')
    ax1.grid(True, alpha=0.3)
    
    # SMA signalai
    ax2 = plt.subplot(gs[1], sharex=ax1)
    ax2.plot(df.index, df['SMA_Signal'], color='blue')
    ax2.set_title('SMA signalai')
    ax2.set_ylabel('Signalas')
    ax2.grid(True, alpha=0.3)
    
    # RSI signalai
    ax3 = plt.subplot(gs[2], sharex=ax1)
    ax3.plot(df.index, df['RSI_Signal'], color='purple')
    ax3.set_title('RSI signalai')
    ax3.set_ylabel('Signalas')
    ax3.grid(True, alpha=0.3)
    
    # MACD signalai
    ax4 = plt.subplot(gs[3], sharex=ax1)
    ax4.plot(df.index, df['MACD_Signal'], color='orange')
    ax4.set_title('MACD signalai')
    ax4.set_ylabel('Signalas')
    ax4.grid(True, alpha=0.3)
    
    # Bendri signalai
    ax5 = plt.subplot(gs[4], sharex=ax1)
    ax5.plot(df.index, df['Combined_Signal'], color='green')
    ax5.set_title('Bendri signalai')
    ax5.set_xlabel('Data')
    ax5.set_ylabel('Signalas')
    ax5.grid(True, alpha=0.3)
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"Signalų palyginimo grafikas išsaugotas: {save_path}")
    
    plt.close()

def create_all_signal_visualizations(df):
    """
    Sukuria visas signalų vizualizacijas
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais ir signalais
    """
    print("Kuriamos signalų vizualizacijos...")
    
    # Sukuriame direktoriją, jei jos nėra
    os.makedirs('data/analysis', exist_ok=True)
    
    # Nubraižome signalus
    plot_signals(df)
    
    # Nubraižome signalų palyginimą
    plot_signal_comparison(df)
    
    print("Signalų vizualizacijos sukurtos.")

if __name__ == "__main__":
    # Įkeliame duomenis
    try:
        signals_path = "data/analysis/signals.csv"
        if os.path.exists(signals_path):
            data = pd.read_csv(signals_path, index_col=0, parse_dates=True)
            create_all_signal_visualizations(data)
        else:
            print(f"Klaida: Nerastas signalų failas {signals_path}")
            print("Pirma paleiskite signalų analizę.")
    except Exception as e:
        print(f"Klaida kuriant signalų vizualizacijas: {e}")