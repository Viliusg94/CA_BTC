"""
Biržos API klientas
-----------------------------
Šis modulis realizuoja sąsają su kriptovaliutų biržos API
realaus laiko duomenims gauti ir prekybos operacijoms vykdyti.
"""

import logging
import time
import hmac
import hashlib
import requests
from datetime import datetime
import websocket
import json
import threading
import pandas as pd

logger = logging.getLogger(__name__)

class ExchangeClient:
    """
    Bazinė klasė darbui su kriptovaliutų biržos API.
    """
    def __init__(self, api_key=None, api_secret=None, exchange="binance"):
        """
        Inicializuoja biržos API klientą.
        
        Args:
            api_key (str): API raktas
            api_secret (str): API slaptas raktas
            exchange (str): Biržos pavadinimas ('binance', 'coinbase', 'kraken')
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = exchange.lower()
        
        # Nustatome API URL pagal pasirinktos biržos pavadinimą
        if self.exchange == "binance":
            self.base_url = "https://api.binance.com"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        elif self.exchange == "coinbase":
            self.base_url = "https://api.exchange.coinbase.com"
            self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        elif self.exchange == "kraken":
            self.base_url = "https://api.kraken.com"
            self.ws_url = "wss://ws.kraken.com"
        else:
            raise ValueError(f"Nepalaikoma birža: {exchange}")
        
        # WebSocket kintamieji
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.data_callbacks = []
        
        logger.info(f"Inicializuotas {self.exchange} API klientas")
    
    def _generate_signature(self, data):
        """
        Sugeneruoja API užklausos parašą.
        
        Args:
            data (str): Duomenys parašui generuoti
            
        Returns:
            str: Sugeneruotas parašas
        """
        if self.api_secret is None:
            return None
            
        if self.exchange == "binance":
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        elif self.exchange == "coinbase":
            timestamp = str(int(time.time()))
            message = timestamp + data
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        else:  # kraken
            timestamp = str(int(time.time() * 1000))
            message = timestamp + data
            signature = hmac.new(
                base64.b64decode(self.api_secret),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
        return signature
    
    def get_ticker(self, symbol):
        """
        Gauna dabartinę kriptovaliutos kainą.
        
        Args:
            symbol (str): Kriptovaliutos simbolis (pvz., 'BTCUSDT')
            
        Returns:
            dict: Kainos informacija
        """
        if self.exchange == "binance":
            endpoint = "/api/v3/ticker/price"
            params = {"symbol": symbol}
        elif self.exchange == "coinbase":
            endpoint = f"/products/{symbol}/ticker"
            params = {}
        else:  # kraken
            endpoint = "/0/public/Ticker"
            params = {"pair": symbol}
        
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Gauta {symbol} kaina: {data}")
            return data
        else:
            logger.error(f"Klaida gaunant kainą: {response.status_code} - {response.text}")
            return None
    
    def get_historical_data(self, symbol, interval="1h", limit=1000):
        """
        Gauna istorinius kriptovaliutos duomenis.
        
        Args:
            symbol (str): Kriptovaliutos simbolis
            interval (str): Laiko intervalas ('1m', '5m', '15m', '1h', '4h', '1d')
            limit (int): Įrašų skaičius
            
        Returns:
            pandas.DataFrame: Istoriniai duomenys
        """
        if self.exchange == "binance":
            endpoint = "/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
        elif self.exchange == "coinbase":
            endpoint = f"/products/{symbol}/candles"
            granularity = {
                "1m": 60, "5m": 300, "15m": 900,
                "1h": 3600, "4h": 14400, "1d": 86400
            }
            params = {
                "granularity": granularity.get(interval, 3600)
            }
        else:  # kraken
            endpoint = "/0/public/OHLC"
            interval_seconds = {
                "1m": 1, "5m": 5, "15m": 15,
                "1h": 60, "4h": 240, "1d": 1440
            }
            params = {
                "pair": symbol,
                "interval": interval_seconds.get(interval, 60)
            }
        
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code != 200:
            logger.error(f"Klaida gaunant istorinius duomenis: {response.status_code} - {response.text}")
            return pd.DataFrame()
        
        data = response.json()
        
        # Apdorojame duomenis pagal skirtingus API formatus
        if self.exchange == "binance":
            # Binance format: [timestamp, open, high, low, close, volume, ...]
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                           'close_time', 'quote_volume', 'trades', 
                                           'taker_buy_base', 'taker_buy_quote', 'ignored'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            # Konvertuojame stulpelius į skaitinius
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
        elif self.exchange == "coinbase":
            # Coinbase format: [timestamp, low, high, open, close, volume]
            df = pd.DataFrame(data, columns=['timestamp', 'low', 'high', 'open', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            
        else:  # kraken
            # Kraken format: [timestamp, open, high, low, close, vwap, volume, count]
            df = pd.DataFrame(data[list(data.keys())[0]], 
                             columns=['timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
        
        return df
    
    def start_websocket(self, symbol, callback=None):
        """
        Pradeda WebSocket ryšį realaus laiko duomenims.
        
        Args:
            symbol (str): Kriptovaliutos simbolis
            callback (function): Funkcija, kuri bus iškviesta gavus naujus duomenis
        """
        if callback:
            self.data_callbacks.append(callback)
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if callback:
                    for cb in self.data_callbacks:
                        cb(data)
            except Exception as e:
                logger.error(f"Klaida apdorojant WebSocket žinutę: {e}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket klaida: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket uždarytas: {close_status_code} - {close_msg}")
            self.running = False
        
        def on_open(ws):
            logger.info(f"WebSocket ryšys atidarytas su {self.exchange}")
            self.running = True
            
            # Prenumeruojame kainų srautą pagal biržą
            if self.exchange == "binance":
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": [f"{symbol.lower()}@ticker"],
                    "id": 1
                }
                ws.send(json.dumps(subscribe_msg))
            elif self.exchange == "coinbase":
                subscribe_msg = {
                    "type": "subscribe",
                    "product_ids": [symbol],
                    "channels": ["ticker"]
                }
                ws.send(json.dumps(subscribe_msg))
            else:  # kraken
                subscribe_msg = {
                    "name": "subscribe",
                    "reqid": 1,
                    "pair": [symbol],
                    "subscription": {"name": "ticker"}
                }
                ws.send(json.dumps(subscribe_msg))
        
        # WebSocket konfigūracija
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Paleidžiame WebSocket atskirame gije
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        logger.info(f"Pradėtas WebSocket ryšys su {self.exchange} simboliui {symbol}")
    
    def stop_websocket(self):
        """
        Sustabdo WebSocket ryšį.
        """
        if self.ws is not None:
            self.ws.close()
            self.running = False
            self.ws = None
            logger.info("WebSocket ryšys uždarytas")
    
    def place_order(self, symbol, side, quantity, price=None, order_type="LIMIT"):
        """
        Pateikia prekybos užsakymą.
        
        Args:
            symbol (str): Kriptovaliutos simbolis
            side (str): Užsakymo pusė ('BUY' arba 'SELL')
            quantity (float): Kiekis
            price (float, optional): Kaina (reikalinga LIMIT užsakymams)
            order_type (str): Užsakymo tipas ('MARKET' arba 'LIMIT')
            
        Returns:
            dict: Užsakymo informacija
        """
        if self.api_key is None or self.api_secret is None:
            logger.error("Nėra API rakto arba slapto rakto")
            return None
        
        try:
            if self.exchange == "binance":
                endpoint = "/api/v3/order"
                params = {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "timestamp": int(time.time() * 1000)
                }
                
                if order_type == "LIMIT":
                    params["price"] = price
                    params["timeInForce"] = "GTC"
                
                # Sugeneruojame parašą
                query_string = '&'.join([f"{key}={params[key]}" for key in params])
                signature = self._generate_signature(query_string)
                params["signature"] = signature
                
                headers = {"X-MBX-APIKEY": self.api_key}
                
                response = requests.post(f"{self.base_url}{endpoint}", params=params, headers=headers)
            
            elif self.exchange == "coinbase":
                endpoint = "/orders"
                
                data = {
                    "product_id": symbol,
                    "side": side.lower(),
                    "size": str(quantity)
                }
                
                if order_type == "LIMIT":
                    data["type"] = "limit"
                    data["price"] = str(price)
                    data["time_in_force"] = "GTC"
                else:
                    data["type"] = "market"
                
                timestamp = str(int(time.time()))
                signature = self._generate_signature(timestamp + "POST" + endpoint + json.dumps(data))
                
                headers = {
                    "CB-ACCESS-KEY": self.api_key,
                    "CB-ACCESS-SIGN": signature,
                    "CB-ACCESS-TIMESTAMP": timestamp,
                    "Content-Type": "application/json"
                }
                
                response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=headers)
            
            else:  # kraken
                endpoint = "/0/private/AddOrder"
                
                data = {
                    "pair": symbol,
                    "type": side.lower(),
                    "ordertype": "limit" if order_type == "LIMIT" else "market",
                    "volume": str(quantity),
                    "nonce": str(int(time.time() * 1000))
                }
                
                if order_type == "LIMIT":
                    data["price"] = str(price)
                
                signature = self._generate_signature("/0/private/AddOrder" + json.dumps(data))
                
                headers = {
                    "API-Key": self.api_key,
                    "API-Sign": signature
                }
                
                response = requests.post(f"{self.base_url}{endpoint}", data=data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Užsakymas pateiktas: {data}")
                return data
            else:
                logger.error(f"Klaida pateikiant užsakymą: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Klaida pateikiant užsakymą: {e}")
            return None