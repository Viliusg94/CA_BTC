"""
Realaus laiko prekybos paleidimo skriptas
------------------------------------------
Šis skriptas paleidžia realaus laiko prekybos valdiklį
kriptovaliutų prekybai.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
import json

# Nustatome, kad būtų naudojamas teisingas kelias iki projekto modulių
sys.path.append('d:/CA_BTC')

from core.app import App
from trading.realtime_trading_controller import RealtimeTradingController

# Konfigūruojame logerį
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/realtime_trading.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_api_keys(file_path):
    """
    Įkrauna API raktus iš failo.
    
    Args:
        file_path (str): Failo kelias
    
    Returns:
        tuple: (api_key, api_secret)
    """
    try:
        with open(file_path, 'r') as f:
            keys = json.load(f)
            return keys.get('api_key'), keys.get('api_secret')
    except Exception as e:
        logger.error(f"Klaida įkraunant API raktus: {e}")
        return None, None

def setup_directories():
    """
    Sukuria reikalingus katalogus, jei jų nėra.
    """
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    os.makedirs("data/realtime", exist_ok=True)

def main():
    """
    Pagrindinis realaus laiko prekybos paleidimo funkcija.
    """
    parser = argparse.ArgumentParser(description="Realaus laiko kriptovaliutų prekyba")
    parser.add_argument('--config', type=str, default="config/trading_config.json", help="Konfigūracijos failo kelias")
    parser.add_argument('--keys', type=str, default="config/api_keys.json", help="API raktų failo kelias")
    parser.add_argument('--exchange', type=str, default="binance", choices=['binance', 'coinbase', 'kraken'], help="Kriptovaliutų birža")
    parser.add_argument('--symbol', type=str, default="BTCUSDT", help="Kriptovaliutos simbolis")
    parser.add_argument('--paper', action='store_true', help="Naudoti 'paper trading' režimą (be tikrų operacijų)")
    
    args = parser.parse_args()
    
    # Sukuriame reikalingus katalogus
    setup_directories()
    
    # Įkrauname API raktus
    api_key, api_secret = load_api_keys(args.keys)
    
    if not api_key or not api_secret:
        logger.warning("API raktai neįkrauti. Veiks tik 'paper trading' režimas.")
    
    # Inicializuojame aplikaciją
    app = App()
    
    # Gauname duomenų bazės sesiją
    db_session = app.container.get_session()
    
    try:
        # Inicializuojame realaus laiko prekybos valdiklį
        controller = RealtimeTradingController(
            api_key=api_key,
            api_secret=api_secret,
            exchange=args.exchange,
            db_session=db_session,
            config_file=args.config
        )
        
        # Nustatome prekybos režimą
        if args.paper:
            controller.set_trading_mode('paper')
        
        # Pradžioje prekyba išjungta
        controller.enable_trading(False)
        
        # Paleidžiame valdiklį
        controller.start()
        
        # Spausdiname instrukcijas
        print("\n=== Realaus laiko prekybos valdiklis aktyvuotas ===")
        print("Valdymo komandos:")
        print("  1 - Įjungti/išjungti prekybą")
        print("  2 - Perjungti prekybos režimą (paper/live)")
        print("  3 - Rodyti dabartinę būseną")
        print("  q - Išeiti")
        
        # Pagrindinis komandų ciklas
        while True:
            command = input("\nĮveskite komandą: ")
            
            if command.lower() == 'q':
                break
            
            if command == '1':
                enabled = not controller.trade_enabled
                controller.enable_trading(enabled)
                print(f"Prekyba {'įjungta' if enabled else 'išjungta'}")
            
            elif command == '2':
                new_mode = 'live' if controller.trading_mode == 'paper' else 'paper'
                controller.set_trading_mode(new_mode)
                print(f"Prekybos režimas pakeistas į: {new_mode}")
            
            elif command == '3':
                status = controller.get_status()
                print("\n=== Dabartinė būsena ===")
                print(f"Veikia: {'Taip' if status['running'] else 'Ne'}")
                print(f"Prekyba įjungta: {'Taip' if status['trade_enabled'] else 'Ne'}")
                print(f"Prekybos režimas: {status['trading_mode']}")
                print(f"Simbolis: {status['symbol']}")
                print(f"Paskutinė kaina: {status['last_price']}")
                
                if 'portfolio' in status:
                    print(f"Balansas: {status['portfolio']['balance']:.2f} USD")
                    print(f"BTC kiekis: {status['portfolio']['btc_amount']:.8f} BTC")
                
                if status['last_decision']:
                    print(f"Paskutinis sprendimas: {status['last_decision']['action']} - {status['last_decision'].get('amount', 0)}")
            
            else:
                print("Nežinoma komanda")
        
        # Sustabdome valdiklį
        controller.stop()
        
    except KeyboardInterrupt:
        print("\nPrograma nutraukta vartotojo")
    except Exception as e:
        logger.error(f"Klaida vykdant realaus laiko prekybą: {e}")
    finally:
        # Išvalome resursus
        app.cleanup()
        print("Programa baigta.")

if __name__ == "__main__":
    main()